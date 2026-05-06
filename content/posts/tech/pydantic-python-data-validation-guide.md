---
title: "Pydantic：Python 类型提示数据验证完全指南"
date: "2026-04-06T22:09:00+08:00"
slug: "pydantic-python-data-validation-guide"
description: "全面介绍 27.4k Stars 的 Pydantic 数据验证库，涵盖 BaseModel、字段类型、验证器、JSON Schema 生成、pydantic-settings 配置管理、pydantic-core Rust 性能优化，以及 API 验证、数据库模型等常见使用模式。"
draft: false
categories: ["技术笔记"]
tags: ["Pydantic", "Python", "数据验证", "类型提示", "FastAPI"]
---

## 学习目标

通过本文，你将全面掌握以下核心能力：

- 深入理解 Pydantic 的项目定位、核心概念和设计理念
- 掌握 BaseModel 的定义和验证机制
- 学会使用 Pydantic 进行数据验证、序列化和 JSON Schema 生成
- 理解 Pydantic V2 的新特性和与 V1 的区别
- 掌握常用字段类型、验证器和自定义验证器
- 学会使用 pydantic-settings 管理应用配置
- 理解 pydantic-core（Rust 实现）的性能优势
- 掌握常见使用模式和最佳实践

---

## 1. 项目概述

### 1.1 是什么

**Pydantic** 是一个基于 **Python 类型提示**的数据验证库。它允许你用纯 Python 类型注解定义数据结构，然后自动进行验证、转换和序列化。

核心理念：用**类型提示**描述数据，用**Pydantic** 验证数据。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **27.4k** |
| GitHub Forks | **2.5k** |
| 贡献者 | 众多 |
| Releases | **193 个** |
| 最新版本 | **v2.12.5** |
| License | **MIT** |
| 语言 | **Python 82.6%**，**Rust 17.2%** |

### 1.3 为什么选择 Pydantic

| 特性 | 说明 |
|------|------|
| **类型安全** | 完全基于 Python 类型提示，与 mypy/pyright 无缝配合 |
| **性能卓越** | Rust 编写的 pydantic-core核心，验证速度极快 |
| **易于使用** | 声明式 API，简单直观 |
| **功能完备** | 验证、序列化、JSON Schema 生成、配置管理 |
| **生态丰富** | pydantic-settings、FastAPI 等周边完善 |
| **活跃维护** | 27k stars，193 releases，持续活跃 |

### 1.4 Pydantic V1 vs V2

| 特性 | V1 | V2 |
|------|-----|-----|
| **架构** | 纯 Python | Rust (pydantic-core) |
| **性能** | 较慢 | 显著提升（10-100x） |
| **API** | 略有不同 | 重新设计，更一致 |
| **兼容性** | - | 内置 V1 兼容层 |

---

## 2. 快速开始

### 2.1 安装

```bash
# pip 安装
pip install -U pydantic

# conda 安装
conda install pydantic -c conda-forge

# 安装 pydantic-settings（配置管理）
pip install pydantic-settings

# 安装所有可选依赖
pip install "pydantic[email]"  # 邮件验证
pip install "pydantic[timezone]"  # 时区支持
```

### 2.2 第一个模型

```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class User(BaseModel):
    id: int                                    # 必需字段
    name: str = "John Doe"                     # 带默认值
    signup_ts: Optional[datetime] = None      # 可选字段
    friends: List[int] = []                    # 列表字段

# 从字典创建（自动验证）
external_data = {
    "id": "123",
    "signup_ts": "2017-06-01 12:22",
    "friends": [1, "2", b"3"]  # 字符串和字节也会被转换
}

user = User(**external_data)

print(user)
#> User id=123 name='John Doe' signup_ts=datetime.datetime(2017, 6, 1, 12, 22) friends=[1, 2, 3]

print(user.id)
#> 123

# 访问原始数据
print(user.model_dump())
# {'id': 123, 'name': 'John Doe', 'signup_ts': datetime.datetime(2017, 6, 1, 12, 22), 'friends': [1, 2, 3]}
```

### 2.3 自动类型转换

Pydantic 不仅验证，还会**自动转换**类型：

```python
class Example(BaseModel):
    int_field: int
    float_field: float
    bool_field: bool
    list_field: List[int]

# 字符串会被自动转换
example = Example(
    int_field="42",        # str → int
    float_field="3.14",    # str → float
    bool_field="yes",       # str → bool
    list_field=[1, 2, "3"]  # 混合类型列表
)

print(example.int_field)    # 42 (int)
print(example.float_field)  # 3.14 (float)
print(example.bool_field)  # True (bool)
print(example.list_field)   # [1, 2, 3] (all int)
```

