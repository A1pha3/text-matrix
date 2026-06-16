---
title: "SymPy：14.6K Stars·纯Python符号计算系统"
date: "2026-04-12T02:31:39+08:00"
slug: sympy-python-computer-algebra-guide
description: "SymPy 是一个纯 Python 符号计算系统，是科学 Python 生态系统的核心组成部分，广泛应用于数学、物理和工程领域。"
draft: false
categories: ["技术笔记"]
tags: ["SymPy", "Python", "符号计算", "数学", "科学计算"]
---

# SymPy：14.6K Stars·纯 Python 符号计算系统·科学 Python 生态系统核心·数学/物理/工程

## 一，项目概述

### 1.1 SymPy 是什么

**SymPy** 是一个纯 Python 编写的计算机代数系统（Computer Algebra System, CAS），用于符号数学计算。

> "SymPy is an open-source computer algebra system written in pure Python."

不依赖外部库，适合教学、科研和工程应用。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **14.6k** ⭐ |
| Forks | 5.3k |
| Watchers | 287 |
| 贡献者 | **1,365** |
| 提交数 | **62,002** |
| 最新版本 | **1.14.0** (2025-04-28) |
| 许可证 | **New BSD** |
| 语言 | Python 98.7%, XSLT 1.3% |

### 1.3 项目起源

```
┌─────────────────────────────────────────────────────────────┐
│                    SymPy 发展历程                                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   2005年：项目启动                                             │
│   └── Ondřej Čertík 夏季开始编写代码                          │
│                                                               │
│   2006年：社区建设                                           │
│   └── Fabian Pedregosa 加入，帮助修复问题                       │
│                                                               │
│   2007年：GSoC 参与                                         │
│   └── 5名学生（Mateusz Paprocki等）贡献大量代码               │
│   └── Pearu Peterson 重写核心，性能提升10-100倍                │
│                                                               │
│   2011年：领导层交接                                          │
│   └── Aaron Meurer（曾是GSoC学生）接任lead developer          │
│                                                               │
│   至今：持续维护                                             │
│   └── 1,365位贡献者，62,000+提交                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 核心特性

| 特性 | 说明 |
|------|------|
| **纯 Python** | 无外部依赖，仅需 Python 标准库 |
| **符号计算** | 符号表达式、展开、简化、导数、积分 |
| **矩阵运算** | 矩阵运算、特征值、行列式 |
| **求解器** | 方程求解、微分方程求解 |
| **物理学** | 经典力学、量子力学、张量 |
| **打印** | LaTeX、ASCII、Unicode 数学符号 |

## 二，安装与配置

### 2.1 安装方式

```bash
# 方法一：pip 安装（推荐）
pip install sympy

# 方法二：conda 安装
conda install -c anaconda sympy

# 方法三：从源码安装
git clone https://github.com/sympy/sympy.git
cd sympy
pip install .
```

### 2.2 验证安装

```python
>>> import sympy
>>> sympy.__version__
'1.14.0'
```

### 2.3 交互式控制台

```bash
# 启动 SymPy 控制台（增强版Python交互环境）
$ bin/isympy

# 或直接使用 isympy 命令
$ isympy
```

## 三，快速入门

### 3.1 基础符号计算

```python
>>> from sympy import Symbol, cos, sin, exp, sqrt
>>> from sympy import integrate, differentiate, limit, series

# 定义符号
>>> x = Symbol('x')
>>> y = Symbol('y')

# 表达式创建
>>> e = (x + y)**2
>>> e
(x + y)**2

# 展开
>>> e.expand()
x**2 + 2*x*y + y**2

# 三角函数化简
>>> cos(x)**2 + sin(x)**2
1
```

### 3.2 微积分

```python
>>> x = Symbol('x')

# 求导
>>> diff(x**3, x)
3*x**2

# 不定积分
>>> integrate(x**2, x)
x**3/3

# 定积分
>>> integrate(0, (x, 0, 1))
1

# 极限
>>> limit(1/x, x, 0, dir='+')
oo

# 泰勒展开
>>> series(exp(x), x, 0, 10)
1 + x + x**2/2 + x**3/6 + x**4/24 + x**5/120 + x**6/720 + x**7/5040 + x**8/40320 + x**9/362880 + O(x**10)
```

### 3.3 方程求解

```python
>>> from sympy import solve, solveset

>>> x = Symbol('x')

