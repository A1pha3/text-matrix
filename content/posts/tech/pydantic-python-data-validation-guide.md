---
title: "Pydantic：Python 类型提示数据验证完全指南"
date: "2026-04-06T22:09:00+08:00"
slug: "pydantic-python-data-validation-guide"
description: "从类型提示如何驱动验证、V2 为什么用 Rust 重写 pydantic-core，到 FastAPI 请求的完整验证路径、严格模式取舍与常见踩坑，一篇讲清 Pydantic 的工程定位与使用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Pydantic", "Python", "数据验证", "类型提示", "FastAPI"]
---

Pydantic V2 把验证核心搬到 Rust 实现的 `pydantic-core` 之后，FastAPI、SQLModel、LangChain 这些下游框架的验证瓶颈被打开了。V1 时代，一个高 QPS 接口里 30%-50% 的 CPU 可能花在 Python 层的字典遍历和类型检查上；V2 把这部分压到 Rust 后，下游框架可以放心地把请求模型做得更复杂，而不必担心验证开销吃掉吞吐。迁移文档里能看到的是 API 表面更一致，看不到的是验证开销从"必须优化掉的成本"变成了"可以放心使用的基建"。

本文按"为什么这样设计 → 怎么用 → 怎么踩坑 → 怎么取舍"展开，覆盖 BaseModel、字段约束、验证器分层、严格模式、JSON Schema 生成、pydantic-settings 配置管理，以及 FastAPI 集成、ORM 模型、Webhook 验证等场景。读者读完应能回答三个问题：类型提示如何被翻译成验证规则、验证与序列化为什么必须成对设计、Rust 核心对 Python 生态意味着什么。

## 本文地图

| 章节 | 回答的问题 | 适合的读者 |
|------|-----------|-----------|
| Pydantic 在 Python 数据栈中的位置 | 它和 dataclasses / attrs / marshmallow 的边界 | 选型阶段 |
| 类型提示如何驱动验证 | 注解怎么变成 Rust 侧的派发表 | 想理解底层 |
| V2 为什么要用 Rust 重写 | 提速来自哪里、代价是什么 | V1 迁移者 |
| BaseModel 与字段定义 | 怎么定义模型、Field 约束分几层 | 入门 |
| 验证器分工 | Field / field_validator / model_validator 怎么选 | 写业务校验 |
| 严格模式 vs 宽松模式 | 什么时候拒绝隐式转换 | 边界设计 |
| 序列化控制 | 输出怎么脱敏、怎么和 ORM 互转 | API 开发 |
| JSON Schema 生成 | 这份 Schema 喂给谁 | 全栈协作 |
| pydantic-settings | 配置怎么验证 | 应用启动 |
| 任务流案例 | 一次 FastAPI 请求怎么穿过验证层 | 想看完整路径 |
| 常见踩坑 / 取舍 / 错误处理 / ORM / Webhook / 迁移 | 真实工程问题 | 按需查阅 |

## Pydantic 在 Python 数据栈中的位置

Python 里"用类型注解描述数据"的库不止 Pydantic 一个，但定位差异明显。选型时先看数据来源：信任内部数据用 `dataclasses`，不信任外部数据用 Pydantic，两者之间看是否需要 schema 与模型分离。四个主要选项的对比：

| 库 | 主要职责 | 是否做运行时验证 | 典型场景 |
|------|----------|-----------------|----------|
| `dataclasses` | 标准库，生成 `__init__`/`__repr__` 等样板方法 | 否，只做类型提示 | 内部数据容器、值对象 |
| `attrs` | 第三方，比 `dataclasses` 更早、更灵活 | 否（可选 `validators`） | 库内部 API、性能敏感对象 |
| `marshmallow` | 序列化/反序列化框架，先于类型提示流行 | 是，但 schema 与类型注解分离 | 老 Flask 项目、显式 schema |
| `Pydantic` | 基于类型提示的运行时验证 + 序列化 + Schema 生成 | 是，且与类型注解合一 | API 边界、配置、领域模型 |

`dataclasses` 和 `attrs` 解决的是"少写样板代码"，它们信任调用方传入的数据；Pydantic 解决的是"不信任外部数据"，需要在系统边界把字典、JSON、查询参数转成可信的 Python 对象。`marshmallow` 也能做这件事，但 schema 单独定义，类型注解和验证规则分离，IDE 提示和 mypy 检查都跟不上。Pydantic 把类型注解本身当成 schema，让静态检查和运行时验证共用同一份事实——一份注解同时驱动 mypy、IDE 补全和运行时验证，这是它在 API 领域被广泛采用的直接原因。

FastAPI 把这个特性推到了路由签名层：`user: CreateUserRequest` 既是 OpenAPI 文档的来源，也是请求体的运行时验证器。一份类型注解驱动文档生成、IDE 补全、运行时验证三件事，下游框架因此可以把请求模型做得更复杂而不用担心验证开销。

## 类型提示如何驱动验证

Pydantic 的验证机制依赖一个 Python 语言特性：类型注解在运行时可被读取。这是它能"用类型注解当 schema"的前提——如果类型注解只是给 IDE 看的静态信息，Pydantic 就无从下手。

```python
from typing import get_type_hints

class User:
    id: int
    name: str = "anonymous"

print(get_type_hints(User))
# {'id': <class 'int'>, 'name': <class 'str'>}
```

`typing.get_type_hints` 能拿到类上声明的类型映射。Pydantic 在 `BaseModel` 的元类里做类似的事情，但走得更远：它把每个字段的类型注解翻译成一组验证规则，编译成 `pydantic-core` 的内部 schema，再在 Rust 侧执行。这一步发生在类定义时，不是实例化时——类型注解被翻译一次，后续每次实例化都走编译后的 schema。

翻译过程大致是：

1. `int` → "必须是整数，或可被 `int()` 转换的字符串/浮点数"
2. `str = Field(min_length=3)` → "必须是字符串，长度 ≥ 3"
3. `List[int]` → "必须是序列，每个元素满足 `int` 规则"
4. `Optional[datetime]` → "可为 `None`，或满足 `datetime` 解析规则"
5. 嵌套 `Address` → "必须是字典，且满足 `Address` 模型的所有字段规则"

每条规则在编译后变成 Rust 侧的一个验证函数，运行时按字段顺序依次调用。嵌套模型的规则会递归展开，所以一个 3 层嵌套的模型，编译后的 schema 是一棵树，运行时按树遍历。

这套翻译在类定义时完成一次，运行时验证直接走编译后的 schema，不再重复解析类型注解。V1 每次验证都要在 Python 层走一遍字段循环和类型判断；V2 把这些编译成 Rust 的派发表，运行时只查表不解析。这也是为什么 V2 的"类定义"比 V1 稍慢——编译 schema 有一次性开销，但这个开销在类定义时付一次，后续每次验证都受益。

类型注解被翻译成 Rust 侧规则后，几个日常使用中高频出现的困惑就有了依据。它们都源于宽松模式这个默认行为——宽松模式为了适配 HTTP 输入做了很多隐式转换，转换规则和 Python 原生行为不完全一致：

