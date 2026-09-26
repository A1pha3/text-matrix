---
title: "ml-explore/mlx 拆解：数组不带 device，操作才带 device"
date: "2026-06-17T15:03:26+08:00"
slug: "ml-explore-mlx-apple-silicon-array-framework"
github_repo: "ml-explore/mlx"
source_key: "gh:ml-explore/mlx"
lastmod: "2026-09-19T00:00:00+08:00"
description: "MLX 是 Apple 机器学习研究团队开源的数组框架。本文按 main 分支源码拆解它的统一内存模型、惰性求值与 eval tape、compile 的重编译边界、Metal/CPU/CUDA 三套后端，以及 ring/MPI/NCCL/JACCL 四套分布式后端。"
draft: false
categories: ["技术笔记"]
tags: ["MLX", "Apple Silicon", "数组框架", "Metal", "分布式训练"]
---

MLX 常被介绍成「Apple Silicon 版的 NumPy + PyTorch」，这个说法把重点放错了。API（应用程序接口）形状像 NumPy 是结果，不是设计动机；真正决定 MLX 其余全部设计的是一个小改动：**数组（array）这个类型上没有「我住在哪个设备上」这个字段**。

在 PyTorch 里 `tensor.device` 是数据的一部分，所以每次跨设备都要写 `.to()`，框架也要真的搬一次内存。在 MLX 里设备是**操作**的属性：同一个 `a`、`b` 可以被 CPU 上的 `add` 用，也可以被 GPU 上的 `add` 用，谁用谁负责访问。

把这一条推到底，后面几件事都是连带结果。表达式求值那一刻没人知道该找哪个后端，于是只能先把「算什么」记下来，惰性求值成为必需；既然没有静态设备分区可提前锁定，图也就得动态构建。多后端共用一套原语则是同一件事的另一面：原语只声明自己在哪个流上跑，换后端不必换语义。

这篇文章按 `ml-explore/mlx` 仓库 `main` 分支的实际源码逐层拆开，并在结尾给出采用顺序与自查问题。它不替读者回答「要不要换掉 PyTorch」。

## 目录

