---
title: "pytest：Python 测试框架的事实标准，从 assert 反射到 fixture 体系"
date: "2026-06-14T21:13:12+08:00"
slug: "pytest-python-testing-framework-advanced-usage-guide"
description: "pytest 是 13.9k stars 的 Python 测试框架事实标准。从 assert 反射讲起，系统拆解 fixture、parametrize、conftest、插件生态等机制与反模式。"
draft: false
categories: ["技术笔记"]
tags: ["pytest", "Python", "测试框架", "单元测试", "Fixture"]
---

# pytest：Python 测试框架的事实标准，从 assert 反射到 fixture 体系

> pytest 的入门门槛很低，一个 `assert` 就能写测试。但真正让它难以替代的是 fixture 体系、parametrize、conftest.py 加上 1300 多个插件——从一行 demo 到十万级用例的测试工程都能撑住。新手常把它当 unittest 替代品，老手把它当测试编排框架，两种用法并不冲突。

## 阅读前

**这篇文章适合谁？**

| 读者画像 | 建议读法 |
|-----------|----------|
| 刚接触 pytest，想快速跑起来 | 重点看"五分钟快速上手"、"内置常用 fixture"、"Marker 系统" |
| 用过 unittest，想把测试工程迁移到 pytest | 重点看"为什么 pytest 成了事实标准"、"Fixture 体系"、"运行 unittest"、"采用顺序建议" |
| 已经在用 pytest，想写好 fixture 和 parametrize | 重点看"Fixture 体系"、"parametrize"、"conftest.py"、"典型反模式" |
| 团队技术负责人，想统一测试规范 | 重点看"采用顺序建议"、"Marker 系统"、"插件机制"、"小结" |

**读完这篇你能做到：**

- 把 `unittest.TestCase` 改写为 pytest 风格，利用自动发现减少样板代码
- 设计 fixture 依赖图，用 scope 和 factory 模式管理测试资源生命周期
- 用 parametrize 把一组数据展开成独立测试用例，失败时精确定位到具体数据行
- 通过 conftest.py 组织跨文件共享，用 marker 给测试分组，合理引入插件

**目录**

