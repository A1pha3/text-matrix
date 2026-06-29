---
title: "Pascal Editor：基于React Three Fiber的WebGPU 3D建筑编辑器"
date: "2026-05-19T20:25:00+08:00"
slug: "pascal-editor-3d-architecture-webgpu"
description: "Pascal Editor是一个用React Three Fiber和WebGPU构建的3D建筑编辑器，采用Turborepo monorepo架构，核心包@pascal-app/core负责状态管理，@pascal-app/viewer负责3D渲染，可在Next.js应用中集成。"
draft: false
categories: ["技术笔记"]
tags: ["React Three Fiber", "WebGPU", "3D编辑器", "TypeScript", "Next.js"]
---

## 学习目标

读完本文后，你应该能够：

1. **理解 Pascal Editor 的技术定位**：知道它是一个技术 demo 而非成熟产品，明确它的适用边界
2. **掌握其核心架构**：理解 Turborepo monorepo 结构、Zustand 三 store 分工、npm 包职责分离
3. **评估是否采用**：根据你的场景判断 Pascal Editor 是否适合作为学习参考或直接依赖
4. **上手修改**：能够在本地启动编辑器，理解 `useScene` / `useViewer` / `useEditor` 三个 store 的分工
5. **扩展能力**：理解 `@pascal-app/core` 和 `@pascal-app/viewer` 如何独立使用，以便在自己的项目中集成

## 目录

