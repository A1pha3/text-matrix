---
title: "Lightweight Charts™：TradingView 开源轻量级金融图表库"
date: "2026-04-12T01:52:00+08:00"
slug: lightweight-charts-tradingview-financial-charts-guide
github_repo: "tradingview/awesome-tradingview"
description: "Lightweight Charts 是 TradingView 开源的轻量级金融图表库，16.3K+ Stars，支持 K线、折线、柱状图等金融图表类型，性能卓越。"
draft: false
categories: ["技术笔记"]
tags: ["JavaScript", "TypeScript", "金融"]
---

# Lightweight Charts™：TradingView 开源轻量级金融图表库

## 项目概述

Lightweight Charts™ 是 TradingView 开源的金融图表库，压缩后约 40KB（gzip），专为网页端金融数据可视化设计。基于 Canvas 渲染，在大数据量场景下性能优于 SVG，可流畅处理 10 万根 K 线。

项目由 TradingView 官方维护，Apache-2.0 开源协议，当前最新稳定版为 v5.2.1（2026 年 8 月发布）。适用场景：页面 JS 已较重，再引入图表库会拖慢加载；或数据量大，ECharts/Highcharts 已出现卡顿。

需要注意，Lightweight Charts 是纯客户端库，不用于 Node.js 等服务端场景；运行要求浏览器支持 ES2020 语法。

## 核心架构

### 设计理念

核心卖点：小（压缩后约 40KB，比 ECharts 小一个数量级）和快（Canvas 渲染，大数据量下帧率更高）。

架构分两层：

- **渲染引擎**：直接操作浏览器 Canvas API，负责数据绘制。不对外暴露，修改渲染逻辑需改源码。
- **API 层**：公开接口，用于创建图表、添加系列、配置样式、绑定事件。

### 技术栈

源码以 TypeScript 为主，部分功能用 JavaScript。目录结构：

- `src/`：核心源码（渲染引擎 + API 层）
- `tests/`：测试文件
- `website/`：官方文档网站源码
- `indicator-examples/`：技术指标示例
- `plugin-examples/`：插件开发示例
- `packages/create-lwc-plugin/`：插件脚手架

打包用 Rollup，输出多种构建变体（standalone/non-standalone，production/development），变体选择取决于项目环境。

## 快速上手

### 安装

三种方式，按项目环境选择：

**1. npm（有构建工具的项目）**

```bash
npm install lightweight-charts
```

支持 tree-shaking，打包时只包含用到的代码。

**2. pkg.pr.new（尝鲜 master 分支）**

```bash
npm install https://pkg.pr.new/lightweight-charts@master
```

安装 master 分支最新代码，可能不稳定，仅用于测试新功能或验证 bug 修复。

**3. CDN（快速原型或无构建工具的项目）**

```html
<script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
```

`standalone` 版本内置了所有依赖，开箱即用。非 `standalone` 版本需项目自身有 d3、moment 等依赖，一般用不到。

### 最小可运行示例

**npm 模块方式**：

```javascript
import { createChart, LineSeries } from 'lightweight-charts';

const container = document.getElementById('chart');
const chart = createChart(container, { width: 400, height: 300 });
const line = chart.addSeries(LineSeries, { color: '#2962FF' });
line.setData([
    { time: '2019-04-11', value: 80.01 },
    { time: '2019-04-12', value: 96.63 },
    { time: '2019-04-13', value: 76.64 },
]);
```

**CDN 方式**：

```html
<div id="chart" style="width: 400px; height: 300px;"></div>
<script>
    const chart = LightweightCharts.createChart(document.getElementById('chart'), {
        width: 400, height: 300,
    });
    const line = chart.addSeries(LightweightCharts.LineSeries);
    line.setData([
        { time: '2019-04-11', value: 80.01 },
        { time: '2019-04-12', value: 96.63 },
    ]);
</script>
```

容器必须有明确宽度和高度，不能靠内容撑开。时间格式为 ISO 8601 字符串或时间戳，不能传 Date 对象。

### 图表配置

创建图表时可以传入丰富的配置选项：

```javascript
import { createChart, CrosshairMode } from 'lightweight-charts';

const chart = createChart(document.body, {
    width: 800,           // 图表宽度
    height: 400,          // 图表高度
    layout: {
        background: { color: '#ffffff' },  // 背景色
        textColor: '#333333',             // 文字颜色
    },
    grid: {
        vertLines: { color: '#e0e0e0' },  // 垂直网格线
        horzLines: { color: '#e0e0e0' },  // 水平网格线
    },
    crosshair: {
        mode: CrosshairMode.Normal,
    },
    rightPriceScale: {
        borderColor: '#d1d1d1',
    },
    timeScale: {
        borderColor: '#d1d1d1',
        timeVisible: true,
        secondsVisible: false,
    },
});
```