---

## 3. 字段类型详解

### 3.1 基础类型

```python
from pydantic import BaseModel
from typing import Union

class BasicTypes(BaseModel):
    name: str                    # 字符串
    age: int                     # 整数
    price: float                 # 浮点数
    is_active: bool              # 布尔值
    data: bytes                 # 字节串
```

### 3.2 可选类型

```python
from typing import Optional

class OptionalTypes(BaseModel):
    name: Optional[str] = None   # 等价于 str | None = None
    age: int | None             # Python 3.10+ 语法
    email: str | None = None
```

### 3.3 集合类型

```python
from typing import List, Dict, Set, Tuple

class Collections(BaseModel):
    tags: List[str]                    # 字符串列表
    scores: Dict[str, int]            # 字典 {name: score}
    unique_ids: Set[int]              # 集合（去重）
    coordinates: Tuple[float, float]   # 元组（固定长度）
    mixed: Tuple[int, str, bool]      # 混合类型元组
```

### 3.4 约束类型

```python
from pydantic import Field
from typing import Literal

class ConstrainedTypes(BaseModel):
    # 数值约束
    positive: int = Field(gt=0)                    # 大于 0
    non_negative: int = Field(ge=0)                # 大于等于 0
    bounded: float = Field(ge=0, le=100)          # 0-100 之间
    
    # 字符串约束
    username: str = Field(min_length=3, max_length=20)
    email: str = Field(pattern=r"^[a-z]+@[a-z]+\.[a-z]+$")
    
    # 列表约束
    scores: List[int] = Field(min_length=1, max_length=10)
    
    # 字面量类型
    status: Literal["pending", "approved", "rejected"]
```

### 3.5 复杂类型

```python
from typing import Any, Callable
from pydantic import HttpUrl, EmailStr, PaymentCardNumber

class ComplexTypes(BaseModel):
    url: HttpUrl                    # URL 自动验证和规范化
    email: EmailStr                # 邮箱格式验证
    card: PaymentCardNumber        # 信用卡号验证 (Luhn 算法)
    phone: str = Field(regex=r"^\+?1?\d{9,15}$")  # 电话号码
    secret: Any                   # 任意类型，不验证
    processor: Callable            # 可调用对象
```

---

## 4. 验证器与约束

### 4.1 Field 内置约束

```python
from pydantic import Field, field_validator

class Product(BaseModel):
    # 数值约束
    price: float = Field(gt=0, le=10000)
    quantity: int = Field(ge=0, le=1000)
    
    # 字符串约束
    sku: str = Field(min_length=8, max_length=16, pattern=r"^[A-Z]{3}-\d{5}$")
    
    # 列表约束
    tags: List[str] = Field(min_length=1, max_length=5)
```

### 4.2 field_validator 自定义验证

```python
from pydantic import field_validator, model_validator

class User(BaseModel):
    username: str
    password: str
    age: int
    
    @field_validator("username")
    @classmethod
    def username_must_be_alphanumeric(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("用户名必须为字母或数字")
        return v.lower()  # 自动转小写
    
    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少为 8")
        if not any(c.isupper() for c in v):
            raise ValueError("密码必须包含大写字母")
        return v
    
    @field_validator("age")
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("年龄必须为正数")
        return v
```

### 4.3 model_validator 模型级验证

```python
from pydantic import model_validator

class Order(BaseModel):
    items: List[dict]
    discount: float
    total: float
    
    @model_validator(mode="after")
    def check_total(self) -> "Order":
        # 计算实际总价
        actual_total = sum(item["price"] * item["qty"] for item in self.items)
        # 减去折扣
        actual_total = actual_total * (1 - self.discount)
        
        # 验证总价匹配
        if abs(actual_total - self.total) > 0.01:
            raise ValueError(f"总价不匹配: 期望 {actual_total}, 实际 {self.total}")
        return self
```

### 4.4 跨字段验证

```python
from pydantic import model_validator

class Event(BaseModel):
    start_date: datetime
    end_date: datetime
    location: str
    
    @model_validator(mode="after")
    def check_dates(self) -> "Event":
        if self.end_date <= self.start_date:
            raise ValueError("结束日期必须晚于开始日期")
        return self
    
    # 另一种方式：使用 depends
    @model_validator(mode="after")
    def check_with_depends(self, info: ValidationInfo) -> "Event":
        # info.data 包含其他字段的值
        if self.location == "online" and self.end_date - self.start_date > timedelta(hours=8):
            raise ValueError("在线活动时长不能超过 8 小时")
        return self
```