# 代数方程求解
>>> solve(x**2 - 4, x)
[-2, 2]

# 微分方程求解
>>> f = Function('f')
>>> x = Symbol('x')
>>> dsolve(f(x).diff(x) - f(x), f(x))
f(x) == C1*e**x

# 求解方程组
>>> solve([x + y - 2, x - y - 0], [x, y])
{x: 1, y: 1}
```

### 3.4 矩阵运算

```python
>>> from sympy import Matrix

>>> M = Matrix([[1, 2], [3, 4]])
>>> M
Matrix([
[1, 2],
[3, 4]])

# 行列式
>>> M.det()
-2

# 逆矩阵
>>> M.inv()
Matrix([
[ -2,   1],
[3/2, -1/2]])

# 特征值
>>> M.eigenvals()
{-2: 1, 3: 1}

# 矩阵乘法
>>> M * M
Matrix([
[ 7, 10],
[15, 22]])
```

## 四，核心模块

### 4.1 模块结构

```
sympy/
├── algebra/              # 代数
│   ├── expr.py          # 表达式基类
│   └── exprtools.py     # 表达式工具
├── calculus/             # 微积分
│   ├── derivatives.py  # 求导
│   ├── integrals.py     # 积分
│   └── limits.py       # 极限
├── core/                # 核心
│   ├── add.py          # 加法
│   ├── mul.py          # 乘法
│   ├── power.py        # 幂
│   └── sympify.py      # 类型转换
├── functions/           # 数学函数
│   ├── elementary/     # 初等函数
│   ├── special/       # 特殊函数
│   └── combinatorial/ # 组合函数
├── geometry/            # 几何
│   ├── point.py       # 点
│   ├── line.py        # 直线
│   └── plane.py       # 平面
├── integrals/          # 积分
│   ├── manual.py      # 手动积分
│   └── risch.py       # Risch算法
├── matrices/           # 矩阵
│   ├── dense.py       # 稠密矩阵
│   └── sparse.py      # 稀疏矩阵
├── ntheory/            # 数论
│   ├── primetest.py   # 素数测试
│   └── factor_.py    # 因式分解
├── parsing/            # 解析
│   ├── latex.py       # LaTeX解析
│   └── maxima.py     # Maxima解析
├── physics/            # 物理
│   ├── hanoi.py       # 汉诺塔
│   ├── mechanics/     # 经典力学
│   └── quantum/       # 量子力学
├── plotting/           # 绘图
├── polys/              # 多项式
│   ├── polytools.py  # 多项式工具
│   ├── rationaltools.py # 有理式
│   └── rootoftools.py # 根
├── printing/           # 打印
│   ├── latex.py       # LaTeX输出
│   ├── mathml.py     # MathML输出
│   ├── pretty.py     # ASCII艺术
│   └── python.py     # Python代码
├── series/             # 级数
│   ├── gruntz.py     # 渐近展开
│   └── limits.py     # 序列极限
├── sets/               # 集合
│   ├── conditionset.py # 条件集
│   ├── fancysets.py  # 特殊集合
│   └── sets.py       # 基础集合
├── simplify/           # 化简
│   ├── powsimp.py   # 幂化简
│   ├── trigsimp.py  # 三角化简
│   └── simplify.py  # 一般化简
├── solvers/            # 求解器
│   ├──ode.py        # 常微分方程
│   ├── pde.py       # 偏微分方程
│   └── solvers.py   # 代数方程
└── utilities/
    ├── autowrap.py  # 自动包装
    ├── codegen.py   # 代码生成
    ├── lambdify.py # Lambda转换
    └── memoization.py # 记忆化
```

### 4.2 常用函数速查

| 模块 | 函数 | 说明 |
|------|------|------|
| `sympy.diff` | `diff(expr, x)` | 求导 |
| `sympy.integrate` | `integrate(expr, x)` | 积分 |
| `sympy.limit` | `limit(expr, x, x0)` | 极限 |
| `sympy.series` | `series(expr, x, x0, n)` | 泰勒展开 |
| `sympy.solve` | `solve(eq, x)` | 方程求解 |
| `sympy.factor` | `factor(expr)` | 因式分解 |
| `sympy.expand` | `expand(expr)` | 展开 |
| `sympy.simplify` | `simplify(expr)` | 化简 |
| `sympy.subs` | `subs(x, y)` | 替换 |
| `sympy.lambdify` | `lambdify(x, expr)` | 转 Lambda |

## 五，高级功能

### 5.1 LaTeX 输出

```python
>>> from sympy import latex, Symbol
>>> x = Symbol('x')
>>> print(latex(x**2 + cos(x)))
x^{2} + \cos\left(x\right)