## 图表类型详解

v5 共提供 6 种系列类型：Area、Bar、Baseline、Candlestick、Histogram、Line。下方详解 4 种最常用的，Bar（柱状 K 线）与 Baseline（基线图）用法类似，可在官方文档查阅。

### 柱状 K 线图（BarSeries）

与 K 线图信息相同，但以竖线加两侧短横线表示；开盘价在左，收盘价在右。

```javascript
const bar = chart.addSeries(BarSeries, { upColor: '#26a69a', downColor: '#ef5350' });
bar.setData([
    { time: '2023-01-01', open: 100, high: 105, low: 98, close: 103 },
]);
```

### 基线图（BaselineSeries）

在一条水平基准线之上显示为一种颜色、之下显示为另一种颜色，适合净值相对 0 轴或某基线的涨跌。

```javascript
const baseline = chart.addSeries(BaselineSeries, {
    topLineColor: '#26a69a', bottomLineColor: '#ef5350',
});
baseline.setData([
    { time: '2023-01-01', value: 100 },
    { time: '2023-01-02', value: 95 },
]);
```

### 折线图（LineSeries）

只画收盘价，适合看趋势。不展示开盘价、最高价、最低价。

```javascript
const line = chart.addSeries(LineSeries, { color: '#2962FF', lineWidth: 2 });
line.setData([
    { time: '2023-01-01', value: 100 },
    { time: '2023-01-02', value: 105 },
    { time: '2023-01-03', value: 102 },
]);
```

`time` 必须是字符串（ISO 8601）或数字（秒级时间戳），不能传 Date 对象。

### K 线图（CandlestickSeries）

一根蜡烛展示开盘、收盘、最高、最低四个价。

```javascript
const candlestick = chart.addSeries(CandlestickSeries, {
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderUpColor: '#26a69a',
    borderDownColor: '#ef5350',
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
});
candlestick.setData([
    { time: '2023-01-01', open: 100, high: 105, low: 98, close: 103 },
    { time: '2023-01-02', open: 103, high: 108, low: 101, close: 106 },
]);
```

每个数据点必须有 `open`、`high`、`low`、`close` 四个字段。

### 柱状图（HistogramSeries）

适合展示成交量或 MACD 等指标。

```javascript
const histogram = chart.addSeries(HistogramSeries, {
    color: '#26a69a',
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume',
});
chart.priceScale('volume').applyOptions({
    scaleMargins: { top: 0.8, bottom: 0 },
});
histogram.setData([
    { time: '2023-01-01', value: 1000000 },
    { time: '2023-01-02', value: 1200000 },
]);
```

### 面积图（AreaSeries）

折线图的变体，在折线和横轴之间填充颜色。适合展示净值曲线、资金流向等。

```javascript
const area = chart.addSeries(AreaSeries, {
    topColor: 'rgba(41, 98, 255, 0.28)',
    bottomColor: 'rgba(41, 98, 255, 0.05)',
    lineColor: '#2962FF',
    lineWidth: 2,
});
area.setData([
    { time: '2023-01-01', value: 100 },
    { time: '2023-01-02', value: 105 },
    { time: '2023-01-03', value: 102 },
]);
```

## 数据管理

### 时间数据格式

支持三种格式：

```javascript
// 1. ISO 8601 日期字符串
{ time: '2023-01-01' }

// 2. ISO 8601 日期时间字符串（需设置 timeVisible: true）
{ time: '2023-01-01T09:30:00' }

// 3. 秒级时间戳（非毫秒级）
{ time: 1672531200 }
```

注意事项：

1. **时间戳必须是秒级**。`Date.now()` 返回毫秒级，需除以 1000：`Math.floor(Date.now() / 1000)`。
2. **数据必须按时间顺序排列**。传入前先排序：`data.sort((a, b) => a.time - b.time)`（时间戳）或 `data.sort((a, b) => a.time.localeCompare(b.time))`（字符串）。
3. **不能传 `Date` 对象**。

### 实时更新

实时行情推送用 `update` 而非 `setData`：

```javascript
// 错误：全量替换，性能差
line.setData(newData);

// 正确：增量更新
line.update({ time: '2023-01-03', value: 110 });
```

- `setData`：替换整个数据集，触发全量重绘。用于初始化和历史数据加载。
- `update`：更新最后一根 K 线或追加新 K 线，触发增量重绘。用于实时行情。

`update` 的时间若与最后一根 K 线相同，则更新该 K 线；否则追加新 K 线。

### 数据切片

数据量大时，用 `setVisibleRange` 只渲染可见范围：