- **为什么 `bool_field="yes"` 会被转成 `True`**：Pydantic 的 `bool` 规则默认接受 `"yes"/"on"/"true"/"1"` 等常见真值字符串，这是"宽松模式"下的转换约定，不是 Python `bool()` 的行为。Python 的 `bool("yes")` 永远是 `True`（非空字符串），但 Pydantic 会识别字面量。
- **为什么 `id: int` 接受 `"123"`**：默认模式下 `int` 规则会尝试字符串到整数的转换，转换失败才报错。这是为了适配 HTTP 表单、URL 参数这些天然是字符串的输入源——如果默认严格，每个字符串字段都要先手动转成目标类型再传给 Pydantic。
- **为什么 `Optional[X] = None` 和 `X | None = None` 行为一致**：两者在 `get_type_hints` 里都解析成 `Union[X, None]`，Pydantic 看到的是同一个类型对象。写哪种是风格选择，不影响验证行为。

## V2 为什么要用 Rust 重写 pydantic-core

V1 的性能瓶颈不是某个函数慢，而是验证循环本身在 Python 层跑。理解这一点，才能看懂 V2 为什么要把核心搬到 Rust，以及为什么有些场景提速大、有些场景提速小。

V1 的验证循环是纯 Python：每个字段调用一次 `getattr`、一次类型判断、一次转换函数，嵌套模型递归下去。对一个 20 个字段、3 层嵌套的请求模型，单次验证可能触发几百次 Python 函数调用。在 FastAPI 这种"每个请求都要验证一次 body"的场景下，验证开销会挤占业务逻辑的 CPU 预算——这也是为什么 V1 时代很多团队不得不手动优化验证逻辑，或者把请求模型拆得很碎。V2 的 Rust 重写让这种妥协不再必要。

V2 把验证核心拆成 `pydantic-core` 这个独立 crate，用 Rust 实现。三个关键变化：

- **类型派发**：编译后的 schema 是一张静态派发表，Rust 侧直接 `match` 类型 ID，跳过 Python 的 `isinstance` 链。V1 每次验证都要走 `isinstance(x, int)` → `isinstance(x, str)` → ... 的链式判断，V2 一次 `match` 就到位。
- **字段循环**：嵌套模型在 Rust 里递归，不回到 Python 层，避免 GIL 上下文切换。V1 嵌套模型每层都要回到 Python 调一次 `__init__`，V2 整棵树在 Rust 里走完。
- **错误收集**：验证失败时，所有错误在 Rust 侧累积成 `Vec<ValLineError>`，最后一次转成 Python 的 `ValidationError`，而不是每错一次都抛 Python 异常。这条变化让"一次返回所有错误"成为默认行为，V1 要自己实现错误收集逻辑。

但 Rust 重写有代价。V2 的几个设计变化都跟这个底层切换有关，理解这些代价才能判断是否值得迁移：

- **API 不兼容**：`@validator` → `@field_validator`、`.dict()` → `.model_dump()`、`.parse_obj()` → `.model_validate()`，因为新 API 要让自定义验证器能被 Rust 侧调用，签名必须改。迁移成本主要落在这里，`bump-pydantic` 工具能半自动处理，但动态调用和元编程场景仍需手动检查。
- **自定义验证器的性能特征变了**：`@field_validator` 仍然是 Python 函数，调用时会从 Rust 侧回到 Python，所以一个模型里挂 10 个 `field_validator` 性能不会比 V1 好太多。真正的提速来自 `Field` 内置约束（`gt`/`min_length`/`pattern`），这些在 Rust 侧直接执行。
- **严格模式（strict mode）成为一级公民**：V1 的转换行为隐式且不可关闭，V2 提供 `strict=True` 让字段拒绝隐式转换。这是 Rust 核心带来的副产品——派发表里多一个分支就能支持严格模式，V1 要在 Python 层加判断就贵得多。

所以"V2 比 V1 快 10-100x"这个数字要分场景看：纯 `Field` 约束的简单模型（比如只有 `int`/`str` 加几个 `gt`/`min_length`）提速最大，因为整条验证路径都在 Rust 里走完；挂满自定义 `field_validator` 的复杂模型提速较小，瓶颈回到了 Python 函数调用，每次验证器调用都要从 Rust 回到 Python 一次。官方 benchmark 测的是前者，真实业务里两者混合，实际提升通常在 5-20x 之间。判断自己的模型能拿到多少提速，看 `Field` 约束和自定义验证器的比例即可——`Field` 约束越多，提速越接近上限；自定义验证器越多，提速越接近下限。

## BaseModel 与字段定义

`BaseModel` 是 Pydantic 的入口。继承它之后，类体里的类型注解会被收集成字段，默认值会成为字段默认。这一步发生在类定义时，不是实例化时——类型注解被翻译成 Rust 侧的 schema，后续每次实例化都走这份 schema。

```python
from datetime import datetime
from pydantic import BaseModel


class User(BaseModel):
    id: int                              # 必填，无默认值
    name: str = "anonymous"              # 可选，带默认值
    signup_ts: datetime | None = None    # 可选，显式标注 None
    tags: list[int] = []                 # 可选，默认空列表


# 从字典创建（自动验证 + 转换）
user = User.model_validate({
    "id": "123",                         # str → int
    "signup_ts": "2017-06-01 12:22",     # str → datetime
    "tags": [1, "2", b"3"],              # 混合类型 → list[int]
})

print(user.id)          # 123
print(user.signup_ts)   # 2017-06-01 12:22:00
print(user.tags)        # [1, 2, 3]
```

这个例子展示了 Pydantic 的核心行为：传入字典，拿到验证过的 Python 对象，类型转换在验证过程中完成。`"123"` 变成 `123`，`"2017-06-01 12:22"` 变成 `datetime`，`[1, "2", b"3"]` 变成 `[1, 2, 3]`——这些都是宽松模式下的隐式转换。

几个容易被忽略的细节，前两个是 V1 → V2 迁移时容易踩的，后一个是 API 重命名。其中 `dict()` 和 `model_dump()` 行为不一致会导致序列化结果和预期不同，迁移时建议全局替换，不要新旧 API 混用：

- **可变默认值可以直接写**：`tags: list[int] = []` 在 Pydantic 里是安全的，因为 `BaseModel` 会深拷贝默认值，不像 `dataclasses` 需要 `field(default_factory=list)`。这是 Pydantic 比 `dataclasses` 更"宽容"的地方，但也意味着默认值会在每次实例化时拷贝，大对象上要注意——一个默认值是 1000 元素字典的字段，每次实例化都会深拷贝一次。
- **`model_validate` 是 V2 的统一入口**：V1 的 `parse_obj` / `parse_raw` / `parse_file` 都被合并进来，分别对应 `model_validate(dict)` / `model_validate_json(str)` / 显式读文件后调用。迁移时按这个对照表替换即可。
- **`model_dump` 替代了 `dict()`**：V2 把所有序列化方法统一到 `model_dump`（返回 dict）和 `model_dump_json`（返回 str），`dict()` 仍可用但会告警，且行为可能与 `model_dump()` 不完全一致。

### 字段约束：Field 的内置规则

`Field` 是给字段附加约束的主要工具。这些约束会被编译进 Rust schema，性能远高于自定义验证器——这是 V2 提速的核心来源之一，能用 `Field` 解决的约束就不要用 `field_validator`。

