# awesome-systematic-trading：8.4K Stars·量化交易资源大全·论文/数据集/代码库·Python/R/JS·策略研究

## 一，项目概述

### 1.1 awesome-systematic-trading 是什么

**awesome-systematic-trading** 是一个精心策划的**量化交易资源集合**，涵盖研究论文、书籍、量化专家、数据集、代码库等全方位资源。

> "A curated collection of research papers, books, quants, datasets, and other resources for systematic trading"

**核心理念**：为量化交易研究者提供一站式资源导航，从学术论文到实战代码，从数据源到策略实现。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **8.4k** ⭐ |
| Forks | 1.1k |
| 贡献者 | **26** |
| 语言 | **Python 98.1%** |

### 1.3 资源分类

```
┌─────────────────────────────────────────────────────────────┐
│              awesome-systematic-trading 资源分类                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   📚 研究论文                    │ 🗃️ 代码库                          │
│   ├── 按策略分类               │ ├── Python                          │
│   ├── 按应用分类               │ ├── TypeScript/JavaScript           │
│   └── 经典论文                 │ ├── R                                │
│                                 │ └── Julia                            │
│                                                               │
│   📊 数据集                    │ 📖 书籍                              │
│   ├── 市场数据                 │ ├── 技术分析                          │
│   ├── 另类数据                 │ ├── 期权交易                          │
│   └── 数据预处理               │ ├── 机器学习                          │
│                                 │ └── 交易心理学                       │
│                                                               │
│   🎓 在线课程                  │ 💰 其他资源                          │
│   ├── 量化金融                │ ├── 博客/视频                        │
│   ├── 交易系统                 │ ├── 社区                              │
│   └── 金融工程                 │ └── 基金公司排名                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 二，研究论文（按策略）

### 2.1 动量/趋势跟踪 (Momentum / Trend Following)

```python
# 经典动量策略论文
momentum_papers = [
    "Jegadeesh & Titman (1993) - Returns to Buying Winners",
    "Asness et al. (2013) - Value and Momentum Everywhere",
    "Moskowitz et al. (2012) - Time Series Momentum",
    "Hurst et al. (2013) - Dynamic Momentum Strategies",
    "Baltas & Sagi (2018) - Volatility Risk and Momentum",
]

# 简单动量策略实现
def momentum_strategy(prices, lookback=12, holding=1):
    """
    简单动量策略
    
    Args:
        prices: 价格序列
        lookback: 回看期（月）
        holding: 持仓期（月）
    """
    # 计算动量信号
    returns = prices.pct_change(periods=lookback)
    
    # 做多动量，做空反向
    signal = returns.shift(holding)
    
    # 生成交易信号
    positions = signal.apply(lambda x: 1 if x > 0 else -1)
    
    return positions
```

### 2.2 均值回归 (Mean Reversion)

```python
# 均值回归策略论文
mean_reversion_papers = [
    "Bouchard et al. (2015) - Statistical Physics of Markets",
    "Pole (2007) - Statistical arbitrage",
    "Gatev et al. (2006) - Pairs Trading",
    "Elliott et al. (2005) - Pairs Trading",
]

# 配对交易策略
def pairs_trading(stock1, stock2, lookback=60, entry_threshold=2.0):
    """
    配对交易策略
    
    Args:
        stock1: 第一只股票
        stock2: 第二只股票
        lookback: 窗口期
        entry_threshold: 入场阈值（标准差）
    """
    # 计算价差
    spread = stock1 - stock2
    
    # 计算 z-score
    mean = spread.rolling(lookback).mean()
    std = spread.rolling(lookback).std()
    z_score = (spread - mean) / std
    
    # 生成信号
    signal = 0
    if z_score > entry_threshold:
        signal = -1  # 做空价差
    elif z_score < -entry_threshold:
        signal = 1   # 做多价差
    elif abs(z_score) < 0.5:
        signal = 0   # 平仓
    
    return signal
```

### 2.3 统计套利 (Statistical Arbitrage)

```python
# 统计套利论文
stat_arb_papers = [
    "Avellaneda & Lee (2010) - Statistical Arbitrage",
    "Bogousslavsky (2016) - Infrequent Rebalancing",
    "Narang (2013) - Inside the Black Box",
    "Rishoo (2019) - RFactor",
]