- [1. 判断：三件事里只有一件是因](#1-判断三件事里只有一件是因)
- [2. 仓库现状与核实口径](#2-仓库现状与核实口径)
- [3. 系统地图：真实目录与职责边界](#3-系统地图真实目录与职责边界)
- [4. array 是一个图节点](#4-array-是一个图节点)
- [5. eval 的真实路径：一条带宽度上限的 BFS tape](#5-eval-的真实路径一条带宽度上限的-bfs-tape)
- [6. 统一内存：操作选设备，而不是数据选设备](#6-统一内存操作选设备而不是数据选设备)
- [7. compile：重编译的边界与融合的上限](#7-compile重编译的边界与融合的上限)
- [8. 多后端：原语只声明接口，kernel 从哪来是另一件事](#8-多后端原语只声明接口kernel-从哪来是另一件事)
- [9. 分布式：四套后端，Ring 只是其中之一](#9-分布式四套后端ring-只是其中之一)
- [10. 一次任务如何流过整个系统](#10-一次任务如何流过整个系统)
- [11. 怎么读 MLX 的性能数字](#11-怎么读-mlx-的性能数字)
- [12. 安装与构建：先对平台矩阵](#12-安装与构建先对平台矩阵)
- [13. 装不上、跑不通时按症状排查](#13-装不上跑不通时按症状排查)
- [14. 与 PyTorch、JAX 的边界](#14-与-pytorchjax-的边界)
- [15. 采用顺序：谁先上、谁再等](#15-采用顺序谁先上谁再等)
- [16. 五个自测题](#16-五个自测题)
- [17. 下一步读哪份代码](#17-下一步读哪份代码)
- [18. 维护指引：本文断言的核实方法与失效条件](#18-维护指引本文断言的核实方法与失效条件)
- [参考来源](#参考来源)

## 1. 判断：三件事里只有一件是因

社区文章谈 MLX 通常并列三件事：统一内存（unified memory）、惰性计算图、多后端。看起来像三个独立卖点，实际是一条因果链上的三层。

| 常被并列的说法 | 它是因还是果 | 依据 |
|---|---|---|
| 数组没有 device 字段，设备属于操作 | **因** | `mlx/array.h` 的 `ArrayDesc` 里没有 `Device` 成员；`Primitive` 基类的 `device()` 直接返回 `stream().device`，注释写的是 `The device the primitive will run on.` |
| 计算必须惰性 | 果 | 设备归属要到求值时才定，表达式求值阶段没法决定后端，只能先把「算什么」记下来。这一条是本文从代码结构读出的推断，文档给的理由见第 4 节 |
| 一套原语三套后端 | 果 | 原语只是接口，`eval_cpu` / `eval_gpu` 各自实现；换后端不换语义 |
| 跨设备零拷贝 | 果 | Apple silicon 的 CPU/GPU 本就共享内存池，MLX 只是没有在 API 上重新引入搬运概念 |

README 列出的是六个特性条目：熟悉的 API、可组合函数变换、惰性计算、动态图构建、多设备、统一内存。前五条别家也有，第六条才是 MLX 的立足点。

## 2. 仓库现状与核实口径

下表数字全部在 2026-09-19 通过 GitHub API、PyPI 的包元数据与一次跳过 blob 的浅克隆得到，方法见文末维护指引。框架类文章里的 star 数和版本号最容易过期，这里把口径写清，方便后续复核。

| 项 | 值 | 口径 |
|---|---|---|
| 仓库 | [ml-explore/mlx](https://github.com/ml-explore/mlx) | — |
| Stars / Forks | 28,473 / 2,263 | GitHub API `stargazers_count` / `forks_count` |
| 未关闭 issue + PR | 156 | `open_issues_count`，含 PR |
| License | MIT | — |
| 建仓 / 最近推送 | 2023-11-28 / 2026-09-17 | `created_at` / `pushed_at` |
| 最新 release tag | `v0.32.2`（2026-08-25） | GitHub Releases |
| `main` 上的版本号 | 0.32.3 | `mlx/version.h` 的 `MLX_VERSION_MAJOR/MINOR/PATCH` |
| PyPI latest | 0.32.2 | `pypi.org/pypi/mlx/json` |
| Python 下限 | 3.10 | `requires_python` |
| 代码规模 | `mlx/` 619 个文件，其中 554 个 `.cpp/.h/.cu/.metal/.mm` | `git ls-tree -r mlx/` |
| 公共算子声明 | `mlx/ops.h` 302 条 `MLX_API` | 计数口径是声明条数，非去重后的函数名数 |
| 原语数量 | `mlx/primitives.h` 118 个 `class`、119 处 `void eval_gpu` | 后者含基类的纯虚与转发声明，不是「119 个可实例化原语」 |
| 姊妹仓库 | `mlx-swift`、`mlx-c`、`mlx-examples`、`mlx-lm`、`mlx-data` | 均在 `ml-explore` 组织下 |

`mlx.nn` 与 `mlx.optimizers` 是纯 Python 包（`python/mlx/nn/`、`python/mlx/optimizers/`），`python/src/` 下没有对应的绑定文件；也就是说高层网络层和优化器这一圈是贴着 PyTorch 的 API 形状用 Python 写的，改动不需要重编 C++。

## 3. 系统地图：真实目录与职责边界

整份核心实现是 C++20，Python 绑定只用 nanobind（`python/src/CMakeLists.txt` 里是 `nanobind_add_module`，仓库内没有 pybind11）。`mlx/backend/` 下有 497 个文件，按目录切分如下。

```text
        Python / C++ / C / Swift API
                    │
     python/src/*.cpp（nanobind）＋ python/mlx/{nn,optimizers}
                    │
   ┌────────────────▼─────────────────┐
   │ 核心  mlx/array  primitives      │
   │  mlx/transforms（eval/grad/vmap）│
   │  mlx/compile  mlx/stream         │
   │  mlx/scheduler  mlx/graph_utils  │
   └───────┬──────────────────┬───────┘
           │                  │
  ┌────────▼────────┐  ┌──────▼───────────────────────┐
  │ backend/common  │  │ backend/gpu（设备无关派发层） │
  │ backend/cpu     │  │ backend/metal  backend/cuda  │
  │ backend/no_cpu  │  │ backend/no_gpu               │
  └─────────────────┘  └──────────────────────────────┘
                    │
        ┌───────────▼──────────────┐
        │ distributed/{ring,mpi,   │
        │  nccl,jaccl}             │
        └──────────────────────────┘
```

| 层 | 关键路径 | 负责 | 不负责 |
|---|---|---|---|
| Python 前端 | `python/src/array.cpp`、`ops.cpp`、`transforms.cpp`、`convert.cpp` | 类型转换、`__repr__`、tree 结构进出 | 不选后端、不管内存 |
| 核心 | `mlx/array.{h,cpp}`、`mlx/primitives.{h,cpp}`、`mlx/transforms.cpp`、`mlx/compile.cpp` | 建图、求值 tape、自动微分、融合与编译 | 不写 kernel |
| 后端公共 | `mlx/backend/common/`、`mlx/backend/gpu/` | 与设备无关的模板（broadcasting、reduce、matmul 骨架）与 GPU 派发 | 不做具体指令 |
| CPU | `mlx/backend/cpu/`，其中 `gemms/cblas.cpp`、`simd/accelerate_simd.h` | BLAS/LAPACK、Accelerate 或 OpenBLAS 路径 | 不知道图结构 |
| Metal | `mlx/backend/metal/`（`kernels/` 137 个文件、`jit/`、`nojit_kernels.cpp`） | MSL 源码、`.air` 编译、pipeline 与 command buffer | 不定义算子语义 |
| CUDA | `mlx/backend/cuda/`（`.cu` + `cublas_utils` + `cudnn_utils`） | CUDA kernel、cuBLAS/cuDNN 路径 | 同上 |
| 关闭占位 | `mlx/backend/no_cpu/`、`no_gpu/`、`metal/no_metal.cpp`、`io/no_gguf.cpp` | 某后端/格式没编译进来时提供可链接的空实现 | — |
| 分布式 | `mlx/distributed/` | 集合通信与后端选择 | 不参与单卡算子执行 |
| IO | `mlx/io/load.cpp`、`safetensors.cpp`、`gguf.cpp`、`gguf_quants.cpp` | safetensors 与 GGUF 读写 | — |

两处和多数二手资料不同的地方值得单独指出。`mlx/primitives/` 这个目录并不存在，全部原语声明集中在 `mlx/primitives.h`、定义在 `mlx/primitives.cpp`。Accelerate 也不是一个后端目录：`MLX_BUILD_ACCELERATE` 是 CMake 的内部变量，`MLX_BUILD_CPU=ON` 时用 `find_library(ACCELERATE_LIBRARY Accelerate)` 探测，探到才加上 `MLX_USE_ACCELERATE` 编译定义；探不到时 Windows 走 `FetchContent` 下载 OpenBLAS 预编译包，其余平台 `find_package(LAPACK REQUIRED)` 加 `find_package(BLAS REQUIRED)`。

## 4. array 是一个图节点

`mlx/array.h` 里 `array` 类开头的注释一句话交代了设计核心：

```cpp
class MLX_API array {
  /* An array is really a node in a graph. It contains a shared ArrayDesc
   * object */
```

真正装东西的 `ArrayDesc` 字段（去掉注释后的实际顺序）：

```cpp
struct MLX_API ArrayDesc {
  Shape shape;
  Strides strides;
  size_t size;
  Dtype dtype;
  std::shared_ptr<Primitive> primitive;
  Status status;
  Event event;
  bool is_tracer{false};
  std::shared_ptr<Data> data;
  int64_t offset{0};
  size_t data_size{0};
  Flags flags{true, true, true};
  std::vector<array> inputs;
  std::vector<array> siblings;
  uint32_t position{0};
};
```

`data` 是 `std::shared_ptr`，注释写明理由：`This is a shared pointer so that *different* arrays can share the underlying data buffer`。也就是说视图、切片和广播出的多个数组可以指向同一块 buffer，靠 `offset` 和 `data_size` 区分各自看到哪一段。`siblings` 与 `position` 服务于多输出原语——基类 `Primitive::eval_cpu` 收的是 `std::vector<array>& outputs`，一个 `Compiled` 节点就能产出多个数组；这些数组互相引用，所以析构要走 `release()` 断开环，`array` 的赋值运算符注释也专门写了这件事。

状态机只有三档，注释本身把语义说完了：

```cpp
enum Status {
  // The output of a computation which has not been scheduled.
  // For example, the status of `x` in `auto x = a + b`.
  unscheduled,
  // The array's `eval_*` function has been run, but the computation is not
  // necessarily complete. The array will have memory allocated and if it is
  // not a tracer then it will be detached from the graph.
  evaluated,
  // If the array is the output of a computation then the computation
  // is complete. Constant arrays are always available (e.g. `array({1, 2,
  // 3})`)
  available
};
```

关键在于 `evaluated` 与 `available` 的差别：前者是「已经排下去、内存已分配，但计算未必跑完」，后者才是「可以安全读」。跨设备读之前要 `wait()`，它等的就是这个差。

PyTorch 的 eager 模式每个 op 落地一次，`print` 时才同步；JAX 要显式 `jit` 才有图。MLX 走的是中间态：图常驻、边界求值。`docs/src/usage/lazy_evaluation.rst` 给的理由有两块，第二块里顺带讲了内存。

- 变换需要图：`grad`、`vmap`、`compile` 都在未求值的图上做改写。
- 只算用到的：`y, _ = fun(x)` 里 `fun` 内部那个 `expensive_fun` 的输出不会被算出来。文档同时提醒这不代表零成本——图仍然被构建了，构建本身有开销。同一节里还举了初始化的例子：`model = Model()` 把 float32 权重建成未求值节点，接着 `load_weights("weights_fp16.safetensors")` 覆盖，峰值内存因此只有 eager 初始化的一半。

## 5. eval 的真实路径：一条带宽度上限的 BFS tape

`array::eval()` 只是一行转发，实际工作全在 `mlx/transforms.cpp` 的 `eval_impl(outputs, async)`。同步版 `eval()` 是 `eval_impl(..., false).wait()`，`async_eval()` 传 `true` 只排不等。

拆开看它做五件事，都能在源码里逐行对上：

1. **选输出流**。先取 `default_stream(default_device())`，然后扫一遍待求值输出，用第一个 `unscheduled` 且有原语的数组自带的 `primitive().stream()` 覆盖。这就是「设备属于操作」的落点：你在 `mx.add(a, b, stream=mx.cpu)` 里传的流，会决定这条子图跑在哪。
2. **造一个根节点**。`array({}, bool_, std::make_shared<Synchronizer>(stream), std::move(outputs))`——用 `Synchronizer` 这个原语把 N 个输出收成一个根，后面所有遍历都从它开始。
3. **遍历建 tape**。用显式栈做 DFS 记录入度，但 tape 的实际排列是 BFS，并且带宽度上限。源码注释是 `Build the tape in BFS order with a width limit`，上限来自 `env::bfs_max_width()`，默认 20，可用环境变量 `MLX_BFS_MAX_WIDTH` 覆盖。仓库没有说明为什么是 20；从代码位置看它约束的是一次求值同时铺开的前沿宽度，要拿它当调优参数用之前得自己测。
4. **插入跨流同步**。`needs_fence` 记录哪些数组跨流产生，`std::unordered_map<uint32_t, Fence> fences` 按流编号复用。这是文档里「MLX 会自动在两个流之间插依赖」那句话的实现层证据。
5. **执行与背压**。tape 反向弹出后取 `arr.primitive().stream()`，先按 `needs_fence` 或 `Event` 等齐输入，再按 `arr.primitive().device()` 分流到 `gpu::eval(arr)` 或 `cpu::eval(arr)`，然后把状态置成 `evaluated`。循环里带一个背压条件：活跃任务数超过 `MAX_ACTIVE_TASKS`（常量 10）或 `get_active_memory()` 越过 `get_memory_limit()` 时，先 `gpu::finalize` 提交的流再 `scheduler::wait_for_one()`。`Event` 则用于 `async_eval` 之后的等待。

`print(y)` 触发求值的路径也具体：`python/src/array.cpp` 把 `__repr__` 绑到 `os << a`，而 `mlx/utils.cpp` 里 `operator<<(std::ostream&, array a)` 的函数体第一行就是 `a.eval()`。

```cpp
std::ostream& operator<<(std::ostream& os, array a) {
  a.eval();
  dispatch_all_types(a.dtype(), [&](auto type_tag) {
    print_array<MLX_GET_TYPE(type_tag)>(os, a);
  });
  return os;
}
```

两条真实报错能帮你判断自己踩到了哪一层：

- `[eval] Attempting to eval an array during function transformations like compile or vmap is not allowed.`：在 `compile`/`vmap` 的追踪期里读了占位数组的值。
- `[async_eval] Not allowed inside a graph transformation.`：在变换里调了 `async_eval`。

`item` 的边界同样有明确文本：`item can only be called on arrays of size 1.`；const 版本额外要求已求值，否则 `item() const can only be called on evaled arrays`。

## 6. 统一内存：操作选设备，而不是数据选设备

`docs/src/usage/unified_memory.rst` 里的表述比任何转述都准：`In MLX, rather than moving arrays to devices, you specify the device when you run the operation.`

```python
import mlx.core as mx

a = mx.random.normal((100,))
b = mx.random.normal((100,))

mx.add(a, b, stream=mx.cpu)   # 同一对数组
mx.add(a, b, stream=mx.gpu)   # 换设备执行，不需要搬数据
```

有依赖时也不用手写同步：

```python
c = mx.add(a, b, stream=mx.cpu)
d = mx.add(a, c, stream=mx.gpu)  # 第二个 add 等 c 可用后才跑
```

文档自己给了一个可复现的对照例子：`a`、`b` 形状 `(4096, 512)` 与 `(512, 4)`，一次 `matmul` 适合 GPU，随后 500 次小 `exp` 在 GPU 上是启动开销主导、更适合 CPU。整条计算全放 GPU 在 M1 Max 上测得 2.8 毫秒，改成 `matmul` 走 GPU、500 次 `exp` 走 CPU 后约 1.4 毫秒。省下来的是几百次小 kernel 在 GPU 上的调度与启动开销。

有一点要纠正很多文章的印象：MLX **有** device API，只是它不在数组上。`mlx/device.h` 暴露 `default_device()`、`set_default_device()`、`is_available(Device)`、`device_count()`、`device_info()`；Python 侧 `docs/src/python/devices_and_streams.rst` 同样列出 `Device`、`Stream`、`set_default_device`、`device_info`、`synchronize` 等。`Device` 结构是 `{DeviceType type; int index;}`，`index` 是为多设备预留的位置，`device_count()` 与 `is_available()` 会按它来判定；`device_info` 的键里 `free_memory`、`uuid`、`pci_bus_id`、`compute_capability_*` 都注明 CUDA only。

所以 MLX 与 PyTorch MPS 后端的差异不在「有没有设备概念」，而在设备挂在哪：PyTorch 挂在张量上，MLX 挂在操作上。写 batch 切分、梯度累积这类需要多设备协作的代码时，差别就是有没有一堆 `device` 参数要往下透传。

## 7. compile：重编译的边界与融合的上限

`mx.compile(fun)` 返回一个产出同样结果的编译版函数。C++ 侧 `mlx/compile.h` 的签名只有两个参数，Python 侧在 `python/src/transforms.cpp` 里绑定，多了用于固定 tree 结构的 `inputs` / `outputs`：

```python
def compile(fun, inputs=None, outputs=None, shapeless=False)
```

`docs/src/usage/compile.rst` 明确列出会触发重新编译的情形：改变 shape 或维度数、改变任一输入的类型、改变输入个数。也就是说**默认情况下 shape 一变就会重编**，只有 `shapeless=True` 才承诺输入 shape 变化不再重编；而按 `mx.compile` 的文档字符串（docstring），即使 `shapeless=True`，改维度数或 dtype 仍然重编。不是所有函数都能 `shapeless=True`，开不了的函数会抛异常，本文没有观察到静默退回未编译路径的情形。

这一条与「动态图所以不用重编译」的常见说法有出入，得区分两层：

- **默认路径（不 compile）**：确实没有编译成本，因为只是建图，改 shape 无感。
- **`mx.compile` 路径**：走的是缓存编译产物，缓存键包含 shape/dtype/输入个数/默认流。README 里 `Dynamic graph construction` 说的「改变 shape 不会触发慢编译」指的是前者。

融合规模有两个硬上限，写在 `mlx/compile.cpp` 顶部：

```cpp
constexpr int max_compile_depth = 11;
constexpr int max_compile_arrays = 24;
```

它们是融合搜索的停止条件：递归向上收可融合节点时，深度到 11 或输入集大小到 24 就停。超过就分成多个 kernel，不是「缓存放不下」。

文档给的一个真实收益例子是 `mlx.nn.gelu`（`x * (1 + mx.erf(x / math.sqrt(2))) / 2`，全是逐元素算子，可整条融进一个 kernel）。在 `(32, 1000, 4096)` 的数组上、10 次预热 + 100 次 `mx.eval` 循环计时，M1 Max 上未编译 15.5 毫秒、编译后 3.1 毫秒。

三条使用约束同样来自文档，都会在真实代码里踩到：

- 编译函数首次调用时用占位输入追踪，因此函数体里 `print` 中间结果会崩。调试用 `mx.disable_compile()` 或环境变量 `MLX_DISABLE_COMPILE`。
- 编译函数应当是纯函数。往外部列表 `append` 中间数组，那个数组是占位符、没有数据，事后打印就崩；要往外带就把它作为返回值。
- 不要在循环里对匿名函数反复 `mx.compile`——文档原话是 `Don't do this, compiles lambda at each iteration`。

## 8. 多后端：原语只声明接口，kernel 从哪来是另一件事

原语的接口形状固定。基类 `Primitive` 要求实现接收输出**列表**的两个纯虚函数，`UnaryPrimitive` 再把它们收窄成单输出版本并转发给 `outputs[0]`。以加法为例，`mlx/primitives.h` 里 `Add` 的实现要求就是两个 override 加一串宏：

```cpp
class MLX_API Add : public UnaryPrimitive {
 public:
  explicit Add(Stream stream) : UnaryPrimitive(stream) {}

  void eval_cpu(const std::vector<array>& inputs, array& out) override;
  void eval_gpu(const std::vector<array>& inputs, array& out) override;

  DEFINE_VMAP()
  DEFINE_GRADS()
  DEFINE_NAME(Add)
  ...
};
```

`Stream` 在构造时传进来，之后这张子图归哪个设备管就定死了。119 处 `void eval_gpu` 声明（含基类那几个）意味着每个原语要在各后端分别落地，`mlx/backend/{cpu,metal,cuda}/primitives.cpp` 提供的就是这一份份实现。

Metal 这条路径的默认行为常被写反。`MLX_METAL_JIT` 默认 **OFF**，此时 `mlx/backend/metal/kernels/CMakeLists.txt` 会用 `xcrun -sdk macosx metal` 把各 `.metal` 编成 `.air`，再链成 `mlx.metallib` 随库安装。打开 JIT 的目的不是「方便热改」，文档写的是**减小二进制体积**：kernel 首次用到时才运行时编译，代价是几百毫秒到几秒的冷启动，编好的 kernel 由系统缓存且跨重启保留。

静态链接 `libmlx.a` 时有一条部署要求：`mlx.metallib` 必须和可执行文件同目录，或者在编译期定义 `METAL_PATH` 指过去。漏掉的表现是库能加载、Metal 算子找不到 kernel。

融合算子有专门的头文件：`mlx/fast.h` 提供 `rms_norm`、`layer_norm`、`rope`、`scaled_dot_product_attention`、`gated_delta_update`，也提供 `metal_kernel(...)` 与 `cuda_kernel(...)` 这两个自定义 kernel 入口，配套教程在 `docs/src/dev/custom_metal_kernels.rst`。背后的 `mlx/fast_primitives.h` 有 14 个类，但口径要注意：这 14 个里含 `RMSNormVJP`、`LayerNormVJP`、`ScaledDotProductAttentionVJP` 这类反向变体，以及 `Custom`、`CustomKernel`、`ConvertFP8`、`Quantize`，并不对应 14 个用户可调用的融合算子。

`docs/src/usage/environment_variables.rst` 把影响性能的开关列全了，其中默认值值得记住：

| 变量 | 默认 | 作用 |
|---|---|---|
| `MLX_ENABLE_TF32` | 1 | 支持的设备上 `float32` 矩阵乘走 TF32；要全精度设 0 |
| `MLX_BFS_MAX_WIDTH` | 20 | 求值 tape 的 BFS 宽度上限 |
| `MLX_MAX_OPS_PER_BUFFER` | 随设备 | 一个 Metal command buffer / CUDA graph 内的算子数上限 |
| `MLX_MAX_MB_PER_BUFFER` | 随设备 | 同上，按内存量限制 |
| `MLX_USE_CUDA_GRAPHS` | 1 | CUDA 后端启用图捕获与重放 |
| `MLX_CUDA_USE_CUDNN_SDPA` | 1 | CUDA 允许用 cuDNN 的缩放点积注意力 |
| `MLX_METAL_FAST_SYNCH` | 0 | 更快的 CPU/GPU 同步路径，需 Metal 3.2（macOS 15+） |

`MLX_METAL_FAST_SYNCH` 保持默认值是文档里明说过的：`docs/src/usage/distributed.rst` 指出它可能导致死锁并把 GPU 卡住，指向 issue [#3142](https://github.com/ml-explore/mlx/issues/3142)，因此默认关闭、最好不设。它也不只服务于分布式，任何 CPU 与 GPU 需要协作的场景都能用，需要 Metal 3.2 即 macOS 15 以上。

## 9. 分布式：四套后端，Ring 只是其中之一

`mlx/distributed/` 下并列四个后端目录：`ring/`、`mpi/`、`nccl/`、`jaccl/`，`mlx/distributed/CMakeLists.txt` 无条件 `add_subdirectory` 全部四个。`distributed.h` 里 `init(bool strict = false, const std::string& bk = "any")` 接受 `'any' / 'ring' / 'jaccl' / 'mpi' / 'nccl'`。

`bk="any"` 的选择顺序在 `distributed.cpp`：CUDA 可用先试 **NCCL**，失败退 **Ring**，再退 **MPI**，最后 **JaCCL**；全失败且 `strict=True` 才抛异常。选定之后同一个后端会被缓存，后续不带参数的 `init()` 返回同一个 group。

公开的集合通信算子在 `mlx/distributed/ops.h`，是 `all_sum`、`all_gather`、`all_max`、`all_min`、`sum_scatter`、`send`、`recv`、`recv_like` 这八个。注意命名是 `all_sum` 而不是 `all_reduce`。

四个后端的定位差别很大，直接照抄文档表格：

| 后端 | 传输 | 定位 | 已知限制 |
|---|---|---|---|
| Ring | TCP 套接字（socket） | 不依赖第三方库，始终可用；文档称通常快于 MPI | 只支持环上相邻通信，任意 `send`/`recv` 不可用 |
| MPI | 由 MPI 实现决定 | 成熟完整的通信库 | 需要本机有 MPI 运行时 |
| NCCL | NCCL | CUDA 环境的默认与首选 | 需要 CUDA 环境 |
| JaCCL | Thunderbolt RDMA | 低延迟，文档称比 Ring 低一个数量级，张量并行需要它 | 见下 |

Ring 的主场不是以太网，是**雷雳环**。`mlx.distributed_config --verbose --hosts h1,h2,h3,h4 --backend ring` 会自动探测雷雳连接、给出配置命令并产出 `hostfile.json`；节点免密 sudo 时加 `--auto-setup` 直接配好。

JaCCL 是这批里最值得注意的一块。它要求 macOS 26.2 以上、带雷雳 5 的机器，用雷雳 RDMA 做通信。启用步骤无法远程完成，必须进 macOS 恢复模式跑 `rdma_ctl enable` 再重启，之后 `ibv_devices` 应能看到 `rdma_en2`…`rdma_en7` 这类设备。拓扑还要求**全连接**：每台机器两两之间都要有线，四台 M3 Ultra 组网时少一条边就不成立（文档用两张图分别标了 valid 与 not valid）。名字本身是 NCCL 的谐音梗，全称 *Jack and Angelos' Collective Communication Library*，也是纪念主导 Apple 雷雳 RDMA 工作的 Jack Beasley。

一个很有用的语义：group 大小为 1 时所有 `mx.distributed` 操作都是 no-op。于是下面这种「是否在分布式环境」的判断可以省掉——

```python
world = mx.distributed.init()
x = mx.distributed.all_sum(x)   # 单进程时直接返回 x
```

启动靠两个 console script（`setup.py` 的 `entry_points`）：`mlx.launch` 与 `mlx.distributed_config`。单机起 4 个进程是 `mlx.launch -n 4 my_script.py`，多机是 `mlx.launch --hosts ip1,ip2,ip3,ip4 my_script.py`。文档给的多机实例是四台 M3 Ultra 用 JaCCL 跑 4-bit DeepSeek-R1：

```bash
mlx.launch --verbose --backend jaccl --hostfile m3-ultra-jaccl.json -- \
     /path/to/remote/python -m mlx_lm chat --model mlx-community/DeepSeek-R1-0528-4bit
```

## 10. 一次任务如何流过整个系统

把前面几层串起来。下面这段只有七行，但每一层的机制都会经过一次。

```python
import mlx.core as mx

def layer(x, w):
    return mx.softmax(mx.matmul(x, w) * 0.125, axis=-1)

x = mx.random.normal((4, 16))
w = mx.random.normal((16, 8))
y = layer(x, w)
print(y)
```

1. `mx.random.normal((4, 16))` 展开成一小段图：`mlx/random.cpp` 里 `normal` 先 `uniform`（其底层是 `RandomBits`），再 `erfinv`、乘 `sqrt(2)`、加 `loc`。随机数没有「已经算好」这一说，`x`、`w` 的 `status` 同样是 `unscheduled`。
2. `mx.matmul(x, w)` 只做一件事：`ArrayDesc{shape=(4,8), dtype=float32, primitive=Matmul, inputs={x,w}}`，`status=unscheduled`，`data` 为空。`* 0.125` 与 `softmax` 依次再包两层，整条链上一个字节都没算。
3. `print(y)` → `operator<<` → `y.eval()` → `eval_impl`：挑输出流（此例落到 `default_stream(default_device())`，而 `mlx/device.cpp` 里默认设备是「GPU 后端可用则 GPU，否则 CPU」），建 `Synchronizer` 根，按 BFS 生成 tape，给每个原语调 `eval_gpu`。
4. 落地时按原语查 `mlx/backend/metal/primitives.cpp` 与 `mlx/backend/metal/matmul.cpp`。这条未编译的路径上一个原语一次 kernel 落地，`Softmax` 不会和前面的乘系数合并。
5. 中间结果在需要时才分配 buffer；`available` 之后打印路径通过 `data<T>()` 取指针，该函数本身已经把 `array_desc_->offset` 加进去了。
6. 若只调 `mx.eval(y)` 不打印，图求值一次，`y` 的 `status` 变成 `available`，后续读取不重算。
7. 若 `fc = mx.compile(layer)`，第一次调用完成追踪与 kernel 生成，`matmul` 之外的逐元素链会被融成更少的 kernel；之后 `fc(x, w)` 走缓存产物。换成 shape `(8,16)` 的输入会新增一份缓存条目而不是复用。

同一个例子上手前先记住一句：`mx.eval` 的成本是每次一图的固定开销，`docs/src/usage/lazy_evaluation.rst` 的建议是把求值放在训练外层循环的边界上，并指出几十到几千个算子一张图都在合适区间。

## 11. 怎么读 MLX 的性能数字

跨框架对比的 microbenchmark 在**主仓库**的 `benchmarks/`（`cpp/`、`numpy/`、`python/` 三组，`python/comparative/` 下是 `bench_mlx.py`、`bench_torch.py`、`compare.py`）。`comparative/README.md` 对它的定位说得很直：实现同一批 microbenchmark 来列出 MLX 相对 PyTorch 的最大可能提升或回退。`mlx-examples` 里只有各示例自带的脚本（`whisper/benchmark.py`、`encodec/benchmarks/bench_mx.py` 与同目录的 `bench_pt.py`、`musicgen/benchmarks/`），没有一张统一的跨框架表格。

据此，本文引用到的四个数字分别测的是：

| 数字 | 出处 | 测什么 | 能推出 | 推不出 |
|---|---|---|---|---|
| 475 tokens/s | `mlx-examples/lora/README.md` | README 正文一句话：Llama 7B 在 WikiSQL 上做 LoRA（低秩适配）时的训练吞吐，芯片是 M2 Ultra；未附完整命令与迭代数 | 7B 级 LoRA 在顶配 Mac 上对个人研究者可日常使用 | 与 CUDA 集群的可比性；README 的 loss 表跑到 1000 iter，这个数字没有对应的迭代区间，也不含数据加载与 checkpoint 落盘 |
| 15.5 ms → 3.1 ms | `docs/src/usage/compile.rst` | `gelu` 在 `(32,1000,4096)` 上、100 次 `mx.eval` 平均、M1 Max | 逐元素链能被融成单 kernel，收益 5× | 未编译路径「比 PyTorch 快」；这是自比 |
| 2.8 ms → 1.4 ms | `docs/src/usage/unified_memory.rst` | 1×matmul + 500×exp，M1 Max | 按算子特征分设备比全放 GPU 快 | 通用加速比；这是特意为小算子构造的例子 |
| 一个数量级延迟差 | `docs/src/usage/distributed.rst` | JaCCL 对比 Ring 的通信延迟 | 雷雳 RDMA 对张量并行是实质选项 | 端到端训练吞吐提升幅度 |

读这四行的共同口径：全部是**同硬件自比**或**微基准**。在本文核实过的 README、docs 与 benchmark 说明里没有「MLX 快过 A100/H100」这类断言，把 475 tokens/s 当成对标数据中心训练能力的证据，等于拿一台工作站的可用性结论去顶替一组本来没做过的横向比较。

## 12. 安装与构建：先对平台矩阵

PyPI 上的 `mlx` 已经拆成前端包 + 后端包：前端带 Python ABI 与平台 tag，后端（`mlx-metal`、`mlx-cpu`、`mlx-cuda-12`、`mlx-cuda-13`）只带平台 tag。`setup.py` 用 `MLX_BUILD_FRONTEND_PACKAGE` / `MLX_BUILD_BACKEND_PACKAGE` 两个环境变量区分，前端包在 Darwin 上硬依赖 `mlx-metal==<同版本号>`。

0.32.2 的实际 wheel 覆盖情况（取自 PyPI JSON）：

| 包 | 平台 |
|---|---|
| `mlx`（前端） | macOS 14/15/26 arm64；manylinux 2.35 aarch64/x86_64；win_amd64/win_arm64 |
| `mlx-metal` | macOS 14/15/26 arm64 |
| `mlx-cpu` | manylinux 2.35 aarch64/x86_64；win_amd64/win_arm64 |
| `mlx-cuda-12` / `mlx-cuda-13` | manylinux 2.35 aarch64/x86_64；win_amd64 |

于是安装命令按平台分四种，README 与 docs 在这点上略有出入（README 写 `mlx[cuda]`，docs 写 `mlx[cuda12]`；`setup.py` 里 `cuda`、`cuda12`、`cuda13` 三个 extra 都存在，`cuda` 指向 `mlx-cuda-12`）：

```bash
pip install mlx            # macOS Apple silicon
pip install mlx[cuda12]    # Linux CUDA 12
pip install mlx[cuda13]    # Linux CUDA 13
pip install mlx[cpu]       # Linux CPU-only
```

官方给出的硬性条件值得逐条核对：

| 目标 | 要求 |
|---|---|
| macOS | Apple silicon、macOS ≥ 14.0、原生 Python ≥ 3.10 |
| CUDA | NVIDIA 架构 ≥ SM 7.5、驱动 ≥ 550.54.14（CUDA 13 需 ≥ 580）、CUDA toolkit ≥ 12.0、glibc ≥ 2.35 |
| Linux CPU | glibc ≥ 2.35、Python ≥ 3.10 |
| 源码构建 | C++20 编译器（Clang ≥ 15）、CMake ≥ 3.25、Xcode ≥ 15 且 macOS SDK ≥ 14.0；Linux 需 `libblas-dev liblapack-dev liblapacke-dev` |

「Linux 上要用 CUDA 必须源码构建」这类说法现在不成立了。源码构建仍然支持，路径是：

```bash
# Python 开发安装
git clone https://github.com/ml-explore/mlx.git mlx && cd mlx
pip install -e ".[dev]"
python setup.py build_ext --inplace
python python/tests/run.py

# 带 CUDA 的 Python 构建
CMAKE_ARGS="-DMLX_BUILD_CUDA=ON" pip install -e ".[dev]"

# C++ 库
mkdir -p build && cd build
cmake .. -DMLX_BUILD_CUDA=ON && make -j
make test && make install
```

CMake 选项以 `CMakeLists.txt` 里的 `option()` 行为准，几个默认值：`MLX_BUILD_METAL`/`MLX_BUILD_CPU`/`MLX_BUILD_TESTS`/`MLX_BUILD_SAFETENSORS`/`MLX_BUILD_GGUF`/`MLX_BUILD_PYTHON_STUBS` 为 ON，`MLX_BUILD_CUDA`、`MLX_BUILD_BENCHMARKS`、`MLX_BUILD_PYTHON_BINDINGS`、`MLX_METAL_JIT`、`MLX_ENABLE_X64_MAC` 为 OFF。要压体积可以 `CMAKE_BUILD_TYPE=MinSizeRel` 加 `BUILD_SHARED_LIBS=ON` 并关掉 CPU 后端与 GGUF/safetensors，再打开 `MLX_METAL_JIT`。

一处文档与构建脚本不一致：`docs/src/install.rst` 的选项表把 `MLX_BUILD_EXAMPLES` 写成 OFF 且完全没列 `MLX_BUILD_CUDA`，而 `CMakeLists.txt` 里 `MLX_BUILD_EXAMPLES` 默认是 ON。以 `grep -n '^option' CMakeLists.txt` 为准。

## 13. 装不上、跑不通时按症状排查

绝大多数失败集中在这六类，前三类出在安装期，后三类在运行期。

| 症状 | 原因 | 处理 |
|---|---|---|
| `error: unable to find utility "metal", not a developer tool or in PATH` | Xcode 未装或未选中 | `xcode-select --install`，再 `sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer` |
| `uname -p` 输出 `x86`（M 系列机器上） | 终端在 Rosetta 下跑，CMake 因此找错架构 | 在 Finder 里取消 App 的「Open using Rosetta」并重启终端 |
| pip 报找不到匹配版本，但 OS/Python 版本都合规 | Python 本身是非原生（`platform.processor()` 为 `i386`） | 换成原生 Python；文档给的推荐做法是用 Conda 重装一份 |
| `mlx.set_default_device(mx.gpu)` 抛 `[set_default_device] Cannot set gpu device without gpu backend.` | 这份构建没有编进 GPU 后端（Metal 与 CUDA 都没开） | 先 `mx.is_available(mx.gpu)` 判断；要用 GPU 得重装带后端的包或重编 |
| Metal kernel 缺失、CPU 路径正常 | 静态链接时 `mlx.metallib` 没在可执行文件旁边 | 拷到同目录，或编译期定义 `METAL_PATH` |
| 在 `mx.compile` 的函数体里 `print` 中间结果就崩 | 追踪期数组是占位符、没有 buffer | 调试期 `mx.disable_compile()` 或 `MLX_DISABLE_COMPILE=1`；生产代码把待观察值作为返回值带出 |

还有两个容易归错类的错误。`float32` 矩阵乘结果和手算不完全一致，多半是 TF32（`MLX_ENABLE_TF32` 默认开），不是 bug；`mx.distributed` 的算子像没生效，先打印 `world.size()`，单进程下它们按设计就是 no-op。

## 14. 与 PyTorch、JAX 的边界

| 维度 | PyTorch 2.x | JAX | MLX |
|---|---|---|---|
| 默认执行 | Eager，每算子落地 | Trace + `jit`，`lazy` 可选 | Lazy 图，边界求值 |
| 设备归属 | 挂在 tensor（`.device`） | 挂在数组（`jax.devices()`） | 挂在操作（`stream=`） |
| 后端 | CPU / CUDA / MPS / XPU 等 | CPU / GPU / TPU | CPU / Metal / CUDA |
| 集合通信 | NCCL / Gloo | `pjit` + `pmap` + GSPMD | Ring / MPI / NCCL / JaCCL |
| 编译 | `torch.compile` 追踪 + 重编 | `jit` 缓存 | `mx.compile`，缓存键含 shape/dtype |
| 主要生态位 | 通用研究 + 工业生产 | TPU 与函数变换研究 | Apple silicon 本地训练与推理、Mac 集群推理 |

按这个表，选 MLX 的理由收敛成三条：硬件是 Apple silicon 且不想维护 `device` 透传；要在单机大内存机器上跑中等模型的微调；想把 C++/Swift 推理嵌进已有工程（`mlx-c`、`mlx-swift` 与 C++ API 是同一套图语义）。

不选的理由同样具体：多机多卡大模型训练缺长年积累的作业经验与故障手册；需要开箱可用的 serving、监控与模型注册组件；需要 HF 权重零转换——MLX 权重要靠转换脚本产出，`mlx-lm` 和 `mlx-community` 覆盖了一部分模型，广度仍不及 PyTorch。

## 15. 采用顺序：谁先上、谁再等

给一个按周推进的顺序，每一步都有可验证的产出，不通过就别进下一步。

1. **确认地基**：`pip install mlx` 后跑 `mx.add(mx.array([1.,2.]), mx.array([3.,4.]), stream=mx.cpu)` 与 `stream=mx.gpu`，两边结果一致说明双后端都在。顺手打印 `mx.device_info()` 记住这台机器的架构字符串。
2. **验证惰性心智**：写一段含未使用分支的函数，用 `mx.eval` 前后对比 `mx.metal.get_active_memory()`。这一步的目的是把「图不等于计算」变成直觉，后面所有性能判断都建立在这上面。
3. **跑一个真实负载**：`mlx-examples/lora` 用 `lora.py --train --iters 600` 走一遍转换、训练、`fuse.py` 合权重。这一轮会暴露你机器上的内存上限。
4. **只在这一步引入 compile**：挑 forward 里逐元素链密集的位置做 `mx.compile`，用第 11 节那条口径（固定 shape、固定 dtype、预热后取均值）测改动前后。
5. **需要嵌入再碰 C++/Swift**：`cmake .. && make -j && make test`，然后按第 8 节处理 `mlx.metallib` 的位置。
6. **多机留到最后**：先读第 9 节的后端表，判断你手上的互联属于哪一档。以太网起步用 Ring；四台以内 M3 Ultra 且能接受进恢复模式开 RDMA，才考虑 JaCCL 与张量并行；CUDA 环境直接 NCCL。

不急着上的画像很清晰：硬件是 Intel Mac（`MLX_ENABLE_X64_MAC` 默认 OFF，且没有对应的官方 wheel）、需要生产级对外服务、或团队完全没有 Mac 侧运维经验。

## 16. 五个自测题

答不上来就回到对应小节，答案都在源码或正文里。

1. `a = mx.array([1., 2.])`、`b = mx.array([3., 4.])`、`c = a + b` 之后，`c` 的 `status` 是哪一档？`mx.eval(c)` 之后呢？如果接着写 `print(c)`，还会不会重算一遍？
2. `fc = mx.compile(f)` 之后连续两次调用输入 shape 从 `(4,16)` 变成 `(8,16)`，再从 `(8,16)` 变成 `(8,16,1)`，分别发生了什么？`shapeless=True` 时结论有变化吗？
3. 文档说 `matmul` 放 GPU、500 次 `exp` 放 CPU 比全放 GPU 快一倍。这条结论依赖 `eval_impl` 里的哪个数据结构？为什么它在 PyTorch MPS 下不好照写？
4. 四台 M3 Ultra 全连成 JaCCL mesh，`mx.distributed.init()` 不带参数会拿到哪个后端？换成以太网连的三台 Linux + CUDA 机器呢？
5. `float32` 的 `matmul` 结果与 `numpy` 手算差在第三位小数，你优先检查哪两个东西？

## 17. 下一步读哪份代码

三条深入路线，每条都给出可核对的起点。

**想搞清执行模型**：`mlx/transforms.cpp` 的 `eval_impl` → `mlx/compile.cpp` 的融合搜索（`max_compile_depth` 附近）→ `mlx/scheduler.cpp` 的 `StreamThread`。对照读 PyTorch 的 `torch/_dynamo/` 会更有味道：两边都在处理「Python 控制流怎么办」，给出的答案不同。

**想写 kernel**：`docs/src/dev/custom_metal_kernels.rst` → `mlx/backend/metal/kernels/` 里挑一个 `.metal` 和它的 `.h` → `mlx/backend/metal/normalization.cpp` 看 host 侧怎么起参数。CUDA 侧同构，入口在 `mlx/backend/cuda/`，PTX 缓存目录由 `MLX_PTX_CACHE_DIR` 控制。

**想做分布式**：`mlx/distributed/distributed.cpp` 的 `init()` 与 `register_group()` → `mlx/distributed/ring/ring.cpp`（自研的 TCP 环）→ `mlx/distributed/nccl/nccl.cpp`（对 NCCL 的封装）。想理解为什么 Ring 不支持任意 `send`/`recv`，读它的拓扑构建部分比读文档快。

## 18. 维护指引：本文断言的核实方法与失效条件

统一核对时间 2026-09-19，对应 `main` 提交 `59d600b5`（版本号 0.32.3，最近推送 2026-09-17）。核实方法固定三步：`git clone --depth 1 --filter=blob:none --no-checkout` 后用 `git ls-tree` 看目录、`git show HEAD:<path>` 按需取文件；PyPI 侧 `curl https://pypi.org/pypi/<pkg>/json` 拿版本与 wheel 文件名；仓库统计走 GitHub API。

下一轮复核请优先重查这些位置，它们失效最快：

- 第 2 节整张快照表：stars/forks/版本/tag 是随时间漂移量。
- 第 12 节的安装矩阵与 extra 名称：`mlx[cuda]` 与 `mlx[cuda12]` 的措辞分歧（README 对 docs）只要合并一次就会变。
- `mlx-cuda` 与 `mlx-cuda-12/13` 的包名与版本对齐情况：PyPI 上历史名 `mlx-cuda` 停在 0.30.0，新名已到 0.32.2。
- 第 9 节 JaCCL 的前置条件：macOS 26.2、恢复模式 `rdma_ctl enable`、全连接 mesh 三条都是阶段性限制，一旦进系统设置就会整段作废。
- 第 8 节 `MLX_METAL_FAST_SYNCH` 的默认值：它挂在 issue #3142 上，修完就该翻回来改。
- 所有代码引用：路径与行号会随重构移动，本文一律只写路径与可 grep 的符号名。

结构性断言的复核口令：

```bash
git ls-tree --name-only HEAD mlx/backend/           # 后端目录清单
git ls-tree -r --name-only HEAD mlx/ | wc -l        # 核心文件数
git show HEAD:mlx/primitives.h | grep -c "void eval_gpu"
git show HEAD:CMakeLists.txt | grep -n '^option'
git show HEAD:docs/src/usage/environment_variables.rst
```

## 参考来源

- 仓库主仓：<https://github.com/ml-explore/mlx>
- 文档站：<https://ml-explore.github.io/mlx/build/html/index.html>
- 统一内存：<https://ml-explore.github.io/mlx/build/html/usage/unified_memory.html>
- 惰性求值与 `compile`：<https://ml-explore.github.io/mlx/build/html/usage/lazy_evaluation.html>、<https://ml-explore.github.io/mlx/build/html/usage/compile.html>
- 分布式与后端：<https://ml-explore.github.io/mlx/build/html/usage/distributed.html>
- 环境变量：<https://ml-explore.github.io/mlx/build/html/usage/environment_variables.html>
- 构建与安装：<https://ml-explore.github.io/mlx/build/html/install.html>
- 示例仓库与 LoRA 数字：<https://github.com/ml-explore/mlx-examples/blob/main/lora/README.md>
- 微基准与对比脚本：<https://github.com/ml-explore/mlx/tree/main/benchmarks/python/comparative>
- Swift / C / LM / 数据 API：<https://github.com/ml-explore/mlx-swift>、<https://github.com/ml-explore/mlx-c>、<https://github.com/ml-explore/mlx-lm>、<https://github.com/ml-explore/mlx-data>