```python
from pydantic import BaseModel, Field
from typing import Literal


class Product(BaseModel):
    # 数值约束
    price: float = Field(gt=0, le=10000, description="单价，单位分")
    quantity: int = Field(ge=0, le=1000)

    # 字符串约束
    sku: str = Field(
        min_length=8,
        max_length=16,
        pattern=r"^[A-Z]{3}-\d{5}$",
        examples=["ABC-12345"],
    )

    # 集合约束
    tags: list[str] = Field(min_length=1, max_length=5, default_factory=list)

    # 字面量类型，用于枚举值
    status: Literal["draft", "published", "archived"] = "draft"
```

约束分三类，覆盖了数值、字符串、集合三种主要数据形态：

| 类别 | 常用参数 | 适用类型 |
|------|----------|----------|
| 数值 | `gt`, `ge`, `lt`, `le`, `multiple_of` | `int`, `float`, `Decimal` |
| 字符串 | `min_length`, `max_length`, `pattern` | `str`, `bytes` |
| 集合 | `min_length`, `max_length` | `list`, `set`, `tuple`, `dict` |

这三类约束都在 Rust 侧执行，没有 Python 调用开销。如果约束需要跨字段（比如"结束时间必须晚于开始时间"），就要用 `model_validator`，代价是回到 Python 层。

`pattern` 接收的是正则字符串，V2 里它替代了 V1 的 `regex` 参数。如果用 `EmailStr`、`HttpUrl`、`PaymentCardNumber` 这些语义类型，Pydantic 会自动加上对应的格式校验（Luhn 算法、URL 规范化等），不需要再写 `pattern`——语义类型的好处是把领域规则封装进类型本身，调用方只要声明类型就拿到完整校验。

### 字段类型分层

按"约束强度"从弱到强，Pydantic 的字段类型大致分四层。选哪一层取决于"数据有多不可信"和"领域规则有多强"：

```python
from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import Any


class Types(BaseModel):
    # 第一层：基础类型，只做类型转换
    name: str
    age: int
    score: float

    # 第二层：约束类型，在转换基础上加边界
    bounded_age: int = Field(ge=0, le=150)
    formatted_sku: str = Field(pattern=r"^[A-Z]{3}-\d{5}$")

    # 第三层：语义类型，内置领域规则
    homepage: HttpUrl                    # URL 规范化 + 协议校验
    email: EmailStr                      # RFC 邮箱格式
    # card: PaymentCardNumber            # Luhn 校验，需要 pydantic[email] 之外的额外依赖

    # 第四层：逃生舱，不做任何校验
    raw_payload: Any
```

`Any` 是逃生舱：它跳过所有验证，原样接收。在"先收下来，后面再处理"的场景里有用，但每用一个 `Any` 就等于在类型边界上开一个口子，长期看会让静态检查失效。能用前三层就不要用第四层；如果非用不可，在 `field_validator` 里补一道业务校验，避免 `Any` 字段一路裸奔到业务层。

## 验证器：Field、field_validator、model_validator 的分工

Pydantic 的验证能力分三层，按"作用范围"递增。选错层会导致性能问题或验证遗漏——`Field` 在 Rust 侧执行，`field_validator` 和 `model_validator` 是 Python 函数，每次验证都要从 Rust 回到 Python。

| 层级 | 装饰器/工具 | 作用对象 | 执行位置 |
|------|-------------|----------|----------|
| 字段级约束 | `Field(...)` | 单个字段 | Rust 侧 |
| 字段级验证器 | `@field_validator` | 单个字段 | Python 侧 |
| 模型级验证器 | `@model_validator` | 整个模型 | Python 侧 |

**优先用 `Field`，不够时再用 `field_validator`，最后才用 `model_validator`**。这是性能事实：`Field` 约束在 Rust 侧执行，没有 Python 调用开销；`field_validator` 和 `model_validator` 是 Python 函数，每次验证都要从 Rust 回到 Python。一个挂满 10 个 `field_validator` 的模型，提速效果会显著低于全用 `Field` 约束的模型。判断标准是：能用 `Field` 参数表达的约束（范围、长度、正则）就用 `Field`，需要自定义逻辑（比如"密码必须包含大写字母"）才用 `field_validator`，需要跨字段（比如"结束时间晚于开始时间"）才用 `model_validator`。

### field_validator：单字段自定义逻辑

当 `Field` 的内置约束不够用时，`field_validator` 用于添加自定义逻辑。它有两个模式，区别在于"拿到的是原始输入还是转换后的值"：

- `mode="before"`：在类型转换**之前**执行，拿到的是原始输入。适合"先把字符串预处理成标准格式，再交给 Pydantic 转换"。
- `mode="after"`（默认）：在类型转换**之后**执行，拿到的是已转换的 Python 对象。适合"转换后的值不满足业务规则"。

```python
from pydantic import BaseModel, field_validator


class User(BaseModel):
    username: str
    password: str
    age: int

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        # mode="after"：v 已经是 str，做业务校验
        if not v.isalnum():
            raise ValueError("用户名只能包含字母和数字")
        return v.lower()

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码至少 8 位")
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含大写字母")
        return v

    @field_validator("age", mode="before")
    @classmethod
    def parse_age(cls, v):
        # mode="before"：v 可能是 "18岁" 这种字符串
        if isinstance(v, str) and v.endswith("岁"):
            return int(v[:-1])
        return v
```

三个高频踩坑点，前两个是装饰器使用问题，第三个是验证器返回值语义。第三个尤其隐蔽——验证器"忘记 return"会导致字段值变成 `None`，且不会报错，这类 bug 在测试覆盖不全时容易漏到生产：

- **`@classmethod` 必须在 `@field_validator` 下面**：装饰器从下往上执行，先 `field_validator` 把函数标记为验证器，再 `classmethod` 把它变成类方法。顺序反了会拿到实例而不是类，且报错信息不直观。
- **`ValueError` 会被自动包装成 `ValidationError`**：不要自己抛 `ValidationError`，抛 `ValueError` 即可，Pydantic 会收集所有字段的错误一次性返回。这条规则也适用于 `AssertionError`——`assert x > 0` 抛出的异常同样会被收集。
- **返回值会替换字段值**：验证器不是"只校验"，它返回什么，字段最终就是什么。`return v.lower()` 会让 `username` 存成小写。如果只想校验不想改值，记得 `return v`。

### model_validator：跨字段与模型级逻辑

当验证依赖多个字段的值时，`field_validator` 不够用，需要 `model_validator`。它也有两个模式，区别在于"在模型实例化之前还是之后执行"：

- `mode="before"`：在模型实例化**之前**执行，接收原始字典，返回处理后的字典。适合"输入字典需要预处理"。
- `mode="after"`：在模型实例化**之后**执行，接收 `self`，可以访问所有字段，返回 `self`。适合"字段间的业务约束"。

```python
from datetime import datetime, timedelta
from pydantic import BaseModel, model_validator


class Event(BaseModel):
    start_date: datetime
    end_date: datetime
    location: str

    @model_validator(mode="after")
    def check_date_order(self) -> "Event":
        if self.end_date <= self.start_date:
            raise ValueError("结束时间必须晚于开始时间")
        return self

    @model_validator(mode="after")
    def check_online_duration(self) -> "Event":
        if self.location == "online":
            duration = self.end_date - self.start_date
            if duration > timedelta(hours=8):
                raise ValueError("线上活动时长不能超过 8 小时")
        return self


# 跨字段错误会被收集到一起
try:
    Event(start_date="2026-01-01 10:00", end_date="2026-01-01 08:00", location="online")
except ValueError as e:
    print(e)
    # 1 validation error for Event
    #   end_date
    #     Value error, 结束时间必须晚于开始时间 [type=value_error, ...]
```