```javascript
chart.timeScale().setVisibleRange({
    from: '2023-01-01',
    to: '2023-01-31',
});

chart.timeScale().subscribeVisibleTimeRangeChange(range => {
    // 动态加载可见范围数据
});
```

Lightweight Charts 没有内置数据分页，需自行实现：监听 `subscribeVisibleTimeRangeChange`，按可视范围向服务端请求数据。

## 交互功能

### 十字线（Crosshair）

```javascript
chart.applyOptions({
    crosshair: {
        mode: LightweightCharts.CrosshairMode.Magnet, // Normal/Magnet/Hidden/MagnetOHLC
        vertLine: { color: '#758696', width: 1, visible: true },
        horzLine: { color: '#758696', width: 1, visible: true },
    },
});
```

CrosshairMode 枚举：`Normal`（自由移动）、`Magnet`（吸附到最近数据点）、`Hidden`（隐藏十字线）、`MagnetOHLC`（吸附至开盘/最高/最低/收盘价）。关闭十字线用 `Hidden`，而非设置 `mode: -1`。关闭线条用 `vertLine.visible`/`horzLine.visible` 设为 `false`。

### 价格线与时间标记

支持在图表上绘制价格线（横线）和标记重要时间点，用于标注支撑位、压力位、关键事件。

价格线（横线）通过系列创建（`.createPriceLine`）；时间标记（阿拉伯数字小圆标）通过系列的 `setMarkers` 设置。核心库没有 `chart.createTimeLine` 方法：

```javascript
// 价格线（横线），由系列创建
const supportLine = line.createPriceLine({
    price: 100, color: '#b71c1c', lineWidth: 1, lineStyle: 2,
    axisLabelVisible: true, title: '支撑位',
});
// 不再需要时移除
line.removePriceLine(supportLine);

// 时间标记（竖线），附着于系列，time 用该系列的时间格式
line.setMarkers([
    { time: '2023-01-01', position: 'aboveBar', color: '#2196F3', shape: 'circle', text: '财报发布' },
]);
```

`position` 可选 `aboveBar`（一侧靠上）或 `belowBar`（另一侧靠下）；`shape` 可选 `circle`、`square`、`arrowUp`、`arrowDown`。

### 响应式调整

图表不会自动跟随容器大小变化，需要手动处理。

**方法一：`autoSize: true`**

```javascript
const chart = createChart(container, { autoSize: true });
```

需浏览器支持 `ResizeObserver`（Chrome 64+, Firefox 69+, Safari 13.1+）。

**方法二：`ResizeObserver`**

```javascript
const chart = createChart(container, {
    width: container.clientWidth, height: container.clientHeight,
});
const resizeObserver = new ResizeObserver(entries => {
    for (const { contentRect: { width, height } } of entries)
        chart.resize(width, height);
});
resizeObserver.observe(container);
```

**方法三：`window.resize`（不推荐，仅容器尺寸变化不触发）**

```javascript
window.addEventListener('resize', () => {
    chart.resize(container.clientWidth, container.clientHeight);
});
```

方法三仅在窗口大小变化时触发，侧边栏展开/收起等容器尺寸变化不会触发，且触发频率高。

## 插件系统

插件用于扩展图表功能，如添加技术指标、自定义绘制、事件处理等。

### 技术指标示例

核心库本身不含现成指标。官方在 `indicator-examples` 目录提供了一批自包含示例（如 SMA、EMA、MACD、平均价格等），每个指标含两种写法：

- **Helper 函数**（推荐）：如 `applyMovingAverageIndicator(sourceSeries, options)`，自动创建指标序列，并在源数据更新时同步重算。
- **纯函数**：如 `calculateMovingAverageIndicatorValues(data)`，从静态数据集直接计算。

示例不被发布到 npm，需复制源码到项目，或自行执行 `indicator-examples` 目录的编译脚本后引入编译产物。以官方 Moving Average 为例，复制 `indicator-examples/src/indicators/moving-average/` 与 `helpers/timestamp-data.ts` 后：

```javascript
import { createChart, CandlestickSeries, LineSeries } from 'lightweight-charts';
import { applyMovingAverageIndicator } from './indicators/moving-average/moving-average';

const chart = createChart(container);
const candlestick = chart.addSeries(CandlestickSeries);
candlestick.setData(candleData);
applyMovingAverageIndicator(candlestick, { period: 14 });
```

若只是想叠加一条自定义指标曲线，也可直接计算好数据后用 `addSeries(LineSeries, {...})` 绘制，不必引入示例代码。

### 自定义插件

使用官方脚手架创建：

```bash
npx create-lwc-plugin my-custom-indicator
```

