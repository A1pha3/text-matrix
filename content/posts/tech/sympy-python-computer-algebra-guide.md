---
title: "SymPy：纯 Python 符号计算系统"
date: "2026-04-12T02:31:39+08:00"
slug: sympy-python-computer-algebra-guide
github_repo: "sympy/sympy"
source_key: "gh:sympy/sympy"
description: "SymPy 是纯 Python 的符号计算系统，是科学 Python 生态的核心组成，用于数学、物理与工程中的符号推导。本文覆盖安装、表达式操作、微积分、方程求解、矩阵、数论、物理模块与代码生成，并标注与数值计算的边界。"
draft: false
categories: ["技术笔记"]
tags: ["Python"]
---

# SymPy：纯 Python 符号计算系统

## 为什么需要符号计算

解 `x + 1 = 2`，要的答案是 `x == 1` 这个精确解，而不是一个近似数。这种"带着未知量推导"的需求，就是符号计算（Symbolic Computation）存在的理由：它把表达式当作对象来化简、求导、积分、解方程，结果仍是精确的符号表达式。

NumPy 计算 `sqrt(2)` 得到 `1.414...`，SymPy 保留 `sqrt(2)` 本身；对它求导得到 `1/(2*sqrt(2))`，再代入某个值才会变成数字。分工一句话：**推导用 SymPy，算数用 NumPy/SciPy**——前者要精确与通用，后者要性能。

## 项目坐标

| 指标 | 数值 |
|------|------|
| Stars | 14.9k（2026-09 实测） |
| 贡献者 | 1,371（1.14 AUTHORS 清单） |
| 最新版本 | 1.14.0（2025-04-27） |
| 许可证 | New BSD |
| 依赖 | 纯 Python；运行时依赖 mpmath（任意精度浮点） |
| Python | ≥ 3.9 |

SymPy 由 Ondřej Čertík 创立于 2005 年，2007 年通过 Google Summer of Code 引入第一批学生贡献者，此后由社区持续维护至今。SageMath 也把它收作符号引擎之一。表中数据随时间变化，更新时以 GitHub 仓库、PyPI 和 AUTHORS 文件为准。

## 学习目标

读完本文，你应该能：

- 说清符号计算与数值计算的差别，以及各自的适用边界
- 安装 SymPy 并用表达式、微积分、方程、矩阵完成常见推导
- 用 `lambdify` 把符号表达式转成 NumPy 数值函数
- 知道物理模块、绘图、LaTeX 输出在哪里，能查文档继续深入

## 安装与验证

```bash
pip install sympy
# 或 conda（官方当前推荐写法）
conda install sympy
```

验证安装：

```python
>>> import sympy
>>> sympy.__version__
'1.14.0'
```

## 快速入门

### 表达式与化简

符号（Symbol）是表达式的原子，加减乘除和函数作用在其上构成表达式树：

```python
>>> from sympy import Symbol, cos, sin, expand, simplify, trigsimp

>>> x = Symbol('x')
>>> y = Symbol('y')

# 表达式创建与展开
>>> e = (x + y)**2
>>> e.expand()
x**2 + 2*x*y + y**2

# 恒等式化简
>>> trigsimp(sin(x)**2 + cos(x)**2)
1

# 通用化简
>>> simplify((x**2 + 2*x + 1)/(x + 1))
x + 1
```

注意 `simplify` 是启发式的，不同表达式化简效果差异很大；对三角函数用 `trigsimp`、对有理式用 `cancel`、对幂指函数用 `powsimp`，通常比 `simplify` 更可控。

### 微积分

```python
>>> from sympy import diff, integrate, limit, series, exp, oo

# 求导
>>> diff(x**3, x)
3*x**2

# 不定积分
>>> integrate(x**2, x)
x**3/3

# 定积分
>>> integrate(1, (x, 0, 1))
1

# 单侧极限
>>> limit(1/x, x, 0, dir='+')
oo

# 泰勒展开（O(x**10) 表示余项）
>>> series(exp(x), x, 0, 10)
1 + x + x**2/2 + x**3/6 + x**4/24 + x**5/120 + x**6/720 + x**7/5040 + x**8/40320 + x**9/362880 + O(x**10)
```

