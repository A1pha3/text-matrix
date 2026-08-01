---
title: "SymPy：14.6K Stars·纯Python符号计算系统"
date: "2026-04-12T02:31:39+08:00"
slug: sympy-python-computer-algebra-guide
description: "SymPy 是一个纯 Python 符号计算系统，是科学 Python 生态系统的核心组成部分，广泛应用于数学、物理和工程领域。"
draft: false
categories: ["技术笔记"]
tags: ["Python"]
---

# SymPy：纯 Python 符号计算系统

SymPy 是一个纯 Python 编写的计算机代数系统（Computer Algebra System, CAS），用于符号数学计算。不依赖外部库，适合教学、科研和工程应用。

| 指标 | 数值 |
|------|------|
| Stars | 14.6k ⭐ |
| 贡献者 | 1,365 |
| 提交数 | 62,002 |
| 最新版本 | 1.14.0 (2025-04-28) |
| 许可证 | New BSD |

项目始于 2005 年，Ondřej Čertík 夏季开始编写代码。2007 年通过 GSoC 迎来 5 名学生贡献者，Pearu Peterson 重写核心后性能提升 10-100 倍。2011 年起由 Aaron Meurer 接手维护至今。

核心特性：纯 Python 无外部依赖、符号表达式操作与简化、求导/积分/极限、矩阵运算、方程/微分方程求解、物理模块（经典力学、量子力学）、LaTeX/ASCII/Unicode 输出。

## 安装

```bash
pip install sympy
# 或 conda
conda install -c anaconda sympy
```

验证安装：

```python
>>> import sympy
>>> sympy.__version__
'1.14.0'
```

## 快速入门

### 基础符号计算

```python
>>> from sympy import Symbol, cos, sin, exp, sqrt
>>> from sympy import integrate, diff, limit, series

>>> x = Symbol('x')
>>> y = Symbol('y')

# 表达式创建与展开
>>> e = (x + y)**2
>>> e
(x + y)**2
>>> e.expand()
x**2 + 2*x*y + y**2

# 三角函数化简
>>> cos(x)**2 + sin(x)**2
1
```

### 微积分

```python
>>> x = Symbol('x')

# 求导
>>> diff(x**3, x)
3*x**2

# 不定积分
>>> integrate(x**2, x)
x**3/3

# 定积分
>>> integrate(1, (x, 0, 1))
1

# 极限
>>> limit(1/x, x, 0, dir='+')
oo

# 泰勒展开
>>> series(exp(x), x, 0, 10)
1 + x + x**2/2 + x**3/6 + x**4/24 + x**5/120 + x**6/720 + x**7/5040 + x**8/40320 + x**9/362880 + O(x**10)
```

### 方程求解

```python
>>> from sympy import solve, solveset, dsolve, Function

>>> x, y = Symbol('x'), Symbol('y')

# 代数方程
>>> solve(x**2 - 4, x)
[-2, 2]

# 微分方程
>>> f = Function('f')
>>> dsolve(f(x).diff(x) - f(x), f(x))
f(x) == C1*e**x

# 方程组
>>> solve([x + y - 2, x - y - 0], [x, y])
{x: 1, y: 1}
```

### 矩阵运算

```python
>>> from sympy import Matrix

>>> M = Matrix([[1, 2], [3, 4]])
>>> M.det()
-2
>>> M.inv()
Matrix([
[ -2,   1],
[3/2, -1/2]])
>>> M.eigenvals()
{-2: 1, 3: 1}
>>> M * M
Matrix([
[ 7, 10],
[15, 22]])
```

## 核心模块

常用函数速查：

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
| `sympy.lambdify` | `lambdify(x, expr)` | 转数值函数 |

## 高级功能

### LaTeX 输出

```python
>>> from sympy import latex, Symbol, Integral
>>> x = Symbol('x')
>>> print(latex(x**2 + cos(x)))
x^{2} + \cos\left(x\right)
>>> print(latex(Integral(x**2, x)))
\int x^{2}\,dx
```

### 代码生成

```python
>>> from sympy import lambdify
>>> x = Symbol('x')
>>> expr = x**2 + 2*x + 1

# 转换为 NumPy 函数
>>> f = lambdify(x, expr, 'numpy')
>>> f(3)
16

# 使用 mpmath 高精度
>>> import mpmath as mp
>>> f_mp = lambdify(x, expr, 'mpmath')
>>> f_mp(mp.mpf('0.5'))
2.25
```

