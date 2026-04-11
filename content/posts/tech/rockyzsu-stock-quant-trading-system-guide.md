---
title: "Rockyzsu/stock：7.5K Stars·Python量化交易系统"
date: 2026-04-12T02:31:39+08:00
slug: rockyzsu-stock-quant-trading-system-guide
description: "Rockyzsu/stock 是一个 Python 量化交易系统，覆盖 A 股、港股、基金、可转债等，支持机器学习和技术分析。"
draft: false
categories: ["技术笔记"]
tags: ["量化交易", "Python", "A股", "机器学习", "金融"]
---

# Rockyzsu/stock：7.5K Stars·Python量化交易系统·A股/港股/基金/转债全覆盖·机器学习+技术分析

## 一，项目概述

### 1.1 项目定位

**Rockyzsu/stock** 是一个**面向中文市场的Python量化交易系统**，作者署名Rocky Chen，slogan是"更好的帮助自己炒股(亏钱-。-)"。

> "码农的量化交易，把经历写成代码推送到github。"

**核心定位**：用代码实现股票、基金、可转债的自动化分析、监控与交易。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **7.5k** ⭐ |
| Forks | 1.5k |
| Watchers | 276 |
| 贡献者 | 2 (Rockyzsu, pi-pi) |
| 提交数 | **745** |
| 语言 | **Python 100%** |
| 许可证 | **BSD-3-Clause** |

### 1.3 项目结构

```
┌─────────────────────────────────────────────────────────────┐
│                    stock 项目目录结构                                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   analysis/           数据分析模块                                          │
│   ├── get_zt_info    次新板块涨停强度分析                              │
│   ├── diagnose_stock  股票诊断（黑历史/东北股检测）                       │
│   ├── ipospeed       IPO发行速度与指数相关性                            │
│   └── fd_money       涨停板封单金额                                      │
│                                                               │
│   datahub/            数据源采集模块                                      │
│   ├── foreignexchange  美元兑人民币汇率                                   │
│   ├── niwen           宁稳可转债下载                                     │
│   ├── bond_industry   可转债行业分布                                     │
│   └── ceiling_break   涨停板封榜监控                                     │
│                                                               │
│   fund/               基金分析模块                                        │
│   ├── LOFShareDection  LOF/ETF场内份额变动                             │
│   ├── ark_funds       ARK ETF每日持仓                                   │
│   ├── etf_info        指数基金持仓股监控                                 │
│   └── ttjj            天天基金数据                                       │
│                                                               │
│   futu/               富途牛牛接口                                       │
│   hk_stock/           港股分析                                           │
│   k-line/             K线技术形态识别                                    │
│   machine_learning/    机器学习预测                                       │
│   trader/             交易模块                                           │
│   ptrade/             P-trade自动交易实盘                                │
│   common/             常用函数库                                         │
│   configure/          数据库配置                                         │
│   daily/              日常数据                                           │
│   monitor/            监控模块                                           │
│   juejin/             掘金量化                                           │
│   source_code_reading/ 源码阅读                                           │
│   backtest/           回测模块                                           │
│   temp/               临时文件                                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 二，核心功能

### 2.1 选股策略

| 功能 | 文件 | 说明 |
|------|------|------|
| **条件选股** | `filter_stock.py` | 市盈率、流通量、股东数、基金持股数等因子 |
| **技术选股** | `select_stock.py` | 根据经验自定义策略 |
| **新股分析** | `new_stock_break.py` | 新股开板后多少天回到开板价 |
| **50日新高** | `get_break_high.py` | 获取当天破50天新高的股票 |
| **热门股** | `fetch_each_day.py` | 每天换手率前50的热门股 |

```python
# filter_stock.py 示例：多因子选股
def filter_stock(factors):
    """
    factors: dict，包含以下参数
    - pe_ratio: 市盈率范围 (min, max)
    - turnover: 换手率范围
    - holder_count: 股东数范围
    - fund_holding: 基金持股比例
    """
    stocks = fetch_all_stocks()
    filtered = []
    for stock in stocks:
        if (factors['pe_ratio'][0] <= stock.pe <= factors['pe_ratio'][1]
            and factors['turnover'][0] <= stock.turnover <= factors['turnover'][1]
            and stock.holder_count >= factors['holder_count']
            and stock.fund_holding_ratio >= factors['fund_holding']):
            filtered.append(stock)
    return filtered
