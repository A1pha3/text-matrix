---
title: "Pascal Editor：浏览器端 3D 建筑建模编辑器的架构拆解"
date: 2026-07-30T23:50:00+08:00
slug: "pascalorg-editor-3d-architecture-guide"
description: "Pascal Editor 是一个基于 React Three Fiber 和 WebGPU 的 3D 建筑编辑器，拥有 20k Stars。本文从 monorepo 架构、节点模型、脏标记渲染管线、CSG 几何运算、插件机制和垂直建模模型六个维度，拆解其工程设计与取舍。"
draft: false
categories: ["技术笔记"]
tags: ["Three.js", "WebGPU", "3D 建筑建模", "React Three Fiber", "编辑器架构"]
---

Pascal Editor 解决的问题不是"在浏览器里画 3D 盒子"——这种东西 Three.js 教程里到处都是。它真正要做的，是在浏览器里跑起一套**结构化的建筑信息编辑器**：用户画一面墙，系统自动处理墙角斜切（mitering）、门窗开洞（CSG cutout）、楼板高程（slab elevation）、屋顶适配（roof clamp）和楼层堆叠（level stacking），同时保持撤销/重做、实时渲染和插件可扩展性。

这是一个在架构上花费了大量心思的项目。下文从六个维度展开它的设计取舍。

## 系统地图

Pascal Editor 是一个 Turborepo monorepo，五个运行时包各司其职：

| 包 | 职责 | 依赖方向 |
|---|---|---|
| `@pascal-app/core` | 节点 schema（Zod）、场景状态（Zustand）、注册表契约、空间查询、事件总线 | 无 Three.js 依赖 |
| `@pascal-app/viewer` | React Three Fiber 渲染、后处理管线、场景注册表、选择管理 | 依赖 core |
| `@pascal-app/editor` | 编辑工具、面板、选择交互、直接操作 UI | 依赖 viewer + core |
| `@pascal-app/nodes` | 内置节点定义（几何、渲染器、系统）——以插件形式注册 | 依赖 core + viewer |
| `apps/editor` | Next.js 宿主应用，组装以上包 | 依赖全部 |

这条依赖链的方向是单向的：core 不知道 Three.js 的存在，viewer 不知道编辑器的工具状态，editor 不关心节点几何如何生成。这种隔离不是装饰性的——它让同一个 viewer 既能在编辑器里运行，也能在只读的 `/viewer/[id]` 路由里嵌入，还能在未来嵌入任意第三方页面。

三套 Zustand store 分别管理各自的状态边界：

- `useScene`（core）——场景数据：节点字典、CRUD 操作、脏节点集合，通过 Persist 中间写入 IndexedDB，通过 Zundo 提供 50 步撤销/重做。
- `useViewer`（viewer）——展示状态：当前选择、楼层显示模式（堆叠/展开/独显）、相机模式、着色与纹理开关。
- `useEditor`（editor）——编辑状态：活动工具、结构层可见性、面板状态。

三个 store 可以独立访问，也可以在 React 组件外通过 `useScene.getState()` 直接读取——这一点对系统层（System）尤为重要，因为系统运行在 `useFrame` 循环里，不能触发 React 重渲染。

## 节点模型：扁平字典与层级语义

建筑数据天然是树形的：场地包含建筑，建筑包含楼层，楼层包含墙/板/天花板/屋顶。最容易想到的表示方法是嵌套树，但 Pascal 选择了**扁平字典**（flat dictionary）。

```typescript
useScene.getState() = {
  nodes: Record<id, AnyNode>,  // 所有节点存在一个 flat map 里
  rootNodeIds: string[],       // 顶层节点（场地）
  dirtyNodes: Set<string>,     // 等待系统处理的节点
}
```

每个节点通过 `parentId` 和 `children` 数组维护层级关系，但数据本身是扁平存储的。这样做的好处：

1. **O(1) 查找**——通过 ID 直接取节点，不需要遍历树。
2. **更新局部化**——修改一面墙不需要序列化整棵建筑树。
3. **持久化简单**——IndexedDB 存的是一个平坦的对象，不需要递归序列化。

节点的类型系统用 Zod 定义，所有节点继承自 `BaseNode`：

```typescript
BaseNode {
  id: string              // 带类型前缀，如 "wall_abc123"
  type: string            // 类型判别器
  parentId: string | null // 父节点引用
  visible: boolean
  camera?: Camera         // 可选的相机位置存档
  metadata?: JSON         // 任意元数据
}
```