`mode="after"` 的验证器可以写多个，Pydantic 会按定义顺序依次执行，所有错误收集完再抛出。用户一次提交能拿到所有字段错误，而不是改一个看到一个——这条特性对前端表单校验尤其重要，用户不用反复提交才能发现下一个错误。

### 一个常见踩坑：验证器里的副作用

验证器会被 `model_validate`、`model_validate_json`、`__init__` 调用，每次实例化都会跑一遍。把 IO 操作（写日志、发请求、写数据库）放进验证器是常见错误：

```python
# 不要这样写
class Order(BaseModel):
    @model_validator(mode="after")
    def save_to_db(self) -> "Order":
        db.save(self)        # 每次反序列化都会写库，包括从缓存读出来时
        return self
```

这段代码的问题在于：从 Redis 缓存反序列化一个 Order 时，也会触发 `db.save(self)`，把缓存里的旧数据写回数据库，覆盖掉最新的业务更新。验证器只做"数据是否合法"的判断，不做"数据要被怎么处理"。需要触发副作用时，在业务层显式调用 `order.save()`，让验证和持久化分开——验证是声明式的、可重入的，持久化是命令式的、有副作用的，两者混在一起会让排查变得困难。

## 严格模式 vs 宽松模式

Pydantic 默认是"宽松模式"（lax mode）：能转换就转换，`"123"` → `123`、`"yes"` → `True`、`"2026-01-01"` → `datetime`。这对 HTTP 输入很友好，因为 URL 参数、表单字段、JSON 字符串本质上都是字符串——如果默认严格，每个字符串字段都要先手动转成目标类型再传给 Pydantic，代码会变得很啰嗦。

宽松模式的代价是它会掩盖调用方的类型错误。一个前端把 `user_id` 误传成字符串 `"123"`，后端静默转换成 `123`，bug 不会暴露，直到某天传了 `"12 3"` 才报错——而这时离 bug 引入已经过去很久，定位成本变高。

严格模式（strict mode）要求输入类型必须与声明类型匹配，不做隐式转换。它适合"数据已经是 Python 对象"的场景，比如服务间调用、ORM 查询结果——这些数据不应该再有字符串到数字的转换需求。开启方式是 `ConfigDict(strict=True)`：

```python
from pydantic import BaseModel, ConfigDict


class StrictUser(BaseModel):
    model_config = ConfigDict(strict=True)

    id: int
    name: str


StrictUser(id=123, name="alice")        # OK
StrictUser(id="123", name="alice")      # 报错：strict mode 不接受 str → int
StrictUser(id=123.0, name="alice")      # 报错：strict mode 不接受 float → int
```

严格模式可以全局开（`ConfigDict(strict=True)`），也可以单字段开（`Field(strict=True)`）。全局开会让所有字段都严格，单字段开只影响指定字段。常见的折中策略是按数据来源分层：

- **API 入口模型用宽松模式**：HTTP 来的数据都是字符串，宽松模式省去手动转换。
- **内部领域模型用严格模式**：服务之间传递的已经是 Python 对象，宽松模式会掩盖类型不匹配。
- **数值字段单独开严格**：`id: int = Field(strict=True)`，避免 `"123"` 被静默接受，因为 ID 通常不应该来自字符串。

在系统边界用宽松，在内部用严格，是更常见的工程实践。严格模式把"转换"和"拒绝"的边界从隐式变成显式，但全局开严格会让 HTTP 输入处理变得很啰嗦——每个字符串字段都要先手动转成目标类型再传给 Pydantic。一个折中方案是只在数值 ID 和布尔字段上开严格：ID 不应该来自字符串，布尔不应该接受 `0/1`，这两类隐式转换最容易掩盖 bug。其他字段（比如 `age: int` 从表单来的 `"18"`）保留宽松，让 Pydantic 处理转换。

## 序列化控制

验证解决"输入是否可信"，序列化解决"输出是否可控"。一个模型从外部接收数据时验证，向外部返回数据时序列化——这两件事必须成对设计，否则会出现"验证通过但输出泄漏敏感字段"的情况。Pydantic 的序列化通过 `model_dump` 和 `model_dump_json` 完成，两者共享一套选项：

```python
from datetime import datetime
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    password_hash: str
    created_at: datetime


user = User(id=1, name="alice", password_hash="***", created_at=datetime.now())

# 默认转 dict，datetime 保持 Python 对象
user.model_dump()
# {'id': 1, 'name': 'alice', 'password_hash': '***', 'created_at': datetime(...)}

# mode="json" 把所有值转成 JSON 兼容类型
user.model_dump(mode="json")
# {'id': 1, 'name': 'alice', 'password_hash': '***', 'created_at': '2026-04-06T...'}

# 排除敏感字段
user.model_dump(exclude={"password_hash"})
# {'id': 1, 'name': 'alice', 'created_at': datetime(...)}

# 只保留指定字段
user.model_dump(include={"id", "name"})
# {'id': 1, 'name': 'alice'}

# 嵌套模型的字段级排除
user.model_dump(exclude={"created_at": True})
```

`model_dump` 在 API 开发中的常见用法，共同点是"同一个模型需要不同的序列化结果"。脱敏、过滤、格式转换都可以在序列化层一次性处理，不必在业务层写一堆 if-else 来控制字段暴露。按出现频率从高到低：

- **API 响应里去掉密码字段**：用 `exclude={"password_hash"}`，或在字段上声明 `Field(exclude=True)` 让它默认不序列化。后者更安全——即使有人忘了在 `model_dump` 里加 `exclude`，字段也不会泄漏。
- **日志里脱敏**：定义一个 `to_log_dict()` 方法，调用 `model_dump(exclude={"password_hash", "token", "secret"})`，避免敏感字段进日志。日志框架的默认序列化不会走 Pydantic，所以要在打印前显式转成脱敏 dict。
- **数据库存储 vs API 返回**：同一个模型可能需要两种序列化结果，用 `model_dump(mode="json")` 给 API（所有值转成 JSON 兼容类型），用 `model_dump()` 给 ORM 转换（保留 Python 对象类型）。

序列化的反向操作是反序列化，V2 统一到 `model_validate`。三个入口对应三种数据源：

```python
# 从字典
User.model_validate({"id": 1, "name": "alice", ...})

# 从 JSON 字符串
User.model_validate_json('{"id": 1, "name": "alice", ...}')

# 从 ORM 对象（需要 model_config = ConfigDict(from_attributes=True)）
User.model_validate(orm_user)
```

`from_attributes=True` 让 `model_validate` 用 `getattr` 而不是 `__getitem__` 取值，这样 SQLAlchemy 模型、dataclass 实例都能直接喂给 `model_validate`。V2 把 ORM 集成做进了核心，不再需要 V1 的 `orm_mode` 配置——"从对象属性取值"和"从字典取值"统一成同一个入口，迁移时把 `orm_mode=True` 改成 `from_attributes=True` 即可。