---

## 5. JSON Schema 生成

### 5.1 自动生成 JSON Schema

```python
import json
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
    age: int | None = None

# 生成 JSON Schema
schema = User.model_json_schema()
print(json.dumps(schema, indent=2))
```

**输出：**

```json
{
  "$defs": {
    "User": {
      "properties": {
        "id": {"title": "Id", "type": "integer"},
        "name": {"title": "Name", "type": "string"},
        "email": {"title": "Email", "type": "string"},
        "age": {"anyOf": [{"type": "integer"}, {"type": "null"}], "default": null, "title": "Age"}
      },
      "required": ["id", "name", "email"],
      "title": "User",
      "type": "object"
    }
  }
}
```

### 5.2 自定义 Schema

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int = Field(title="用户ID", description="唯一标识符")
    username: str = Field(min_length=3, max_length=20, title="用户名")
    email: str = Field(title="邮箱", description="用户邮箱地址")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 123,
                "username": "john",
                "email": "john@example.com"
            }
        }
    }
```

---

## 6. 序列化与反序列化

### 6.1 模型转字典/JSON

```python
class User(BaseModel):
    id: int
    name: str
    created_at: datetime

user = User(id=1, name="John", created_at=datetime.now())

# 转字典
print(user.model_dump())
# {'id': 1, 'name': 'John', 'created_at': datetime.datetime(...)}

# 转 JSON 字符串
print(user.model_dump_json())
# '{"id":1,"name":"John","created_at":"2024-01-15T12:00:00"}'

# 指定格式
print(user.model_dump(mode="json"))  # datetime 转 ISO 字符串
print(user.model_dump(exclude={"id"}))  # 排除字段
print(user.model_dump(include={"name"}))  # 只包含字段
```

### 6.2 从字典/JSON 创建

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

# 从字典创建
user = User.model_validate({"id": 1, "name": "John"})

# 从 JSON 字符串创建
json_str = '{"id": 2, "name": "Jane"}'
user = User.model_validate_json(json_str)

# 兼容旧 API (V1)
user = User.construct(**{"id": 3, "name": "Bob"})  # 不验证，不推荐
```

### 6.3 嵌套模型

```python
from pydantic import BaseModel
from typing import List

class Address(BaseModel):
    street: str
    city: str
    country: str

class Person(BaseModel):
    name: str
    address: Address                    # 嵌套模型
    emails: List[str]                 # 字符串列表

data = {
    "name": "John",
    "address": {"street": "123 Main St", "city": "NYC", "country": "USA"},
    "emails": ["john@example.com", "j@work.com"]
}

person = Person.model_validate(data)
print(person.address.city)  # "NYC"
```

---

## 7. pydantic-settings 配置管理

### 7.1 基本用法

```python
# settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    database_url: str
    secret_key: str
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False  # 环境变量大小写不敏感
    )

# .env 文件
# APP_NAME=MyApplication
# DEBUG=true
# DATABASE_URL=postgresql://localhost/mydb
# SECRET_KEY=my-secret-key
```