ID 生成用 `nanoid` 加上类型前缀（`wall_`、`slab_`、`door_`），在调试和日志里一眼就能看出节点类型。

建筑节点的层级语义是固定的：

```
Site
└── Building
    └── Level
        ├── Wall → Item (doors, windows)
        ├── Slab
        ├── Ceiling → Item (lights)
        ├── Roof
        ├── Zone
        ├── Scan (3D reference)
        └── Guide (2D reference)
```

这种层级不是随意的组合——它直接影响垂直模型的计算规则（后文详述）。

## 脏标记渲染管线：数据与渲染解耦

Pascal 的渲染管线是这篇文章里最值得拆开看的工程决策。

大多数 React Three Fiber 项目会把几何生成直接放在组件里：props 变了，组件重新渲染，几何体跟着重建。这种模式在简单场景里没问题，但在建筑编辑器里会炸——一栋大楼可能有几百面墙，每次修改都全量重建几何体会卡帧。

Pascal 的做法是引入**脏标记队列**（dirty node queue）：

```
用户操作（点击/拖拽）
    ↓
工具处理器调用 useScene.updateNode()
    ↓
节点数据更新，同时节点 ID 加入 dirtyNodes
    ↓
React 重渲染 NodeRenderer（只是更新占位 mesh）
    ↓
System 在 useFrame 里检测 dirtyNodes
    ↓
遍历脏节点 → 查 sceneRegistry → 重建几何体 → 清除脏标记
```

关键在于，React 组件只负责创建占位 mesh 和注册到 `sceneRegistry`，不做几何计算。几何重建的工作交给 **System**——运行在 `useFrame` 循环里的无渲染 React 组件（返回 `null`）。

### 场景注册表

`sceneRegistry` 是一个全局可变映射，连接节点 ID 和 Three.js 的 `Object3D` 实例：

```typescript
sceneRegistry = {
  nodes: Map<id, Object3D>,   // ID → 3D 对象
  byType: {
    wall: Set<id>,            // 按类型索引
    item: Set<id>,
    // ...
  },
}
```

渲染器通过 `useRegistry` hook 同步注册（`useLayoutEffect`，在首次绘制前就位）。系统层通过 `sceneRegistry.nodes.get(id)` 做 O(1) 查找，不需要遍历场景图。

注册表的规则很严格：一个节点 ID 只能注册一个 `Object3D`；如果渲染器生成了多个 mesh，注册最外层的 group。core 层的系统不允许使用注册表——它们只操作纯数据。只有 viewer 层的系统才能做 Three.js 对象查找。

### System 的分层

系统分两类，住在不同的包里：

**Core 系统**（`packages/core/src/systems/`）——纯逻辑，不碰 Three.js：

| 系统 | 职责 |
|---|---|
| `WallSystem` | 墙体斜切、墙角连接 |
| `CeilingSystem` | 基于多边形的天花板生成 |
| `RoofSystem` | 坡屋顶形状 |
| `ItemSystem` | 物品变换、碰撞检测 |

**Viewer 系统**（`packages/viewer/src/systems/`）——可以操作 Three.js 对象：

| 系统 | 职责 |
|---|---|
| `LevelSystem` | 楼层可见性（堆叠/展开/独显/手动） |
| `WallCutout` | 在墙体几何上开门窗洞口 |
| `ZoneSystem` | 区域显示与标签 |
| `GuideSystem` | 辅助参考几何 |

Core 系统和 viewer 系统都挂在 `<Viewer>` 内部，但它们之间有严格的规则：core 不 import Three.js，viewer 不包含业务逻辑。

### 处理模式

脏节点的处理逻辑简洁到可以写成伪代码：

```typescript
useFrame(() => {
  for (const id of dirtyNodes) {
    const obj = sceneRegistry.nodes.get(id)
    const node = useScene.getState().nodes[id]
    updateGeometry(obj, node)
    dirtyNodes.delete(id)
  }
})
```

只有被标记为脏的节点才会重建几何。修改一面墙的厚度时，只有那面墙会被重新生成——其他几百面墙的几何体完全不受影响。

### 注册表驱动的节点定义

新版本引入了一套 registry-driven 模型，把"一种节点类型需要什么"拆成三个可选字段：

| 字段 | 用途 |
|---|---|
| `geometry` | 纯函数 `(node, ctx) => Object3D`，框架自动在脏节点上调用 |
| `renderer` | 自定义 React 组件（用于 GLB、HTML 标签、drei helper） |
| `system` | 每帧运行的组件（动画、脏级联、材质更新） |