1. [先给判断](#先给判断)
2. [系统地图](#系统地图)
3. [核心架构](#核心架构)
   - 3.1 [状态管理（Zustand）](#1-状态管理zustand)
   - 3.2 [节点系统](#2-节点系统)
   - 3.3 [包职责分离](#3-包职责分离)
   - 3.4 [技术栈](#4-技术栈)
4. [适用边界](#适用边界)
5. [npm 包](#npm-包)
6. [自测题](#自测题)
7. [练习](#练习)
8. [进阶路径](#进阶路径)
9. [资料口径说明](#资料口径说明)
10. [结论](#结论)

<!--more-->

## 先给判断

Pascal Editor 是一个面向 3D 建筑/场景编辑场景的技术 demo，而不是一个开箱即用的产品。它的关键价值在于**展示了如何用现代 Web 技术栈构建 3D 编辑器**：React Three Fiber 做渲染，Zustand 做状态管理，Turborepo 做工程结构。

如果你在研究 WebGPU 时代的 3D Web 应用，它值得一看；如果你需要一个能直接使用的 3D 编辑器，它还不到那个成熟度。

## 系统地图

```
Pascal Editor (Turborepo Monorepo)
│
├── apps/
│   └── editor/          # Next.js编辑器应用
│       ├── UI组件        # 工具栏、侧边栏、面板
│       ├── 编辑器状态    # useEditor (Zustand)
│       └── 自定义行为    # 编辑器特定系统
│
└── packages/
    ├── core/            # 核心逻辑包
    │   ├── 节点Schema    # BaseNode类型定义
    │   ├── useScene      # 场景状态 (Zustand)
    │   ├── 系统          # 几何生成、空间查询
    │   └── 事件总线      # 包间通信
    │
    └── viewer/           # 3D渲染包
        ├── useViewer    # 查看器状态 (Zustand)
        ├── 3D渲染        # React Three Fiber
        ├── 默认相机/控制  #
        └── 后处理        #
```

## 核心架构

### 1. 状态管理（Zustand）

项目用 Zustand 做状态管理，分三个独立 store：

**useScene（core 包）：**
- 管理场景数据：nodes、root IDs、dirty nodes
- CRUD 操作
- 持久化到 IndexedDB
- undo/redo 支持（通过 Zundo）

**useViewer（viewer 包）：**
- 查看器状态：当前选择、层级显示模式、相机模式

**useEditor（apps/editor）：**
- 编辑器状态：活动工具、结构层可见性、面板状态

```typescript
// React组件中订阅状态
const nodes = useScene((state) => state.nodes)
const levelId = useViewer((state) => state.selection.levelId)

// 在回调中访问状态（不在React组件内）
const node = useScene.getState().nodes[id]
```

### 2. 节点系统

所有场景节点继承`BaseNode`：

```typescript
interface BaseNode {
  id: string          // 类型前缀+随机ID，如"wall_abc123"
  type: string        // 类型区分符
  parentId: string | null  // 父子关系
  visible: boolean
  camera?: Camera     // 可选保存的相机位置
  metadata?: JSON     // 任意元数据
}
```

### 3. 包职责分离

| 包 | 职责 | 可独立使用 |
|----|------|-----------|
| **@pascal-app/core** | 节点 Schema、场景状态、系统（几何生成、空间查询、事件总线） | ✅ 可以 |
| **@pascal-app/viewer** | 3D 渲染、默认相机/控制、后处理 | ✅ 可以（已有默认设置） |
| **apps/editor** | UI 组件、工具、编辑器特定行为 | ❌ 依赖 core 和 viewer |

### 4. 技术栈

- **渲染**：React Three Fiber + WebGPU（推测）
- **状态管理**：Zustand + Zundo（undo/redo）
- **持久化**：IndexedDB
- **工程管理**：Turborepo
- **应用框架**：Next.js
- **语言**：TypeScript

## 适用边界

**该用：**
- 研究 React Three Fiber + Zustand 的 3D 应用架构
- 学习如何设计可复用的 3D 渲染包
- 构建需要模块化拆分的复杂 3D 应用

**不该用：**
- 需要直接可用的 3D 建筑编辑器——它更多是技术 demo
- 没有 React/TypeScript 经验——代码阅读门槛较高
- 生产环境——项目成熟度不足以支撑生产

## npm 包

项目发布了两独立的 npm 包：

```bash
# 核心逻辑
npm install @pascal-app/core

# 3D渲染组件
npm install @pascal-app/viewer
```

## 自测题

1. **Pascal Editor 是一个成熟的产品还是技术 demo？**
   <details>
   <summary>点击查看答案</summary>
   它是一个技术 demo，展示了如何用现代 Web 技术栈构建 3D 编辑器，但还不是开箱即用的成熟产品。
   </details>

2. **Pascal Editor 使用了哪三个 Zustand store？它们的职责分别是什么？**
   <details>
   <summary>点击查看答案</summary>
   - `useScene`（core 包）：管理场景数据（nodes、root IDs、dirty nodes），提供 CRUD 操作，持久化到 IndexedDB，支持 undo/redo
   - `useViewer`（viewer 包）：管理查看器状态（当前选择、层级显示模式、相机模式）
   - `useEditor`（apps/editor）：管理编辑器状态（活动工具、结构层可见性、面板状态）
   </details>

3. **`@pascal-app/core` 和 `@pascal-app/viewer` 是否可以独立使用？**
   <details>
   <summary>点击查看答案</summary>
   是的，这两个包都可以独立使用。`@pascal-app/core` 包含节点 Schema、场景状态、系统（几何生成、空间查询、事件总线）；`@pascal-app/viewer` 包含 3D 渲染、默认相机/控制、后处理，且已有默认设置。
   </details>

4. **Pascal Editor 的节点系统基于什么接口？请写出一个节点的基本结构。**
   <details>
   <summary>点击查看答案</summary>
   所有场景节点继承 `BaseNode` 接口：
   ```typescript
   interface BaseNode {
     id: string          // 类型前缀+随机ID，如"wall_abc123"
     type: string        // 类型区分符
     parentId: string | null  // 父子关系
     visible: boolean
     camera?: Camera     // 可选保存的相机位置
     metadata?: JSON     // 任意元数据
   }
   ```
   </details>

5. **如果你想在现有 Next.js 项目中集成 Pascal Editor 的 3D 渲染能力，应该安装哪个 npm 包？**
   <details>
   <summary>点击查看答案</summary>
   应该安装 `@pascal-app/viewer`，它负责 3D 渲染，且可以独立使用（已有默认设置）。
   </details>

---

## 练习

### 练习 1：本地启动 Pascal Editor

1. 克隆仓库：`git clone https://github.com/pascalorg/editor`
2. 安装依赖：`npm install`（或 `pnpm install`）
3. 启动开发服务器：`npm run dev`（或按项目 README 说明）
4. 在浏览器中打开 Next.js 编辑器应用，尝试创建一个简单场景

### 练习 2：理解 Zustand Store 订阅

在 React 组件中订阅 `useScene` store 的状态：

```typescript
import { useScene } from '@pascal-app/core';

function NodeList() {
  const nodes = useScene((state) => state.nodes);
  return (
    <ul>
      {Object.values(nodes).map(node => (
        <li key={node.id}>{node.type}: {node.id}</li>
      ))}
    </ul>
  );
}
```

### 练习 3：扩展节点 Schema

在 `@pascal-app/core` 中定义一个新的节点类型，继承 `BaseNode`，并添加到场景中。

---

## 进阶路径

1. **理解 React Three Fiber**：学习 R3F 的渲染机制、相机控制、后处理，参考 [React Three Fiber 文档](https://docs.pmnd.rs/react-three-fiber)
2. **深入 Zustand**：学习 Zustand 的中间件（如 Zundo for undo/redo）、异步 action、跨 store 通信
3. **研究 Turborepo**：理解 monorepo 的工程化实践，学习如何设计可独立发布的 npm 包
4. **学习 WebGPU**：理解 WebGPU 的渲染管线、shader 编程，参考 [WebGPU 规范](https://www.w3.org/TR/webgpu/)
5. **构建自己的 3D 编辑器**：基于 Pascal Editor 的架构，添加自己的工具和功能，参考 [Three.js 编辑器](https://threejs.org/editor/) 的设计

---

## 资料口径说明

1. **项目成熟度**：Pascal Editor 是一个技术 demo，项目成熟度不足以支撑生产环境。本文基于 GitHub 仓库的代码结构和 README 信息，未进行深入的功能测试。
2. **技术栈推测**：本文提到"WebGPU（推测）"，因为标题提到 WebGPU 但代码中可能仍使用 WebGL。具体渲染后端需要查看源码确认。
3. **npm 包版本**：`@pascal-app/core` 和 `@pascal-app/viewer` 的版本和 API 可能随时间变化，请以 [npm 官网](https://www.npmjs.com/) 的最新信息为准。
4. **性能指标**：本文未提供性能指标（如 FPS、内存占用）。实际性能取决于场景复杂度、设备硬件、渲染后端（WebGL/WebGPU）。
5. **兼容性**：本文未测试浏览器兼容性。React Three Fiber 和 WebGPU 的兼容性取决于目标浏览器。
6. **许可证**：项目使用 MIT 许可证，允许自由使用、修改和分发。

---

## 结论

Pascal Editor 是一个有技术含量的 3D Web 应用示例。它的价值不在于"这是一个好用的编辑器"，而在于**展示了如何用现代工程实践构建复杂的 3D Web 应用**：monorepo 结构、模块化包设计、Zustand 状态管理、React Three Fiber 渲染。

如果你在研究 3D Web 应用的技术架构，这个项目的代码结构值得参考；如果你只是在找一个能用的 3D 编辑器，等项目更成熟再说。

---

**仓库信息**：https://github.com/pascalorg/editor | Stars: 15,716 | License: MIT | 语言： TypeScript