`limit` 的 `dir` 参数控制趋近方向：`'+'` 从右侧、`'-'` 从左侧，处理不连续点时二者结果可能不同。

### 方程求解

```python
>>> from sympy import solve, dsolve, Function

# 代数方程
>>> solve(x**2 - 4, x)
[-2, 2]

# 线性方程组
>>> solve([x + y - 2, x - y], [x, y])
{x: 1, y: 1}

# 常微分方程：f'(x) - f(x) = 0
>>> f = Function('f')
>>> dsolve(f(x).diff(x) - f(x), f(x))
Eq(f(x), C1*exp(x))
```

`dsolve` 的返回是 `Eq(左式, 右式)` 形式，`C1` 是待定常数。高阶、非线性或带初始条件的方程，先查 `dsolve` 的 `hint` 参数与文档中支持的类型表。

### 矩阵运算

```python
>>> from sympy import Matrix

>>> M = Matrix([[1, 2], [3, 4]])
>>> M.det()
-2
>>> M.inv()
Matrix([
[-2,   1],
[3/2, -1/2]])
>>> M.eigenvals()
{5/2 - sqrt(33)/2: 1, 5/2 + sqrt(33)/2: 1}
```

特征值以符号表达式给出，这正是符号计算的价值：不经过浮点近似，特征值可以直接是 `sqrt(33)` 的精确组合。

## 核心模块速查

| 函数 | 用法 | 说明 |
|------|------|------|
| `diff` | `diff(expr, x)` | 求导 |
| `integrate` | `integrate(expr, x)` | 积分 |
| `limit` | `limit(expr, x, x0)` | 极限 |
| `series` | `series(expr, x, x0, n)` | 泰勒展开 |
| `solve` | `solve(eq, x)` | 方程求解 |
| `factor` | `factor(expr)` | 因式分解 |
| `expand` | `expand(expr)` | 展开 |
| `simplify` | `simplify(expr)` | 化简 |
| `trigsimp` | `trigsimp(expr)` | 三角化简 |
| `cancel` | `cancel(expr)` | 有理式通分化简 |
| `subs` | `expr.subs(x, 2)` | 代入求值 |
| `lambdify` | `lambdify(x, expr)` | 转数值函数 |

## 高级功能

### LaTeX 输出

```python
>>> from sympy import latex, Integral

>>> latex(x**2 + cos(x))
x^{2} + \cos{\left(x \right)}
>>> latex(Integral(x**2, x))
\int x^{2}\, dx
>>> latex(Integral(x**2, (x, 0, 1)))
\int\limits_{0}^{1} x^{2}\, dx
```

生成的 LaTeX 可直接嵌入 Markdown 的 `$$` 公式块，或用于 Jupyter Notebook 的数学渲染。

### 代码生成

```python
>>> from sympy import lambdify, Symbol, sin, cos
>>> import numpy as np

>>> x = Symbol('x')
>>> expr = sin(x) + cos(x)

# 转成 NumPy 数值函数，支持向量化输入
>>> f = lambdify(x, expr, 'numpy')
>>> f(np.array([0, np.pi/2, np.pi]))
[ 1.  1. -1.]

# 用 mpmath 提供高精度
>>> import mpmath as mp
>>> f_mp = lambdify(x, x**2 + 2*x + 1, 'mpmath')
>>> f_mp(mp.mpf('0.5'))
2.25
```

`lambdify` 是符号与数值的分界线：推导阶段用符号，批量计算阶段把表达式编译成数值函数，避免逐次调用 `subs` 的 Python 层开销。

### 符号矩阵进阶

```python
>>> from sympy import Matrix, symbols

>>> a, b, c = symbols('a b c')
>>> M = Matrix([[a, b], [c, a]])

>>> M.charpoly()
PurePoly(lambda**2 - 2*a*lambda + a**2 - b*c, lambda, domain='ZZ[a,b,c]')

>>> M.eigenvects()
[(a - sqrt(b*c), 1, [Matrix([
[-a/c + (a - sqrt(b*c))/c],
[                       1]])]),
 (a + sqrt(b*c), 1, [Matrix([
[-a/c + (a + sqrt(b*c))/c],
[                       1]])])]
```

`eigenvects` 返回 `(特征值, 重数, 特征向量列表)` 的三元组列表，特征向量同样以符号形式给出。