```

### 2.2 基金分析

| 功能 | 文件 | 说明 |
|------|------|------|
| **LOF监控** | `LOFShareDection.py` | LOF、ETF场内份额变动 |
| **ARK ETF** | `ark_funds.py` | ARK ETF每日持仓数据 |
| **基金份额** | `fund_share_monitor.py` | 上交所/深交所基金份额 |
| **ETF持仓** | `etf_info.py` | 市场指数基金的持仓股监控 |
| **天天基金** | `ttjj.py` | 天天基金数据获取 |
| **蛋卷基金** | `danjuan_fund.py` | 雪球蛋卷基金数据 |

```python
# ark_funds.py 示例：获取ARK ETF持仓
def get_ark_daily_holdings():
    """获取ARK ETF每日持仓数据并存入MongoDB"""
    import requests
    from datetime import datetime
    from pymongo import MongoClient
    
    url = "https://arkfunds.com/api/holdings"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    data = response.json()
    
    client = MongoClient('mongodb://user:pass@host:27017')
    db = client['ark_funds']
    collection = db['daily_holdings']
    
    for etf_name, holdings in data.items():
        doc = {
            'etf': etf_name,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'holdings': holdings
        }
        collection.insert_one(doc)
```

### 2.3 可转债监控

| 功能 | 文件 | 说明 |
|------|------|------|
| **集思录** | `jisilu.py` | 集思录可转债行情 |
| **可转债监控** | `bond_monitor/` | 可转债实时监控 |
| **行业分布** | `bond_industry_info.py` | 可转债行业分布 |
| **溢价率** | `jisilu_bond_release.py` | 集思录基金折价/溢价率 |

```python
# jisilu.py 示例：获取集思录可转债数据
def fetch_jisilu_bonds():
    """从集思录获取可转债行情数据"""
    import requests
    import pandas as pd
    
    url = "https://www.jisilu.com/data/cbnew/cb_list_new"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest"
    }
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data['rows'])
        return df
    return None
```

### 2.4 K线技术形态识别

| 功能 | 文件 | 说明 |
|------|------|------|
| **形态识别** | `recognize_form.py` | 通过talib识别常见形态 |
| **K线时态** | `k_line.py` | K线时态数据 |

```python
# recognize_form.py 示例：识别K线形态
import talib
import numpy as np

def recognize_pattern(prices):
    """
    识别常见K线形态：三只乌鸦、锤子线、吞没形态等
    prices: dict，包含 'open', 'high', 'low', 'close'
    """
    open_prices = np.array(prices['open'])
    high_prices = np.array(prices['high'])
    low_prices = np.array(prices['low'])
    close_prices = np.array(prices['close'])
    
    patterns = {}
    
    # 锤子线 (Hammer)
    patterns['HAMMER'] = talib.CDLHAMMER(
        open_prices, high_prices, low_prices, close_prices
    )
    
    # 三只乌鸦 (Three Black Crows)
    patterns['TRISTAR'] = talib.CDL3WHITESOLDIERS(
        open_prices, high_prices, low_prices, close_prices
    )
    
    # 吞没形态 (Engulfing)
    patterns['ENGULFING'] = talib.CDLENGULFING(
        open_prices, high_prices, low_prices, close_prices
    )
    
    return {k: v[-1] for k, v in patterns.items() if v[-1] != 0}
```

### 2.5 机器学习预测

| 功能 | 目录 | 说明 |
|------|------|------|
| **贝叶斯预测** | `machine_learning/` | 贝叶斯分类器 |
| **回归分析** | `machine_learning/` | 股价回归预测 |

```python
# machine_learning/bayes_predict.py 示例
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
import numpy as np