# 统计套利框架
class StatisticalArbitrage:
    def __init__(self, securities, lookback=20):
        self.securities = securities
        self.lookback = lookback
        self.weights = None
        
    def compute_weights(self):
        """计算套利权重"""
        returns = self.securities.pct_change()
        cov = returns.rolling(self.lookback).cov()
        inv_cov = np.linalg.pinv(cov.values)
        
        # 均值方差优化
        mu = returns.mean()
        self.weights = inv_cov @ mu
        
        return self.weights
    
    def backtest(self, test_data):
        """回测策略"""
        self.compute_weights()
        portfolio_returns = (test_data.pct_change() * self.weights).sum(axis=1)
        cumulative = (1 + portfolio_returns).cumprod()
        return cumulative
```

### 2.4 机器学习交易 (Machine Learning Trading)

```python
# 机器学习论文
ml_papers = [
    "Dixon et al. (2016) - Machine Learning Trading",
    "Fischer & Krauss (2018) - Deep Learning LSTM",
    "Buehler et al. (2019) - Deep Hedging",
    "Kolm & Ritter (2019) - ML for Finance",
]

# LSTM 预测模型
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

def build_lstm_model(sequence_length, n_features):
    """构建 LSTM 价格预测模型"""
    model = Sequential([
        LSTM(64, input_shape=(sequence_length, n_features), 
             return_sequences=True),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1)  # 预测下一个收益率
    ])
    
    model.compile(optimizer='adam', loss='mse')
    return model

def train_and_predict(prices, lookback=60):
    """训练并预测"""
    # 准备数据
    X, y = [], []
    for i in range(lookback, len(prices)):
        X.append(prices[i-lookback:i])
        y.append(prices[i])
    
    X, y = np.array(X), np.array(y)
    
    # 训练模型
    model = build_lstm_model(lookback, X.shape[2])
    model.fit(X, y, epochs=50, batch_size=32, verbose=0)
    
    # 预测
    predictions = model.predict(X)
    return predictions
```

### 2.5 加密货币交易 (Crypto Trading)

```python
# 加密货币论文
crypto_papers = [
    "Makarov & Schoar (2020) - Crypto Trading",
    "Liu (2019) - Crypto momentum",
    "Gedeck et al. (2022) - Machine Learning Crypto",
]

# 跨交易所套利
def crypto_arbitrage(exchange1_prices, exchange2_prices, fees=0.001):
    """
    跨交易所套利策略
    
    Args:
        exchange1_prices: 交易所1价格
        exchange2_prices: 交易所2价格
        fees: 交易费用
    """
    # 计算价差
    spread = exchange1_prices - exchange2_prices
    
    # 扣除费用后仍有利润
    net_spread = spread - fees * 2
    
    # 生成信号
    signal = np.where(net_spread > 0, 1,  # 买入交易所1，卖出交易所2
                np.where(net_spread < 0, -1, 0))  # 反向
    
    return signal
```

## 三，研究论文（按应用）

### 3.1 回测 (Backtesting)

```python
# 回测论文
backtest_papers = [
    "DeMiguel et al. (2009) - Portfolio Selection",
    "Bailey et al. - Quantitative Investing",
    "Hsu (2019) - Backtesting",
]

# 事件驱动回测框架
class EventDrivenBacktester:
    def __init__(self, initial_capital=100000):
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        
    def on_signal(self, signal, price, timestamp):
        """信号触发"""
        if signal != 0:
            # 计算仓位
            position_size = (self.capital * 0.1) / price
            
            if signal == 1:
                self.buy(position_size, price, timestamp)
            elif signal == -1:
                self.sell(position_size, price, timestamp)
    
    def buy(self, size, price, timestamp):
        """买入"""
        cost = size * price
        if cost <= self.capital:
            self.capital -= cost
            self.positions[timestamp] = {'size': size, 'price': price}
            self.trades.append({'action': 'BUY', 'size': size, 'price': price})
    
    def sell(self, size, price, timestamp):
        """卖出"""
        if timestamp in self.positions:
            pnl = (price - self.positions[timestamp]['price']) * size
            self.capital += pnl + self.positions[timestamp]['size'] * price
            self.trades.append({'action': 'SELL', 'size': size, 'price': price})
            del self.positions[timestamp]
    
    def get_metrics(self):
        """计算回测指标"""
        returns = [t['price'] for t in self.trades]
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
        max_dd = self.max_drawdown()
        return {'sharpe': sharpe, 'max_drawdown': max_dd}
```

### 3.2 投资组合管理 (Portfolio Management)

```python
# 组合管理论文
portfolio_papers = [
    "Markowitz (1952) - Portfolio Selection",
    "Sharpe (1964) - Capital Asset Pricing Model",
    "Fama & French (1993) - Three Factor Model",
    "Carhart (1997) - Four Factor Model",
]