### 数论

```python
>>> from sympy import isprime, prime, factorint, totient

>>> isprime(97)
True
>>> prime(100)   # 第 100 个素数
541
>>> factorint(123456)
{2: 6, 3: 1, 643: 1}
>>> totient(100)  # 欧拉函数
40
```

`isprime` 对 2^64 以内的数给出确定性结果，更大的数走强 BPSW 素性测试——理论上属于概率性判别，但目前没有已知反例；`prime` 背后是素数筛缓存，频繁取第 n 个素数时效率可接受。

## 物理模块

### 经典力学

动力学符号（dynamicsymbols）自动带上时间依赖，求导即为速度、加速度：

```python
>>> from sympy.physics.mechanics import dynamicsymbols

>>> q1 = dynamicsymbols('q1')
>>> q1
q1(t)
>>> q1.diff()   # 对时间求导
Derivative(q1(t), t)
```

完整的拉格朗日或牛顿方法在 `sympy.physics.mechanics` 下：`LagrangesMethod`、`Particle`、`ReferenceFrame` 等类把多体系统的方程搭建与求解封装起来，适合机器人学与刚体动力学。

### 量子力学

用玻色子算符示例对易关系：

```python
>>> from sympy.physics.quantum.boson import BosonOp
>>> from sympy.physics.quantum import Commutator

>>> ann = BosonOp('a')          # 湮灭算符
>>> cre = BosonOp('a', False)   # 产生算符
>>> Commutator(ann, cre).doit() # [a, a†] = 1
1
```

`BosonOp` 的构造参数第二个位置控制升/降算符。更复杂的态矢量、位置动量算符在 `sympy.physics.quantum` 下按模块组织，按需导入对应子模块。

## 绘图

```python
>>> from sympy import symbols, plot, sin, cos, exp, pi

>>> x = symbols('x')
>>> p1 = plot(sin(x), (x, -pi, pi))
>>> p2 = plot(sin(x), cos(x), exp(-x), (x, -2*pi, 2*pi))
>>> p2.save('plot.png')

# 需要定制轴标签时，关闭自动显示再接 Matplotlib
>>> p3 = plot(sin(x), (x, 0, 2*pi), show=False)
>>> p3.xlabel = 'x'
>>> p3.ylabel = 'sin(x)'
>>> p3.show()
```

3D 绘图用 `plot3d`，曲面、等高线、参数曲线分别有独立入口。绘图默认返回 `Plot` 对象，`save` 支持常见图片格式；在 Jupyter 中直接显示对象即可内联渲染。

## 性能边界与优化

SymPy 是纯 Python 实现，大型符号计算（如高阶多项式、复杂定积分）可能明显慢于 Mathematica 等原生 CAS。两条缓解路径：

1. **推导阶段**：优先化简到最小表达式再继续，避免表达式膨胀——`factor`/`cancel`/`trigsimp` 选对方向通常比 `simplify` 快。
2. **数值阶段**：用 `lambdify` 转成 NumPy/SciPy，或在 `numpy` 后端上批量向量化。

对超大规模数值计算，直接使用 NumPy/SciPy，符号层只负责离线推导公式。

## 常见问题

**SymPy 和 Mathematica / MATLAB 的符号工具箱相比如何？**

SymPy 免费开源，覆盖符号计算的绝大部分日常需求；Mathematica 在超大多项式、专业数学领域工具箱与整体性能上更强。对大多数教学与工程推导，SymPy 足够。

**可以在生产环境使用 SymPy 吗？**

可以，但注意性能边界。建议用 `lambdify` 把符号表达式转成数值函数投入运行，避免在生产路径上反复做符号推导；性能关键部分改用 NumPy/SciPy。

**为什么 `simplify` 结果和我预期不同？**

`simplify` 是启发式搜索，方向不对就返回原式。针对性使用 `trigsimp`（三角）、`cancel`（有理式）、`factor`（多项式）、`powsimp`（幂指）通常更可控。

**`subs` 和 `lambdify` 有什么区别？**

`subs` 做符号替换，每次返回新表达式，适合少量代入；`lambdify` 编译成数值函数，支持向量化与高性能批量计算。

## 引用

若在论文中使用 SymPy，官方建议引用：

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