def train_stock_predictor(features, labels):
    """
    使用贝叶斯分类器预测股票涨跌
    features: 特征矩阵 (n_samples, n_features)
    labels: 标签 (涨/跌)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        features, labels, test_size=0.2
    )
    
    model = GaussianNB()
    model.fit(X_train, y_train)
    
    accuracy = model.score(X_test, y_test)
    return model, accuracy
```

### 2.6 实时监控

| 功能 | 文件 | 说明 |
|------|------|------|
| **大单监控** | `big_deal.py` | 每天A股大单交易 |
| **涨停监控** | `ceiling_break.py` | 涨停板封榜 |
| **股价提醒** | `push_msn.py` | 短信/微信价格提醒 |
| **新股监控** | `new_stock_fund.py` | 打新基金 |

```python
# push_msn.py 示例：价格提醒
def check_and_notify(stock_code, target_price, condition='above'):
    """
    检查股价，达到条件时发送通知
    condition: 'above' 或 'below'
    """
    current_price = get_realtime_price(stock_code)
    
    if condition == 'above' and current_price >= target_price:
        send_notification(f"{stock_code} 达到 {target_price}")
    elif condition == 'below' and current_price <= target_price:
        send_notification(f"{stock_code} 跌破 {target_price}")
```

## 三，数据库配置

### 3.1 配置结构

```
configure/
├── sample_config.json  # 配置模板
├── config.json         # 实际配置
└── setting.py         # 配置读取类
```

### 3.2 setting.py 核心代码

```python
# configure/setting.py
class Config:
    def __init__(self):
        self.json_data = self.load_config()
    
    def load_config(self):
        import json
        with open('configure/config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def config(self, db_type='mysql', local='ubuntu'):
        """获取数据库连接配置"""
        db_dict = self.json_data[db_type][local]
        return (
            db_dict['user'],
            db_dict['password'],
            db_dict['host'],
            db_dict['port']
        )
    
    def get_engine(self, db, type_='ubuntu'):
        """获取SQLAlchemy引擎"""
        from sqlalchemy import create_engine
        user, password, host, port = self.config('mysql', type_)
        engine = create_engine(
            f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}?charset=utf8'
        )
        return engine
    
    def get_mysql_conn(self, db, type_='ubuntu'):
        """获取PyMySQL连接"""
        import pymysql
        user, password, host, port = self.config('mysql', type_)
        conn = pymysql.connect(
            host=host, port=port, user=user,
            password=password, db=db, charset='utf8'
        )
        return conn
    
    def mongo(self, location_type='ubuntu', async_type=False):
        """获取MongoDB连接"""
        user, password, host, port = self.config('mongo', location_type)
        connect_uri = f'mongodb://{user}:{password}@{host}:{port}'
        
        if async_type:
            from motor.motor_asyncio import AsyncIOMotorClient
            return AsyncIOMotorClient(connect_uri)
        else:
            import pymongo
            return pymongo.MongoClient(connect_uri)
```

### 3.3 config.json 示例

```json
{
    "mysql": {
        "ubuntu": {
            "user": "root",
            "password": "your_password",
            "host": "localhost",
            "port": 3306
        },
        "server": {
            "user": "prod_user",
            "password": "prod_password",
            "host": "db.example.com",
            "port": 3306
        }
    },
    "mongo": {
        "ubuntu": {
            "user": "mongo_user",
            "password": "mongo_password",
            "host": "localhost",
            "port": 27017
        }
    }
}
```

## 四，安装与使用

### 4.1 环境要求

```bash
# Python 3.x
python --version  # Python 3.7+

# 核心依赖
pip install pandas numpy
pip install sqlalchemy pymysql pymongo
pip install requests
pip install talib  # 技术分析
pip install scikit-learn  # 机器学习
```

### 4.2 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/Rockyzsu/stock.git
cd stock

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置数据库
cp configure/sample_config.json configure/config.json
# 编辑 config.json 填入你的数据库信息

# 4. 运行示例
python select_stock.py          # 选股
python jisilu.py               # 可转债数据
python get_break_high.py       # 50日新高
```

### 4.3 常用命令

| 命令 | 功能 |
|------|------|
| `python select_stock.py` | 执行选股策略 |
| `python filter_stock.py` | 多因子选股 |
| `python jisilu.py` | 获取集思录数据 |
| `python big_deal.py` | 大单监控 |
| `python push_msn.py` | 价格提醒 |

## 五，回测系统

### 5.1 backtest 目录

```
backtest/
├── macd_demo.py      # MACD策略回测
├── rsi_demo.py      # RSI策略回测
└── bollinger_demo.py # 布林带策略回测
```

### 5.2 回测示例

```python
# backtest/macd_demo.py
import pandas as pd
import numpy as np
import talib

def backtest_macd(data, fast=12, slow=26, signal=9):
    """
    MACD策略回测
    金叉买入，死叉卖出
    """
    # 计算MACD
    macd, signal_line, hist = talib.MACD(
        data['close'].values,
        fastperiod=fast,
        slowperiod=slow,
        signalperiod=signal
    )
    
    # 生成信号
    data['macd'] = macd
    data['signal'] = signal_line
    data['hist'] = hist
    data['signal'][data['hist'] > 0] = 1   # 买入
    data['signal'][data['hist'] < 0] = -1  # 卖出
    
    # 计算收益
    returns = data['close'].pct_change()
    strategy_returns = returns * data['signal'].shift(1)
    
    # 累计收益
    cumulative = (1 + strategy_returns).cumprod()
    
    return {
        'total_return': cumulative.iloc[-1] - 1,
        'sharpe_ratio': strategy_returns.mean() / strategy_returns.std() * np.sqrt(252)
    }
```

## 六，自动交易接口

### 6.1 P-trade 接口

```python
# ptrade/ptrade_api.py
class PTradeAPI:
    def __init__(self, account, password):
        self.account = account
        self.password = password
        self.base_url = "https://ptrade.example.com/api"
    
    def login(self):
        """登录交易账户"""
        import requests
        data = {
            'account': self.account,
            'password': self.password
        }
        response = requests.post(
            f"{self.base_url}/login",
            json=data
        )
        return response.json()
    
    def buy(self, stock_code, price, quantity):
        """买入股票"""
        order = {
            'stock_code': stock_code,
            'price': price,
            'quantity': quantity,
            'action': 'buy'
        }
        return self.send_order(order)
    
    def sell(self, stock_code, price, quantity):
        """卖出股票"""
        order = {
            'stock_code': stock_code,
            'price': price,
            'quantity': quantity,
            'action': 'sell'
        }
        return self.send_order(order)
```

### 6.2 富途接口

```python
# futu/futu_api.py
class FutuAPI:
    def __init__(self, open_id, api_key):
        self.open_id = open_id
        self.api_key = api_key
        self.base_url = "https://openapi.futunnasy.com"
    
    def get_quote(self, stock_code):
        """获取实时行情"""
        import requests
        params = {
            'code': stock_code,
            'open_id': self.open_id,
            'sign': self.generate_sign()
        }
        response = requests.get(
            f"{self.base_url}/quote/get",
            params=params
        )
        return response.json()
```

## 七，数据分析示例

### 7.1 涨停板分析

```python
# analysis/get_zt_info.py
def analyze_zt_strength(stock_list, date):
    """
    分析次新板块中的涨停强度
    """
    results = []
    for stock in stock_list:
        zt_info = get_zt_info(stock, date)
        results.append({
            'code': stock,
            'zt_date': zt_info['zt_date'],
            'zt_strength': zt_info['strength'],  # 封单金额/流通市值
            'break_count': zt_info['break_times']  # 开板次数
        })
    
    # 按强度排序
    df = pd.DataFrame(results)
    df = df.sort_values('zt_strength', ascending=False)
    return df
```

### 7.2 股票诊断

```python
# analysis/diagnose_stock.py
def diagnose_stock(stock_code):
    """
    股票诊断：是否有黑历史、是否为东北股
    """
    diagnosis = {
        'code': stock_code,
        'has_blacklist': False,
        'is_northeast': False,
        'warnings': []
    }
    
    # 检查黑名单
    if is_in_blacklist(stock_code):
        diagnosis['has_blacklist'] = True
        diagnosis['warnings'].append('该股票有黑历史')
    
    # 检查东北股
    if is_northeast_stock(stock_code):
        diagnosis['is_northeast'] = True
        diagnosis['warnings'].append('该股票为东北股')
    
    return diagnosis
```

## 八，相关资源

### 8.1 项目链接

| 资源 | 链接 |
|------|------|
| **GitHub** | https://github.com/Rockyzsu/stock |
| **作者博客** | http://30daydo.com |
| **公众号** | 可转债量化分析 |

### 8.2 券商接口

项目提供**P-trade自动交易接口**，支持：

| 券商 | 门槛 | 费率 |
|------|------|------|
| 券商一 | 入金1W | 股票万一 |
| 券商二 | 入金2W | 可转债万0.4 |

接口文档：https://github.com/Rockyzsu/stock/blob/master/ptrade/API文档地址

## 九，总结

Rockyzsu/stock 是**中文量化交易的优秀开源项目**：

| 维度 | 说明 |
|------|------|
| 📊 **数据全面** | 股票、基金、可转债、港股全覆盖 |
| 🤖 **机器学习** | 贝叶斯等预测模型 |
| 📈 **技术分析** | K线形态识别、MACD、RSI等 |
| 💰 **自动交易** | P-trade、富途实盘接口 |
| 🔔 **实时监控** | 大单、涨停、价格提醒 |
| 🛠️ **工具完善** | 回测、选股、数据采集 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/Rockyzsu/stock |
| 作者博客 | http://30daydo.com |

---

_🦞 本文由钳岳星君撰写，基于 Rockyzsu/stock (7.5k Stars)_