三个字段独立组合。一个简单的货架只需要 `geometry`；一个带 HTML 标签的区域需要 `renderer` + `system`；一扇门需要 `geometry` + 动画 `system`。框架的 `<GeometrySystem>` 组件统一处理所有声明了 `def.geometry` 的节点——不用为每种节点类型写一个定制系统。

## CSG 与建筑几何

建筑编辑器绕不开 CSG（Constructive Solid Geometry）：在墙上开门窗洞口是最典型的 Boolean 减法运算。

Pascal 使用 `three-bvh-csg` 做几何布尔运算，配合 `three-mesh-bvh` 加速空间查询。这部分代码在 `packages/viewer/src/lib/csg-utils.ts` 和 `packages/viewer/src/systems/wall/` 下。

CSG 的工程挑战不在于算法本身，而在于如何在编辑器的实时帧循环里不卡帧。Pascal 的策略：

1. **延迟到脏节点处理**——门窗开洞只在墙体节点被标记为脏时才重新计算。
2. **最小化重建范围**——拖动一扇门只会把宿主墙标记为脏，不会触发整层楼的几何重建。
3. **属性保全**——CSG 运算可能丢失 UV、法线等属性，`ensureRenderableGeometryAttributes` 函数负责补全缺失的 `position`/`normal`/`uv`/`uv2` 属性，确保生成的几何体可以被 PBR 材质正确渲染。

墙体几何还处理了斜切（mitering）——两面墙相交时，端面按角度自动切割成斜角。这部分逻辑通过 `GeometryContext` 的 `siblings` 字段拿到同层级的相邻墙体，计算共享墙角的几何形状。

## 后处理管线：WebGPU 与 TSL

Pascal 是少数把 WebGPU 作为一等渲染器的 Web 3D 项目。后处理管线（`post-processing.tsx`）基于 Three.js 的 TSL（Three Shading Language）节点系统构建，包含：

- **SSGI**（屏幕空间全局光照）——提供环境光遮蔽（AO）和间接弹光，参数化的 `radius`、`aoIntensity`、`thickness` 可调。
- **Ink Edges**——屏幕空间墨水描边，有 `off`/`soft`/`strong` 三档。
- **Merged Outline**——选中高亮，合并渲染 14 个内部 RT。
- **Zone Pass**——区域半透明填充，独立合成在场景之上，避免透明面污染 SSGI 的深度/法线缓冲。
- **Overlay Pass**——编辑器 UI 叠加（gizmo、手柄、工具预览），渲染在所有后处理之后。
- **AgX 色调映射**——在输出前做场景级调色（对比度 1.05，饱和度 1.1）。

图层系统用 Three.js 的 `Layers` 把不同类型的几何体分到独立的渲染通道：

| 图层 | 值 | 用途 |
|---|---|---|
| `SCENE_LAYER` | 0 | 场景几何体 |
| `OVERLAY_LAYER` | 1 | 编辑器叠加（gizmo、手柄） |
| `ZONE_LAYER` | 2 | 区域填充（独立合成） |
| `GRID_LAYER` | 3 | 地面网格（参与场景深度遮挡） |
| `SHADOW_ONLY_LAYER` | 4 | 只投影不渲染的几何体 |

这套图层分配不是随意编号——每个图层都对应后处理管线里的一个独立渲染 pass，有明确的深度/合成规则。区域图层走单独的 `zonePass`，是因为半透明材质如果进入 SSGI 的深度/法线缓冲会导致错误的 AO 计算。网格放在场景 pass 而非 overlay pass，是因为它需要被建筑几何体遮挡才看起来对。

WebGPU 渲染器的创建本身也有讲究。`WebGPURenderer` 的初始化是异步的（`await init()`），React Three Fiber 的 `<Canvas>` 在 `useLayoutEffect` 里同步调用 `configure()`，两个并发的 configure 调用会各自创建一个渲染器。Pascal 用 `WeakMap<HTMLCanvasElement, Promise<WebGPURenderer>>` 缓存渲染器实例和进行中的初始化 Promise，保证同一个 canvas 上只创建一个渲染器。

## 垂直模型：建筑学约束的代码化

这可能是 Pascal 在建筑领域最深的一层工程。

普通 3D 编辑器里，物体的垂直位置就是 Y 坐标——你把它放在哪它就在哪。建筑信息建模（BIM）的要求不同：一面墙的顶部应该跟随楼层高度，除非被上方的楼板下表面截断；一个天花板的高度应该跟随楼层，除非上方有覆盖的楼板；一部楼梯的上升高度要么跟随目标楼板，要么显式指定。

