---
title: "SmolML：纯Python实现的机器学习库，从自动微分到完整模型"
date: "2026-05-17T20:02:25+08:00"
slug: "smolml-machine-learning-library-from-scratch"
description: "SmolML是一个完全使用纯Python标准库实现的机器学习库，不依赖NumPy/SciPy等外部包。通过完整的自动微分引擎Value和N维数组MLArray两大核心模块，构建了从线性回归、神经网络到SVM、K-Means的完整模型体系。本文深入剖析其核心架构与实现原理，并提供从入门到扩展的完整指南。"
draft: false
categories: ["技术笔记"]
tags: ["Machine Learning", "Python", "Autograd", "Neural Network", "从头实现"]
---

## 概述

[SmolML](https://github.com/rodmarkun/SmolML)是一个**纯Python机器学习库**，GitHub Stars 443，MIT许可证。项目仅使用Python标准库（`collections`、`random`、`math`），不依赖NumPy、SciPy或任何外部机器学习框架。其目标不是生产使用，而是通过**完全从头构建**的方式，让开发者深入理解机器学习的核心原理。

项目作者在README中明确指出：

> The best way to truly understand complex topics like machine learning is often to **build them yourself**.

这正是SmolML的设计哲学。

## 项目架构总览

SmolML采用清晰的四层模块结构：

```
smolml/
├── core/                  # 核心基础设施
│   ├── value.py          # 自动微分引擎（autograd）
│   └── ml_array.py       # N维数组实现
├── models/               # 机器学习模型
│   ├── nn/               # 神经网络
│   ├── tree/             # 决策树与随机森林
│   ├── regression/       # 线性与多项式回归
│   ├── svm/              # 支持向量机
│   └── unsupervised/     # K-Means聚类
├── utils/                # 工具函数
│   ├── activation.py     # 激活函数
│   ├── initializers.py   # 权重初始化
│   ├── losses.py         # 损失函数
│   └── optimizers.py     # 优化器
└── preprocessing/        # 数据预处理
    └── scalers.py        # 标准化与归一化
```

---

## 第一层：Core模块——机器学习的数学地基

Core模块是整个库的基石，包含两个核心类：`Value`（自动微分引擎）和`MLArray`（N维数组）。

### 1.1 Value：自动微分引擎

`smolml/core/value.py`中的`Value`类参考了[karpathy/micrograd](https://github.com/karpathy/micrograd)的设计思路，是整个自动微分系统的核心。

#### 核心数据结构

```python
class Value:
    def __init__(self, data, _children=(), _op=""):
        self.data = data              # 标量数值
        self.grad = 0                # 梯度（导数）
        self._backward = lambda: None # 反向传播函数
        self._prev = set(_children)   # 前驱节点（计算图）
        self._op = _op                # 操作类型
```

每个`Value`对象存储一个标量值，同时记录其计算图中的前驱节点和操作类型。

#### 支持的运算操作

`Value`通过Python的特殊方法（dunder methods）重载了以下运算：

| 操作 | 方法 | 梯度计算 |
|------|------|----------|
| 加法 | `__add__`, `__radd__` | `∂(a+b)/∂a = 1`, `∂(a+b)/∂b = 1` |
| 乘法 | `__mul__`, `__rmul__` | 乘积法则 `∂(ab)/∂a = b` |
| 幂运算 | `__pow__` | `∂(a^n)/∂a = n·a^(n-1)` |
| 绝对值 | `__abs__` | 符号函数 |
| 除法 | `__truediv__` | 转化为乘法：`a/b = a·b⁻¹` |
| 指数 | `exp()` | `∂eˣ/∂x = eˣ` |
| 对数 | `log()` | `∂ln(x)/∂x = 1/x` |
| ReLU | `relu()` | `∂ReLU/∂x = 1 if x>0 else 0` |
| Tanh | `tanh()` | `∂tanh/∂x = 1 - tanh²(x)` |

#### 反向传播实现

反向传播通过拓扑排序保证计算顺序：

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
    self.grad = 1  # 输出对自身的导数为1
    for v in reversed(topo):
        v._backward()
```

**关键细节**：

- `self.grad = 1` 初始化最终输出节点的梯度
- `reversed(topo)`确保从叶节点到根节点的反向计算顺序
- 每个操作的梯度通过闭包（`_backward`）捕获计算时的上下文

#### 多路径梯度累积

当一个变量参与多条计算路径时，梯度会累加（`+=`）：

```python
def __add__(self, other):
    # ...
    def _backward():
        self.grad += out.grad   # 累加而非赋值
        other.grad += out.grad
    out._backward = _backward
```

### 1.2 MLArray：纯Python的N维数组

`smolml/core/ml_array.py`实现了一个类NumPy接口的N维数组，但所有元素都包装为`Value`对象以支持自动微分。

#### 数据结构

```python
class MLArray:
    def __init__(self, data):
        self.data = self._process_data(data)  # 递归处理，嵌套列表或Value
```

支持的数据格式：
- 标量：`MLArray(3.14)` → shape `()`
- 1D向量：`MLArray([1, 2, 3])` → shape `(3,)`
- 2D+矩阵：`MLArray([[1,2], [3,4]])` → shape `(2, 2)`

`_process_data`递归地将所有基础数值转换为`Value`对象。

#### 矩阵乘法

矩阵乘法`@`运算符通过`__matmul__`实现：

```python
def __matmul__(self, other):
    return self.matmul(other)

def matmul(self, other):
    # 处理1D向量（转为行/列矩阵）
    # 处理多维数组的reshape
    # 双层循环计算：C[i][j] = sum(A[i][k] * B[k][j])
```

关键实现细节：
- 自动处理1D向量与2D矩阵的转换
- 支持多维批量矩阵乘法
- 内部遍历使用Python循环（无NumPy向量化，性能较低但逻辑透明）

#### 广播机制

`_broadcast_shapes`和`_broadcast_and_apply`实现了NumPy风格的广播：

```python
@staticmethod
def _broadcast_shapes(shape1, shape2):
    # (3,4,5) | (4,1) → (3,4,5)
    # 将短shape左边补1
    # 对应维度不相等时，若其中一个为1则可广播
```

#### 批量元素操作

元素级操作（element-wise）通过`_element_wise_operation`统一处理：

```python
def _element_wise_operation(self, other, op):
    # 1. 广播形状计算
    target_shape = self._broadcast_shapes(self.shape, other.shape)
    # 2. 递归应用操作（含广播）
    result = self._broadcast_and_apply(self.data, other.data, 
                                        self.shape, other.shape, 
                                        target_shape, op)
    return MLArray(result)
```

#### 规约操作

`sum`、`mean`、`std`、`min`、`max`等规约操作支持指定轴：

```python
def mean(self, axis=None):
    if axis is None:
        flat = self.flatten(self.data)
        return MLArray(sum(flat)) / len(flat)
    # 按轴规约时需要转置处理
```

#### 索引与切片

`__getitem__`支持NumPy风格的索引：

```python
arr[0]           # 第一个元素
arr[1, 2]        # 行列索引
arr[:, 0]        # 切片选取
arr[1:3, :]      # 范围切片
```

#### 重启梯度

`restart()`方法用于训练循环中重置所有`Value`的梯度：

```python
def restart(self):
    self._restart_data(self.data)
    return self

def _restart_data(self, data):
    if isinstance(data, Value):
        data.grad = 0
    elif isinstance(data, list):
        for item in data:
            self._restart_data(item)
```

---

## 第二层：Utils模块——训练的基础构件

Utils模块包含神经网络训练所需的核心组件。

### 2.1 激活函数（activation.py）

所有激活函数都是元素级操作，返回新的`MLArray`：

```python
def relu(x):
    return _element_wise_activation(x, lambda val: val.relu())

def sigmoid(x):
    def sigmoid_single(val):
        return 1 / (1 + (-val).exp())
    return _element_wise_activation(x, sigmoid_single)

def softmax(x, axis=-1):
    # 沿指定轴归一化
    # 减最大值保证数值稳定性
    max_val = x.max()
    exp_x = (x - max_val).exp()
    return exp_x / exp_x.sum(axis=axis)
```

支持的激活函数：

| 函数 | 公式 | 适用场景 |
|------|------|----------|
| `relu` | max(0, x) | 默认选择，深度网络 |
| `leaky_relu` | x if x>0 else α·x | 防止dying ReLU |
| `elu` | x if x>0 else α(eˣ-1) | 平滑负值区域 |
| `sigmoid` | 1/(1+e⁻ˣ) | 二分类输出 |
| `softmax` | eˣⁱ/Σeˣʲ | 多分类输出 |
| `tanh` | (e²ˣ-1)/(e²ˣ+1) | 隐藏层（-1到1输出） |
| `linear` | x | 回归输出层 |

### 2.2 权重初始化（initializers.py）

初始化策略直接影响训练稳定性：

```python
class XavierUniform:
    @staticmethod
    def initialize(*dims):
        fan_in, fan_out = dims[0], dims[-1]
        limit = math.sqrt(6. / (fan_in + fan_out))
        # 生成[-limit, limit]均匀分布

class XavierNormal:
    @staticmethod
    def initialize(*dims):
        std = math.sqrt(2. / (fan_in + fan_out))
        # 生成均值0、标准差std的高斯分布

class HeInitialization:
    @staticmethod
    def initialize(*dims):
        fan_in = dims[0]
        std = math.sqrt(2. / fan_in)
        # ReLU网络最优
```

**原理**：
- Xavier适合tanh/sigmoid（方差与输入输出尺寸相关）
- He适合ReLU（只考虑输入尺寸，因为ReLU会杀死一半神经元）

### 2.3 损失函数（losses.py）

```python
def mse_loss(y_pred, y_true):
    diff = y_pred - y_true
    return (diff * diff).mean()

def binary_cross_entropy(y_pred, y_true):
    epsilon = 1e-15  # 防止log(0)
    y_pred = clip(y_pred, epsilon, 1-epsilon)
    return -(y_true * y_pred.log() + (1-y_true) * (1-y_pred).log()).mean()

def categorical_cross_entropy(y_pred, y_true):
    epsilon = 1e-15
    y_pred = clip(y_pred, epsilon, 1.0)
    return -(y_true * y_pred.log()).sum(axis=1).mean()
```

### 2.4 优化器（optimizers.py）

优化器框架：

```python
class Optimizer:
    def __init__(self, learning_rate=0.01):
        self.learning_rate = learning_rate
    
    def update(self, object, object_idx, param_names):
        raise NotImplementedError
```

**SGD（随机梯度下降）**：

```python
class SGD(Optimizer):
    def update(self, object, object_idx, param_names):
        # θ = θ - α∇θ
        return tuple(
            getattr(object, name) - self.learning_rate * getattr(object, name).grad()
            for name in param_names
        )
```

**SGDMomentum（带动量的SGD）**：

```python
class SGDMomentum(Optimizer):
    def __init__(self, learning_rate=0.01, momentum_coefficient=0.9):
        super().__init__(learning_rate)
        self.momentum_coefficient = momentum_coefficient
        self.velocities = {}  # 存储每层速度
    
    def update(self, object, object_idx, param_names):
        # v = βv + α∇θ
        # θ = θ - v
        if object_idx not in self.velocities:
            self.velocities[object_idx] = {...}
        
        for name in param_names:
            v = self.velocities[object_idx][name]
            v = self.momentum_coefficient * v + self.learning_rate * getattr(object, name).grad()
            self.velocities[object_idx][name] = v
            new_params.append(getattr(object, name) - v)
```

**AdaGrad（自适应梯度）**：

```python
class AdaGrad(Optimizer):
    def update(self, object, object_idx, param_names):
        # θ = θ - (α / √(G + ε)) * ∇θ
        # G是历史梯度的累加平方和
```

**Adam（自适应矩估计）**：

```python
class Adam(Optimizer):
    def update(self, object, object_idx, param_names):
        # m = β₁m + (1-β₁)∇θ  （一阶矩估计/动量）
        # v = β₂v + (1-β₂)∇θ² （二阶矩估计/RMSProp）
        # m̂ = m / (1-β₁ᵗ)     （偏置校正）
        # v̂ = v / (1-β₂ᵗ)
        # θ = θ - α * m̂ / (√v̂ + ε)
```

---

## 第三层：Models模块——完整模型实现

### 3.1 神经网络（nn/）

#### DenseLayer（全连接层）

```python
class DenseLayer:
    def __init__(self, input_size, output_size, 
                 activation_function=activation.linear,
                 weight_initializer=initializers.XavierUniform):
        self.weights = weight_initializer.initialize(input_size, output_size)
        self.biases = zeros(1, output_size)  # 初始化为0
        self.activation_function = activation_function
    
    def forward(self, input_data):
        z = input_data @ self.weights + self.biases  # 线性变换
        return self.activation_function(z)              # 激活
```

**核心公式**：`output = activation(input @ weights + biases)`

#### NeuralNetwork（前馈网络）

```python
class NeuralNetwork:
    def __init__(self, layers, loss_function, optimizer=None):
        self.layers = layers
        self.loss_function = loss_function
        self.optimizer = optimizer or optimizers.SGD()
    
    def train(self, X, y, epochs, verbose=True, print_every=100):
        for epoch in range(epochs):
            y_pred = self.forward(X)          # 前向传播
            loss = self.loss_function(y_pred, y)  # 计算损失
            loss.backward()                  # 反向传播
            
            for idx, layer in enumerate(self.layers):
                layer.update(self.optimizer, idx)  # 更新参数
            
            # 重置梯度，准备下一轮
            X.restart(); y.restart()
            for layer in self.layers:
                layer.weights.restart()
                layer.biases.restart()
```

**训练循环**：

```
for epoch in epochs:
    → forward(X)         # 前向传播，构建计算图
    → loss(pred, y)     # 计算损失
    → loss.backward()    # 反向传播，计算梯度
    → update params      # 使用优化器更新
    → restart gradients  # 重置梯度
```

### 3.2 回归模型（regression/）

#### LinearRegression

```python
class LinearRegression(Regression):
    def predict(self, X):
        return X @ self.weights + self.bias
```

#### PolynomialRegression

通过`generate_combinations`生成多项式特征：

```python
# 输入2特征，degree=2
# 生成: [x₁, x₂, x₁², x₁x₂, x₂²]
def generate_combinations(self, n_features, degree):
    result = []
    def obtain_combination(curr, remaining, min_idx):
        if remaining == 0:
            result.append(curr)
            return
        for i in range(min_idx, n_features):
            obtain_combination(curr + [i], remaining-1, i)
    for d in range(1, degree+1):
        obtain_combination([], d, 0)
    return result
```

### 3.3 决策树（tree/）

#### DecisionTree（CART算法）

```python
class DecisionTree:
    def __init__(self, max_depth=None, min_samples_split=2, 
                 min_samples_leaf=1, task="classification"):
        # 分类：使用信息增益（熵）
        # 回归：使用MSE reduction
```

关键方法：

```python
def _find_best_split(self, X, y):
    # 遍历所有特征和所有候选阈值
    # 分类：计算 information_gain = H(parent) - Σ(n_i/n)H(child_i)
    # 回归：计算 gain = MSE(parent) - Σ(n_i/n)MSE(child_i)

def _information_gain_entropy(self, parent, left, right):
    def entropy(y):
        counts = Counter(y)
        probs = [c/len(y) for c in counts.values()]
        return -sum(p * math.log2(p) for p in probs if p > 0)
```

#### RandomForest

通过Bagging集成多棵决策树：

```python
class RandomForest:
    def __init__(self, n_estimators=10, max_depth=None, 
                 min_samples_split=2, task="classification"):
        self.trees = [DecisionTree(...) for _ in range(n_estimators)]
    
    def fit(self, X, y):
        for tree in self.trees:
            # Bootstrap采样
            indices = random.choices(range(len(X)), k=len(X))
            tree.fit(X[indices], y[indices])
    
    def predict(self, X):
        # 投票（分类）或平均（回归）
```

### 3.4 支持向量机（svm/）

#### SVM（二分类）

使用SMO（Sequential Minimal Optimization）算法训练：

```python
class SVM:
    def fit(self, X, y):
        # SMO主循环
        # 1. 选择一个αᵢ
        # 2. 选择另一个αⱼ形成工作集
        # 3. 优化二元问题
        # 4. 更新b和误差缓存
        
    def _take_step(self, i1, i2, X_data, y_data, errors):
        # 计算上下界 L, H
        # 计算η = K₁₁ + K₂₂ - 2K₁₂
        # 更新α₂ = clip(α₂ + y₂(E₁-E₂)/η, L, H)
        # 更新α₁ = α₁ + s(α₂_old - α₂_new)
```

支持核函数：
- `linear`: K(x₁,x₂) = x₁·x₂
- `rbf`: K(x₁,x₂) = exp(-γ||x₁-x₂||²)
- `poly`: K(x₁,x₂) = (γx₁·x₂ + r)^d

### 3.5 K-Means聚类（unsupervised/）

```python
class KMeans:
    def fit(self, X_train):
        self._initialize_centroids(X_train)  # 随机选择k个样本
        
        for _ in range(self.max_iters):
            distances = self._compute_distances(X_train)  # 欧氏距离
            self._assign_clusters(distances)               # 分配到最近中心
            if self._update_centroids(X_train):            # 更新中心并检查收敛
                break
```

---

## 第四层：Preprocessing模块——数据标准化

### 4.1 StandardScaler

```python
class StandardScaler:
    def fit(self, X):
        self.mean = X.mean(axis=0)      # 按列计算均值
        self.std = X.std(axis=0)         # 按列计算标准差
    
    def transform(self, X):
        return (X - self.mean) / self.std  # Z-score标准化
```

### 4.2 MinMaxScaler

```python
class MinMaxScaler:
    def transform(self, X):
        return (X - self.min) / (self.max - self.min)  # 映射到[0,1]
```

---

## 实战示例

### 示例1：训练一个神经网络

```python
from smolml.core.ml_array import MLArray
from smolml.models.nn import DenseLayer, NeuralNetwork
from smolml.utils.activation import relu, softmax
from smolml.utils.losses import categorical_cross_entropy
from smolml.utils.optimizers import Adam

# 构建网络：输入4维 → 隐藏层8 → 隐藏层8 → 输出3类
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

# 准备数据（随机生成示例）
X = MLArray([[0.1, 0.2, 0.3, 0.4], [0.5, 0.6, 0.7, 0.8]])
y = MLArray([[1, 0, 0], [0, 1, 0]])

# 训练
losses = network.train(X, y, epochs=1000, verbose=True, print_every=100)
```

### 示例2：使用决策树分类

```python
from smolml.models.tree import DecisionTree

# 训练数据
X = MLArray([[1, 2], [2, 3], [3, 1], [4, 5], [5, 4]])
y = MLArray([0, 0, 0, 1, 1])

# 创建并训练
tree = DecisionTree(max_depth=3, task="classification")
tree.fit(X, y)

# 预测
predictions = tree.predict(MLArray([[1.5, 2.5]]))
print(predictions.to_list())  # [0]

# 可视化树结构
tree.show_tree(feature_names=["feature_0", "feature_1"])
```

### 示例3：K-Means聚类

```python
from smolml.models.unsupervised import KMeans
from smolml.preprocessing import MinMaxScaler

# 数据
X = MLArray([[1, 2], [1.5, 1.8], [5, 8], [8, 8], [1, 0.6], [9, 11]])

# 标准化
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# 聚类
kmeans = KMeans(n_clusters=2, max_iters=100, tol=1e-4)
labels = kmeans.fit_predict(X_scaled)

print(labels.to_list())  # [0, 0, 1, 1, 0, 1]
```

---

## 扩展开发指南

### 添加新的激活函数

在`smolml/utils/activation.py`中添加函数：

```python
def swish(x):
    """Swish: x * sigmoid(x)"""
    return x * sigmoid(x)
```

### 添加新的损失函数

在`smolml/utils/losses.py`中添加：

```python
def hinge_loss(y_pred, y_true, margin=1.0):
    """
    SVM风格铰链损失
    L = max(0, margin - y_true * y_pred)
    """
    diff = MLArray([margin]) - y_true * y_pred
    return (diff.relu()).mean()
```

### 添加新的优化器

在`smolml/utils/optimizers.py`中添加：

```python
class RMSProp(Optimizer):
    """
    RMSProp: θ = θ - (α / √(E[g²] + ε)) * g
    使用指数加权移动平均的梯度平方
    """
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

### 添加新模型

以添加简单的KNN（K近邻）为例：

```python
# smolml/models/knn/knn.py
from smolml.core.ml_array import MLArray

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
            # 计算与所有训练样本的距离
            distances = []
            for train_sample in self.X_train.data:
                diff = MLArray(train_sample) - MLArray(sample)
                dist = (diff * diff).sum().sqrt()
                distances.append((dist.data, self._get_label(train_sample)))
            
            # 找k个最近邻
            distances.sort(key=lambda x: x[0])
            k_nearest = [d[1] for d in distances[:self.k]]
            
            # 投票
            from collections import Counter
            prediction = Counter(k_nearest).most_common(1)[0][0]
            predictions.append(prediction)
        
        return MLArray(predictions)
    
    def _get_label(self, sample):
        # 根据样本索引从y_train获取标签
        pass  # 需要实现索引映射
```

---

## 设计哲学与局限性

### 设计亮点

1. **透明性**：每个操作都直接对应数学公式，无隐藏优化
2. **纯标准库**：仅用`math`、`random`、`collections`，无外部依赖
3. **完整计算图**：从标量自动微分扩展到多维数组，计算图完整保留
4. **模块化设计**：Core→Utils→Models分层清晰，易于扩展

### 性能局限

由于纯Python实现，SmolML存在固有的性能瓶颈：

```python
# 矩阵乘法是三层嵌套循环
for i in range(a.shape[0]):
    for j in range(b.shape[index_b]):
        result[i][j] = sum(a.data[i][k] * b.data[k][j] for k in range(a.shape[1]))
```

对比NumPy底层使用BLAS库（高度优化的C/Fortran代码），SmolML慢了**100-1000倍**。

### 使用场景

- ✅ 学习机器学习原理
- ✅ 理解反向传播细节
- ✅ 教学演示
- ❌ 大规模数据处理
- ❌ 生产环境部署

---

## 总结

SmolML用约2000行纯Python代码，构建了一个**完整但精简的机器学习框架**。其核心价值不在于替代NumPy/Scikit-learn，而在于**消除了机器学习的黑箱性质**。

通过阅读源码，你可以：
- 理解自动微分如何通过计算图和链式法则实现
- 掌握优化器（从SGD到Adam）的设计差异
- 深入理解神经网络前向传播与反向传播的完整流程
- 学会如何从头构建一个机器学习框架

项目地址：[https://github.com/rodmarkun/SmolML](https://github.com/rodmarkun/SmolML)

---

*本文所有代码和架构信息均来自SmolML项目源码（MIT许可证）。*