- [一、项目坐标](#一项目坐标)
- [二、为什么 pytest 成了事实标准](#二为什么-pytest-成了事实标准)
- [三、五分钟快速上手](#三五分钟快速上手)
- [四、pytest 机制总览](#四pytest-机制总览)
- [五、Fixture 体系](#五fixture-体系)
- [六、parametrize——数据驱动测试](#六parametrize数据驱动测试)
- [七、conftest.py——跨文件共享](#七conftestpy跨文件共享)
- [八、内置常用 fixture](#八内置常用-fixture)
- [九、Marker 系统](#九marker-系统)
- [十、运行 unittest](#十运行-unittest)
- [十一、一次完整的测试执行过程](#十一次完整的测试执行过程)
- [十二、插件机制](#十二插件机制)
- [十三、典型反模式与避坑建议](#十三典型反模式与避坑建议)
- [十四、什么时候用 pytest，什么时候用别的](#十四什么时候用-pytest什么时候用别的)
- [十五、采用顺序建议](#十五采用顺序建议)
- [十六、小结](#十六小结)
- [进阶路径](#进阶路径)

## 一、项目坐标

| 字段 | 值 |
|------|------|
| 仓库 | [pytest-dev/pytest](https://github.com/pytest-dev/pytest) |
| 主语言 | Python（支持 Python 3.10+ 或 PyPy3） |
| Stars | 13.9k |
| Forks | 3.2k |
| License | MIT |
| 创始人 | Holger Krekel（2004 年至今） |
| 插件数 | 1300+ 外部插件（官方收录列表见 [plugin_list](https://docs.pytest.org/en/latest/reference/plugin_list.html)） |

pytest 的 README 开篇就是定位：**"makes it easy to write small tests, yet scales to support complex functional testing for applications and libraries"**。"easy → scales" 这条承诺贯穿后续所有设计。

## 二、为什么 pytest 成了事实标准

Python 生态里测试框架不止一个：`unittest`（标准库）、`nose2`、`doctest` 都能写测试。pytest 在十几年里几乎一统江湖，原因有三。

**1. 反射式 assert 失败信息。** 这是新手最先感知到的不同。`unittest` 要求你写 `self.assertEqual(a, b)`，pytest 允许直接写 `assert a == b`——pytest 在断言失败时通过 AST（抽象语法树，Abstract Syntax Tree）改写拿到 a、b 的实际值，再做求值对比，打印出"哪个变量、什么值、为什么不等"。

官方 README 给的最小例子：

```python
# content of test_sample.py
def inc(x):
    return x + 1

def test_answer():
    assert inc(3) == 5
```

运行 `pytest` 的输出不是干巴巴的 `AssertionError`，而是：

```
>       assert inc(3) == 5
E       assert 4 == 5
E        +  where 4 = inc(3)
```

`where 4 = inc(3)` 这一行是关键：pytest 把 `inc(3)` 重新求值一遍，告诉你"4 是从哪来的"。这种内省（introspection）在处理嵌套表达式、长链调用、复杂数据结构比较时尤其救命。

**2. 自动发现。** 不需要写 suite、不需要继承 TestCase、不需要注册。pytest 默认扫描当前目录及子目录下文件名匹配 `test_*.py` 或 `*_test.py` 的文件，把其中以 `test_` 开头的函数和 `Test` 开头的类里的 `test_` 方法自动收集为测试用例。这套约定让"加一个测试 = 加一个函数"成为可能。

**3. 插件架构。** pytest 把几乎所有非核心能力都做成插件——`pytest-cov`（覆盖率）、`pytest-mock`（mock 包装）、`pytest-django`（Django 集成）、`pytest-asyncio`（异步测试）、`pytest-xdist`（并行执行）——这 1300+ 插件构成了扩展生态，单元测试到端到端测试都有对应的工具。

assert 反射降低了动笔成本，自动发现减少了样板代码，插件架构覆盖了长尾需求。三者叠加，unittest 在新项目里基本退到了"兼容性选项"的位置。

---

<div style="padding: 12px; border-radius: 6px; background: #f5f7fa; margin: 16px 0;">

**📝 自测：理解了"为什么"吗？**

1. pytest 的 `assert a == b` 和 unittest 的 `self.assertEqual(a, b)` 在失败时输出有什么本质差别？
2. 为什么 `test_answer()` 这个函数名能让 pytest 自动发现它，而不需要注册？
3. 如果有一个 Django 项目，你应该装哪个 pytest 插件？

<details>
<summary>点击查看参考答案</summary>

1. **本质差别**：pytest 通过 AST 改写对 `a` 和 `b` 做二次求值，输出"具体变量的实际值 + 推导链"；unittest 只输出相等性判定失败，不显示变量的推导过程。
2. **原因**：pytest 的测试发现规则是扫描文件名匹配 `test_*.py` 或 `*_test.py` 的文件，从中收集 `test_` 开头的函数。函数命名符合约定就自动被收集。
3. **答案**：`pytest-django`，它提供了 Django 专用的 fixture（如 `client`、`db`、`admin_client` 等）和 Django 集成配置。

</details>

</div>

## 三、五分钟快速上手

### 3.1 安装

```bash
pip install pytest
```

验证安装：

```bash
pytest --version
# pytest 8.x.x
```

### 3.2 第一个测试

```python
# test_sample.py
def inc(x):
    return x + 1

def test_answer():
    assert inc(3) == 4   # 故意写对，演示通过
```

```bash
$ pytest
============================= test session starts ==============================
collected 1 item

test_sample.py .                                                          [100%]

============================== 1 passed in 0.01s ===============================
```

把 `== 4` 改成 `== 5`，再跑一次，你会看到前面那段 `where 4 = inc(3)` 的反射输出。

### 3.3 常用命令行参数

| 参数 | 作用 |
|------|------|
| `pytest` | 递归扫描当前目录 |
| `pytest test_x.py` | 只跑指定文件 |
| `pytest -k "login"` | 按名字关键字过滤 |
| `pytest -m slow` | 按 marker 过滤（需要先注册 marker） |
| `pytest -x` | 遇到第一个失败就停 |
| `pytest --maxfail=3` | 最多累计 N 个失败后停 |
| `pytest -v` | 详细模式（显示每个测试名） |
| `pytest -s` | 不捕获 `print`（`--capture=no`） |
| `pytest --tb=short` | 控制 traceback 详细度（`long`/`short`/`line`/`no`） |
| `pytest -p no:cacheprovider` | 禁用某个插件 |

日常用到的 CLI 参数基本就是这 10 个，剩下的能力都通过 fixture 和插件暴露。

## 四、pytest 机制总览

在深入 fixture 之前，先看一眼 pytest 的机制全家福。下面这张表把 pytest 内部几套主要机制拆开——谁管资源准备、谁管数据展开、谁管共享范围、谁管测试筛选：

| 机制 | 解决什么问题 | 作用范围 | 与谁配合 |
|------|-------------|----------|----------|
| **fixture** | 测试资源准备与清理（setup/teardown） | 通过 scope 控制，从 function 到 session | parametrize、conftest.py |
| **parametrize** | 把一组数据展开成独立测试用例 | 测试函数级（通过 `@pytest.mark.parametrize`） | fixture（参数名引用 fixture） |
| **conftest.py** | 跨文件共享 fixture 和 hook，无需 import | 目录级（对该目录及子目录所有测试可见） | fixture、hook |
| **marker** | 给测试打标签，按标签筛选执行 | 测试函数/类级（通过 `@pytest.mark.xxx`） | CLI `-m` 参数 |
| **hook** | 在 pytest 执行流程的特定节点插入自定义逻辑 | 会话级（通过 conftest.py 或插件注册） | conftest.py、插件 |
| **插件** | 扩展 pytest 核心能力（覆盖率、mock、并行等） | 会话级（通过 `pip install` + entry_points 注册） | hook、fixture |

遇到"这个 fixture 在哪些文件里可见"、"marker 和 parametrize 的区别是什么"这类问题时，回来看这张表比翻 API 文档快。

## 五、Fixture 体系

`assert` 和自动发现让你愿意用 pytest；fixture 决定了你能不能把它用深。

### 5.1 fixture 是什么

fixture 是一个由 `@pytest.fixture` 装饰的函数，职责是"准备测试需要的资源，并在测试结束后清理"。测试函数通过同名参数声明自己需要哪个 fixture，pytest 负责在调用测试前执行 fixture、在测试结束后按依赖逆序清理。

```python
import pytest

@pytest.fixture
def db():
    print("连接数据库")
    yield {"conn": "fake-conn"}
    print("关闭连接")   # yield 之后的代码就是 teardown

def test_query(db):
    assert db["conn"] == "fake-conn"
```

`yield` 是 fixture 的分界点：之前是 setup，之后是 teardown。一个函数同时承载 setup 和 teardown，比 unittest 的 `setUp/tearDown` + `setUpClass/tearDownClass` 两对方法要清晰。

### 5.2 scope：fixture 的生命周期

fixture 默认 `scope="function"`，意味着每个测试函数都拿一份全新的实例。pytest 提供 5 个 scope：

| scope | 含义 | 典型场景 |
|-------|------|----------|
| `function`（默认） | 每个测试函数一份 | 临时对象、轻量 mock |
| `class` | 每个测试类一份 | 类内共享状态 |
| `module` | 每个 .py 文件一份 | 整个文件共用一个 client |
| `package` | 每个包（带 `__init__.py`）一份 | 跨文件共享但要包级隔离 |
| `session` | 整个测试会话一份 | 数据库连接池、HTTP client |

scope 越大，setup 次数越少，测试越快，但要警惕"测试间状态污染"。session 级 fixture 几乎一定要配合"只读 + 内部复制"使用，否则后续测试会被前面的副作用拖死。

```python
@pytest.fixture(scope="session")
def engine():
    # 全测试会话只启动一次重型资源
    eng = create_engine("sqlite:///:memory:")
    yield eng
    eng.dispose()
```

### 5.3 autouse：隐式 fixture

如果某个 fixture 必须对所有测试都生效，可以加 `autouse=True`，pytest 会自动调用它，测试函数不用写参数。

```python
@pytest.fixture(autouse=True)
def reset_config():
    Config.load_defaults()
    yield
    Config.clean()
```

autouse 是把双刃剑：好处是少写一行参数，代价是新人读测试时不知道背后跑了什么。团队代码风格上，autouse 只建议用在"环境级别的副作用清理"（如重置全局配置、清空 mock 缓存），业务准备逻辑用显式参数。

### 5.4 factory fixture：参数化资源

有时候测试需要"一组"资源，而不是"一个"资源。factory fixture 的模式：fixture 返回一个工厂函数，测试调用这个函数创建新实例。

```python
@pytest.fixture
def make_user(db):
    created = []
    def _make(name, role="user"):
        u = db.create_user(name=name, role=role)
        created.append(u)
        return u
    yield _make
    # 清理：删除所有创建的 user
    for u in created:
        db.delete_user(u)

def test_admin(make_user):
    admin = make_user("alice", role="admin")
    assert admin.can_publish()
```

factory 模式把"fixture 管理资源生命周期"和"测试控制资源内容"解耦——fixture 只管怎么建和怎么删，测试只管建什么和怎么用。

### 5.5 fixture 之间的依赖

fixture 可以依赖其他 fixture——参数列表写名字就行。

```python
@pytest.fixture
def db():
    return Database(":memory:")

@pytest.fixture
def user_repo(db):
    return UserRepository(db)

def test_create(user_repo):
    user_repo.create("bob")
    assert user_repo.count() == 1
```

pytest 会先算依赖图，按拓扑序逐层 setup。这样可以把"重型资源 → 业务封装 → 业务对象"逐层封装，测试只用关心"我需要哪个业务对象"，不用关心它依赖什么。

---

<div style="padding: 12px; border-radius: 6px; background: #f5f7fa; margin: 16px 0;">

**📝 练习：设计一个 fixture 依赖链**

假设你要测试一个订单服务，它依赖数据库连接和 Redis 缓存。请设计 3 个 fixture：

- `db_conn`：scope=module 的数据库连接
- `redis_conn`：scope=module 的 Redis 连接
- `order_service`：依赖 `db_conn` 和 `redis_conn`，返回 `OrderService` 实例

写出 fixture 定义和依赖关系。假设 `connect_database`、`redis.Redis`、`OrderService` 已经在项目中可用。

<details>
<summary>点击查看参考实现</summary>

```python
import pytest
import redis  # 需安装：pip install redis

@pytest.fixture(scope="module")
def db_conn():
    conn = connect_database("postgresql://localhost/testdb")
    yield conn
    conn.close()

@pytest.fixture(scope="module")
def redis_conn():
    r = redis.Redis(host="localhost", port=6379, db=0)
    yield r
    r.close()

@pytest.fixture
def order_service(db_conn, redis_conn):
    svc = OrderService(db=db_conn, cache=redis_conn)
    return svc

def test_create_order(order_service):
    order = order_service.create({"item": "book", "qty": 1})
    assert order.id is not None
```

pytest 的依赖解析顺序：`db_conn` 和 `redis_conn`（同层，可并行）→ `order_service`（依赖前两者）→ `test_create_order`。

</details>

</div>

## 六、parametrize——数据驱动测试

fixture 解决"怎么准备环境"，parametrize 解决"怎么准备数据"。

```python
import pytest

@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add(a, b, expected):
    assert a + b == expected
```

跑一次，pytest 会展开成 4 个独立测试用例，每个用例会显示自己的 `nodeid`（如 `test_add[1-2-3]`），失败时精确定位到具体数据行。

给每条数据起个可读的名字，CI 日志会更友好：

```python
@pytest.mark.parametrize("a,b,expected", [
    pytest.param(1, 2, 3, id="positive"),
    pytest.param(0, 0, 0, id="zero"),
    pytest.param(-1, 1, 0, id="mixed-sign"),
])
def test_add(a, b, expected):
    assert a + b == expected
```

输出会变成 `test_add[positive]` `test_add[zero]`，一眼就能看到是哪类用例挂掉。

parametrize 还能和 fixture 叠加：把 fixture 名字写进参数列表，pytest 会先把 fixture 跑起来，再用 parametrize 展开数据。fixture × parametrize 的笛卡尔积是数据驱动测试的常用组合。

## 七、conftest.py——跨文件共享

写测试多了，很多 fixture 在多个文件里都要用。把 fixture 写进 `conftest.py`，pytest 会自动让它对该目录及子目录下的所有测试可见，**不需要 import**。

```
project/
├── conftest.py           # 公共 fixture，对整个 project 可见
├── tests/
│   ├── conftest.py       # tests 层 fixture，对 tests/ 下可见
│   ├── unit/
│   │   ├── conftest.py
│   │   └── test_foo.py
│   └── integration/
│       ├── conftest.py
│       └── test_bar.py
```

`conftest.py` 的可见性规则：fixture 树和目录树同构，靠近根的 conftest 越"通用"，靠近叶子的 conftest 越"专用"。不用 import 就能让 fixture 跨文件可见，这一点是 fixture 体系能在大型项目里铺开的前提。

不要在 conftest.py 里写测试函数——pytest 不会收集它们，文件名虽然带 test 也无效。conftest.py 只放 fixture、hook、plugin 配置。

---

<div style="padding: 12px; border-radius: 6px; background: #f5f7fa; margin: 16px 0;">

**📝 自测：conftest.py 可见性规则**

```
ecommerce/
├── conftest.py            # fixture: api_base_url = "https://api.example.com"
├── tests/
│   └── conftest.py        # fixture: db_conn
│   └── orders/
│       └── test_order.py  # 这里能用到哪些 fixture？
│   └── payments/
│       └── test_pay.py    # 这里能用到哪些 fixture？
```

在 `test_order.py` 中，你能通过参数名直接使用 `api_base_url` 和 `db_conn` 吗？需要 import 吗？

<details>
<summary>点击查看参考答案</summary>

`test_order.py` 可以**直接使用** `api_base_url`（来自 `ecommerce/conftest.py`）和 `db_conn`（来自 `ecommerce/tests/conftest.py`），都不需要 import。

pytest 从测试文件所在目录向上遍历 `conftest.py`，越靠近测试文件的 `conftest.py` 优先级越高。如果 `tests/conftest.py` 和 `ecommerce/conftest.py` 定义了同名 fixture，`tests/` 下的那个会覆盖上级的。

</details>

</div>

## 八、内置常用 fixture

pytest 自带了一批"开箱即用"的 fixture，覆盖测试 90% 的副作用处理需求：

| fixture | 作用 |
|---------|------|
| `tmp_path` | 提供一个唯一的临时目录（`pathlib.Path` 类型），测试结束自动清理 |
| `tmp_path_factory` | session 级临时目录工厂 |
| `monkeypatch` | 临时修改属性/环境变量/字典项，测试结束自动还原 |
| `capsys` / `capfd` | 捕获 `print` / 文件输出 |
| `caplog` | 捕获 logging 输出 |
| `pytester` | 给插件作者用，跑"会产出测试的测试" |
| `request` | 提供当前测试的元信息（函数名、参数、marker） |

举例——`monkeypatch` 是写单元测试时改环境变量最干净的方式：

```python
import mypkg.config  # 假设 mypkg 已安装，config 模块有 DEBUG 属性

def test_debug_mode(monkeypatch):
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setattr("mypkg.config.DEBUG", True)
    assert mypkg.config.DEBUG is True
    # 测试结束，DEBUG 自动还原
```

`tmp_path` 也是必备：

```python
def test_write_report(tmp_path):
    target = tmp_path / "report.txt"
    data = "## 标题\n正文内容"
    write_report(target, data)  # 假设 write_report 已定义
    assert target.read_text().startswith("##")
```

`capsys` / `caplog` 让"测 print 输出"和"测 log 输出"成为可能，避免在测试里塞一堆 `print` 调试。

## 九、Marker 系统——给测试打标签

marker 用来给测试"打标签"——跳过、加预期失败、按标签分组执行。

```python
import pytest

@pytest.mark.skip(reason="还没修")
def test_broken():
    assert False

@pytest.mark.xfail(reason="已知 bug")
def test_known_bug():
    assert 1 + 1 == 3

@pytest.mark.slow
def test_heavy():
    import time; time.sleep(10)
```

命令行按 marker 过滤：

```bash
pytest -m slow          # 只跑慢测试
pytest -m "not slow"    # 跑所有非慢测试
```

自定义 marker 必须在 `pytest.ini` / `pyproject.toml` 里注册，否则 pytest 8+ 会发出 `PytestUnknownMarkWarning`：

```toml
[tool.pytest.ini_options]
markers = [
    "slow: 标记耗时较长的集成测试",
    "integration: 跨服务集成测试",
]
```

marker 的命名应该表达"为什么跳过/为什么分组"，而不是"测试在做什么"。前者是"业务维度"（slow / integration / smoke），后者是"测试名"（test_login）——后者已经能通过测试名表达，再加 marker 就是冗余。

## 十、运行 unittest

pytest 兼容 `unittest`——所有继承 `unittest.TestCase` 的类 pytest 都能跑。

```python
import unittest

class TestStringMethods(unittest.TestCase):
    def test_upper(self):
        self.assertEqual("foo".upper(), "FOO")
```

`pytest` 直接执行。`unittest` 的 `setUp/tearDown`、`@unittest.skip` 装饰器全部生效，断言失败时同样享受 pytest 的反射式输出。

这条兼容性的实际意义：**老项目可以渐进式迁移**——不用一次性把 `unittest.TestCase` 全改成 `def test_xxx()`，新写的测试用 pytest 风格，老测试保持原样，逐步替换。

## 十一、一次完整的测试执行过程

前面把 fixture、parametrize、conftest、marker 拆开讲了，这里用一个完整案例把它们串起来。以下面这个项目结构为例：

```
calculator/
├── conftest.py
├── src/
│   └── calc.py
└── tests/
    ├── conftest.py
    └── test_operations.py
```

**calculator/src/calc.py**（被测代码）：

```python
class Calculator:
    def __init__(self, db_url):
        self.db_url = db_url
        self._result = 0

    def clear(self):
        self._result = 0

    def add(self, a, b):
        self._result = a + b
        return self._result

    def multiply(self, a, b):
        self._result = a * b
        return self._result

    def result(self):
        return self._result
```

**calculator/conftest.py：**

```python
import pytest

@pytest.fixture(scope="session")
def db_url():
    """session 级：整个测试会话只需要一个数据库地址"""
    return "sqlite:///:memory:"
```

**calculator/tests/conftest.py：**

```python
import pytest
from src.calc import Calculator

@pytest.fixture
def calc(db_url):  # 依赖上层的 db_url
    """每个测试函数都拿到一个全新 Calculator 实例"""
    c = Calculator(db_url)
    c.clear()
    yield c
    c.clear()
```

**calculator/tests/test_operations.py：**

```python
import pytest

@pytest.mark.parametrize("a,b,expected", [
    pytest.param(1, 2, 3, id="positive"),
    pytest.param(-1, 5, 4, id="mixed"),
    pytest.param(0, 0, 0, id="zero"),
])
def test_add(calc, a, b, expected):
    assert calc.add(a, b) == expected

@pytest.mark.slow
def test_complex_calc(calc):
    calc.add(1, 2)
    calc.multiply(3, 4)
    assert calc.result() == 12
```

当运行 `pytest` 时，pytest 内部经历了以下步骤：

```
1. 测试发现
   ├── 扫描 tests/ 目录下匹配 test_*.py 的文件
   ├── 找到 test_operations.py
   └── 从中收集 test_add 和 test_complex_calc

2. fixture 依赖解析
   ├── test_add(calc, a, b, expected) → 需要 fixture: calc
   │   └── calc(db_url) → 需要 fixture: db_url
   ├── test_complex_calc(calc) → 需要 fixture: calc
   │   └── same chain
   └── 构建依赖图: db_url → calc → [test_add, test_complex_calc]

3. parametrize 展开
   ├── test_add 展开为 3 个独立用例：
   │   ├── test_add[positive]
   │   ├── test_add[mixed]
   │   └── test_add[zero]

4. fixture setup（按拓扑序）
   ├── db_url (scope=session): 只运行一次，返回 "sqlite:///:memory:"
   ├── calc (scope=function): 每个测试函数运行一次
   │   ├── test_add[positive]: setup calc → 测试 → teardown calc
   │   ├── test_add[mixed]:    setup calc → 测试 → teardown calc
   │   ├── test_add[zero]:     setup calc → 测试 → teardown calc
   │   └── test_complex_calc:  setup calc → 测试 → teardown calc

5. marker 筛选（如果指定了 -m）
   └── pytest -m slow → 只跑 test_complex_calc

6. 报告输出
   ├── test_add[positive] .     [25%]
   ├── test_add[mixed]    .     [50%]
   ├── test_add[zero]     .     [75%]
   └── test_complex_calc  .     [100%]
```

这个流程把 conftest 的层级作用域、fixture scope 的执行次数、parametrize 的展开和 marker 的过滤时机全部织在一起。排查"为什么某个 fixture 跑了太多次"或"为什么子目录的测试看不到这个 fixture"时，对照上面 6 步往回推。

## 十二、插件机制——pytest 的"长尾"

pytest 本身只做三件事：测试发现、fixture 调度、报告输出。其他能力（覆盖率、mock、并行、Django 集成、asyncio 集成）全部由插件完成。

一个最简插件就是带 hook 实现的 `conftest.py`：

```python
# conftest.py
def pytest_runtest_makereport(item, call):
    if call.when == "call":
        print(f"✅ {item.nodeid} 跑完了")
```

更复杂的插件打包成 `pytest-<name>`，通过 `pip install` 安装，通过 `entry_points` 注册到 pytest。

`pytest --trace-config` 可以看到当前会话加载了哪些插件；`pytest -p no:cacheprovider` 可以临时禁用某个插件——这两条命令是排查"为什么测试突然变慢了 / 为什么某个 fixture 行为不对"的首选工具。

新人最容易踩的坑是"上来就装一堆插件"。先把 pytest 内置的 `tmp_path` / `monkeypatch` / `capsys` 用熟，再按需引入 `pytest-mock`（替代手写 mock）、`pytest-cov`（覆盖率）、`pytest-xdist`（并行）。其他插件多数是"特定框架的桥接"（Django/FastAPI/airflow 等），遇到再说。

## 十三、典型反模式与避坑建议

| 反模式 | 后果 | 修正 |
|--------|------|------|
| 在 fixture 里做 `import` 大对象、scope=function | 每个测试都重导入，测试变慢 | 改成 `scope="module"` 或 `session` |
| 用 `pytest.fail()` 抛异常代替 `assert` | 失去 assert 反射信息 | 改用 `assert` 或 pytest 内置断言 |
| 测试里 `time.sleep(N)` 等异步事件 | 慢且不稳定 | 改用 `monkeypatch` / 事件注入 |
| 在 conftest.py 里写测试函数 | pytest 不会收集 | 测试放到 `test_*.py` 文件 |
| 测试间共享可变全局状态 | 后运行的测试受前面副作用影响 | 用 fixture scope 隔离 |
| 写超长参数列表的 parametrize | 失败信息像天书 | 用 `pytest.param(..., id="...")` 起可读名字 |
| `assert` 后不写消息 | 失败时只看到"AssertionError" | `assert x == y, "期望 y 因为 xxx"` |

---

<div style="padding: 12px; border-radius: 6px; background: #f5f7fa; margin: 16px 0;">

**📝 自测：能识别反模式吗？**

看下面这段代码，找找有哪些反模式：

```python
# tests/test_user.py
state = []

def test_create_user():
    state.append("user1")
    assert len(state) == 1

def test_delete_user():
    state.append("user2")
    assert len(state) == 1  # 这个测试能独立通过吗？
```

<details>
<summary>点击查看参考答案</summary>

**反模式**：测试间共享可变全局状态 `state`。

`test_delete_user` 单独跑时 `len(state) == 1` 能通过（state 只有 `["user2"]`）；但如果 `test_create_user` 先跑，state 会变成 `["user1", "user2"]`，`test_delete_user` 就挂了。

**修正**：把 `state` 变成一个 fixture（scope=function）：

```python
import pytest

@pytest.fixture
def state():
    return []

def test_create_user(state):
    state.append("user1")
    assert len(state) == 1

def test_delete_user(state):
    state.append("user2")
    assert len(state) == 1
```

每个测试函数都拿到独立的 `state` 列表，互不影响。这也是为什么 fixture 默认 scope=function——默认最安全。

</details>

</div>

## 十四、什么时候用 pytest，什么时候用别的

pytest 不是银弹，少数场景下别的工具更合适：

| 场景 | 推荐 |
|------|------|
| 纯标准库、小型工具 | `unittest`（标准库不需要额外依赖） |
| 纯文档示例验证 | `doctest` |
| 行为驱动（BDD，Given-When-Then） | `pytest-bdd`（保留 pytest 生态）或 `behave` |
| 大规模端到端（E2E）| Playwright / Cypress（pytest 只做编排） |
| 性能基准 | pytest-benchmark / locust（不要和功能测试混在一个 suite） |
| 强类型契约测试 | hypothesis（基于属性的测试，pytest 风格但独立库） |

## 十五、采用顺序建议

把 pytest 引入一个 Python 项目，按下面这个顺序铺：

1. **第一周**：装上 `pytest`，给现有 `unittest` 测试加上 pytest 跑通，CI 改成 `pytest`。这一阶段不重写任何东西，只是切换工具链。
2. **第二周**：开始用 `assert` 替代 `self.assertEqual`，把简单的 `setUp` 改成 `@pytest.fixture`。完成 30% 的迁移就够，剩下 70% 看团队节奏。
3. **第一月**：把跨文件共享的 setup 拆进 `conftest.py`，引入 `pytest-cov` 看覆盖率。
4. **第二月**：按业务需要引入 `pytest-mock`（替换 unittest.mock 的复杂语法）、`pytest-xdist`（并行执行，CI 时间减半）、业务框架对应的桥接插件（`pytest-django` / `pytest-asyncio` 等）。
5. **持续**：自定义团队 marker（`smoke` / `regression` / `slow`），写一份 `conftest.py` 编码规范，新人入职照着改。

## 十六、小结

- pytest 的入门成本是"一个 `assert` + 一行 `pytest`"，不要被 1300+ 插件的生态规模吓到。
- 真正决定 pytest 能不能用好的是 fixture 体系：`yield` 分 setup/teardown、scope 控制生命周期、factory 模式做参数化资源、conftest.py 做跨文件命名空间。
- parametrize 是数据驱动测试的标配；marker 是测试分组的标配；`monkeypatch` / `tmp_path` / `capsys` 是副作用处理的三件套。
- pytest 兼容 unittest，老项目可以渐进式迁移，不需要一次性重写。
- 1300+ 插件是"按需引入"，不是"全装上"——内置 fixture 才是 80% 场景的主力。

pytest 不只是一个写测试的工具，它是一套测试编排框架。理解这一层定位差异，比记住 10 个 fixture API 更值得。

---

## 进阶路径

如果你已经掌握了本文内容，可以沿着下面三条路深入：

**路径一：pytest 插件开发**
- 阅读 [pytest 官方插件开发指南](https://docs.pytest.org/en/stable/how-to/writing_plugins.html)，了解 hook 规范
- 给团队写一个自定义 marker 收集和报告插件（从 `pytest_runtest_makereport` 起步）
- 研究 `pytest-cov` 源码，理解它如何 hook 覆盖率收集

**路径二：属性测试（Property-Based Testing）**
- 学习 [hypothesis](https://hypothesis.readthedocs.io/) 库，把"手写用例"改为"声明属性约束"
- 典型的属性测试场景：序列化/反序列化一致性（`encode(decode(x)) == x`）、排序单调性、idempotency
- hypothesis 和 pytest 的 parametrize 天然协同，可以通过 `@given` 装饰器直接集成

**路径三：测试工程化**
- 引入 `pytest-xdist` 做并行执行（CI 加速 2-4 倍），但要先确保测试之间没有共享可变状态
- 用 `pytest-benchmark` 把关键路径的性能纳入 CI 检查（"这个 PR 不能让 add() 变慢 10%"）
- 配置 `pytest.ini` / `pyproject.toml` 统一团队的测试配置（marker 注册、默认参数、插件列表）
- 在 CI 中按 marker 分层跑：`smoke` 在每次 commit，`regression` 在 PR 阶段，`slow` 在 nightly

---

<div style="padding: 12px; border-radius: 6px; background: #f5f7fa; margin: 16px 0;">

**📝 最终自测清单**

做完一遍后，检查你能不能：

- [ ] 不查文档，写出一个带 `yield` 的 fixture，并解释 setup 和 teardown 的时机
- [ ] 说出 `scope="function"` 和 `scope="session"` 的取舍场景，以及 session 级 fixture 的注意事项
- [ ] 用 `@pytest.mark.parametrize` 写一组数据驱动测试，并给每条数据起好可读的 id
- [ ] 解释为什么 conftest.py 里的 fixture 不需要 import，以及它的可见范围规则
- [ ] 说出至少 3 个 pytest 内置 fixture 的名字和用途
- [ ] 写出一个 team marker 的注册和过滤命令
- [ ] 列出 3 个常见反模式，并说出修正方案
- [ ] 解释 pytest 的测试发现规则：什么文件名会被收集、什么函数名会被收集

</div>

---

**参考链接**

- [pytest 官方文档](https://docs.pytest.org/en/stable/)
- [GitHub 仓库](https://github.com/pytest-dev/pytest)
- [插件索引](https://docs.pytest.org/en/latest/reference/plugin_list.html)
- [assert 反射机制详解](https://docs.pytest.org/en/stable/how-to/assert.html)
- [fixture 体系](https://docs.pytest.org/en/stable/explanation/fixtures.html)
- [测试发现规则](https://docs.pytest.org/en/stable/explanation/goodpractices.html#python-test-discovery)
