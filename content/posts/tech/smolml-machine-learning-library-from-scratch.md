---
title: "SmolML：纯 Python 实现的机器学习库，从自动微分到完整模型"
date: "2026-05-17T20:02:25+08:00"
slug: "smolml-machine-learning-library-from-scratch"
description: "SmolML 是一个完全使用纯 Python 标准库实现的机器学习库，不依赖 NumPy/SciPy 等外部包。通过完整的自动微分引擎 Value 和 N 维数组 MLArray 两大核心模块，构建了从线性回归、神经网络到 SVM、K-Means 的完整模型体系。"
draft: false
categories: ["技术笔记"]
tags: ["Machine Learning", "Python", "Autograd", "Neural Network", "从头实现"]
---

## 这篇文章在讲什么

SmolML 是一个只有约 2000 行纯 Python 代码的机器学习库，GitHub Stars 443，MIT 许可证。它不依赖 NumPy、SciPy 或任何外部框架——只用 `math`、`random`、`collections` 这三个标准库模块。

本文先讲清楚 SmolML 的四层架构分别做什么、彼此怎么衔接，然后拆开自动微分引擎（Value）和 N 维数组（MLArray）的实现细节，最后给一个完整的训练流转案例，把这几层串起来。

读完可以判断：如果你正在教机器学习课、想自己动手理解反向传播，或者需要一个零依赖的微型实验环境，SmolML 是不是你要的东西。

## 学习目标

- Value 对象上的 `backward()` 是怎样通过拓扑排序和闭包把梯度从输出传到输入的。
- MLArray 的矩阵乘法和广播在纯 Python 里具体怎么做，代价是什么。
- 一个完整的训练循环（forward → loss → backward → update → restart）在 SmolML 里如何串联。
- 哪些场景适合用 SmolML，哪些场景应该直接用 NumPy/Scikit-learn。

## 项目架构总览

SmolML 按职责分成四层，上下层之间有明确的依赖方向：

```
smolml/
├── core/                  # 基础设施：自动微分 + N 维数组
│   ├── value.py          # Value — 标量级 autograd 引擎
│   └── ml_array.py       # MLArray — 类 NumPy 的多维数组
├── utils/                # 训练构件：激活、初始化、损失、优化器
│   ├── activation.py
│   ├── initializers.py
│   ├── losses.py
│   └── optimizers.py
├── models/               # 模型实现
│   ├── nn/               # 前馈神经网络
│   ├── tree/             # 决策树与随机森林
│   ├── regression/       # 线性与多项式回归
│   ├── svm/              # 支持向量机
│   └── unsupervised/     # K-Means 聚类
└── preprocessing/        # 数据预处理
    └── scalers.py        # StandardScaler、MinMaxScaler
```

关键依赖链路：`utils` 层的所有组件都作用在 `core` 层的 `MLArray` 上；`models` 层组合 `utils` 层的构件来构建完整模型；`preprocessing` 层独立于上述链路，只做数据变换。

## 第一层：Core——数学地基

Core 模块只有两个类：`Value`（自动微分引擎）和 `MLArray`（N 维数组）。整个库的梯度计算和矩阵运算都建在这两个类上面。

### 1.1 Value：自动微分引擎

