---
title: "Pascal Editor：基于React Three Fiber的WebGPU 3D建筑编辑器"
date: "2026-05-19T20:25:00+08:00"
slug: "pascal-editor-3d-architecture-webgpu"
description: "Pascal Editor是一个用React Three Fiber和WebGPU构建的3D建筑编辑器，采用Turborepo monorepo架构，核心包@pascal-app/core负责状态管理，@pascal-app/viewer负责3D渲染，可在Next.js应用中集成。"
draft: false
categories: ["技术笔记"]
tags: ["React Three Fiber", "WebGPU", "3D编辑器", "TypeScript", "Next.js"]
---

## 先给判断

Pascal Editor是一个面向3D建筑/场景编辑场景的技术demo，而不是一个开箱即用的产品。它的核心价值在于**展示了如何用现代Web技术栈构建3D编辑器**：React Three Fiber做渲染，Zustand做状态管理，Turborepo做工程结构。

如果你在研究WebGPU时代的3D Web应用，它值得一看；如果你需要一个能直接使用的3D编辑器，它还不到那个成熟度。

<!--more-->

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

项目用Zustand做状态管理，分三个独立store：

**useScene（core包）：**
- 管理场景数据：nodes、root IDs、dirty nodes
- CRUD操作
- 持久化到IndexedDB
- undo/redo支持（通过Zundo）

**useViewer（viewer包）：**
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
| **@pascal-app/core** | 节点Schema、场景状态、系统（几何生成、空间查询、事件总线） | ✅ 可以 |
| **@pascal-app/viewer** | 3D渲染、默认相机/控制、后处理 | ✅ 可以（已有默认设置） |
| **apps/editor** | UI组件、工具、编辑器特定行为 | ❌ 依赖core和viewer |

### 4. 技术栈

- **渲染**：React Three Fiber + WebGPU（推测）
- **状态管理**：Zustand + Zundo（undo/redo）
- **持久化**：IndexedDB
- **工程管理**：Turborepo
- **应用框架**：Next.js
- **语言**：TypeScript

## 适用边界

**该用：**
- 研究React Three Fiber + Zustand的3D应用架构
- 学习如何设计可复用的3D渲染包
- 构建需要模块化拆分的复杂3D应用

**不该用：**
- 需要直接可用的3D建筑编辑器——它更多是技术demo
- 没有React/TypeScript经验——代码阅读门槛较高
- 生产环境——项目成熟度不足以支撑生产

## npm包

项目发布了两独立的npm包：

```bash
# 核心逻辑
npm install @pascal-app/core

# 3D渲染组件
npm install @pascal-app/viewer
```

## 结论

Pascal Editor是一个有技术含量的3D Web应用示例。它的价值不在于"这是一个好用的编辑器"，而在于**展示了如何用现代工程实践构建复杂的3D Web应用**：monorepo结构、模块化包设计、Zustand状态管理、React Three Fiber渲染。

如果你在研究3D Web应用的技术架构，这个项目的代码结构值得参考；如果你只是在找一个能用的3D编辑器，等项目更成熟再说。

---

**仓库信息**：https://github.com/pascalorg/editor | Stars: 15,716 | License: MIT | 语言: TypeScript