# Black-Litterman 模型
class BlackLitterman:
    def __init__(self, market_cap_weights, cov_matrix, views=None):
        self.market_weights = market_cap_weights
        self.cov = cov_matrix
        self.views = views  # 观点矩阵
        
    def compute_weights(self, tau=0.05, delta=2.5):
        """计算 BL 权重"""
        # 市场均衡收益
        pi = delta * self.cov @ self.market_weights
        
        if self.views is not None:
            # 融入观点
            P, Q, Omega = self.views['P'], self.views['Q'], self.views['omega']
            scaled_cov = tau * self.cov
            
            # 后验收益
            M = np.linalg.inv(np.linalg.inv(scaled_cov) + P.T @ np.linalg.inv(Omega) @ P)
            mu = M @ (np.linalg.inv(scaled_cov) @ pi + P.T @ np.linalg.inv(Omega) @ Q)
        else:
            mu = pi
            
        # 最优权重
        weights = np.linalg.inv(delta * self.cov) @ mu
        return weights / weights.sum()
```

## 四，数据集

### 4.1 市场数据

```python
# 市场数据源
market_data_sources = {
    'yfinance': 'Yahoo Finance - 免费股票数据',
    ' quandl': 'Quandl - 金融数据API',
    ' polygon': 'Polygon.io - 实时/历史数据',
    ' alpaca': 'Alpaca - 免佣金股票API',
    ' binance': 'Binance - 加密货币数据',
    ' ccxt': 'CCXT - 加密货币聚合API',
}

# 使用 yfinance 获取数据
import yfinance as yf

def get_market_data(tickers, start='2010-01-01', end='2024-12-31'):
    """获取市场数据"""
    data = yf.download(tickers, start=start, end=end)
    return data['Adj Close']
```

### 4.2 另类数据 (Alternative Data)

```python
# 另类数据源
alternative_data = {
    'sec_edgar': 'SEC EDGAR - 监管文件',
    'finnhub': 'Finnhub - 新闻/情感数据',
    'twitter': 'Twitter API - 社交媒体',
    'satellite': 'Satellite Imagery - 卫星图像',
    'credit_card': '信用卡数据 - 消费趋势',
}

# SEC 文件解析
import requests

def get_sec_filings(cik, filing_type='10-K'):
    """获取 SEC 文件"""
    base_url = f'https://data.sec.gov/submissions/CIK{cik}.json'
    headers = {'User-Agent': 'Your Name your@email.com'}
    
    response = requests.get(base_url, headers=headers)
    filings = response.json()['filings']['recent']
    
    return filings
```

### 4.3 数据预处理

```python
# 数据清洗
def clean_price_data(prices):
    """清洗价格数据"""
    # 1. 处理缺失值
    prices = prices.fillna(method='ffill')  # 前向填充
    prices = prices.dropna()
    
    # 2. 处理异常值
    z_scores = np.abs((prices - prices.mean()) / prices.std())
    prices = prices[z_scores < 3]
    
    # 3. 对齐时间戳
    prices = prices.sort_index()
    
    return prices

# 特征工程
def create_features(prices):
    """创建技术指标特征"""
    features = pd.DataFrame(index=prices.index)
    
    # 收益率
    features['returns'] = prices.pct_change()
    
    # 移动平均
    features['ma_20'] = prices.rolling(20).mean()
    features['ma_50'] = prices.rolling(50).mean()
    
    # 波动率
    features['vol_20'] = prices.rolling(20).std()
    
    # 动量
    features['momentum_12'] = prices.pct_change(12)
    
    return features
```

## 五，代码库

### 5.1 Python 量化库

```python
# 主要 Python 量化库
python_libraries = {
    # 回测框架
    'backtrader': '功能丰富的回测引擎',
    'zipline': 'Quantopian 开源回测',
    'quantconnect': '云端量化平台',
    '手把手教你学 Python': '教学资源',
    
    # 数据处理
    'pandas': '数据处理基础',
    'numpy': '数值计算',
    'scipy': '科学计算',
    
    # 机器学习
    'scikit-learn': '机器学习',
    'tensorflow': '深度学习',
    'pytorch': '深度学习',
    
    # 金融专用
    'quantlib': '金融衍生品定价',
    'ffn': '金融函数库',
    'pyfolio': '组合分析',
}

# 使用 Backtrader 回测
import backtrader as bt