[smolml/core/value.py](https://github.com/rodmarkun/SmolML) 中的 `Value` 类参考了 [karpathy/micrograd](https://github.com/karpathy/micrograd) 的设计。每个 `Value` 对象既存一个标量值，又记录它在计算图中的位置：

```python
class Value:
    def __init__(self, data, _children=(), _op=""):
        self.data = data              # 标量数值
        self.grad = 0                # 梯度
        self._backward = lambda: None # 反向传播函数（闭包）
        self._prev = set(_children)   # 前驱节点
        self._op = _op                # 操作类型（如 "+"、"*"）
```

`_prev` 是一个集合，存的是当前 Value 依赖的前驱节点。`_backward` 是一个闭包，在创建计算节点时就捕获了操作类型和操作数，反向传播时不需要重新推导——直接执行。

Value 通过 Python 特殊方法重载了以下运算，每个运算都内嵌了对应的梯度公式：

| 操作 | 方法 | 梯度计算 |
|------|------|----------|
| 加法 | `__add__`, `__radd__` | `∂(a+b)/∂a = 1`, `∂(a+b)/∂b = 1` |
| 乘法 | `__mul__`, `__rmul__` | 乘积法则 `∂(ab)/∂a = b` |
| 幂运算 | `__pow__` | `∂(aⁿ)/∂a = n·aⁿ⁻¹` |
| 绝对值 | `__abs__` | 符号函数 |
| 除法 | `__truediv__` | 转化为乘法：`a/b = a·b⁻¹` |
| 指数 | `exp()` | `∂eˣ/∂x = eˣ` |
| 对数 | `log()` | `∂ln(x)/∂x = 1/x` |
| ReLU | `relu()` | `∂ReLU/∂x = 1 if x>0 else 0` |
| Tanh | `tanh()` | `∂tanh/∂x = 1 - tanh²(x)` |

反向传播用拓扑排序保证执行顺序：

```python
def backward(self):
    topo = []
    visited = set()
    def build_topo(v):
        if v not in visited:
            visited.add(v)
            for child in v._prev:
                build_topo(child)
            topo.append(v)
    build_topo(self)
    self.grad = 1  # 输出对自身的导数为 1
    for v in reversed(topo):
        v._backward()
```

注意两件事：

- `self.grad = 1` 把最终输出节点的梯度初始化为 1——这是链式法则的起点。
- `reversed(topo)` 保证从输出往输入方向逐层调用 `_backward`，先算的节点后执行。

当一个变量参与多条计算路径（比如同一个权重同时出现在两个分支里），梯度要累加而不是覆盖，所以 `_backward` 里用的是 `+=`：

```python
def __add__(self, other):
    # ...
    def _backward():
        self.grad += out.grad
        other.grad += out.grad
    out._backward = _backward
```

### 1.2 MLArray：纯 Python 的 N 维数组

[smolml/core/ml_array.py](https://github.com/rodmarkun/SmolML) 实现了一个接口接近 NumPy 的 N 维数组，区别是数组里每个元素都被包装成 `Value` 对象——这意味着 MLArray 上的所有运算都自带自动微分。

```python
class MLArray:
    def __init__(self, data):
        self.data = self._process_data(data)  # 递归将所有数值包装为 Value
```

支持的数据格式：标量 `MLArray(3.14)` → shape `()`；一维向量 `MLArray([1, 2, 3])` → shape `(3,)`；二维矩阵 `MLArray([[1,2], [3,4]])` → shape `(2, 2)`。

矩阵乘法通过 `__matmul__` 实现。一维向量会自动转为行/列矩阵，多维情况做 reshape。核心是双层 Python 循环：`C[i][j] = sum(A[i][k] * B[k][j])`，不依赖任何向量化加速。

广播机制 `_broadcast_shapes` 和 `_broadcast_and_apply` 模仿 NumPy 的行为：短 shape 左边补 1，对应维度不相等时，若其中一个为 1 则可广播。

元素级操作统一走 `_element_wise_operation`：先算广播后的目标 shape，再递归应用到每个元素。

规约操作（`sum`、`mean`、`std`、`min`、`max`）支持指定轴。不指定轴时做全局规约；指定轴时需要转置处理。

索引支持 NumPy 风格：`arr[0]`、`arr[1, 2]`、`arr[:, 0]`、`arr[1:3, :]`。

训练循环中，每个 epoch 结束后需要把所有权重的梯度清零。`restart()` 方法递归遍历 MLArray 里的所有 Value，把 `grad` 置为 0。

## 一个完整的训练流转案例

在进入后续模块之前，先看一个具体的一次前向 + 反向 + 参数更新，把上面讲的 Value 和 MLArray 串起来。

假设有一个简单的二分类网络：输入 2 维 → 隐藏层 3 个神经元（ReLU）→ 输出 1 维（sigmoid）。一次训练迭代走下面 6 步：

```
1. 输入 X (MLArray) 和权重 W (MLArray) 做矩阵乘法
   → X @ W 内部调用 MLArray.matmul()
   → 矩阵乘法内部每个元素乘积调用 Value.__mul__()
   → 每次 __mul__() 都创建一个新 Value 节点并注册 _backward 闭包

2. 加上偏置 b（广播）
   → (X @ W) + b 调用 Value.__add__()
   → 广播意味着同一个 b 被多条路径引用，梯度会累加

3. 过激活函数
   → relu() 对每个元素调用 Value.relu()
   → 每个 relu() 记录自己是否在正半轴，决定反向时梯度是否传递

4. 计算损失
   → binary_cross_entropy(y_pred, y_true)
   → 内部调用 .log()、.__mul__()、.mean()，继续扩展计算图

5. loss.backward()
   → 从 loss 节点出发，拓扑排序遍历整张计算图
   → reversed(topo) 逐节点执行 _backward() 闭包
   → 每个 _backward 根据操作类型（加/乘/relu/log）计算本节点的局部梯度
   → 局部梯度乘以来自下游的累积梯度（链式法则），累加到 _prev 中每个节点的 .grad

6. optimizer.update()
   → 遍历所有 DenseLayer 的 weights 和 biases
   → 每个参数 = 参数 - learning_rate * 参数.grad()
   → 调用 MLArray.restart() 把所有 .grad 清零，准备下一轮
```

这 6 步里，步骤 1-4 只建计算图，不做数值计算；步骤 5 才执行梯度计算；步骤 6 用梯度更新参数并清零。理解这个时序，就理解了 SmolML 整个训练流程。

## 第二层：Utils——训练的基础构件

Utils 层提供四个组件，都直接操作 MLArray。

### 2.1 激活函数（activation.py）

所有激活函数都是元素级操作，接收 MLArray，返回新的 MLArray：

```python
def relu(x):
    return _element_wise_activation(x, lambda val: val.relu())

def sigmoid(x):
    def sigmoid_single(val):
        return 1 / (1 + (-val).exp())
    return _element_wise_activation(x, sigmoid_single)

def softmax(x, axis=-1):
    max_val = x.max()
    exp_x = (x - max_val).exp()
    return exp_x / exp_x.sum(axis=axis)
```

`softmax` 里减 `max_val` 是为了数值稳定性——防止 `exp` 在大值上溢出。

支持的激活函数：

| 函数 | 公式 | 适用场景 |
|------|------|----------|
| `relu` | max(0, x) | 深度网络默认选择 |
| `leaky_relu` | x if x>0 else α·x | 防止 dying ReLU |
| `elu` | x if x>0 else α(eˣ-1) | 平滑负值区域 |
| `sigmoid` | 1/(1+e⁻ˣ) | 二分类输出 |
| `softmax` | eˣⁱ/Σeˣʲ | 多分类输出 |
| `tanh` | (e²ˣ-1)/(e²ˣ+1) | 隐藏层（-1 到 1 输出） |
| `linear` | x | 回归输出层 |

### 2.2 权重初始化（initializers.py）

初始化策略的选择直接影响训练能否收敛：

```python
class XavierUniform:
    @staticmethod
    def initialize(*dims):
        fan_in, fan_out = dims[0], dims[-1]
        limit = math.sqrt(6. / (fan_in + fan_out))
        # 生成 [-limit, limit] 均匀分布

class HeInitialization:
    @staticmethod
    def initialize(*dims):
        fan_in = dims[0]
        std = math.sqrt(2. / fan_in)
        # 均值 0、标准差 std 的高斯分布
```

Xavier 初始化适合搭配 tanh/sigmoid 使用，方差根据输入和输出神经元数量共同调节。He 初始化只考虑输入维度——因为 ReLU 会把一半的神经元输出置零，实际活跃的神经元只有一半，所以方差需要更大。

### 2.3 损失函数（losses.py）

```python
def mse_loss(y_pred, y_true):
    diff = y_pred - y_true
    return (diff * diff).mean()

def binary_cross_entropy(y_pred, y_true):
    epsilon = 1e-15
    y_pred = clip(y_pred, epsilon, 1-epsilon)
    return -(y_true * y_pred.log() + (1-y_true) * (1-y_pred).log()).mean()

def categorical_cross_entropy(y_pred, y_true):
    epsilon = 1e-15
    y_pred = clip(y_pred, epsilon, 1.0)
    return -(y_true * y_pred.log()).sum(axis=1).mean()
```

BCE 和交叉熵中的 `epsilon = 1e-15` 是为了防止 `log(0)` 产生 `-inf`。

### 2.4 优化器（optimizers.py）

所有优化器继承同一个基类：

```python
class Optimizer:
    def __init__(self, learning_rate=0.01):
        self.learning_rate = learning_rate

    def update(self, object, object_idx, param_names):
        raise NotImplementedError
```

SGD 最简单：`θ = θ - α∇θ`。SGDMomentum 在 SGD 上加了动量项 `v = βv + α∇θ`，用字典 `self.velocities` 按层索引存储速度。AdaGrad 维护历史梯度平方的累加和 `G`，更新公式为 `θ = θ - (α / √(G + ε)) * ∇θ`——适合稀疏特征，但 `G` 单调递增会导致后期学习率趋近于零。

Adam 结合了动量（一阶矩估计）和 RMSProp（二阶矩估计），并加入了偏置校正：

```
m = β₁m + (1-β₁)∇θ     # 一阶矩（动量）
v = β₂v + (1-β₂)∇θ²    # 二阶矩（自适应学习率）
m̂ = m / (1-β₁ᵗ)        # 偏置校正
v̂ = v / (1-β₂ᵗ)
θ = θ - α * m̂ / (√v̂ + ε)
```

偏置校正是因为 `m` 和 `v` 初始化为 0，早期迭代会偏向零，除以 `(1-βᵗ)` 可以补偿这个偏差。

## 第三层：Models——完整模型实现

### 3.1 神经网络（nn/）

DenseLayer 封装了一个线性变换加一个激活函数：

```python
class DenseLayer:
    def __init__(self, input_size, output_size,
                 activation_function=activation.linear,
                 weight_initializer=initializers.XavierUniform):
        self.weights = weight_initializer.initialize(input_size, output_size)
        self.biases = zeros(1, output_size)
        self.activation_function = activation_function

    def forward(self, input_data):
        z = input_data @ self.weights + self.biases
        return self.activation_function(z)
```

NeuralNetwork 把多个 DenseLayer 串起来，训练循环的结构很直接：

```python
class NeuralNetwork:
    def train(self, X, y, epochs, verbose=True, print_every=100):
        for epoch in range(epochs):
            y_pred = self.forward(X)
            loss = self.loss_function(y_pred, y)
            loss.backward()

            for idx, layer in enumerate(self.layers):
                layer.update(self.optimizer, idx)

            X.restart(); y.restart()
            for layer in self.layers:
                layer.weights.restart()
                layer.biases.restart()
```

注意 `restart()` 的调用范围：不仅每一层的权重和偏置要清零梯度，输入 `X` 和标签 `y` 也被包装成了 MLArray（它们的元素也是 Value），所以也需要清零——否则上一轮的梯度残留在计算图里。

### 3.2 回归模型（regression/）

LinearRegression 就是一个不带激活函数的单层网络：`predict(X) = X @ weights + bias`。

PolynomialRegression 先通过 `generate_combinations` 生成多项式特征，再送给线性模型。例如 2 特征 degree=2 时生成 `[x₁, x₂, x₁², x₁x₂, x₂²]`。

### 3.3 决策树（tree/）

DecisionTree 用 CART 算法。分类任务用信息增益（熵）：`gain = H(parent) - Σ(n_i/n)·H(child_i)`。回归任务用 MSE 减少量。`_find_best_split` 遍历所有特征和候选阈值，选出增益最大的切分点。

RandomForest 通过 Bagging 集成多棵决策树：每棵树用 Bootstrap 采样（有放回随机抽样）训练，预测时分类投票、回归取平均。

### 3.4 支持向量机（svm/）

SVM 用 SMO（Sequential Minimal Optimization）算法训练。SMO 的核心思路是每次只优化两个拉格朗日乘子 αᵢ 和 αⱼ，因为约束 Σαᵢyᵢ = 0 意味着改一个必须同时改另一个。`_take_step` 先计算 α₂ 的上下界 `[L, H]`，再用 `η = K₁₁ + K₂₂ - 2K₁₂` 求解析解，clip 到界内，最后更新 α₁ 和偏置 b。

支持三种核函数：linear（内积）、rbf（高斯核）、poly（多项式核）。

### 3.5 K-Means 聚类（unsupervised/）

流程是标准的 Lloyd 算法：随机选 k 个样本做初始中心 → 算每个样本到各中心的欧氏距离 → 分配到最近中心 → 用簇内均值更新中心 → 重复直到中心不再移动或达到最大迭代次数。

## 第四层：Preprocessing——数据标准化

StandardScaler 做 Z-score 标准化：`(X - mean) / std`。MinMaxScaler 映射到 `[0, 1]`：`(X - min) / (max - min)`。两者都按列（特征维度）计算统计量。

## 实战示例

### 示例 1：训练一个神经网络

```python
from smolml.core.ml_array import MLArray
from smolml.models.nn import DenseLayer, NeuralNetwork
from smolml.utils.activation import relu, softmax
from smolml.utils.losses import categorical_cross_entropy
from smolml.utils.optimizers import Adam

layers = [
    DenseLayer(4, 8, activation_function=relu),
    DenseLayer(8, 8, activation_function=relu),
    DenseLayer(8, 3, activation_function=softmax)
]

network = NeuralNetwork(
    layers=layers,
    loss_function=categorical_cross_entropy,
    optimizer=Adam(learning_rate=0.01)
)

X = MLArray([[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]])
y = MLArray([[1, 0, 0], [0, 1, 0]])

losses = network.train(X, y, epochs=1000, verbose=True, print_every=100)
```

### 示例 2：决策树分类

```python
from smolml.models.tree import DecisionTree

X = MLArray([[1, 2], [2, 3], [3, 1], [4, 5], [5, 4]])
y = MLArray([0, 0, 0, 1, 1])

tree = DecisionTree(max_depth=3, task="classification")
tree.fit(X, y)

predictions = tree.predict(MLArray([[1.5, 2.5]]))
print(predictions.to_list())  # [0]

tree.show_tree(feature_names=["feature_0", "feature_1"])
```

### 示例 3：K-Means 聚类

```python
from smolml.models.unsupervised import KMeans
from smolml.preprocessing import MinMaxScaler

X = MLArray([[1, 2], [1.5, 1.8], [5, 8], [8, 8], [1, 0.6], [9, 11]])

scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=2, max_iters=100, tol=1e-4)
labels = kmeans.fit_predict(X_scaled)

print(labels.to_list())  # [0, 0, 1, 1, 0, 1]
```

## 扩展开发指南

SmolML 的模块化设计让添加新组件很简单：遵循现有接口，不需要修改核心代码。

### 添加激活函数

在 `smolml/utils/activation.py` 中添加：

```python
def swish(x):
    """Swish: x * sigmoid(x)"""
    return x * sigmoid(x)
```

### 添加损失函数

在 `smolml/utils/losses.py` 中添加：

```python
def hinge_loss(y_pred, y_true, margin=1.0):
    """SVM 风格铰链损失：L = max(0, margin - y_true * y_pred)"""
    diff = MLArray([margin]) - y_true * y_pred
    return (diff.relu()).mean()
```

### 添加优化器

在 `smolml/utils/optimizers.py` 中添加：

```python
class RMSProp(Optimizer):
    """RMSProp: 使用指数加权移动平均的梯度平方来调节学习率"""
    def __init__(self, learning_rate=0.01, decay_rate=0.99):
        super().__init__(learning_rate)
        self.decay_rate = decay_rate
        self.epsilon = 1e-8
        self.square_gradients = {}

    def update(self, object, object_idx, param_names):
        if object_idx not in self.square_gradients:
            self.square_gradients[object_idx] = {
                name: zeros(*getattr(object, name).shape)
                for name in param_names
            }

        new_params = []
        for name in param_names:
            g = getattr(object, name).grad()
            self.square_gradients[object_idx][name] = (
                self.decay_rate * self.square_gradients[object_idx][name] +
                (1 - self.decay_rate) * g**2
            )
            new_params.append(
                getattr(object, name) - self.learning_rate * g /
                (self.square_gradients[object_idx][name].sqrt() + self.epsilon)
            )
        return tuple(new_params)
```

### 添加新模型（以 KNN 为例）

```python
# smolml/models/knn/knn.py
from smolml.core.ml_array import MLArray
from collections import Counter

class KNN:
    def __init__(self, k=3):
        self.k = k
        self.X_train = None
        self.y_train = None

    def fit(self, X, y):
        self.X_train = X
        self.y_train = y
        return self

    def predict(self, X):
        predictions = []
        for sample in X.data:
            distances = []
            for train_sample in self.X_train.data:
                diff = MLArray(train_sample) - MLArray(sample)
                dist = (diff * diff).sum().sqrt()
                distances.append((dist.data, self._get_label(train_sample)))

            distances.sort(key=lambda x: x[0])
            k_nearest = [d[1] for d in distances[:self.k]]
            prediction = Counter(k_nearest).most_common(1)[0][0]
            predictions.append(prediction)

        return MLArray(predictions)

    def _get_label(self, sample):
        pass  # 需要实现索引映射
```

## 性能：纯 Python 的代价

SmolML 的矩阵乘法是三层嵌套 Python 循环：

```python
for i in range(a.shape[0]):
    for j in range(b.shape[index_b]):
        result[i][j] = sum(a.data[i][k] * b.data[k][j] for k in range(a.shape[1]))
```

NumPy 底层调用 BLAS（用 C/Fortran 实现的高度优化线性代数库），同样的矩阵乘法比纯 Python 快 100 到 1000 倍。

这个差距测的是什么呢？**只测了矩阵运算的吞吐量**，不是整个训练流程的端到端速度。在小模型（几百个参数、几千条样本）上，训练循环中反向传播建图和 Python 解释器开销的占比可能比矩阵乘法本身更高。所以这个 100-1000x 的数字主要说明：SmolML 不适合跑需要大规模矩阵运算的场景——比如训练几百 MB 的权重矩阵，或者处理百万级样本。

这个数字**不能**说明 SmolML 的算法正确性有问题，也不能说明它不适合教学和小规模实验。

## 什么时候用 SmolML

按优先级排列：

1. **教机器学习课**。自动微分、反向传播、计算图这些概念，让学生改一行 `_backward` 闭包然后立刻看到梯度变化，比对着 PPT 讲有效得多。
2. **自己动手验证理解**。如果你看完了 Andrej Karpathy 的 micrograd 视频，想自己动手搭一个更完整的版本，SmolML 是一个很合适的参考——它把 micrograd 的标量 autograd 扩展到了多维数组和完整模型。
3. **需要一个零依赖的原型环境**。当你只想快速验证一个算法思路，不想装 NumPy/SciPy 或者配 CUDA 环境，SmolML 的 `pip install` 就是零额外依赖。
4. **读源码学习框架设计**。2000 行代码、四层清晰分层，读一遍就能理解一个 ML 框架从矩阵运算到模型训练的完整链路。

下面的场景**不适合**用 SmolML：

- 训练数据超过几万条或者模型参数量超过几千。纯 Python 循环会让每个 epoch 变成分钟级。
- 生产环境部署。没有序列化格式、没有推理优化、没有 GPU 支持。
- 需要与现有 ML 生态（Pandas 数据管线、ONNX 导出、模型 serving）对接的场景。

如果你已经熟悉 NumPy 和 PyTorch，读 SmolML 源码的价值主要在前两块（教学和验证），不需要用它来跑实验。

---

项目地址：[https://github.com/rodmarkun/SmolML](https://github.com/rodmarkun/SmolML)

*本文所有代码和架构信息均来自 SmolML 项目源码（MIT 许可证）。*