## JSON Schema 生成对 API 文档的意义

Pydantic 能从模型自动生成 JSON Schema。在 FastAPI 生态里，这份 Schema 是关键基础设施——它不只是文档，还是前后端协作的契约。

```python
import json
from pydantic import BaseModel, Field


class User(BaseModel):
    id: int = Field(description="用户唯一标识")
    name: str = Field(min_length=3, max_length=20, description="用户名")
    email: str = Field(description="邮箱地址")
    age: int | None = Field(default=None, ge=0, le=150)


print(json.dumps(User.model_json_schema(), indent=2, ensure_ascii=False))
```

```json
{
  "properties": {
    "id": {
      "description": "用户唯一标识",
      "title": "Id",
      "type": "integer"
    },
    "name": {
      "description": "用户名",
      "maxLength": 20,
      "minLength": 3,
      "title": "Name",
      "type": "string"
    },
    "email": {
      "description": "邮箱地址",
      "title": "Email",
      "type": "string"
    },
    "age": {
      "anyOf": [
        {"type": "integer"},
        {"type": "null"}
      ],
      "default": null,
      "maximum": 150,
      "minimum": 0,
      "title": "Age"
    }
  },
  "required": ["id", "name", "email"],
  "title": "User",
  "type": "object"
}
```

这份 Schema 的下游消费者不止 Swagger UI。`Field` 的 `description`、`examples` 这些参数会进 Schema，被多个工具消费——这也是 Pydantic 模型的字段定义比普通 dataclass 更"啰嗦"的原因：每个参数都在为下游工具提供输入。三个主要消费者：

- **FastAPI 用它生成 OpenAPI**：路由函数签名里的 `user: User` 会被 FastAPI 转成 `User.model_json_schema()`，嵌入到 OpenAPI 文档里，Swagger UI 直接渲染。
- **前端可以用它生成 TypeScript 类型**：`openapi-typescript`、`quicktype` 这类工具能从 JSON Schema 生成前端类型定义，让前后端类型一致。改后端字段时前端类型自动更新，省去手动同步。
- **测试可以用它生成 mock 数据**：`hypothesis` 等属性测试库能从 Schema 生成符合约束的随机数据，覆盖边界值。

`Field` 上的 `description`、`examples`、`title` 会进 Schema，所以写好这些注释不只是文档，是整个工具链的输入——前端拿到的 OpenAPI 文档里会有这些字段，Swagger UI 会渲染它们。`model_config` 里的 `json_schema_extra` 可以追加任意字段，常用来给 OpenAPI 加 `example`：

```python
from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: str
    age: int = Field(ge=18, le=120)

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "alice",
                "email": "alice@example.com",
                "age": 28,
            }
        }
    }
```

## pydantic-settings：把配置当成数据来验证

`pydantic-settings` 是 Pydantic 的姊妹库，专门处理应用配置。它把环境变量、`.env` 文件、命令行参数都当成数据源，用同一套 BaseModel 验证规则处理。配置缺失或类型错误在启动时暴露，而不是运行时才报错——手写 `os.getenv` 只在读取时返回字符串，类型转换和校验都要自己写。

```python
# settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    database_url: str
    secret_key: str
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# .env
# APP_NAME=MyApplication
# DEBUG=true
# DATABASE_URL=postgresql://localhost/mydb
# SECRET_KEY=your-secret-key
```

`BaseSettings` 继承自 `BaseModel`，所以所有验证能力都可用：`Field` 约束、`field_validator`、`model_validator` 都能挂上去。区别在于数据源：`BaseModel` 只接收显式传入的参数，`BaseSettings` 会按优先级从多个来源读取字段值：

1. 显式传入的参数（`Settings(debug=True)`）
2. 环境变量（`DEBUG=true`）
3. `.env` 文件
4. 字段默认值

按这个优先级，本地开发用 `.env`，生产用环境变量，临时覆盖用参数，不需要改代码。配置错误会在 `Settings()` 实例化时抛 `ValidationError`，应用启动阶段就暴露问题，而不是等到某个请求触发到错误的配置值才崩溃。

### 嵌套配置

复杂配置通常需要分组，`pydantic-settings` 支持嵌套。把数据库、Redis、应用配置分成独立的 settings 类，再组合到顶层 Settings 里，每个服务的配置有自己的字段约束和默认值：

```python
from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    name: str
    user: str
    password: str


class RedisSettings(BaseSettings):
    host: str = "localhost"
    port: int = 6379
    db: int = 0


class Settings(BaseSettings):
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    app_name: str

    model_config = SettingsConfigDict(env_nested_delimiter="__")


# 环境变量用双下划线表示嵌套：
# DATABASE__HOST=db.example.com
# DATABASE__PORT=5432
# DATABASE__NAME=prod
# DATABASE__USER=app
# DATABASE__PASSWORD=***
# REDIS__HOST=cache.example.com
# APP_NAME=MyApp
```

`env_nested_delimiter="__"` 让 `DATABASE__HOST` 自动映射到 `settings.database.host`。这比把所有配置拍平成 `DATABASE_HOST`、`REDIS_HOST` 更有结构，也更容易在 docker-compose 里按服务分组——一个服务的所有配置共享同一个前缀，删除或迁移时一目了然。

### 配置验证的常见用法

配置验证的常见需求有三类：端口范围限制、日志级别枚举、列表型配置从环境变量读取。下面这个例子覆盖了这三种场景：

```python
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    port: int = Field(default=8000, ge=1024, le=65535)
    allowed_hosts: list[str] = ["localhost"]
    log_level: str = Field(pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_hosts(cls, v):
        # 允许环境变量里用逗号分隔：ALLOWED_HOSTS=a.com,b.com
        if isinstance(v, str):
            return [h.strip() for h in v.split(",")]
        return v

    model_config = SettingsConfigDict(env_prefix="APP_")
```

`env_prefix="APP_"` 让所有字段从 `APP_PORT`、`APP_ALLOWED_HOSTS` 读取，避免与系统环境变量冲突。`field_validator(mode="before")` 把逗号分隔的字符串转成列表，这是处理"环境变量只能是字符串"限制的常见模式——环境变量没有列表类型，只能用字符串编码，`before` 验证器在类型转换前介入，把字符串拆成列表再交给 Pydantic。

## 任务流案例：一次 FastAPI 请求的完整验证路径

前面分散讲了字段、验证器、序列化、Schema，现在把它们串起来，看一次真实的 API 请求如何穿过 Pydantic 的验证层。这条路径能回答三个问题：验证错误怎么定位、性能瓶颈在哪一层、验证器该挂在哪一层。

假设有一个创建用户的接口，覆盖嵌套模型、Field 约束、field_validator、model_validator、响应模型，能展示 Pydantic 在真实 API 里的完整用法：