class MyStrategy(bt.Strategy):
    def __init__(self):
        self.ma = bt.indicators.SMA(period=20)
        
    def next(self):
        if self.data.close > self.ma:
            self.buy()
        elif self.data.close < self.ma:
            self.sell()

cerebro = bt.Cerebro()
cerebro.addstrategy(MyStrategy)
cerebro.broker.setcash(100000)
cerebro.run()
```

### 5.2 R 量化库

```R
# R 量化库
r_libraries <- c(
  # 回测
  'quantstrat' = '策略回测框架',
  'PerformanceAnalytics' = '组合分析',
  'TTR' = '技术指标',
  
  # 统计
  'stats' = '基础统计',
  'forecast' = '时间序列预测',
  
  # 机器学习
  'caret' = '机器学习',
  'randomForest' = '随机森林'
)

# quantstrat 示例
library(quantstrat)

# 初始化
initDate <- "2000-01-01"
fromDate <- "2000-01-01"
toDate <- "2024-12-31"

# 创建策略
strategy("ma_cross") <- function() {
  add.indicator(name = "SMA", 
                arguments = list(x = quote(mktdata), 
                                n = 20),
                label = "fast")
}
```

### 5.3 Julia 量化库

```julia
# Julia 量化库
julia_libraries = [
    'JuMP.jl' => '数学优化',
    'Flux.jl' => '机器学习',
    'DataFrames.jl' => '数据处理',
    'Dates.jl' => '日期时间',
]

# 简单 Julia 回测
function backtest(prices, signals)
    returns = diff(prices) ./ prices[1:end-1]
    strategy_returns = returns .* signals[2:end]
    cumulative = cumprod(1 .+ strategy_returns)
    return cumulative
end
```

## 六，书籍推荐

### 6.1 技术分析

```python
# 技术分析书籍
technical_books = [
    "Technical Analysis of the Financial Markets - John Murphy",
    "Japanese Candlestick Charting Techniques - Steve Nison",
    "Encyclopedia of Chart Patterns - Thomas Bulkowski",
    "Trading for a Living - Alexander Elder",
]

# 突破策略示例
def breakout_strategy(prices, lookback=20):
    """突破策略"""
    # 计算最高价/最低价
    highest = prices.rolling(lookback).max()
    lowest = prices.rolling(lookback).min()
    
    # 信号
    signal = 0
    if prices > highest.shift(1):
        signal = 1   # 突破买入
    elif prices < lowest.shift(1):
        signal = -1  # 跌破卖出
    
    return signal
```

### 6.2 期权交易

```python
# 期权书籍
options_books = [
    "Options, Futures, and Other Derivatives - John Hull",
    "The Options Playbook - Brian Overby",
    "Option Volatility and Pricing - Sheldon Natenberg",
    "Dynamic Hedging - Nassim Taleb",
]

# Black-Scholes 定价
from scipy.stats import norm

def black_scholes(S, K, T, r, sigma, option_type='call'):
    """
    Black-Scholes 期权定价
    
    Args:
        S: 当前股价
        K: 行权价
        T: 到期时间（年）
        r: 无风险利率
        sigma: 波动率
        option_type: 'call' 或 'put'
    """
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    
    if option_type == 'call':
        price = S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
    else:
        price = K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)
    
    return price
```

### 6.3 机器学习与交易

```python
# ML 交易书籍
ml_trading_books = [
    "Machine Learning for Algorithmic Trading - Stefan Jansen",
    "Advances in Financial Machine Learning - Marcos López de Prado",
    "Quantitative Trading - Ernest Chan",
    "Algorithmic Trading - Duncan Aldington",
]

# 随机森林选股
from sklearn.ensemble import RandomForestClassifier

def select_stocks_rf(features, labels, n_trees=100):
    """
    使用随机森林选股
    
    Args:
        features: 特征矩阵
        labels: 标签（1=上涨，0=下跌）
        n_trees: 树的数量
    """
    model = RandomForestClassifier(n_estimators=n_trees, random_state=42)
    model.fit(features, labels)
    
    # 特征重要性
    importance = model.feature_importances_
    
    return model, importance
```

## 七，在线课程

### 7.1 量化金融课程

```python
# 推荐课程
courses = {
    'quantconnect': 'QuantConnect 量化交易课程',
    'udemy_quant': 'Udemy 量化交易课程',
    'coursera_ml': 'Coursera 机器学习课程',
    'edx_finance': 'edX 金融工程课程',
}