Pascal 把这些规则编码成了一套**解析链**：

| 存储字段 | 含义 | 缺失时的回退 |
|---|---|---|
| `level.height` | 楼层高度（米），按楼层序号做前缀和得到世界 Y | 迁移时写入的派生高度 |
| `wall.height` | 显式墙高（半墙、女儿墙、抬高的支撑墙） | 平面绑定：顶部跟随楼层高度和覆盖楼板下表面 |
| `ceiling.height` | 显式天花板高度 | 跟随楼层：`min(楼层高度, 覆盖楼板下表面) - 0.01` |
| `slab.elevation` | 楼板顶面（行走面），楼层局部坐标 | 默认 0.05 |
| `slab.thickness` | 向下生长：占据 `[elevation - thickness, elevation]` | 默认 0.05 |
| `supportSlabId` | 墙体或物品的支撑宿主——只在支撑面高程不一致时持久化 | 每次查询时选举 |

这套模型的一个关键设计是：**缺失即数据**。`wall.height`、`ceiling.height`、`stair.totalRise` 这些字段在 Zod schema 里是 `.optional()` 且**没有 `.default()`**——缺失意味着"跟随规则"，有值意味着"显式覆盖"。创建节点时显式写入值；更新时传入 `undefined` 会删除这个键（通过 `mergeNodeUpdate` 实现），而不是写入 `undefined`。

解析时有一组 helper 函数，避免在代码里出现 `?? 2.5` 这样的硬编码回退：

- `getWallPlaneTop`——平面绑定墙体的顶部
- `resolveWallTop` / `resolveWallEffectiveHeight`——考虑支撑底座后的实际墙顶/墙高
- `getCeilingClampBound`——天花板的钳制边界
- `resolveStairTotalRise`——楼梯的上升高度优先级链

加载旧数据时有一个常驻迁移（`migrateNodes` Pass 3），把社区自动存档里的旧节点分类为"平面绑定"或"显式高度"，用 0.20 米的容差判断（通过线上数据普查标定——确实存在故意矮 0.20 米的墙，不能误判）。

## 插件机制

Pascal 的插件不是"额外功能"——内置节点（wall、slab、door、window 等）本身就是通过同一套 `Plugin` manifest 注册的，没有内部 API 和外部 API 之分。

一个插件的形状：

```typescript
export const myPlugin: Plugin = {
  id: 'acme:furniture-pack',
  apiVersion: 1,
  nodes: [couchDefinition, armchairDefinition],
}
```

每个 `NodeDefinition` 可以贡献：

- `schema`——Zod schema，定义节点的数据结构
- `defaults`——新建实例时的初始值
- `capabilities`——可选/可删/可复制等能力标记
- `parametrics`——属性面板的自动生成 UI
- `geometry`——纯函数几何生成
- `renderer`——自定义 React 组件（GLB、drei、TSL）
- `system`——每帧运行逻辑（动画、脏级联）
- `floorplan`——2D 平面图渲染
- `tool`——3D 放置/移动工具
- `presentation`——面板/侧边栏元数据
- `mcp`——AI 消费者的工具描述

注册表在启动时加载内置插件，然后调用 `discoverPlugins()` 加载外部插件。v1 只支持 add-only——热卸载需要拆除所有已挂载的实例，超出当前范围。重复的 `kind` 在生产环境直接抛错，在开发环境（HMR）替换并告警。