```python
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

app = FastAPI()


class Address(BaseModel):
    street: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(pattern=r"^\d{6}$")


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    age: int = Field(ge=18, le=120)
    tags: List[str] = Field(default_factory=list, max_length=10)
    address: Address

    @field_validator("password")
    @classmethod
    def check_password_complexity(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含大写字母")
        if not any(c.islower() for c in v):
            raise ValueError("密码必须包含小写字母")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含数字")
        return v

    @model_validator(mode="after")
    def check_username_not_in_password(self) -> "CreateUserRequest":
        if self.username.lower() in self.password.lower():
            raise ValueError("密码不能包含用户名")
        return self


class CreateUserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime


@app.post("/users", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(req: CreateUserRequest) -> CreateUserResponse:
    # 走到这里时，req 已经是验证过的 CreateUserRequest 实例
    # 不需要再写 if not req.email 或 if req.age < 18 这种判断

    # 业务逻辑：存数据库（伪代码）
    user_id = save_to_db(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        age=req.age,
        address=req.address.model_dump(),
    )

    # 响应也走 Pydantic 验证，确保不泄漏 password_hash
    return CreateUserResponse(
        id=user_id,
        username=req.username,
        email=req.email,
        created_at=datetime.now(),
    )
```

请求从 HTTP 入口到业务逻辑的路径：

1. **FastAPI 接收请求体**：原始 JSON 字符串 `{"username": "alice", "email": "alice@example.com", ...}`。这一步 FastAPI 还没碰 Pydantic，只是把 body 读进来。
2. **FastAPI 调用 `CreateUserRequest.model_validate_json(payload)`**：这一步在 Rust 侧完成 JSON 解析 + 类型转换 + `Field` 约束检查。整个解析+验证在一次 Rust 调用里完成，不回到 Python。
3. **Rust 侧执行 `Field` 约束**：`username` 长度、`pattern` 匹配、`age` 范围、`address.postal_code` 正则——全部在 Rust 里跑完，不回到 Python。这是 V2 提速的主要来源。
4. **Rust 侧调用 Python 的 `field_validator`**：`check_password_complexity` 是 Python 函数，Rust 通过 `PyCallable` 回调到 Python，拿到返回值或异常。这一步有 Rust ↔ Python 的上下文切换开销。
5. **Rust 侧调用 Python 的 `model_validator`**：`check_username_not_in_password` 需要 `self`，所以等所有字段验证完后，在 Python 侧构造实例，再调用这个验证器。
6. **所有错误收集到 `ValidationError`**：如果 `username` 不合规、`password` 不含大写字母、`age` 超范围，三个错误会一次性返回，而不是改一个看到一个。错误收集在 Rust 侧完成，最后转成 Python 异常。
7. **FastAPI 拿到 `CreateUserRequest` 实例**：传给路由函数 `create_user(req)`，业务代码只处理已验证的数据。
8. **业务逻辑执行**：`save_to_db`、`hash_password` 等纯业务操作，不掺杂验证逻辑。这是 Pydantic 价值的体现——业务代码不用再写 `if not req.email` 这种判断。
9. **响应序列化**：`response_model=CreateUserResponse` 让 FastAPI 把返回值用 `CreateUserResponse.model_validate(...)` 再验证一次，确保不泄漏 `password_hash` 等字段。响应验证是常被忽略的安全边界。
10. **OpenAPI 文档自动生成**：`CreateUserRequest.model_json_schema()` 和 `CreateUserResponse.model_json_schema()` 被嵌入 OpenAPI，Swagger UI 直接渲染请求/响应示例。文档生成发生在应用启动时，不是请求时。

这条路径里，Pydantic 出现了三次：请求验证、响应验证、文档生成。一份类型注解驱动三件事，省下的是"维护三份独立 schema"的成本——请求模型改字段时，OpenAPI 文档自动更新，前端 TypeScript 类型重新生成，运行时验证规则同步生效，不需要人工同步三处。

## 常见踩坑

V1 → V2 迁移和日常使用中最容易踩的 7 个坑，前两个是迁移期的高频问题，后五个是使用中的常见误解。

### 1. `Field(regex=...)` 在 V2 里不生效

V1 用 `regex`，V2 改成 `pattern`。`regex` 在 V2 里不会报错，但会被忽略，导致约束静默失效——这是 V1 → V2 迁移里最隐蔽的坑，因为代码看起来没问题，测试也可能漏掉（只有特定输入才会触发约束）。

```python
# V1（已弃用）
sku: str = Field(regex=r"^[A-Z]{3}-\d{5}$")

# V2
sku: str = Field(pattern=r"^[A-Z]{3}-\d{5}$")
```

迁移时全局搜 `regex=` 替换成 `pattern=`，否则约束会静默消失。建议在 CI 里加一条 grep 检查，防止后续代码重新引入这个问题。

### 2. 可变默认值的拷贝开销

```python
class Config(BaseModel):
    # 看起来没问题，但每次实例化都会深拷贝这个大字典
    rules: dict = {"complex": {"nested": {"data": [...] * 1000}}}
```

`BaseModel` 会深拷贝默认值，避免实例间共享可变状态。但大对象上这个拷贝开销不可忽略——一个 1000 元素的字典默认值，每次实例化都会深拷贝一次。改用 `default_factory` 可以让默认值按需构造：

```python
class Config(BaseModel):
    rules: dict = Field(default_factory=lambda: load_rules_from_file())
```

### 3. `model_validator(mode="after")` 里修改字段不会触发重新验证

```python
class Order(BaseModel):
    total: float
    discount: float

    @model_validator(mode="after")
    def apply_discount(self) -> "Order":
        self.total = self.total * (1 - self.discount)  # 直接改 self
        return self
```

这样写能跑，但 `total` 被修改后不会重新触发 `total` 的 `field_validator`。如果 `total` 有 `Field(ge=0)` 约束，修改成负数也不会报错。`mode="after"` 的验证器是"事后调整"，不是"重新验证"。需要重新验证时，用 `self.model_validate(self.model_dump())` 显式重新走一遍——但这会带来一次完整的验证开销，如果性能敏感，更好的做法是把折扣计算放在业务层，而不是验证器里。

### 4. `Optional[X]` 不等于"有默认值"

```python
class User(BaseModel):
    name: Optional[str]      # 必填，但可以是 None
    email: Optional[str] = None  # 可选，默认 None
```

`Optional[str]` 只表示"类型可以是 `str` 或 `None`"，不表示"字段可以不传"。要让它可选，必须显式给默认值 `= None`。这是从类型提示语义继承下来的，Pydantic 没有改变它——`Optional` 在 `typing` 模块里就是 `Union[X, None]` 的别名，跟"是否有默认值"是两件事。

### 5. `model_dump()` vs `dict()` 的迁移

V2 里 `dict()` 仍可用但会告警，且行为可能与 `model_dump()` 不完全一致（递归调用、嵌套模型的序列化选项）。迁移时统一替换，避免新旧 API 混用导致行为不一致：

```python
# V1
user.dict()
user.json()
user.parse_obj(data)
user.parse_raw(json_str)

# V2
user.model_dump()
user.model_dump_json()
user.model_validate(data)
user.model_validate_json(json_str)
```

### 6. 严格模式下 `bool` 不接受 `0/1`

```python
from pydantic import BaseModel, ConfigDict


class Strict(BaseModel):
    model_config = ConfigDict(strict=True)
    flag: bool


Strict(flag=True)     # OK
Strict(flag=1)        # 报错：strict mode 不接受 int → bool
Strict(flag="true")   # 报错：strict mode 不接受 str → bool
```