>>> # 积分
>>> from sympy import Integral
>>> print(latex(Integral(x**2, x)))
\int x^{2}\,dx
```

### 5.2 代码生成

```python
>>> from sympy import lambdify
>>> x = Symbol('x')
>>> expr = x**2 + 2*x + 1

# 转换为NumPy函数
>>> f = lambdify(x, expr, 'numpy')
>>> f(3)
16

# 使用mpmath高精度
>>> import mpmath as mp
>>> f_mp = lambdify(x, expr, 'mpmath')
>>> f_mp(mp.mpf('0.5'))
2.25
```

### 5.3 符号矩阵

```python
>>> from sympy import Matrix, symbols, Function

>>> a, b, c = symbols('a b c')
>>> M = Matrix([[a, b], [c, a]])
>>> M
Matrix([
[a, b],
[c, a]])

>>> M.charpoly()
PurePoly(lambda**2 - 2*a*lambda + a**2 - b*c, lambda, domain='ZZ[a,b,c]')

>>> M.eigenvects()
[(a - sqrt(b*c), 1, [Matrix([
[-b/(a - sqrt(b*c))],
[                     1]])],
 (a + sqrt(b*c), 1, [Matrix([
[-b/(a + sqrt(b*c))],
[                     1]]))]
```

### 5.4 数论

```python
>>> from sympy import isprime, prime, factorint, totient

# 素数测试
>>> isprime(97)
True

# 第100个素数
>>> prime(100)
547

# 整数分解
>>> factorint(123456)
{2: 6, 3: 1, 643: 1}

# 欧拉函数
>>> totient(100)
40
```

## 六，物理模块

### 6.1 经典力学

```python
>>> from sympy.physics.mechanics import *
>>> from sympy import symbols, Function

>>> q1, q2 = dynamicsymbols('q1 q2')
>>> q1_d, q2_d = dynamicsymbols('q1 q2', 1)

>>> M = Matrix([[2, 0], [0, 2]])
>>> F = Matrix([[2*q2_d**2], [0]])

>>> M
Matrix([
[2, 0],
[0, 2]])

>>> F
Matrix([
[2*q2_d**2],
[      0]])
```

### 6.2 量子力学

```python
>>> from sympy.physics.quantum import *
>>> from sympy import symbols, I, hbar

>>> a = AnnihilationOperator('a')
>>> a_d = CreationOperator('a')

>>> a * a_d  # 不对易
I + a_d*a

>>> a_d * a  # 粒子数算符
a_d*a
```

## 七，绘图

### 7.1 2D 绘图

```python
>>> from sympy import symbols, plot, sin, cos, exp
>>> x = symbols('x')

# 基础绘图
>>> p1 = plot(sin(x), (x, -pi, pi))

# 多函数绘图
>>> p2 = plot(sin(x), cos(x), exp(-x), (x, -2*pi, 2*pi))

# 保存
>>> p2.save('plot.png')
```

### 7.2 3D 绘图

```python
>>> from sympy import symbols, plot3d
>>> x, y = symbols('x y')

>>> plot3d(x**2 + y**2, (x, -5, 5), (y, -5, 5))
```

## 八，性能优化

### 8.1 自动简化和记忆化

```python
>>> from sympy import simplify, trigsimp

# 三角简化
>>> trigsimp(sin(x)**2 + cos(x)**2)
1

# 通用简化
>>> simplify((x**2 + 2*x + 1)/(x + 1))
x + 1
```

### 8.2 数值计算

```python
>>> from sympy import N, sqrt, pi

# 数值计算
>>> N(sqrt(2))
1.41421356237310

>>> N(pi, dps=50)  # 50位精度
3.1415926535897932384626433832795028841971693993751
```

## 九，与其他工具集成

### 9.1 NumPy/SciPy

```python
>>> import numpy as np
>>> from sympy import lambdify

>>> x = Symbol('x')
>>> expr = sin(x) + cos(x)

>>> # 转NumPy函数
>>> f = lambdify(x, expr, 'numpy')
>>> f(np.array([0, pi/2, pi]))
array([ 1.        ,  1.41421356,  -1.        ])
```

### 9.2 Matplotlib

```python
>>> import matplotlib.pyplot as plt
>>> from sympy import plot

>>> p = plot(sin(x), (x, 0, 2*pi), show=False)
>>> p.xlabel = 'x'
>>> p.ylabel = 'sin(x)'
>>> p.show()
```

### 9.3 LaTeX 文档

```python
>>> from sympy import latex, Integral, Symbol

>>> x = Symbol('x')
>>> expr = Integral(x**2, (x, 0, 1))

>>> print(latex(expr))
\int_{0}^{1} x^{2}\,dx

>>> # 在Jupyter中显示
>>> expr  # 自动渲染为LaTeX
```

## 十，贡献指南

### 10.1 开发环境搭建

```bash
# 克隆仓库
git clone https://github.com/sympy/sympy.git
cd sympy

# 安装开发依赖
pip install -r requirements-dev.txt

# 以开发模式安装
pip install -e .

# 运行测试
./setup.py test

# 运行特定测试
bin/test sympy/core/tests/test_arit.py
```

### 10.2 贡献流程

```
┌─────────────────────────────────────────────────────────────┐
│                    SymPy 贡献流程                                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   1. Fork 仓库到自己的GitHub账号                              │
│                                                               │
│   2. 克隆到本地                                              │
│      git clone https://github.com/YOUR_NAME/sympy.git         │
│                                                               │
│   3. 创建功能分支                                            │
│      git checkout -b my-feature                                 │
│                                                               │
│   4. 编写代码并测试                                          │
│      ./setup.py test                                           │
│                                                               │
│   5. 提交并推送到你的Fork                                     │
│      git commit -m "Add: my feature"                          │
│      git push origin my-feature                                 │
│                                                               │
│   6. 在GitHub上创建Pull Request                               │
│                                                               │
│   7. 等待代码审查和合并                                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 10.3 寻找入门任务

推荐从以下标签的任务开始：
- **Easy to Fix** - 适合新手
- **Up for Grabs** - 没有特定 assignee

## 十一，引用

### 11.1 论文引用

```bibtex
@article{meurer2017sympy,
  title={SymPy: symbolic computing in Python},
  author={Meurer, Aaron and Smith, Christopher P and Paprocki, Mateusz
           and {\v{C}}ert{\'i}k, Ond{\v{r}}ej and Kirpichev, Sergey B
           and Rocklin, Matthew and Kumar, Amit and Ivanov, Sergiu
           and Moore, Jason K and Singh, Sartaj and Rathnayake, Thilina
           and Vig, Sean and Granger, Brian E and Muller, Richard P
           and Bonazzi, Francesco and Gupta, Harsh and Vats, Shivam
           and Johansson, Fredrik and Pedregosa, Fabian and Curry, Matthew J
           and Terrel, Andy R and Rou{\v{c}}ka, {\v{S}}t{\v{e}}p{\'a}n
           and Saboo, Ashutosh and Fernando, Isuru and Kulal, Sumith
           and Cimrman, Robert and Scopatz, Anthony},
  journal={PeerJ Computer Science},
  volume={3},
  pages={e103},
  year={2017}
}
```

### 11.2 在线资源

| 资源 | 链接 |
|------|------|
| **官网** | https://sympy.org |
| **文档** | https://docs.sympy.org |
| **GitHub** | https://github.com/sympy/sympy |
| **讨论区** | https://groups.google.com/forum/#!forum/sympy |
| **Gitter** | https://gitter.im/sympy/sympy |

## 十二，总结

SymPy 是纯 Python 符号计算项目：

| 维度 | 说明 |
|------|------|
| 纯 Python | 无外部依赖，易于部署 |
| 符号计算 | 导数、积分、极限、方程求解 |
| 矩阵运算 | 特征值、行列式、矩阵分解 |
| 物理学 | 经典力学、量子力学模块 |
| 高性能 | 自动简化、记忆化优化 |
| 易集成 | NumPy、SciPy、Matplotlib |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| 官网 | https://sympy.org |
| 文档 | https://docs.sympy.org |
| GitHub | https://github.com/sympy/sympy |
| 论文 | https://doi.org/10.7717/peerj-cs.103 |

---

_🦞 本文由钳岳星君撰写，基于 SymPy (14.6k Stars)_