[`pascalorg/plugin-trees`](https://github.com/pascalorg/plugin-trees) 是一个完整的参考插件，包含程序化树木、花草、草地和预设面板，可以 clone 后作为起点。

## 一次完整的操作流：画一面墙并开门洞

把上面几层串起来，看一次真实操作如何流过系统。

1. **用户激活 WallTool**——`useEditor` 的 tool 切换为 `wall-tool`，`ToolManager` 挂载 `WallTool` 组件。
2. **用户在网格上点击两个点**——`WallTool` 通过 `grid:click` 事件拿到地面坐标，调用 `useScene.createNode()` 创建一个 `WallNode`（类型 `wall`，带 `start` 和 `end` 坐标）。
3. **节点进入 store**——`createNode` 把节点写入 `nodes` 字典，加入 `dirtyNodes`，通过 Zundo 记入撤销历史。Persist 中间件异步写入 IndexedDB。
4. **React 渲染**——`SceneRenderer` 遍历 `rootNodeIds`，递归到新墙所在的 Level，挂起 `NodeRenderer`，按 `type` 分发到 `WallRenderer`。`WallRenderer` 创建一个空 mesh，用 `useRegistry(node.id, 'wall', ref)` 注册到 `sceneRegistry`。
5. **系统处理脏节点**——下一帧 `useFrame` 里，`GeometrySystem` 发现 `dirtyNodes` 包含新墙 ID。通过 `sceneRegistry.nodes.get(id)` 拿到 mesh，调用 `def.geometry(node, ctx)` 生成几何体——包括计算厚度、高度、斜切相邻墙体。旧的子 mesh 被 dispose，新的被挂上。脏标记清除。
6. **用户拖一扇门到墙上**——`ItemTool` 通过空间查询 `canPlaceOnWall` 验证位置，调用 `createNode` 创建 `DoorNode`，作为墙的子节点。
7. **墙体再次变脏**——`DoorNode` 的创建把自身和父节点（墙）都标记为脏。`WallCutout` 系统在下一帧检测到墙在脏队列里，计算门洞的 Boolean 减法，在墙体几何上开洞。
8. **后处理合成**——`scenePass` 渲染 SCENE_LAYER 和 GRID_LAYER（网格被墙遮挡），`zonePass` 渲染区域（如果有），`overlayPass` 渲染工具 UI，最终通过 AgX 色调映射输出到 canvas。

整个过程从用户点击到画面更新，通常在 1-2 帧内完成。撤销（Ctrl+Z）回滚 store 状态，节点变更重新进入脏队列，几何体重建——同一条管线，无需特殊路径。

## 技术栈选型

| 技术 | 角色 |
|---|---|
| React 19 + Next.js 16 | UI 框架与宿主应用 |
| Three.js（WebGPU renderer） | 3D 渲染 |
| React Three Fiber + Drei | React 的 Three.js 绑定 |
| Zustand | 状态管理（三个独立 store） |
| Zod | schema 验证（节点类型系统） |
| Zundo | Zustand 的撤销/重做中间件 |
| three-bvh-csg | Boolean 几何运算（门窗开洞） |
| three-mesh-bvh | 空间加速结构 |
| Turborepo | monorepo 管理 |
| Bun | 包管理器 |

WebGPU 在这里是默认路径，并非可选项。Viewer 在挂载前检测 `'gpu' in navigator` 或 WebGL2 回退能力，不支持时展示一个"3D viewer unavailable"的占位组件。后处理管线里的 TSL 节点（`ssgi`、`denoise`、`inkedEdges`）直接使用 `three/webgpu` 的导出——这不是 WebGL renderer 能跑的代码。

## 适用边界与采用建议

**Pascal Editor 适合：**

- 需要在浏览器里做建筑/室内设计 3D 编辑的团队
- 想学习 React Three Fiber + WebGPU 生产级架构的开发者
- 研究编辑器架构模式（脏标记、registry-driven、CSG 管线、插件系统）的工程师
- 需要 BIM 级别的垂直约束（楼层/楼板/墙体/屋顶联动）的项目

**不直接适合：**

- 通用 3D 建模（Maya/Blender 替代）——节点类型局限于建筑领域
- 游戏 3D 引擎——没有物理、动画系统、脚本绑定
- 需要服务端渲染 3D 的场景——WebGPU 是浏览器 API

**学习路径建议：**

1. 先读 `wiki/architecture/`——这是项目自带的架构文档，质量极高，覆盖了 systems、renderers、scene registry、events、layers、spatial queries、vertical model 等所有核心概念。
2. 从 `packages/core/src/schema/` 切入——Zod schema 定义了所有节点类型的数据结构，是理解整个系统的起点。
3. 跟踪一次 `useScene.updateNode()` 调用——从 store 更新到脏标记到系统处理到几何重建，理解这条管线就理解了 Pascal 的核心设计。
4. 读 `packages/viewer/src/components/viewer/post-processing.tsx`——WebGPU 后处理管线的生产级实现，包括 SSGI、ink edges、zone/overlay 分通道合成。
5. 研究 `wiki/architecture/vertical-model.md`——建筑学约束如何映射到数据模型和代码逻辑，是 BIM 工程的教科书级参考。

Pascal Editor 用 20k Stars 证明了一件事：浏览器端的 3D 编辑器可以做到专业级，关键不在渲染效果有多炫，而在于数据模型、渲染管线和约束系统是否被认真设计过。