### 符号矩阵

```python
>>> from sympy import Matrix, symbols
>>> a, b, c = symbols('a b c')
>>> M = Matrix([[a, b], [c, a]])
>>> M.charpoly()
PurePoly(lambda**2 - 2*a*lambda + a**2 - b*c, lambda, domain='ZZ[a,b,c]')
>>> M.eigenvects()
[(a - sqrt(b*c), 1, [Matrix([[-b/(a - sqrt(b*c))], [1]])]),
 (a + sqrt(b*c), 1, [Matrix([[-b/(a + sqrt(b*c))], [1]])])]
```

### 数论

```python
>>> from sympy import isprime, prime, factorint, totient
>>> isprime(97)
True
>>> prime(100)
547
>>> factorint(123456)
{2: 6, 3: 1, 643: 1}
>>> totient(100)
40
```

## 物理模块

### 经典力学

```python
>>> from sympy.physics.mechanics import *
>>> from sympy import symbols, Function
>>> q1, q2 = dynamicsymbols('q1 q2')
>>> q1_d, q2_d = dynamicsymbols('q1 q2', 1)
>>> M = Matrix([[2, 0], [0, 2]])
>>> F = Matrix([[2*q2_d**2], [0]])
```

### 量子力学

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

## 绘图

```python
>>> from sympy import symbols, plot, sin, cos, exp, plot3d
>>> x = symbols('x')

# 2D 基础绘图
>>> p1 = plot(sin(x), (x, -pi, pi))
# 多函数
>>> p2 = plot(sin(x), cos(x), exp(-x), (x, -2*pi, 2*pi))
# 保存
>>> p2.save('plot.png')

# 3D 绘图
>>> x, y = symbols('x y')
>>> plot3d(x**2 + y**2, (x, -5, 5), (y, -5, 5))
```

## 性能优化

SymPy 是纯 Python 实现，性能不如 C/C++ 实现的专业 CAS（如 Mathematica）。但对于中小规模的符号计算，性能足够。大规模计算建议使用 NumPy/SciPy 进行数值计算，或使用 `lambdify()` 将符号表达式转为数值函数。

内置的自动简化和记忆化机制能有效减少重复计算：

```python
>>> from sympy import simplify, trigsimp, N, sqrt, pi

# 三角简化
>>> trigsimp(sin(x)**2 + cos(x)**2)
1
# 通用简化
>>> simplify((x**2 + 2*x + 1)/(x + 1))
x + 1

# 高精度数值计算
>>> N(sqrt(2))
1.41421356237310
>>> N(pi, dps=50)
3.1415926535897932384626433832795028841971693993751
```

## 与其他工具集成

```python
# NumPy/SciPy
>>> import numpy as np
>>> from sympy import lambdify
>>> x = Symbol('x')
>>> expr = sin(x) + cos(x)
>>> f = lambdify(x, expr, 'numpy')
>>> f(np.array([0, pi/2, pi]))
array([ 1.        ,  1.41421356,  -1.        ])

# Matplotlib
>>> import matplotlib.pyplot as plt
>>> p = plot(sin(x), (x, 0, 2*pi), show=False)
>>> p.xlabel = 'x'
>>> p.ylabel = 'sin(x)'
>>> p.show()

# LaTeX 文档嵌入
>>> from sympy import latex, Integral
>>> expr = Integral(x**2, (x, 0, 1))
>>> print(latex(expr))
\int_{0}^{1} x^{2}\,dx
```

## 常见问题

**SymPy 和 Mathematica/MATLAB 的符号计算工具箱相比如何？**

SymPy 是开源免费的，Mathematica/MATLAB 是商业软件。功能上 SymPy 覆盖了符号计算的大部分常见需求，但在大规模多项式计算、专业数学领域工具箱上可能不如商业软件。对大多数用户来说 SymPy 已经足够。

**可以在生产环境中使用 SymPy 吗？**

可以，但需要注意性能。建议用 `lambdify()` 将符号表达式转为数值函数，避免在生产中进行复杂的符号推导。性能关键部分考虑用 C/C++ 实现。

## 引用

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

## 资源

| 资源 | 链接 |
|------|------|
| 官网 | https://sympy.org |
| 文档 | https://docs.sympy.org |
| GitHub | https://github.com/sympy/sympy |
| 论文 | https://doi.org/10.7717/peerj-cs.103 |