### 7.2 嵌套配置

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Database(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    name: str

class Settings(BaseSettings):
    database: Database = Field(default_factory=Database)
    app_name: str

# 环境变量: DATABASE__HOST, DATABASE__PORT, DATABASE__NAME
```

### 7.3 验证与默认值

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    port: int = Field(default=8000, ge=1024, le=65535)
    allowed_hosts: List[str] = ["localhost"]
    
    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_hosts(cls, v):
        if isinstance(v, str):
            return [h.strip() for h in v.split(",")]
        return v
    
    model_config = SettingsConfigDict(env_prefix="APP_")
```

---

## 8. pydantic-core 性能优化

### 8.1 什么是 pydantic-core

Pydantic V2 的核心验证逻辑使用 **Rust** 重写，性能提升 **10-100x**。

```python
# pydantic-core 自动使用
# 无需额外安装，基于 Rust 实现

class LargeDataset(BaseModel):
    id: int
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]]

# 验证 10000 条数据
import time
start = time.time()
for item in dataset:
    LargeDataset.model_validate(item)
print(f"耗时: {time.time() - start:.3f}s")  # V2 比 V1 快很多
```

### 8.2 性能对比

| 场景 | Pydantic V1 | Pydantic V2 | 提升 |
|------|-------------|-------------|------|
| 简单模型验证 | 1x | 10x | 10x |
| 嵌套模型验证 | 1x | 20x | 20x |
| JSON Schema 生成 | 1x | 5x | 5x |
| 序列化 | 1x | 15x | 15x |

### 8.3 性能优化建议

```python
# ✅ 推荐：使用 model_validator 而不是多个 field_validator
class GoodModel(BaseModel):
    @model_validator(mode="after")
    def validate_all(self) -> "GoodModel":
        # 一次验证所有字段
        return self

# ❌ 避免：多个 field_validator
class BadModel(BaseModel):
    @field_validator("x")
    def validate_x1(self, v): ...
    @field_validator("x")
    def validate_x2(self, v): ...  # 多次验证，效率低

# ✅ 推荐：使用 Field 内置约束
class OptimizedModel(BaseModel):
    name: str = Field(min_length=1, max_length=100)  # 内置约束，Rust 优化
```

---

## 9. 常见使用模式

### 9.1 API 请求验证

```python
from pydantic import BaseModel, EmailStr, Field
from typing import List

class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(min_length=8)
    age: int = Field(ge=18, le=120)
    tags: List[str] = Field(default_factory=list)

# FastAPI 示例
from fastapi import FastAPI, HTTPException
app = FastAPI()

@app.post("/users")
def create_user(user: CreateUserRequest):
    # user 已经验证过了
    return {"id": 1, **user.model_dump()}
```

### 9.2 数据库模型

```python
from pydantic import BaseModel, Field
from datetime import datetime

class UserInDB(BaseModel):
    id: int
    username: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_row(cls, row: tuple) -> "UserInDB":
        return cls(
            id=row[0],
            username=row[1],
            hashed_password=row[2],
            created_at=row[3],
            updated_at=row[4]
        )
```

### 9.3 Webhook 验证

```python
from pydantic import BaseModel, HttpUrl
from typing import Literal

class GitHubWebhook(BaseModel):
    action: Literal["opened", "closed", "merged"]
    repository: str
    sender: str
    url: HttpUrl = Field(description="仓库 URL")
    
    @classmethod
    def from_request(cls, payload: dict) -> "GitHubWebhook":
        return cls.model_validate(payload)
```

---

## 10. 常见问题与解决方案

### 10.1 验证失败处理

```python
from pydantic import ValidationError, BaseModel
from typing import List

class User(BaseModel):
    name: str
    age: int

try:
    user = User(name="John", age="invalid")
except ValidationError as e:
    print(e.error_count())  # 错误数量
    for error in e.errors():
        print(f"字段: {error['loc']}, 错误: {error['msg']}")
```

### 10.2 动态模型创建

```python
from pydantic import create_model

# 动态创建模型
DynamicUser = create_model(
    "DynamicUser",
    name=(str, ...),
    age=(int, Field(ge=0)),
    __doc__="Dynamically created user model"
)

user = DynamicUser(name="John", age=30)
```

### 10.3 JSON Schema 自定义

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int = Field(title="用户 ID", description="唯一标识")
    email: str = Field(title="邮箱", format="email")
    
    model_config = {
        "json_schema_extra": {
            "example": {"id": 1, "email": "user@example.com"}
        }
    }

# 生成自定义 Schema
schema = User.model_json_schema()
```

---

## 11. 总结

Pydantic 是 Python 生态中**最流行的数据验证库**，具有以下核心优势：

**为什么选择 Pydantic：**

| 优势 | 说明 |
|------|------|
| **类型安全** | 完全基于类型提示，与类型检查器无缝配合 |
| **性能卓越** | Rust 编写的核心，验证速度极快 |
| **易于使用** | 声明式 API，几行代码完成验证 |
| **功能完备** | 验证、序列化、JSON Schema、配置管理 |
| **生态成熟** | FastAPI 等主流框架首选 |
| **活跃社区** | 27k stars，持续维护 |

**适用场景：**

- API 请求/响应验证
- 配置文件解析
- 数据库模型定义
- Webhook 验证
- CLI 参数验证
- 任何需要数据验证的场景

**官方资源：**

- GitHub：https://github.com/pydantic/pydantic
- 文档：https://docs.pydantic.dev/
- PyPI：https://pypi.org/project/pydantic
- 讨论组：https://github.com/pydantic/pydantic/discussions
- pydantic-settings：https://docs.pydantic.dev/latest/concepts/settings/