严格模式下 `bool` 只接受 `True`/`False`，不接受 `0/1/"true"`。如果数据源是数据库的 `TINYINT(1)`，要么用宽松模式，要么在 `field_validator(mode="before")` 里手动转换——后者更安全，因为它把"数据库存储格式"和"业务模型类型"的转换显式化，而不是依赖隐式行为。

### 7. `EmailStr` 需要额外依赖

```bash
pip install "pydantic[email]"
```

`EmailStr` 依赖 `email-validator` 库，不安装会 `ImportError`。`pydantic[email]` 这个 extras 会自动装上。部署时如果用 `pip install pydantic` 而忘了 `[email]`，本地能跑线上报错——这类问题在 Docker 镜像里尤其常见，因为本地开发环境和 CI 构建环境的 `requirements.txt` 可能不一致。建议在 `pyproject.toml` 里声明 extras，而不是依赖开发者记住装哪个。

## 与其他库的取舍

选型时不要只看"哪个更好"，要看"数据来源是什么"。内部数据用 `dataclasses`，外部数据用 Pydantic，需要 schema 与模型分离的老项目用 `marshmallow`，需要灵活性和 slots 的库内部 API 用 `attrs`。

### Pydantic vs `dataclasses`

`dataclasses` 适合"信任输入"的场景：内部数据结构、值对象、不需要运行时验证的容器。它没有验证开销，但也没有验证保护。如果数据来自外部（HTTP、文件、消息队列），用 `dataclasses` 等于把验证责任推给调用方，长期看会出 bug——某个调用方忘了校验，脏数据就一路流到业务层。判断标准很简单：数据来源是否在你的控制范围内？是的话用 `dataclasses`，不是的话用 Pydantic。

两者可以混用：API 边界用 Pydantic，内部领域模型用 `dataclasses`，Pydantic 模型通过 `model_dump()` 转成 dict 再构造 dataclass。这种分层让验证开销只发生在边界，内部传递的是轻量级的 dataclass 实例。

### Pydantic vs `attrs`

`attrs` 比 `dataclasses` 更灵活，支持 slots、自定义 `__init__`、验证器（但需要显式声明）。它的性能比 Pydantic V1 好，但比 V2 差——V2 的 Rust 核心让 `Field` 约束的执行开销低于 `attrs` 的 Python 验证器。`attrs` 的验证器是"可选附加"，不像 Pydantic 把验证作为核心契约。如果项目已经在用 `attrs` 且没有外部数据验证需求，不必迁移；如果是新项目且需要处理 API 输入，Pydantic 更合适。`attrs` 适合库内部 API，因为它的 slots 和内存布局对性能敏感的内部对象更友好。

### Pydantic vs `marshmallow`

`marshmallow` 比 Pydantic 早，在 Flask 生态里常见。它的 schema 是单独定义的，与模型类分离——这是它的设计哲学，认为 schema 和模型应该解耦：

```python
# marshmallow
class UserSchema(Schema):
    name = fields.Str(required=True)
    age = fields.Int(validate=validate.Range(min=0))

# Pydantic
class User(BaseModel):
    name: str
    age: int = Field(ge=0)
```

`marshmallow` 的分离设计在"schema 与模型解耦"上有优势，但代价是类型注解和验证规则不共享，IDE 提示和静态检查跟不上。新项目用 Pydantic 更主流；老 Flask 项目迁移成本高时可以保留 `marshmallow`，新接口可以试 `pydantic` + Flask-Pydantic 扩展，逐步替换而不是一次性重写。

## 错误处理与排查

### ValidationError 的结构

验证失败时，Pydantic 抛出 `ValidationError`，里面包含所有字段的错误信息——不是只报第一个错误，而是收集完所有错误再抛出。这个设计让前端可以一次性显示所有字段问题，用户不用反复提交。

```python
from pydantic import BaseModel, ValidationError, Field


class User(BaseModel):
    name: str = Field(min_length=3)
    age: int = Field(ge=0, le=150)


try:
    User(name="ab", age=200)
except ValidationError as e:
    print(e.error_count())           # 2
    for err in e.errors():
        print(err)
        # {'type': 'string_too_short', 'loc': ('name',), 'msg': 'String should have at least 3 characters', 'input': 'ab', 'ctx': {'min_length': 3}}
        # {'type': 'less_than_equal', 'loc': ('age',), 'msg': 'Input should be less than or equal to 150', 'input': 200, 'ctx': {'le': 150}}
```

`errors()` 返回一个列表，每项包含五个字段，覆盖了"什么错、错在哪、错的原因、错的输入、错的上下文"：

- `type`：错误类型枚举（`string_too_short`、`less_than_equal`、`value_error` 等），可以用来做 i18n 或前端错误映射。前端按 `type` 显示对应的本地化文案，比按 `msg` 字符串匹配更稳定。
- `loc`：错误位置元组，嵌套字段是 `("address", "city")`，列表元素是 `("tags", 0)`。`loc` 是元组不是字符串，因为列表索引是整数，用点分字符串会丢失类型信息。
- `msg`：人类可读的错误信息。默认是英文，可以通过 `errors()` 的 `include_url` 参数控制是否包含文档链接。
- `input`：触发错误的原始输入值。调试时很有用，可以看到"用户到底传了什么"。
- `ctx`：约束参数（`{"min_length": 3}`、`{"le": 150}`），用于自定义错误信息。前端可以用它显示"密码至少需要 8 位"这种带具体数字的提示。

### 把 ValidationError 转成 HTTP 响应

FastAPI 自动把 `ValidationError` 转成 422 响应，但其他框架需要手动处理。手动处理的好处是可以自定义错误格式，让它匹配前端的错误处理约定：

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

app = FastAPI()


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": [
                {
                    "field": ".".join(str(loc) for loc in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"],
                }
                for err in exc.errors()
            ]
        },
    )
```

把 `loc` 转成点分路径（`address.city` 而不是 `("address", "city")`）对前端更友好。前端表单校验库通常按字段路径匹配错误，点分字符串比元组更容易对接。

### 排查指引

遇到验证问题时，先按症状定位，再深入排查：

| 症状 | 可能原因 | 排查方向 |
|------|----------|----------|
| 约束不生效 | `Field(regex=...)` 在 V2 被忽略 | 改成 `pattern=` |
| 验证器没被调用 | `@classmethod` 顺序错了 | `@field_validator` 在上，`@classmethod` 在下 |
| `Optional[X]` 报"字段缺失" | 没给默认值 | 改成 `Optional[X] = None` |
| 严格模式下 `bool` 报错 | 不接受 `0/1/"true"` | 用宽松模式或 `field_validator(mode="before")` 转换 |
| `EmailStr` ImportError | 没装 `email-validator` | `pip install "pydantic[email]"` |
| 嵌套模型字段错误定位错 | `loc` 是元组不是字符串 | 用 `".".join(loc)` 转成点分路径 |
| 性能不如预期 | 自定义验证器太多 | 把能改成 `Field` 约束的都改掉 |

表格里的前四项是 V1 → V2 迁移后最常见的问题，后三项是日常使用中的高频踩坑。性能问题如果排除了验证器数量，下一步是看模型嵌套深度——3 层以上嵌套在 V1 里是性能黑洞，V2 里虽然好很多，但仍建议拆分。

## 数据库模型与 ORM 集成

Pydantic 不直接做 ORM，但常与 SQLAlchemy 配合。常见模式是"ORM 模型 + Pydantic schema"分离：ORM 模型负责持久化，Pydantic schema 负责 API 边界验证和字段暴露控制。这种分离让数据库结构和 API 契约可以独立演化。

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, ConfigDict

Base = declarative_base()


# SQLAlchemy 模型：负责持久化
class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)


# Pydantic schema：负责 API 边界验证
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime
    # 注意：不暴露 hashed_password


class UserCreate(BaseModel):
    username: str
    email: str
    password: str = Field(min_length=8)


# 从 ORM 对象构造响应
def get_user(user_id: int) -> UserOut:
    orm_user = session.query(UserORM).get(user_id)
    return UserOut.model_validate(orm_user)
```