核心是实现 `requestData`、`requestMoreData`、`calcBase` 等钩子函数。官方文档对插件开发介绍较简略，细节需参考 `plugin-examples` 目录。如果只是添加自定义指标，可直接用 `addSeries` 绘制计算好的数据，不必写插件。

## 样式定制

支持全局设置和系列单独设置。

### 全局样式

影响背景、文字、网格线、十字线等：

```javascript
chart.applyOptions({
    layout: {
        background: { type: 'solid', color: '#1a1a1a' },
        textColor: '#d1d1d1', fontSize: 12, fontFamily: 'Roboto, Arial, sans-serif',
    },
    grid: {
        vertLines: { color: '#2a2a2a' },
        horzLines: { color: '#2a2a2a' },
    },
    crosshair: {
        vertLine: { color: '#555', width: 1, style: 2, labelBackgroundColor: '#2a2a2a' },
        horzLine: { color: '#555', width: 1, style: 2, labelBackgroundColor: '#2a2a2a' },
    },
});
```

### 系列样式

每个系列可单独设置，覆盖全局样式：

```javascript
const series = chart.addSeries(CandlestickSeries, {
    upColor: '#26a69a', downColor: '#ef5350',
    borderUpColor: '#26a69a', borderDownColor: '#ef5350',
    wickUpColor: '#26a69a', wickDownColor: '#ef5350',
    title: 'AAPL',
});

series.applyOptions({ upColor: '#00C853', downColor: '#FF1744' });
```

`applyOptions` 用于动态修改，创建系列时用 `addSeries` 的第二个参数传入初始样式。

## 构建变体

| 依赖 | 模式 | ES Module | IIFE |
|------|------|-----------|------|
| 无 | 生产 | `lightweight-charts.production.mjs` | - |
| 无 | 开发 | `lightweight-charts.development.mjs` | - |
| 有 | 生产 | `lightweight-charts.standalone.production.mjs` | `standalone.production.js` |
| 有 | 开发 | `lightweight-charts.standalone.development.mjs` | `standalone.development.js` |

选择原则：npm 项目直接 `import`，打包工具自动匹配；CDN 项目用 `standalone` 版本（内置依赖）；开发用 `development`（报错信息更全），生产用 `production`（体积更小）。

## 性能优化

上万根 K 线时，从以下方面优化。

### 数据优化

- **降低时间精度**：秒级数据改为日级或小时级，数据量从 10 万降至几百根。
- **数据采样**：对历史数据降采样，如 1 分钟 K 线合并为 5 分钟。
- **只加载可见范围**：用 `setVisibleRange` 配合 `subscribeVisibleTimeRangeChange` 动态加载。

### 渲染优化

- **利用数据合并（Conflation）**：v5.1+ 提供 `enableConflation` 选项，图表缩小时自动合并相邻数据点，让数万根 K 线的渲染在大缩放级别下依然流畅（默认关闭，需显式开启）：
  ```javascript
  const chart = createChart(container, {
      timeScale: { enableConflation: true, conflationThresholdFactor: 2.0 },
  });
  ```
- **关掉不需要的功能**：`crosshair: { mode: CrosshairMode.Hidden }` 隐藏十字线减少计算。
- **批量更新**：用 `requestAnimationFrame` 合并频繁更新：

```javascript
let pendingUpdate = null;
websocket.onmessage = event => {
    pendingUpdate = JSON.parse(event.data);
    requestAnimationFrame(() => {
        if (pendingUpdate) { line.update(pendingUpdate); pendingUpdate = null; }
    });
};
```

- **多个图表用独立 chart 实例**，避免性能互相影响。

### 内存优化

- `chart.remove()` 及时销毁不需要的图表。
- 指标计算（MACD、RSI）可放到 Web Worker 中，避免阻塞主线程。

## 许可与归属

Apache-2.0 协议。使用要求：

1. 分发修改版本需保留原始版权声明。
2. 在网页显著位置添加 [TradingView](https://www.tradingview.com/) 链接。
3. 若分发构建产物，附上官方 `NOTICE` 文件，说明使用了 Lightweight Charts。

官方要求以可读方式标注 TradingView 为产品创作者，但库没有内置的 attribution 开关配置，需在页面中自行放置链接与版权声明。

## 参考资源

- [官方 Demo](https://www.tradingview.com/lightweight-charts/)
- [官方文档](https://tradingview.github.io/lightweight-charts/)
- [插件示例](https://tradingview.github.io/lightweight-charts/plugin-examples/)
- [awesome-tradingview](https://github.com/tradingview/awesome-tradingview)
- [GitHub 仓库](https://github.com/tradingview/lightweight-charts)

---

*本文基于 [tradingview/lightweight-charts](https://github.com/tradingview/lightweight-charts)（Apache-2.0 License）编写。*