# 学习路径
learning_path = [
    "1. Python 基础",
    "2. 金融基础知识",
    "3. 统计学与计量经济学",
    "4. 时间序列分析",
    "5. 机器学习",
    "6. 量化策略开发",
    "7. 回测与风险管理",
    "8. 实盘交易",
]
```

## 八，其他资源

### 8.1 博客/社区

```python
# 推荐博客
blogs = [
    'https://www.quantopian.com' => 'Quantopian 社区',
    'https://www.quantconnect.com' => 'QuantConnect',
    'https://www.systematictrading.org' => 'Systematic Trading',
    'https://www.tradingview.com' => 'TradingView',
    'https://www.elitetrader.com' => 'Elite Trader',
]

# 量化新闻源
news_feeds = [
    'https://www.ft.com/markets' => 'Financial Times',
    'https://www.wsj.com/markets' => 'Wall Street Journal',
    'https://www.reuters.com/markets' => 'Reuters',
]
```

### 8.2 基金排名

```python
# 对冲基金排名
hedge_funds = {
    'Bridgewater': 'Ray Dalio 全天候策略',
    'Two Sigma': '系统化交易',
    'D.E. Shaw': '量化对冲',
    'Citadel': '做市与量化',
    'Renaissance': 'Medallion Fund',
}

# 共同基金
mutual_funds = {
    'AQR': 'Cliff Asness 量化',
    'Two Sigma': '系统化投资',
    'Man Group': 'CTA/量化',
}
```

## 九，最佳实践

### 9.1 策略开发流程

```python
# 量化策略开发流程
strategy_development = """
1. 想法生成
   - 文献研究
   - 市场观察
   - 数据挖掘

2. 数据准备
   - 数据获取
   - 数据清洗
   - 特征工程

3. 策略设计
   - 信号生成
   - 仓位管理
   - 风险管理

4. 回测验证
   - 样本内测试
   - 参数优化
   - 样本外验证

5. 实盘准备
   - 模拟交易
   - 风险管理
   - 技术架构

6. 执行监控
   - 实时监控
   - 性能评估
   - 策略迭代
"""

# 避免过度拟合
def avoid_overfitting(cv_results, max_params=10):
    """避免过度拟合"""
    n_params = len(cv_results['params'])
    train_score = cv_results['train_score'].mean()
    test_score = cv_results['test_score'].mean()
    
    # 检查是否过度拟合
    if n_params > max_params:
        print("警告：参数过多，可能过度拟合")
    
    # 检查泛化能力
    if train_score - test_score > 0.1:
        print("警告：训练/测试差距过大")
    
    return test_score
```

### 9.2 风险管理

```python
# 风险管理框架
class RiskManager:
    def __init__(self, max_position=0.1, max_loss=0.2):
        self.max_position = max_position  # 最大仓位
        self.max_loss = max_loss  # 最大亏损
        self.daily_pnl = []
        
    def check_risk(self, portfolio_value, trade_size, price):
        """检查风险"""
        position_value = trade_size * price
        position_pct = position_value / portfolio_value
        
        # 仓位限制
        if position_pct > self.max_position:
            trade_size = portfolio_value * self.max_position / price
            
        # 止损检查
        if len(self.daily_pnl) > 0:
            cumulative_loss = sum(self.daily_pnl)
            if cumulative_loss < -self.max_loss * portfolio_value:
                return 0  # 触发止损
                
        return trade_size
```

## 十，总结

**awesome-systematic-trading** 是 **8.4k Stars 的量化交易资源宝库**：

| 分类 | 内容 |
|------|------|
| 📚 **研究论文** | 动量、均值回归、统计套利、机器学习、加密货币 |
| 🗃️ **代码库** | Python、R、Julia、TypeScript |
| 📊 **数据集** | 市场数据、另类数据、数据预处理 |
| 📖 **书籍** | 技术分析、期权、机器学习、交易心理学 |
| 🎓 **课程** | 量化金融、交易系统、金融工程 |
| 💰 **资源** | 博客、社区、基金排名 |

**核心亮点**：
- ✅ **全面覆盖**：从论文到实战全链路
- ✅ **精选内容**：高质量资源导航
- ✅ **多语言支持**：Python/R/Julia
- ✅ **持续更新**：社区活跃

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/paperswithbacktest/awesome-systematic-trading |
| Backtrader | https://www.backtrader.com |
| QuantConnect | https://www.quantconnect.com |
| Zipline | https://zipline.io |
| sklearn | https://scikit-learn.org |

---

_🦞 本文由钳岳星君撰写，基于 awesome-systematic-trading (8.4k Stars)_
