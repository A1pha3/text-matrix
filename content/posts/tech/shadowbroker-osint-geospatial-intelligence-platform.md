---
categories: ["技术笔记"]
date: "2026-05-18T20:00:00+08:00"
slug: "shadowbroker-osint-geospatial-intelligence-platform"
description: "ShadowBroker是一款开源地理空间情报平台，整合60+实时OSINT数据源到统一地图界面，涵盖航班、船舶、卫星、监控摄像头等多种数据层。本文详解其架构、数据源生态、InfoNet隐私边界及Docker快速部署方法。"
---

# ShadowBroker：开源地理空间情报平台入门指南

**ShadowBroker**（`BigBodyCobain/Shadowbroker`，7.4k ⭐）是一款将全球开放源情报（OSINT）聚合到统一暗色地图界面的开源项目。它整合了航班、船舶、监控摄像头、卫星、地震、GPS干扰等60余个实时数据流，以35+个可叠加图层呈现，并支持 SAR 地面变化检测、实验性 InfoNet 隐匿通讯及 HMAC 签名的 Agent 命令通道。

---

## 一、核心架构

ShadowBroker 采用前后端分离设计：

| 组件 | 技术栈 | 作用 |
|------|--------|------|
| 前端 | Next.js + MapLibre GL | 地图渲染、图层切换、视觉模式切换 |
| 后端 | FastAPI (Python) | 数据聚合、API代理、Agent通道 |
| 部署 | Docker Compose | 一键启动，无需本地编译 |

```bash
git clone https://github.com/BigBodyCobain/Shadowbroker.git
cd Shadowbroker
docker compose up -d
```

启动后访问 `http://localhost:3000` 即可进入地图界面。

---

## 二、60+数据源与35+图层

ShadowBroker 的数据层涵盖多个维度，以下是主要类别：

**航空 & 船舶**
- ADS-B 航班追踪
- AIS 船舶自动识别系统

**监控 & 通讯**
- CCTV 监控摄像头分布
- Police Scanner 警用无线电
- Mesh Radio 网状无线电网络

**太空 & 地球物理**
- Spy Satellites 间谍卫星轨道
- Earthquakes 地震活动
- GPS Jamming GPS干扰区域
- Satellites 卫星位置

**地表变化检测**
- SAR Ground Change Detection，基于 NASA OPERA 和 Copernicus EGMS 的合成孔径雷达地面变化检测，可识别地形扰动

**实验性功能**
- InfoNet：去中心化隐匿消息系统 + Sovereign Shell 治理经济（testnet，无隐私保证）

---

## 三、五种视觉模式

界面支持五种地图渲染模式，通过顶部切换器选择：

- **DEFAULT**：标准地图视图
- **SATELLITE**：卫星影像底图
- **FLIR**：红外热成像模拟风格
- **NVG**：夜视镜（NVG）绿色单色模式
- **CRT**：老式阴极射线管模拟效果

不同模式适用于不同光照环境和视觉偏好。

---

## 四、右键上下文情报

在地图任意位置**右键点击**，会弹出该地点的综合情报卡，包含：

- 国家档案（Country Dossier）
- 国家元首信息
- Wikipedia 百科摘要
- Sentinel-2 卫星实拍影像

无需切换标签页，在地图内即可获取地点背景信息。

---

## 五、InfoNet：隐私边界与实验状态

InfoNet 是 ShadowBroker 中的去中心化隐匿消息系统，设计目标是绕过互联网审查。但项目方**明确声明**：

> InfoNet 为实验性 testnet，**no privacy guarantee**，尚未实现端到端加密。

具体来说：
- InfoNet 基于模糊化（obfuscation）+ 去中心化路由
- Sovereign Shell 是其内置的治理代币经济模型
- 数据传输路径未经过完整加密验证
- **不适合处理真正敏感的信息**

如果你需要强隐私保证的通讯工具，应选择已经过广泛审计的 Signal 或类似方案。InfoNet 更适合作为 OSINT 可视化的附加模块，而非主力通讯工具。

---

## 六、Agent 命令通道（HMAC 签名）

ShadowBroker 内置了一个 **HMAC-signed agentic command channel**，支持 OpenClaw 及任何使用 HMAC 签名的 Agent 系统接入。

这意味着：
- Agent 可以通过签名消息远程查询地图数据
- 命令内容经过 HMAC 校验，防止篡改
- 可作为地理情报的自动化获取层

对于部署了 OpenClaw 的用户，这提供了一个结构化的情报获取接口。

---

## 七、Docker 快速部署

ShadowBroker 全部采用预构建镜像，无需本地编译 Rust/C++ 等组件：

```yaml
# docker-compose.yml 核心配置
services:
  frontend:
    image: shadowbroker/frontend:latest
    ports:
      - "3000:3000"
    depends_on:
      - backend

  backend:
    image: shadowbroker/backend:latest
    environment:
      - API_KEY=${API_KEY}
    ports:
      - "8000:8000"
```

```bash
# 一键启动
docker compose up -d

# 查看日志
docker compose logs -f
```

**注意**：部分数据层（如 ADS-B、AIS）需要第三方 API Key，请在 `.env` 中配置对应密钥。

---

## 八、使用边界与伦理考量

ShadowBroker 整合的所有数据均为**公开发布的 OSINT 数据**，不涉及未授权的监控或数据窃取。具体而言：

| 数据类型 | 来源 | 性质 |
|----------|------|------|
| ADS-B 航班 | 公开广播 | 国际标准，合法 |
| AIS 船舶 | MarineTraffic 等 | 航海法规要求 |
| CCTV 分布 | 公开地图 | 仅标注摄像头存在，不涉及内容 |
| 地震/卫星 | NASA/Copernicus | 科研数据开放获取 |

然而，这并不意味着可以随意滥用：
- **CCTV 摄像头分布图层** 仅标注位置，不应用于寻找监控盲区等目的
- **SAR 变化检测** 数据涉及地形变化分析，存在被滥用于关键基础设施破坏的风险
- **右键国家档案** 中的敏感国家元首信息，应仅用于正当研究目的

**负责任地使用** 是该项目的基本使用伦理。所有数据均可自托管，不存在用户追踪机制。

---

## 九、适用场景

ShadowBroker 适合以下场景：

- **威胁情报分析**：结合航班/船舶轨迹，追踪特定目标的地理活动
- **地缘政治研究**：地震、GPS干扰、卫星轨道等多维度数据叠加分析
- **应急响应**：自然灾害期间的 SAR 变化检测 + 实时交通数据
- **技术学习**：MapLibre GL + FastAPI 全栈架构参考

---

## 十、总结

ShadowBroker 将散落在各处的大量公开 OSINT 数据源整合到一个统一的地图界面中，以35+可叠加图层、五种视觉模式、右键情报卡等交互设计，让地理空间情报的获取和分析变得可视化且高效。它还通过 SAR 地面变化检测、InfoNet 消息系统和 HMAC Agent 通道，展示了从数据展示向主动情报能力延伸的可能性。

但请记住：**数据是公开的，行动是自己的**。请务必在法律和伦理框架内使用这一工具。