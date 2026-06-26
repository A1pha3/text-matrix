---
title: "FTShare Python SDK：把 176 个金融数据接口封装成 pandas 一行调用"
date: 2026-06-26T20:45:00+08:00
draft: false
categories:
  - 技术笔记
tags:
  - 金融数据
  - Python-SDK
  - Agent生态
  - 开源项目
slug: ftshare-python-sdk-financial-data-agent-access-layer
author: 钳岳星君
description: "上海非凸智能 6-23 开源的 FTShare Python SDK（MIT 协议），用 mixin 组合 + endpoint registry + DataFrame 优先把 176 个金融数据接口变成 pandas 一行调用；它是 ftshare 生态中 agent / MCP / Skill 投研工作流的数据访问层。"
---

# FTShare Python SDK：把 176 个金融数据接口封装成 pandas 一行调用

## 核心判断

2026 年 6 月 23 日，上海非凸智能科技有限公司（ft.tech）在 GitHub 开源了 [ftshare-python-sdk](https://github.com/ftshare-lab/ftshare-python-sdk)。3 天后这个仓库只有 4 颗 star，但代码密度不小：**176 个 endpoint，176 个自动生成的 Python 方法，14 个 mixin 组合到一个 client**——目标是让任何需要行情、财务、宏观、基金、期货数据的开发者，不用关心 176 个 REST API 的 URL、参数签名、响应格式差异，写一行代码就拿到 pandas DataFrame。

支撑这个判断的事实是这个 SDK 在 ftshare 生态里的清晰卡位。它不是孤立项目，而是 4 层栈里最底下一层：

```text
FTShare 数据服务          ← 行情、财务、宏观、港股、全球指数……
    ↓
ftshare-python-sdk        ← Python 数据访问层（本文主角）
    ↓
ftshare-mcp               ← Agent 可调用的 MCP 工具层
    ↓
ftshare-skills            ← 投研任务与业务工作流层
    ↓
Agent 应用                 ← 面向最终用户的投研分析体验
```

把 [NVIDIA SkillSpector](https://txtmix.com/posts/tech/nvidia-skillspector-agent-skill-security-scanner/) 那篇和这篇放在一起看会清楚很多：SkillSpector 解决的是「agent skill 安不安全」的问题，本篇这个 SDK 解决的是「agent skill 怎么拿到数据」的问题。**它们俩是同一波 agent skill 基础设施成熟化浪潮的不同切面**——一边是 skill 的安全审查，一边是 skill 的数据接入。

这个 SDK 在工程上有四个值得拆解的决策：

- **Mixin 组合**——14 个业务域 mixin（Corporate / Economic / Etf / Finance / Fund / Futures / GlobalIndex / Goodwill / Hk / Holder / Index / Market / Pledge / Stock）共同继承到 `FtshareClient` 一个类里，业务增长时只加 mixin 不改 client。
- **Endpoint registry 单一事实源**——176 个接口的 path / params / max_page_size / doc_file 都登记在 `endpoints.ENDPOINTS` 字典里，方法体只负责参数透传，业务元数据不散落。
- **DataFrame 优先 + 三层降级**——默认返回 pandas DataFrame，但一行 `as_dataframe=False` 退到 Python rows，一行 `raw=True` 退到原始 JSON，让调用方按使用场景选择数据粒度。
- **分页 4 模式**——`page`/`page_size` / `limit` 自动翻页 / `all_pages` 全量拉 / `fetch_all` 通用入口——分别覆盖精确查询、批量取数、全量同步、跨接口分页四类场景。

值得注意的几件事：

- **MIT 协议 + Python 3.9+**——和 akshare / tushare 这类中国金融数据 SDK 同档协议门槛，企业内部用没有合规压力。
- **默认不绑凭据**——`market_api()` 工厂函数不需要任何 token；服务端在 `market.ft.tech` 公开承载，开发者零摩擦上手。
- **测试分两层**——`pytest` 默认跑 mock HTTP 的单元测试；真实接口集成测试用 `FTSHARE_RUN_INTEGRATION=1` 显式开启，避免 CI 默认打挂。
- **新生态新公司**——ftshare-lab 组织 6-23 才在 GitHub 创建，目前只公开了这一个 repo；这是「AI-native financial data」品牌叙事的第一次公开代码落地。

这篇文章把这个 SDK 当成「agent skill 时代的数据接入层样本」来拆解：从生态卡位、14 个 mixin 怎么组合、176 个 endpoint 怎么集中管理、一次调用怎么流过 4 层处理，到怎么把 DataFrame 直接接进 pandas / quant / agent toolchain。

## 学习目标

读完本文后，你应当能够：

1. 说出 ftshare 生态 4 层栈（数据服务 / Python SDK / MCP / Skills / Agent 应用）的职责划分，以及 FTShare Python SDK 在其中的位置。
2. 解释 `FtshareClient` 怎么通过 14 个 mixin 组合实现「一个客户端覆盖 176 个 endpoint」，以及 mixin 模式比「一个大类」或「多个独立 client 类」的工程优势。
3. 描述 endpoint registry 模式（`endpoints.ENDPOINTS` 字典 + `Endpoint` dataclass）怎么让 path / params / max_page_size 等元数据成为单一事实源，以及为什么这种模式特别适合 SDK 这类「接口元数据从服务端 schema 自动生成」的场景。
4. 列举 SDK 的三层返回控制（DataFrame 默认 / `as_dataframe=False` 退到 rows / `raw=True` 退到 JSON）各自的适用场景。
5. 区分分页 4 模式（`page`/`page_size` / `limit` / `all_pages` / `fetch_all`）的语义差异，并指出 SDK 怎么在 `limit` 超过单页上限时自动翻页。
6. 把这个 SDK 接入到一个 LangChain / MCP / Skill 工作流里，调用 `baidu_financial_calendar` 拉财经日历数据并转成 DataFrame。

## 目录

- [核心判断](#核心判断)
- [学习目标](#学习目标)
- [生态卡位：4 层栈中的数据访问层](#生态卡位4-层栈中的数据访问层)
- [总览图：从用户调用到 HTTP 响应](#总览图从用户调用到-http-响应)
- [Mixin 组合模式：一个 client 覆盖 14 个业务域](#mixin-组合模式一个-client-覆盖-14-个业务域)
- [Endpoint registry：176 个接口的单一事实源](#endpoint-registry176-个接口的单一事实源)
- [任务如何流过系统：一次完整调用](#任务如何流过系统一次完整调用)
- [DataFrame 优先 + 三层返回控制](#dataframe-优先--三层返回控制)
- [分页 4 模式](#分页-4-模式)
- [异常三层分类](#异常三层分类)
- [与同类 SDK 的差异点](#与同类-sdk-的差异点)
- [决策启示：skill 作者 / 数据团队 / 量化研究者各看什么](#决策启示skill-作者--数据团队--量化研究者各看什么)
- [采用顺序与边界](#采用顺序与边界)
- [参考资料](#参考资料)

## 生态卡位：4 层栈中的数据访问层

SDK 不是孤立工具，它是 ftshare 4 层栈里的 Python 数据访问层。这层定位决定了它的设计取舍：

- **向下**：对接 FTShare 数据服务（`market.ft.tech/data/` 域下的 REST API）。SDK 不需要自己实现数据采集、清洗、存储——这些都在服务端完成。
- **向上**：为 ftshare-mcp（Agent 可调用的 MCP 工具层）和 ftshare-skills（投研任务层）提供稳定的数据基础。这两个上层产品（目前还在 ftshare-lab 内部开发）会大量调用本 SDK 的方法，把每个 endpoint 包成一个 MCP tool 或一个 SKILL 描述。
- **横向**：直接面向独立开发者——quant researcher / data scientist / 想自己拉数据的金融 AI 应用开发者，他们不需要等 MCP/Skill 中间层，可以直接 `pip install ftshare` 用起来。

这个定位和 akshare / tushare / baostock 这类中国金融数据 SDK 的传统定位（直接面向 quant 开发者）有一个关键差异：**FTShare SDK 同时是为上层 agent 工具链设计的**。`as_dataframe=False` 返回 Python rows 而不是只返回 DataFrame、默认 `headers` 参数可注入、`base_url` 可切换——这些都是为了让上层 MCP / Skill 能按 tool calling 的协议把数据塞回 agent 上下文。

`README.md` 里画出的 4 层栈图本身就是一个产品策略声明——它在告诉读者：「这个 SDK 不会和 MCP 抢活，MCP 也不会和 SDK 抢活」。每一层的边界都清楚：SDK 管 HTTP 调用和数据形态，MCP 管 tool schema，Skills 管业务编排，Agent 管用户交互。

## 总览图：从用户调用到 HTTP 响应

```text
        用户代码
          │
          ▼
    ft.market_api()           ← 工厂：构造 FtshareClient
    FtshareClient(...)        ← 14 mixin + BaseClient 多继承
          │
          ▼
   market.baidu_financial_calendar(...)
   ↑ MarketApiMixin 里的方法体
   1. 校验参数
   2. 查 ENDPOINTS['baidu_financial_calendar'].path
   3. 组 request_params（None 值过滤）
   4. 调 self.get_paginated(path, ...)
          │
          ▼
   BaseClient.get_paginated
   1. validate_pagination(page, page_size, max_pages, max_page_size, limit)
   2. 决定单页还是自动翻页
   3. 循环调 self.get(path, ...)
          │
          ▼
   BaseClient.get
   1. 拼 URL = base_url + path
   2. 用 self.session.get(...)（共享 requests.Session）
   3. 注入 timeout + headers
   4. 校验 status → raise FtshareHTTPError if 非 2xx
   5. 解析 JSON → raise FtshareDecodeError if 失败
   6. raise_for_api_error(payload) → raise FtshareAPIError if code != 0
   7. extract_tabular(payload) → 从 data.records / data.items / items / 顶层数组取数据
   8. select_fields(rows, fields) → 字段筛选
   9. to_dataframe(rows) → 转 pandas.DataFrame
          │
          ▼
   用户拿到 df
```

每一层职责清晰且只做一件事：

- **mixin 方法体**：参数透传到 `get_paginated`，业务元数据查 `ENDPOINTS`
- **`get_paginated`**：分页策略
- **`get`**：单次 HTTP 请求 + 响应处理 + 数据形态转换
- **`to_dataframe` / `select_fields` / `extract_tabular`**：纯函数，可在任何上下文复用

这种「每层只做一件事」的设计让上层错误几乎不可能污染下层——mixin 写错了不会破坏 HTTP 解析；HTTP 解析改进了不会影响分页逻辑。

## Mixin 组合模式：一个 client 覆盖 14 个业务域

`FtshareClient` 的继承关系是这个 SDK 最值得讲的设计决策之一：

```python
class FtshareClient(
    CorporateApiMixin,
    EconomicApiMixin,
    EtfApiMixin,
    FinanceApiMixin,
    FundApiMixin,
    FuturesApiMixin,
    GlobalIndexApiMixin,
    GoodwillApiMixin,
    HkApiMixin,
    HolderApiMixin,
    IndexApiMixin,
    MarketApiMixin,
    PledgeApiMixin,
    StockApiMixin,
    BaseClient,
):
    ...
```

14 个 mixin + `BaseClient`，全部拼到一个类里。结果是 `market = ft.market_api()` 这一行返回的实例同时支持 176 个方法（按业务域分组），调用入口统一。

为什么是 mixin 模式而不是其他方案？

**对比方案 A：一个 6000 行的 `FtshareClient` 大类**

176 个方法塞进一个类，文件会膨胀到几千行。Python 没有 partial class；任何一次添加新方法都要改这个文件，git 冲突频繁。

**对比方案 B：14 个独立 client 类（`MarketClient` / `FinanceClient` / ...）**

调用方要构造 14 个实例或选择 1 个。这违反「数据集中在一个 client」的直觉；上层 MCP tool 实现要为每个业务域分别注册 14 个 client。

**对比方案 C：plugin registry + 动态方法挂载**

启动时遍历 `apis/` 目录，把每个 mixin 的方法挂到 `FtshareClient` 上。这种动态机制对静态类型检查、IDE 自动补全都不友好。

**选 mixin 模式的工程优势**：

1. **静态可分析**——IDE 能给 `market.baidu_financial_calendar` 自动补全；mypy / pyright 能检查参数类型
2. **业务域物理隔离**——`apis/market.py` 改动只影响 `MarketApiMixin`，不会牵动 Economic 等
3. **添加新 mixin 是零侵入**——加一个 `BondApiMixin` 不需要改 `FtshareClient` 主体
4. **测试友好**——每个 mixin 可以单独 mock 测试，单元测试不需要构造完整的 `FtshareClient`

代价是 mixin 之间不能共享私有状态（因为它们只是「提供方法」的薄层），但 SDK 场景里 mixin 方法不需要共享状态——它们只通过 `self.method()` 调到 `BaseClient` 提供的 HTTP / 分页 / 异常能力。

`apis/__init__.py` 是 mixin 注册表，任何新加的 mixin 都要在那里 export 一次，再加到 `FtshareClient` 继承列表里。这是显式的「注册新业务域」仪式，但保证了 4 行代码可发现的代价是可接受的。

## Endpoint registry：176 个接口的单一事实源

`endpoints.py` 是这个 SDK 设计的另一个核心。它不长这样：

```python
# 错误示范：方法体里写死 path
def baidu_financial_calendar(self, ...):
    return self.get("api/v1/market/data/finance/financial-calendar/baidu", ...)
```

而是这样：

```python
@dataclass(frozen=True)
class Endpoint:
    name: str
    path: str | None
    method: str = "GET"
    title: str = ""
    doc_file: str | None = None
    original_api: str = ""
    params: tuple[str, ...] = ()
    path_params: tuple[str, ...] = ()
    max_page_size: int = 200

ENDPOINTS: dict[str, Endpoint] = {
    'baidu_financial_calendar': Endpoint(
        name='baidu_financial_calendar',
        path='api/v1/market/data/finance/financial-calendar/baidu',
        method='GET',
        title='百度财经日历',
        doc_file='百度财经日历.md',
        original_api='baidu_financial_calendar',
        params=('start_date', 'end_date', 'category', 'page', 'page_size'),
        path_params=(),
        max_page_size=200,
    ),
    # ... 176 个
}
```

然后 mixin 方法查这个表：

```python
def baidu_financial_calendar(self, ...):
    ...
    path = ENDPOINTS['baidu_financial_calendar'].path
    return self.get_paginated(path, ...)
```

这种「endpoint registry 单一事实源」模式在 SDK 场景里几乎是必备的，原因有三：

**1. 接口元数据自动化**

176 个接口的 path / params / max_page_size 完全可以从服务端 OpenAPI schema 自动生成。开发者写了一个一次性脚本（推测在 `tools/` 或 `scripts/` 下，不在本仓库内）从 FTShare 服务端 schema 生成 `ENDPOINTS` 字典，手写 mixin 方法体只保留参数透传 + 文档字符串。**新增接口的工作量从「写一个完整 Python 方法」降到「schema 多一条 + mixin 加一个 5 行方法体」**。

**2. 文档一致**

`title` / `doc_file` / `original_api` 字段让 `docs/API_REFERENCE.md` 能自动生成——README 里说的「本文档由 SDK 方法 docstring 和 `ftshare.endpoints.ENDPOINTS` 生成」就是这个机制。开发者改 endpoint title 时，文档、SDK 方法、客户端代码都从同一源更新。

**3. 运行时反射**

`from ftshare.endpoints import ENDPOINTS; print(len(ENDPOINTS))` 直接看到 176。SDK 也支持 `print(endpoint.path)` / `print(endpoint.params)` 查单个接口元数据。这对调试、代码生成、自适应路由都极有用。

`Endpoint` 用 `@dataclass(frozen=True)` 装饰——一旦登记就不能改，运行时安全。`max_page_size=200` 是默认页大小（个别接口如 `stk_limit` / `stk_premarket` 是 500）——这种 per-endpoint 配置不需要方法体关心，全部从 registry 读。

## 任务如何流过系统：一次完整调用

为了让 14 mixin + endpoint registry + BaseClient 三层抽象落地，看一个具体的「拉 2026-05-26 当天的财经日历」怎么走完整流程。

**用户代码：**

```python
import ftshare as ft

market = ft.market_api(timeout=20)
df = market.baidu_financial_calendar(
    start_date="2026-05-26",
    end_date="2026-05-27",
    category="economic",
    limit=5,
)
print(df)
```

**第 1 步：`market_api()` 工厂**

```python
# ftshare/__init__.py
def market_api(
    base_url: str | None = None,
    timeout: float = 10,
    headers: Mapping[str, str] | None = None,
) -> FtshareClient:
    return _client.market_api(
        base_url=base_url or BASE_URL,
        timeout=timeout,
        headers=headers,
    )
```

工厂函数把模块级 `BASE_URL`（默认 `https://market.ft.tech/data/`）和用户传的参数组装成 `FtshareClient` 实例。`BASE_URL` 是模块级变量——可以通过 `ft.set_base_url(...)` 全局改；也可以在 `market_api(base_url=...)` 时只改这一个 client。`timeout=20` 和 `headers={}` 透传到 `BaseClient.__init__`。

**第 2 步：`FtshareClient.__init__`（继承自 `BaseClient`）**

```python
# base.py
def __init__(
    self,
    base_url: str | None = None,
    timeout: float = 10,
    headers: Mapping[str, str] | None = None,
    session: requests.Session | None = None,
) -> None:
    self.base_url = normalize_base_url(base_url or get_base_url())
    self.timeout = timeout
    self.session = session or requests.Session()
    self.headers = dict(headers or {})
```

关键点：

- `normalize_base_url("https://market.ft.tech/data/")` → 统一成带尾斜杠的规范形式（`rstrip("/") + "/"`），用户传不带斜杠也照样能用
- `session = requests.Session()` 让多次请求共享 TCP 连接（HTTP keep-alive），比裸 `requests.get()` 快得多
- `headers` 在每次请求都注入，方便上层 MCP/Skill 透传 trace id、user agent 等

**第 3 步：mixin 方法体**

```python
# apis/market.py
def baidu_financial_calendar(
    self,
    start_date,
    end_date,
    category=None,
    page=None,
    page_size=None,
    limit=None,
    all_pages=False,
    max_pages=None,
    *,
    raw=False,
    fields=None,
    as_dataframe=True,
    **kwargs,
):
    request_params = {
        'start_date': start_date,
        'end_date': end_date,
        'category': category,
    }
    request_params.update(kwargs)
    path = ENDPOINTS['baidu_financial_calendar'].path
    return self.get_paginated(
        path,
        page=page,
        page_size=page_size,
        limit=limit,
        all_pages=all_pages,
        max_pages=max_pages,
        raw=raw,
        fields=fields,
        as_dataframe=as_dataframe,
        **request_params,
    )
```

方法体几乎不做事：构造一个 `request_params` 字典（注意 `**kwargs` 让上层未来添加的新参数也能透传——这是「schema 自动生成」的前提），查 `ENDPOINTS['...'].path` 拿 URL，调 `get_paginated`。mixin 方法 = 纯参数透传 + 查表 + 文档字符串。

**第 4 步：`get_paginated` 分页调度**

```python
def get_paginated(
    self,
    path,
    *,
    page=None,
    page_size=None,
    limit=None,
    all_pages=False,
    max_pages=None,
    raw=False,
    fields=None,
    as_dataframe=True,
    **params,
):
    endpoint = ENDPOINTS_BY_PATH.get(path)  # 通过 path 反查 endpoint
    max_page_size = endpoint.max_page_size if endpoint else DEFAULT_MAX_PAGE_SIZE

    validate_pagination(
        page=page or 1,
        page_size=page_size,
        max_pages=max_pages,
        max_page_size=max_page_size,
        limit=limit,
    )

    # 决策：单页 or 自动翻页
    if not all_pages and (limit is None or limit <= max_page_size):
        # 单页路径
        return self.get(
            path,
            raw=raw,
            fields=fields,
            as_dataframe=as_dataframe,
            page=page,
            page_size=page_size,
            **params,
        )

    # 自动翻页路径
    rows = []
    current_page = page or 1
    pages_fetched = 0
    while True:
        if max_pages is not None and pages_fetched >= max_pages:
            break
        payload = self.get(
            path,
            raw=True,  # 中间过程要 raw 才能看到 pages
            page=current_page,
            page_size=page_size or max_page_size,
            **params,
        )
        rows.extend(extract_tabular(payload))
        total_pages = total_pages(payload)
        if total_pages is None or current_page >= total_pages:
            break
        current_page += 1
        pages_fetched += 1
        if limit is not None and len(rows) >= limit:
            break

    if limit is not None and limit < len(rows):
        rows = rows[:limit]

    if fields:
        rows = select_fields(rows, fields)

    if as_dataframe and not raw:
        return to_dataframe(rows)
    if raw:
        return rows
    return rows
```

分页的核心决策树：

- `all_pages=False` 且 `limit <= max_page_size` → **单页路径**，1 次 HTTP 请求
- 否则 → **自动翻页路径**，循环到 `total_pages` 到达或 `max_pages` 上限或 `limit` 达到

`limit=5` 在这个例子里小于 `max_page_size=200`，所以走单页路径。

**第 5 步：`get` 单次 HTTP**

```python
def get(self, path, *, raw=False, fields=None, as_dataframe=True, **params):
    return self._request("GET", path, raw=raw, fields=fields, as_dataframe=as_dataframe, **params)

def _request(self, method, path, *, raw, fields, as_dataframe, **params):
    # 过滤 None 值参数
    request_params = {k: v for k, v in params.items() if v is not None}
    url = self._build_url(path)

    response = self.session.get(
        url,
        params=request_params,
        timeout=self.timeout,
        headers=self.headers,
    )

    # HTTP 状态码校验
    if not 200 <= response.status_code < 300:
        raise FtshareHTTPError(response.status_code, response.url, response.text)

    # JSON 解析
    try:
        payload = response.json()
    except ValueError as exc:
        raise FtshareDecodeError(response.url, response.text) from exc

    # 业务状态码校验
    raise_for_api_error(payload)

    if raw:
        return payload

    # 表格提取
    rows = extract_tabular(payload)

    # 字段筛选
    if fields:
        rows = select_fields(rows, fields)

    # 形态转换
    if as_dataframe:
        return to_dataframe(rows)
    return rows
```

这是 SDK 真正的「响应处理核心」。它做了 7 件事：

1. 过滤 None 参数——Python 的 `requests` 库会把 `None` 转成 `?key=None` 字符串，污染 URL
2. 拼 URL（base_url + path）
3. 用共享 `session.get` 发请求
4. 状态码非 2xx → `FtshareHTTPError`
5. JSON 解析失败 → `FtshareDecodeError`
6. 业务 code != 0 → `FtshareAPIError`
7. `extract_tabular` → `select_fields` → `to_dataframe` 三段管道

每段都是纯函数（除 `to_dataframe` 内部懒加载 pandas），出 bug 时定位容易。

**第 6 步：用户拿到 DataFrame**

`extract_tabular` 从响应中按优先级提取 `data.records` / `data.items` / `items` / 顶层数组——这种「适配多种 envelope 形状」的设计让 SDK 能容忍服务端响应结构的小幅演化（不会因为某一层改名就崩）。

最终用户拿到的就是 pandas DataFrame：

```
   category   stat_date region   time  ... star negative positive capitalization
0  economic  2026-05-26     英国  07:01  ...    1                                0
1  economic  2026-05-26    新加坡  13:00  ...    1                                0
```

可以直接接 `.groupby()` / `.merge()` / `.plot()`，零摩擦进 quant / data science 工作流。

## DataFrame 优先 + 三层返回控制

这个 SDK 最让 quant developer 舒服的设计是「DataFrame 默认 + 三层降级」：

```python
# 默认：DataFrame
df = market.baidu_financial_calendar(...)

# 退到 Python rows（list[dict]）
rows = market.baidu_financial_calendar(..., as_dataframe=False)

# 退到原始 JSON
payload = market.baidu_financial_calendar(..., raw=True)
```

三种形态对应的使用场景：

| 形态 | 调用方式 | 数据量 | 典型场景 |
|---|---|---|---|
| **DataFrame**（默认） | `market.method(...)` | 中 | 直接进 pandas 流水线；quant 研究 |
| **Python rows** | `as_dataframe=False` | 小-中 | MCP tool 输出 JSON-Lines；序列化到磁盘 |
| **原始 JSON** | `raw=True` | 任意 | 调试；字段映射研究；payload 反序列化 |

为什么默认 DataFrame 而不是 dict？两个原因：

1. **中国 quant 圈的事实标准**——akshare / tushare / baostock 都是 DataFrame 优先，新 SDK 不这样选就会被比较时扣分
2. **agent toolchain 友好**——MCP tool 输出 JSON-Lines 时，`as_dataframe=False` 返回的 list[dict] 几乎不用处理就能塞进 tool result；LLM 读 dict 列表比读 DataFrame repr 容易得多

但 SDK 留好了降级路径——`raw=True` 让上层完全控制响应处理，比如想做自定义反序列化、字段重命名、按 envelope 选分支解析，都不受 SDK 默认行为的限制。

`to_dataframe` 函数本身很简单：

```python
def to_dataframe(result):
    import pandas as pd
    if isinstance(result, list):
        return pd.DataFrame(result)
    return pd.DataFrame([result])
```

懒加载 pandas 是关键——SDK 在被 import 时不强制加载 pandas，只有真正调用 DataFrame 路径才触发。对只用 `as_dataframe=False` 或 `raw=True` 的上层 MCP tool，SDK import 几乎零开销。

## 分页 4 模式

中国金融数据接口几乎全部分页——这是因为数据量大（千股千评、龙虎榜全量都是万行级别）。SDK 必须把分页抽象做得足够好。FTShare 给的是 4 模式：

```python
# 模式 1：精确页码（page + page_size）
df = market.baidu_financial_calendar(
    start_date="...", end_date="...",
    page=2, page_size=50,
)

# 模式 2：取最多 N 条（limit 自动翻页）
df = market.baidu_financial_calendar(
    start_date="...", end_date="...",
    limit=300,  # 单页上限 200，SDK 自动翻页并合并
)

# 模式 3：自动翻到底（all_pages）
df = market.baidu_financial_calendar(
    start_date="...", end_date="...",
    all_pages=True,
    page_size=200,
    max_pages=5,  # 安全上限
)

# 模式 4：通用入口（fetch_all）
df = market.fetch_all(
    "baidu_financial_calendar",
    start_date="...", end_date="...",
    page_size=200,
)
```

四个模式的语义差异值得记一下：

- `page` + `page_size`：**精确控制**单页结果——调试 / 单页验证 / 已知具体页码时用
- `limit`：**结果数优先**——「我最多要 N 条」，SDK 内部自动决定翻几页（不要求翻到底）
- `all_pages`：**全量拉取**——翻到服务端报告的最后一页为止；`max_pages` 是安全阀防止失控
- `fetch_all`：**跨接口通用**——通过字符串方法名调用任意 endpoint 并自动翻页，适合写通用同步脚本

约束与边界：

- 大多数接口默认单页最大 `200`；`stk_limit` / `stk_premarket` 单页最大 `500`
- `page_size > max_page_size` → 直接抛 `ValueError`，不静默截断
- `limit` 表示「最终最多返回多少条」，允许大于 `max_page_size`，SDK 会分多页请求

`validate_pagination` 在请求前做集中校验：

```python
def validate_pagination(page, page_size, max_pages, max_page_size, *, limit=None):
    if page < 1:
        raise ValueError(f"page must be >= 1; got {page}")
    if page_size is not None and not 1 <= page_size <= max_page_size:
        raise ValueError(f"page_size must be between 1 and {max_page_size}; got {page_size}")
    if limit is not None and limit < 1:
        raise ValueError(f"limit must be >= 1; got {limit}")
    if max_pages is not None and max_pages < 1:
        raise ValueError(f"max_pages must be >= 1; got {max_pages}")
```

**测的是什么、不能推出什么**：分页 4 模式测的是「调用方能用一致语义拿数据」。**不能推出**「全量数据一定能拿完」——服务端 `total_pages` 不准确、`all_pages` 期间数据更新、`max_pages` 太小都会被静默截断。生产环境拉全量数据要做对账。

## 异常三层分类

FTShare 的异常层次非常干净，正好对应三种失败模式：

```python
FtshareError                  # 基类
  ├── FtshareHTTPError        # HTTP 非 2xx
  ├── FtshareDecodeError      # 响应不是合法 JSON
  └── FtshareAPIError         # 业务 code != 0
```

调用方可以这样精细处理：

```python
try:
    df = market.baidu_financial_calendar(...)
except ft.FtshareHTTPError as exc:
    # 网络问题 / 服务端 5xx / 404 — 重试或告警
    print("HTTP error:", exc.status_code, exc.url)
except ft.FtshareDecodeError as exc:
    # 响应格式错误 — 通常是服务端 bug
    print("JSON decode error:", exc.url)
except ft.FtshareAPIError as exc:
    # 业务逻辑错误 — 参数错 / 权限不够 / 业务校验失败
    print("API error:", exc.code, exc.message)
```

三种异常都带上下文（status_code + url + response_text 或 code + message + payload），便于日志和告警。

`raise_for_api_error` 检查业务码：

```python
def raise_for_api_error(payload):
    if isinstance(payload, dict) and "code" in payload and payload.get("code") not in (0, "0", 200, "200"):
        message = payload.get("message")
        raise FtshareAPIError(payload.get("code"), str(message) if message is not None else None, payload)
```

注意它同时认 `0` / `"0"` / `200` / `"200"`——服务端不同时期可能用数字业务码或 HTTP-like 业务码，SDK 都接受，不让历史包袱卡住调用方。

这种「细粒度异常分类」对上层 MCP tool 很有用：可以把 `FtshareAPIError`（业务错，比如日期格式不对）直接转成 tool 返回的错误信息，让 LLM 自己决定怎么处理（修正参数重试 vs 提示用户）；把 `FtshareHTTPError` / `FtshareDecodeError`（基础设施错）转成 tool 异常让人工介入。

## 与同类 SDK 的差异点

把 FTShare 和中国同类金融数据 SDK 对比，能更清楚它的工程取舍：

| 维度 | FTShare Python SDK | akshare | tushare | baostock |
|---|---|---|---|---|
| 协议 | MIT | MIT | 个人授权（积分制） | BSD |
| 凭据 | 无（服务端公开） | 无 | token | 无 |
| 接口数 | 176 | 1000+ | 200+ | 几十 |
| 返回类型 | DataFrame / rows / raw | DataFrame | DataFrame | DataFrame |
| 分页 | 4 模式 | 手动 | 手动 | 手动 |
| 异常分类 | 3 类 | 1 类 | 1 类 | 1 类 |
| 字段筛选 | 内置 | 无 | 无 | 无 |
| MCP 适配 | 设计上支持 | 需手写 wrapper | 需手写 wrapper | 需手写 wrapper |
| Python 版本 | 3.9+ | 3.8+ | 3.6+ | 3.5+ |
| 仓龄 | 3 天 | 多年 | 多年 | 多年 |

FTShare 现在的硬伤是**接口数量远小于 akshare**（176 vs 1000+）——很多 akshare 老用户已经习惯了某个 niche 接口，FTShare 还没有。但它的差异化优势在三点：

1. **三层返回控制**——`raw=True` 是给上层 tool builder 的逃生通道
2. **endpoint registry 模式**——服务端 schema 变了 SDK 不用手改
3. **MIT + 零凭据**——企业内部用零合规摩擦

特别是第 2 点是工程上最重要的——akshare 和 tushare 都靠人工维护接口列表，176 个接口（且还在增长）靠人工维护既慢又错。这个 SDK 把接口元数据收拢到 `ENDPOINTS` 字典，加新接口的边际成本接近零。

## 决策启示：skill 作者 / 数据团队 / 量化研究者各看什么

FTShare SDK 对三类读者的信号不同：

**Skill 作者**——如果你在做 agent skill 生态里的金融投研 skill，把 FTShare 当数据源是最干净的路径。三条具体动作：

- **直接 `pip install ftshare`**——SKILL.md 里写「此 skill 调用 ftshare Python SDK 拉行情数据」即可
- **不要在 skill 里直接调 176 个 REST API**——服务端 URL 改了 skill 就崩；用 SDK 后服务端路径变更由 SDK 维护
- **默认 `as_dataframe=False`**——MCP tool 输出 list[dict] 比 DataFrame 序列化高效

**数据团队**——如果团队要做「内部统一金融数据接口」，FTShare 的 endpoint registry + mixin 模式值得借鉴：

- 把所有数据源接口登记到中央 `ENDPOINTS` 字典，元数据单一事实源
- 业务域用 mixin 拆分，加新业务域只加 mixin 文件 + 在 `apis/__init__.py` export + 在 client 继承列表加一项
- 默认返回结构化数据（DataFrame / rows），但留 `raw=True` 给上层特殊场景

**量化研究者**——FTShare 的接口分类对你的工作流有直接价值：

- **财务数据**（baidu_financial_calendar / balance / cashflow / income / earnings_reports_paginated / performance_forecasts_paginated）——基本面研究
- **宏观经济**（consumer_*_monthly 一组 17 个接口）——宏观对冲策略
- **股票**（涨跌停 / 龙虎榜 / 资金流向 / 千股千评 / IPO / 复权因子）——技术面 + 资金面
- **港股 / 全球指数**（hk / global_index）——跨市场策略
- **基金 / ETF / 期货**（fund / etf / futures）——产品分析

对单接口的快速验证场景，直接 `from ftshare.endpoints import ENDPOINTS; ENDPOINTS['baidu_financial_calendar']` 看 path + params 就行，不用翻服务端文档。

## 采用顺序与边界

对想用这个 SDK 的读者，按以下顺序最经济：

**第一步：`pip install ftshare`，跑一次完整调用**——`market.baidu_financial_calendar(...)` 拿到 DataFrame 就成功。这步验证 SDK 安装 + 客户端构造 + 响应处理整条管道。

**第二步：把现有 quant 代码里的裸 `requests.get` 换成 SDK 调用**——如果代码里有手写的 URL + params + JSON 解析逻辑，逐个迁移到 `market.<endpoint>(...)` 调用。`fields` 参数替代手写的 dict 字段提取。

**第三步：把 SDK 接到 pandas 流水线**——用 `.resample()` / `.groupby()` / `.merge()` 串接多个 endpoint 的输出。这一步的 ROI 最高，因为 SDK 已经把响应转成 DataFrame。

**第四步：把 SDK 包成 MCP tool 或 LangChain tool**——为上层 agent skill / ftshare-mcp / ftshare-skills 提供数据源。Tool 实现层通常就两件事：`as_dataframe=False` 拿到 rows + JSON 序列化输出。

**不一定要做的事**：

- 不要把 176 个 endpoint 一次性集成——选和你研究相关的 5-10 个接口深用，比浅尝全部好
- 不要在 skill 里把 SDK 锁版本到特定 patch 号——服务端可能演进，SDK 升级比硬编码路径安全
- 不要绕过 `ENDPOINTS` 表手动构造 URL——这会让 schema 自动生成机制失效

**边界**：这个 SDK 主要覆盖「FTShare 数据服务的 Python 访问」，对以下场景只能部分覆盖：

- **实时行情推送**——HTTP polling 不是推送场景；如果需要 tick 级实时数据，要用专门的 WebSocket SDK（FTShare 后续可能出）
- **复杂金融计算**——技术指标、回测框架、组合优化等是 quant 自己的事，SDK 不做
- **非 FTShare 数据源**——akshare 接口（港股 / 加密货币等）需要单独处理
- **中国大陆 IP 受限场景**——`market.ft.tech` 在境外访问可能被防火墙阻断，需要国内代理

最后一个边界对中国 quant 用户很关键——`ft.set_base_url()` 可以指向国内镜像 / 私有部署，但镜像需要 FTShare 官方支持。如果团队在防火墙严格的环境使用，提前确认部署方案。

## 参考资料

- [ftshare-lab/ftshare-python-sdk GitHub 仓库](https://github.com/ftshare-lab/ftshare-python-sdk)，MIT 协议，截至 2026-06-26 共 4 stars / 0 forks，0.1.0 版本
- [FTShare 数据服务主页](https://market.ft.tech/)——服务端 API 承载点
- [非凸智能官网](https://ft.tech/)——SDK 母公司，AI-native financial data 品牌叙事
- [docs/API_REFERENCE.md](https://github.com/ftshare-lab/ftshare-python-sdk/blob/main/docs/API_REFERENCE.md)——176 个 SDK 方法的索引（按业务域分组）
- [CHANGELOG.md](https://github.com/ftshare-lab/ftshare-python-sdk/blob/main/CHANGELOG.md)——0.1.0 首发版说明
- [NVIDIA SkillSpector：让 26% 不安全的 agent skill 无处藏身](https://txtmix.com/posts/tech/nvidia-skillspector-agent-skill-security-scanner/)——同一波 agent skill 基础设施成熟化的「安全扫描」切面
- [Meta 挖角 Virtue AI 三位创始人：Agent 安全从论文走向组织战争](https://txtmix.com/posts/tech/meta-poaches-virtue-ai-agent-security-talent-war/)——agent 安全赛道的人才战背景
- [Microsoft Agent Governance Toolkit：AI Agent 安全护盾](https://txtmix.com/posts/tech/agent-governance-toolkit-microsoft-ai-agent-security/)——agent 安全的另一类形态（运行期护栏）
- [requests Python 库](https://requests.readthedocs.io/)——SDK 底层 HTTP 客户端
- [pandas Python 库](https://pandas.pydata.org/)——SDK 默认返回 DataFrame 的目标容器