`from_attributes=True` 让 `model_validate` 用 `getattr` 取值，所以 `UserOut.model_validate(orm_user)` 能直接从 SQLAlchemy 对象读字段。`UserOut` 不声明 `hashed_password`，所以即使 ORM 对象上有这个字段，响应里也不会出现——这是"用 schema 控制暴露"的标准模式，比在业务代码里手动 `del orm_user.hashed_password` 更可靠，因为 schema 是声明式的，不会因为某次代码修改而漏掉。

SQLModel 是 Pydantic + SQLAlchemy 的融合方案，把两者合并成一个类，适合中小项目。大型项目里分离 ORM 和 schema 更清晰，因为持久化关注点和 API 边界关注点会逐渐分化——ORM 模型要适应数据库迁移、索引优化，API schema 要适应前端需求变化，两者耦合在一起会让任何一方的改动都牵动另一方。

## Webhook 验证

Webhook 是典型的"不信任外部输入"场景：来自 GitHub、Stripe 的 payload 必须验证签名和字段。签名验证保证数据来源可信，字段验证保证数据结构符合预期——两者缺一不可，签名通过但字段结构变化同样会导致处理逻辑出错。

```python
from typing import Literal
from pydantic import BaseModel, HttpUrl, Field


class GitHubWebhook(BaseModel):
    action: Literal["opened", "closed", "reopened"]
    number: int = Field(ge=1)
    repository: dict  # 嵌套结构，按需展开
    sender: dict
    url: HttpUrl = Field(description="仓库 URL")


# FastAPI 端点
@app.post("/webhooks/github")
def github_webhook(
    payload: GitHubWebhook,
    x_hub_signature_256: str = Header(...),
    x_github_event: str = Header(...),
    raw_body: bytes = Body(...),
):
    # 1. 验证签名（用 raw_body，不是解析后的 payload）
    if not verify_signature(raw_body, x_hub_signature_256, secret):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid signature")

    # 2. payload 已经是验证过的 GitHubWebhook 实例
    if x_github_event == "pull_request":
        handle_pr_event(payload.action, payload.number)

    return {"status": "ok"}
```

Webhook 集成里有三个细节，没注意到会在生产环境出诡异问题——签名验证失败但日志显示请求正常，或者新事件类型被静默丢弃。按重要性排序：

- **签名验证用原始 body**：`payload: GitHubWebhook` 已经被 FastAPI 解析过，签名要用 `raw_body: bytes = Body(...)` 拿原始字节算 HMAC，否则换行符、字段顺序差异会导致签名不匹配。这是 Webhook 集成里最常见的坑——签名总是对不上，但代码看起来没问题。
- **`Literal` 限定 action 枚举**：GitHub 新增 action 时，旧版本 Pydantic 会拒绝，避免未处理的 case 静默通过。这条策略的代价是需要定期跟进 GitHub 的 action 新增，否则合法事件会被拒。
- **`HttpUrl` 规范化 URL**：自动去掉尾部斜杠、补全协议，避免下游处理时出意外。

## 迁移与采用顺序

新项目和 V1 迁移项目分别有不同的采用路径。核心判断是：Pydantic 的价值在"不信任边界"上最大，越往系统内部、越信任数据，它的收益越小。

### 新项目

直接用 Pydantic V2，没有理由从 V1 开始。`pydantic-settings` 单独装，因为它从 2.0 起独立成包——`pip install pydantic pydantic-settings`。如果用 FastAPI，FastAPI 0.100+ 已原生支持 V2，不需要额外配置。

### V1 项目迁移

迁移成本主要在三处。前两处是机械性改动，第三处需要重新审视验证逻辑：

1. **API 重命名**：`.dict()` → `.model_dump()`、`.parse_obj()` → `.model_validate()`、`@validator` → `@field_validator`、`Config` 内部类 → `model_config = ConfigDict(...)`。可以用 `bump-pydantic` 工具半自动迁移，但迁移后要逐个检查，工具会漏掉一些动态调用。
2. **自定义验证器签名变化**：V1 的 `@validator` 接收 `(cls, v, values, config, field)`，V2 的 `@field_validator` 只接收 `(cls, v)` 或 `(cls, v, info)`。依赖 `values` 的逻辑要改成 `model_validator(mode="after")` 里访问 `self`。这一步是迁移里最容易出 bug 的地方，因为 `values` 在 V1 里是已验证字段的字典，在 V2 里改用 `self` 后是字段属性，访问方式不同。
3. **严格模式默认行为**：V1 的某些隐式转换在 V2 里改了，比如 `bool("false")` 在 V1 是 `True`（非空字符串），在 V2 是 `False`（识别 "false" 字面量）。迁移后要重跑测试覆盖这些边界，尤其是依赖隐式转换的测试用例。

### 采用顺序建议

按 ROI 从高到低排序，建议的采用顺序如下。每一步都可以独立交付价值，不需要一次性全做：

- **第一步：API 边界**。把 FastAPI 路由的请求/响应模型用 Pydantic 重写，拿到验证 + 文档 + 类型提示三重收益。API 边界本来就是"不信任数据"的地方，Pydantic 的价值在这里最直接，ROI 最高。
- **第二步：配置管理**。用 `pydantic-settings` 替代手写的 `os.getenv` 调用，让配置缺失和类型错误在启动时暴露，而不是运行时。改动小，但能消除一类"生产环境配置写错导致运行时崩溃"的 bug。
- **第三步：内部领域模型**。把核心业务对象用 Pydantic 建模，配合 `strict=True` 让内部传递的类型不匹配尽早暴露。这一步要权衡——内部模型如果频繁变更，Pydantic 的验证开销可能不划算。
- **第四步：ORM 集成**。用 Pydantic schema 包装 SQLAlchemy 模型，控制 API 响应的字段暴露，解决"ORM 模型字段和 API 响应字段不一致"的问题。
- **暂缓**：纯计算函数的输入输出、性能敏感的热路径（每秒百万次调用的代码），这些场景 `dataclasses` 或裸 dict 更合适。判断标准是：如果这段代码已经在用 profiler 优化，验证开销可能就是下一个瓶颈。

把它放在边界，让内部代码处理已经验证过的 Python 对象，是 Pydantic 最经济的用法。

## 官方资源

- GitHub：https://github.com/pydantic/pydantic
- 文档：https://docs.pydantic.dev/
- PyPI：https://pypi.org/project/pydantic
- 讨论组：https://github.com/pydantic/pydantic/discussions
- pydantic-settings：https://docs.pydantic.dev/latest/concepts/settings/
