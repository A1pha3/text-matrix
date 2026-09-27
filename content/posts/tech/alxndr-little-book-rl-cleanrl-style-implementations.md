---
title: "The Little Book of RL：从零到 PPO 的 CleanRL 风格实现解析"
date: 2026-07-15T21:27:31+08:00
lastmod: 2026-09-27T00:00:00+08:00
draft: false
slug: alxndr-little-book-rl-cleanrl-style-implementations
github_repo: "alxndrTL/little-book-rl"
source_key: "gh:alxndrTL/little-book-rl"
description: "alxndrTL/little-book-rl 仓库深度拆解——一本配套 PyTorch 实现的小型强化学习书，覆盖 MC / SARSA / Q-learning / n-step SARSA / SARSA(λ) / DQN / REINFORCE / VPG / SPG / PPO 全套 10 个算法。"
categories: ["技术笔记"]
tags: ["强化学习", "PyTorch", "Python", "开源"]
---

# The Little Book of RL：从零到 PPO 的 CleanRL 风格实现解析

> 仓库：[alxndrTL/little-book-rl](https://github.com/alxndrTL/little-book-rl)
> 配套书 PDF：[book.pdf](https://github.com/alxndrTL/little-book-rl/blob/main/book.pdf) — 约 20MB / V1 (June 2026)
> 作者：Alexandre Torres Leguet（[alxndrTL](https://github.com/alxndrTL)）/ 约 1.6k stars / 书以 CC BY-SA 4.0（非商业）分发
> 配套实现：6 个 Python 文件，约 65KB，覆盖 10 个 RL 算法

这是一本短小但完整的强化学习入门书，加一份"教学优先"的 PyTorch 实现。README 里的自我定位是"从基础到应用算法的 RL 入门"，代码则把书里讲到的算法逐一实现了一遍——两个部分一一对应，这是它和大多数"只有书"或"只有代码"的 RL 资源最大的不同。

下面按实现层把它拆开看。

---

## 一、整体结构

仓库内容分四块：

| 路径 | 内容 | 用途 |
|---|---|---|
| `book.pdf` | 书的主文件 | 约 20MB 完整正文（V1 June 2026） |
| `algos/value_based/` | 基于价值函数的方法 | tabular.py + dqn.py |
| `algos/policy_based/` | 基于策略梯度的方法 | reinforce.py + spg.py + vpg.py + ppo.py |
| `supplementary/` | 动态规划的严格证明 | 2021 年写的补充材料 |

（另有 `assets/` 存放封面海报，无代码。）

配套实现覆盖 10 个算法：

```text
tabular  : MC, SARSA, Q-learning, n-step SARSA, SARSA(λ)   (5)
value    : DQN                                             (1)
policy   : REINFORCE, VPG, SPG, PPO                        (4)
```

代码停在了 PPO：A2C / SAC / TD3 / DDPG 和 model-based 算法都没有实现。这不是偷懒——书的结尾有一节 "What this book does not cover"，把这些方向连同 offline RL、multi-agent、hierarchical RL 一起列为存而不论，第 5、6 章只做概念级展开（RL×LLMs 与 AlphaGo Zero），不再配代码。

---

## 二、tabular.py：一个文件覆盖 5 个 tabular 算法

这是仓库里教学密度最高的文件——MC、SARSA、Q-learning、n-step SARSA、SARSA(λ)，五个算法全在一个 341 行的 Python 文件里，靠一个 `--algo` 参数切换。

### 2.1 用 tyro 做 CLI（不是 argparse）

```python
from dataclasses import dataclass
import tyro

@dataclass
class Args:
    algo: Literal["mc", "sarsa", "q_learning", "n_step_sarsa", "sarsa_lambda"] = "q_learning"
    n_step: int = 4
    lambda_: float = 0.9
    trace_type: Literal["accumulating", "replacing"] = "replacing"
```

（节选；完整 Args 还有 env_id、total_timesteps、学习率、ε 调度、评估频率等字段。）每个字段下面的 docstring 会被 tyro 自动生成进 `--help`。这是 CleanRL 风格的起点：用 `tyro` 替代 `argparse`，让 dataclass 直接当 CLI schema，超参数、默认值、文档写在一处。

### 2.2 5 个算法的核心 update 对比

每个算法一个 `run_episode_*` 函数。把它们放一起看更新公式：

| 算法 | Target | 更新 |
|---|---|---|
| **MC** | $G_t = \sum_{k=t}^{T-1} \gamma^{k-t} r_k$ | $Q[s,a] \mathrel{+}= \alpha (G_t - Q[s,a])$ |
| **SARSA** | $r + \gamma Q[s',a']$ | $Q[s,a] \mathrel{+}= \alpha (r + \gamma Q[s',a'] - Q[s,a])$ |
| **Q-learning** | $r + \gamma \max_{a'} Q[s',a']$ | $Q[s,a] \mathrel{+}= \alpha (r + \gamma \max Q[s',a'] - Q[s,a])$ |
| **n-step SARSA** | $\sum_{j=\tau}^{\tau+n-1} \gamma^{j-\tau} r_j + \gamma^n Q[s_{\tau+n}, a_{\tau+n}]$ | 同上模板 |
| **SARSA(λ)** | TD error $\delta = r + \gamma Q[s',a'] - Q[s,a]$ | $Q \mathrel{+}= \alpha \delta E$, $E \mathrel{*}= \gamma \lambda$ |

五个算法共享同一个 update 模板：算出 target 或 TD error，乘学习率，写回 Q 表。把公式并排放，能直接看出 tabular RL 算法为什么这么少——它们本质是一个模板的不同填空，差别只在 target 怎么取：整条回报（MC）、单步 bootstrap（SARSA / Q-learning）、n 步折中（n-step），或者用 eligibility trace 把 TD error 广播到整张表（SARSA(λ)）。

### 2.3 SARSA(λ) 的 eligibility trace 实现

```python
def run_episode_sarsa_lambda(env, Q, E, args, eps, rng):
    E.fill(0.0)
    s, _ = env.reset()
    a = epsilon_greedy(Q, s, eps, n_actions, rng)
    while True:
        s_next, r, term, trunc, _ = env.step(a)
        if term or trunc:
            delta = r - Q[s, a]
            a_next = None
        else:
            a_next = epsilon_greedy(Q, s_next, eps, n_actions, rng)
            delta = r + args.gamma * Q[s_next, a_next] - Q[s, a]

        if args.trace_type == "accumulating":
            E[s, a] += 1.0
        else:
            E[s, a] = 1.0

        Q += args.learning_rate * delta * E
        E *= args.gamma * args.lambda_

        if term or trunc:
            break
        s, a = s_next, a_next
```

源码 docstring 标明这是 Sutton & Barto §12.7 的 1-for-1 实现。两个关键点：

1. eligibility trace $E[s,a]$ 与 $Q[s,a]$ 同 shape，每次访问按 `trace_type` 累加（accumulating）或覆盖（replacing），默认 replacing。
2. TD error $\delta$ 算出来后乘 $E$ 广播到整张 Q 表：`Q += alpha * delta * E`——所有最近访问过的 state-action 都会被更新，强度按 trace 衰减。这一步是 SARSA(λ) 与 SARSA 的分水岭：前者一次更新影响一条历史，后者只动当前这对 state-action。

### 2.4 epsilon schedule 用线性衰减

```python
def linear_schedule(start_e: float, end_e: float, duration: float, t: int) -> float:
    slope = (end_e - start_e) / duration
    return max(end_e, start_e + slope * t)
```

与 CleanRL DQN 相同的 ε 线性衰减（源码注释原话 "linear ε schedule, like CleanRL DQN"）：`start_e=1.0` 衰减到 `end_e=0.05`，`exploration_fraction=0.5` 表示在前一半训练步里衰减完。

---

## 三、policy_based/：4 个策略梯度算法

### 3.1 REINFORCE（reward-to-go 策略梯度）

```python
def reward_to_go(rewards, gamma):
    """G_t = sum_{k=t}^{T-1} gamma^{k-t} r_k (computed backward)"""
    G = np.zeros(len(rewards), dtype=np.float32)
    running = 0.0
    for t in reversed(range(len(rewards))):
        running = rewards[t] + gamma * running
        G[t] = running
    return G
```

从后往前累计 reward-to-go，把每个时间步的折扣回报算成 O(n)——正向逐点算是 O(n²)。然后是梯度步：

```python
# g_hat = (1/N) * sum_i sum_t G_t^i * grad log pi(a_t^i | s_t^i)
log_probs = agent.log_prob(batch_obs, batch_actions)
loss = -(batch_G * log_probs).sum() / args.num_trajectories
```

注意负号——optimizer 只能做 minimize，所以"最大化期望回报"写成"最小化负期望回报"。

#### Agent 类（无 critic）

```python
class Agent(nn.Module):
    def __init__(self, envs):
        super().__init__()
        self.actor = nn.Sequential(
            layer_init(nn.Linear(np.array(envs.single_observation_space.shape).prod(), 64)),
            nn.Tanh(),
            layer_init(nn.Linear(64, 64)),
            nn.Tanh(),
            layer_init(nn.Linear(64, envs.single_action_space.n), std=0.01),
        )

    def get_action(self, x):
        logits = self.actor(x)
        return Categorical(logits=logits).sample()
```

没有 critic，纯 actor-only——这是 REINFORCE 的标志，源码 docstring 也写着 "No critic — only the policy network pi_theta."。输出层 `std=0.01` 的小初始化让初始 logits 接近 0，策略接近均匀分布；初始策略熵太低的话，早期梯度会把策略迅速推向次优动作。

### 3.2 PPO（policy_based 里最复杂的文件）

PPO 文件 332 行，是 policy_based 目录里最长的（tabular.py 341 行是全仓库最长）。它的 docstring 把"书里没讲但实现里要做的事"全部列了出来：

```python
"""
Proximal Policy Optimization (PPO) as described in the book.
copied here for the sake of completeness, original code at: https://github.com/vwxyzjn/cleanrl/

Few implementation details not described in the book:
- collection is done with a fixed number of steps per environment, instead of a fixed number of complete trajectories (discussed in the book)
- specific initialization scheme for the policy network weights
- vectorized environment interaction (allows to collect multiple trajectories in parallel)
- Adam optimizer instead of gradient descent
- GAE (explained in the book) for both policy and critic updates
- multiple critic epochs per iteration
- advantage normalization, very common
- LR annealing
- only one loss is optimized (so one global LR), which is the sum of: policy loss, value loss, entropy loss
  we thus have ent_coef and vf_coef to weight 2 of the 3 losses in the final loss
- entropy loss penalizes low entropy policies, thus encourages exploration
- value loss is a clipped version of the value loss in the book, similar to PPO. (clip_vf)
- grad norm clipping, common in supervised learning (max_grad_norm)
- early stop the current update if the KL divergence between new and old policies exceeds a threshold (target_kl)
"""
```

这段注释是全仓库对学习者最值钱的部分——它把"理论 → 工程"的 gap 逐条标了出来。第一行也交代了血统：这份 PPO 直接来自 CleanRL。读这本书的 PPO 实现，等于读 CleanRL 的 PPO 实现，再加一份书里的理论对照。

### 3.3 PPO 的关键工程组件（仓库里的实现）

#### A. Agent 类（actor + critic）

```python
class Agent(nn.Module):
    def __init__(self, envs):
        super().__init__()
        self.critic = nn.Sequential(
            layer_init(nn.Linear(np.array(envs.single_observation_space.shape).prod(), 64)),
            nn.Tanh(),
            layer_init(nn.Linear(64, 64)),
            nn.Tanh(),
            layer_init(nn.Linear(64, 1), std=1.0),
        )
        self.actor = nn.Sequential(
            layer_init(nn.Linear(np.array(envs.single_observation_space.shape).prod(), 64)),
            nn.Tanh(),
            layer_init(nn.Linear(64, 64)),
            nn.Tanh(),
            layer_init(nn.Linear(64, envs.single_action_space.n), std=0.01),
        )

    def get_action_and_value(self, x, action=None):
        logits = self.actor(x)
        probs = Categorical(logits=logits)
        if action is None:
            action = probs.sample()
        return action, probs.log_prob(action), probs.entropy(), self.critic(x)
```

两点值得留意：

- 输出层的初始化方差是刻意设计：actor 输出层 `std=0.01`、critic 输出层 `std=1.0`，都小于 `layer_init` 默认的 √2（正交初始化）。actor 的 logits 从接近 0 开始，初始策略接近均匀分布；critic 的初始 value 幅度小，训练初期不会给出离谱的回报预测。
- `get_action_and_value` 一次 forward 同时返回 action、log_prob、entropy、value 四样，采样和更新两个阶段共用这一个入口。

#### B. 核心 PPO 损失（论文原版）

```python
_, newlogprob, entropy, newvalue = agent.get_action_and_value(b_obs[mb_inds], b_actions.long()[mb_inds])
logratio = newlogprob - b_logprobs[mb_inds]
ratio = logratio.exp()

mb_advantages = b_advantages[mb_inds]
if args.norm_adv:
    mb_advantages = (mb_advantages - mb_advantages.mean()) / (mb_advantages.std() + 1e-8)

# unclipped
pg_loss1 = -mb_advantages * ratio
# clipped
pg_loss2 = -mb_advantages * torch.clamp(ratio, 1 - args.clip_coef, 1 + args.clip_coef)
pg_loss = torch.max(pg_loss1, pg_loss2).mean()
```

`clip_coef=0.2` 沿用 PPO 论文默认。`torch.max(pg_loss1, pg_loss2)` 对应论文里对 surrogate 目标取 min 的悲观形式，效果是单向截断：当某条样本的 ratio 冲出 $[1-\varepsilon, 1+\varepsilon]$、且冲出的方向正在兑现优势时，clipped 项在这个方向上梯度为零，策略不再被鼓励继续往外走；而 ratio 朝"变差"方向偏离时梯度仍然保留，把策略拉回区间。信任区域就是这么落地的。

#### C. Value loss（clipped 版）

```python
# Value loss
newvalue = newvalue.view(-1)
if args.clip_vloss:
    v_loss_unclipped = (newvalue - b_returns[mb_inds]) ** 2
    v_clipped = b_values[mb_inds] + torch.clamp(
        newvalue - b_values[mb_inds],
        -args.clip_coef,
        args.clip_coef,
    )
    v_loss_clipped = (v_clipped - b_returns[mb_inds]) ** 2
    v_loss_max = torch.max(v_loss_unclipped, v_loss_clipped)
    v_loss = 0.5 * v_loss_max.mean()
else:
    v_loss = 0.5 * ((newvalue - b_returns[mb_inds]) ** 2).mean()
```

value 的 clipping 思路与 policy 同构，但截断的不是 ratio 本身，而是新 value 相对旧 value 的偏移量（`torch.clamp(newvalue - b_values, ±clip_coef)`）：critic 单次更新最多移动 `clip_coef`，防止回报信号一乐观、value 函数就跟着飞。`clip_vloss=True` 是论文原始设定。

#### D. GAE（Generalized Advantage Estimation）

PPO docstring 说 GAE "explained in the book"。仓库代码里的 GAE 计算：

```python
with torch.no_grad():
    advantages = torch.zeros_like(rewards).to(device)
    lastgaelam = 0
    for t in reversed(range(args.num_steps)):
        if t == args.num_steps - 1:
            nextnonterminal = 1.0 - next_done
            nextvalues = next_value
        else:
            nextnonterminal = 1.0 - dones[t + 1]
            nextvalues = values[t + 1]
        delta = rewards[t] + args.gamma * nextvalues * nextnonterminal - values[t]
        advantages[t] = lastgaelam = delta + args.gamma * args.gae_lambda * nextnonterminal * lastgaelam
    returns = advantages + values
```

GAE(λ) 把不同步数的 advantage 估计按 $\gamma\lambda$ 做指数加权：λ 小偏向单步 TD（低方差、高偏差），λ 大偏向整条 Monte Carlo 回报（高方差、低偏差），`gae_lambda=0.95` 是常用的折中。注意整个计算在 `torch.no_grad()` 下、且发生在 epoch 循环之前——advantage 每轮采样只算一次，后面复用。

### 3.4 与 CleanRL 的关系

PPO 文件开头写明：

> copied here for the sake of completeness, original code at: https://github.com/vwxyzjn/cleanrl/

这份 PPO 实现是 CleanRL 的逐字移植。两个由此而来、值得记住的事实：

1. CleanRL 的范式是单文件、可执行、超参数即文档，tensorboard / wandb 集成开箱即用——"教学优先"和"工程正确"在它这里不冲突。
2. Little Book of RL 直接以 CleanRL 为实现参考，而不是自己另写一套教学代码。对入门者这是个低成本的选择：读完书里的公式，再去读工业界真实在用的那份代码，中间没有第二套方言。

### 3.5 一次 update 里数据怎么流（以 ppo.py 为例）

把 PPO 的一次更新拆成数据视角，共 6 步：

1. **采样**：`num_envs=4` 个 CartPole 并行跑 `num_steps=128` 步，每个 (env, step) 存下 obs / action / logprob / reward / done / value，得到一个 `(128, 4)` 的 batch（512 条经验）。
2. **GAE 回溯**：从最后一步倒着算 `delta = r + γ·V(s') − V(s)`，再累积 `lastgaelam = delta + γ·λ·lastgaelam`，得到每条经验的 advantage；returns = advantage + value。
3. **展平 + 打乱**：把 `(128, 4)` 展平成 512 条，`num_minibatches=4` 切出 4 个 minibatch，每个 128 条。
4. **K epoch 更新**：对每个 minibatch 跑 4 个 epoch（`update_epochs=4`），每次用当前策略重算 `logratio = logprob_new − logprob_old`，`ratio = exp(logratio)`。
5. **三损失加权**：`loss = pg_loss − ent_coef·entropy + vf_coef·value_loss`，`backward()` 后 `clip_grad_norm_(0.5)` 再 `optimizer.step()`。
6. **早停判定**：`approx_kl > target_kl` 就 break 当前 update，进入下一轮采样（`target_kl` 默认为 None，即默认不启用）。

这条链路里最容易看漏的一点：同一个 rollout 会被复用 4 个 epoch，但 advantage 只在采样后算一次，不再重算——advantage 的"新鲜度"完全押在 ratio 还没偏离太远这个假设上，clip 和早停都是为这个假设兜底的。

---

## 四、10 个算法的演进关系

把仓库里 10 个算法按理论血缘排成两条线：

```text
价值线（value_based/）                策略线（policy_based/）
──────────────────────               ──────────────────────
MC            整条回报，无 bootstrap    SPG        整条回报，actor-only
SARSA         单步 on-policy TD        REINFORCE  reward-to-go，actor-only
Q-learning    单步 off-policy max      VPG        critic 做 baseline（+可选 GAE）
n-step SARSA  n 步 target              PPO        clip 目标 + GAE + critic
SARSA(λ)      eligibility trace
DQN           Q-learning + 神经网络 + replay buffer + target network
```

对应关系：

- tabular 五算法共享 update 模板（第二节那张表的五种 target）。
- 策略线四个算法按 actor-only → actor-critic 递进：SPG 一条 trajectory 共用一个折扣回报，REINFORCE 换成逐时间步的 reward-to-go，VPG 加上 critic 做 baseline（默认 advantage 是 $G_t - V(s_t)$，GAE 是 `use_gae` 开关），PPO 再叠加 clip 目标。
- DQN 是 Q-learning 的非线性推广：同一套 update 公式，Q 表换成神经网络，加上 experience replay 和 target network 稳住训练。
- PPO 相对 VPG 加的是约束（clipped surrogate），相对 REINFORCE 加的是 critic 和数据复用。

两条线各自走到头，正好拼出现代 RL 实践的主干：价值线通向 DQN 一族，策略线通向 PPO——后者正是 RLHF 训练大语言模型所用的算法，书第 5 章接的 GRPO 就是它的变体。

---

## 五、这本书没讲、但代码里绕不开的工程细节

仓库代码和注释暴露了几个 RL 入门书一般不讲、工程上却必踩的点：

### 5.1 初始化方差

```python
layer_init(nn.Linear(64, envs.single_action_space.n), std=0.01)
```

`layer_init` 底下是 `torch.nn.init.orthogonal_`（正交初始化，CleanRL 从惯例实现里继承的标准件），actor 输出层 `std=0.01`、critic 输出层 `std=1.0`，都小于默认的 √2。actor 的初始 logits 接近 0，初始策略接近均匀分布，避免训练一开始就 collapse 到低熵；critic 的初始 value 幅度小，回归目标不会从离谱的起点开始。

### 5.2 vectorized env

所有 policy-based 文件都用 `gym.vector.SyncVectorEnv` 并行采样。论文里通常一句 "parallel rollout" 带过，工程上却是 PPO 的默认打法：单 env 逐条采样时 rollout 阶段会成为瓶颈，数据也喂不满 minibatch。

### 5.3 步数 vs trajectory 计数

PPO docstring 明确说：

> collection is done with a fixed number of steps per environment, instead of a fixed number of complete trajectories (discussed in the book)

REINFORCE 按 `num_trajectories`（固定 trajectory 数）收集，PPO 按 `num_steps`（固定步数）收集。这是 on-policy 算法的一个工程分叉：episode 长度稳定时按条数收最干净，长度方差大或很长时按步数收才能保证每轮数据量可预测。REINFORCE 的实现里还能看到按条数收的现实代价——4 个并行 env 收满 16 条 trajectory 后，多余的半截 episode 要 trim 掉。

### 5.4 entropy bonus

PPO docstring：

> entropy loss penalizes low entropy policies, thus encourages exploration

`ent_coef=0.01` 是熵正则的权重——给策略加一项"别太确定"的奖励。没有它，策略梯度在收敛后期很容易 collapse 到 greedy policy，探索就此停摆。

### 5.5 LR annealing + grad clip

PPO 用 `anneal_lr=True`（学习率随训练线性衰减）和 `max_grad_norm=0.5`（梯度范数截断）。这两个不是 PPO 论文的硬性要求，但在长训练里是防止后期震荡的工程保险。

### 5.6 target_kl 早停

```python
if args.target_kl is not None and approx_kl > args.target_kl:
    break
```

新旧策略的 KL 散度超过 `target_kl` 就提前终止当前 update——PPO "trust region" 思想的直接落地。注意 `target_kl` 默认为 None，即这个保险默认是关着的；CleanRL 的经验是 clip 本身已经够用，早停作为可选的更严格约束存在。

---

## 六、这本书的局限（写给认真学 RL 的人）

书在结尾 "What this book does not cover" 一节自己列了清单，下面用实现层的视角过一遍：

### 6.1 没有连续动作空间

全部代码假设 `gym.spaces.Discrete`，用 `Categorical` 分布，`ppo.py` 还用 assert 锁死了离散动作空间。书 3.1 的 Remark 提到连续状态可以离散化或交给函数逼近器，4.1 也点明策略网络输出高斯分布的均值和方差就能处理连续动作，但配套代码没有实现这一块——SAC / TD3 / DDPG 一族在 does not cover 清单里。做 robotics 或自动控制的读者需要另找材料。

### 6.2 没有 model-based 算法实现

书第 6 章用 AlphaGo Zero 讲了 model-based 思路——原文写它 "can be seen as a form of policy iteration coupled with a model-based approach"，improvement 步是 "a modified version of an MCTS rollout"。但仓库 6 个代码文件里没有 model-based 实现，MCTS、世界模型、Dreamer 都停在纸面。

### 6.3 没有 multi-agent / hierarchical

multi-agent RL 和 hierarchical RL（Options / Feudal Networks）只出现在 does not cover 清单里。第 6 章 AlphaGo Zero 借 self-play 触及了双人零和完全信息博弈，但一般化的 multi-agent 框架没有展开——这恰是工业 RL（推荐系统、运筹优化）常见的形态。

### 6.4 没有 offline RL / imitation learning

offline RL 在清单里（CQL / IQL / behavior cloning baselines）。唯一沾边的是第 6 章 AlphaGo Zero 的 evaluation 步：把搜索改进后的策略蒸馏回 base policy 用的正是 behavior cloning / SFT（书里还配了 System 1 / System 2 的比喻）。固定数据集、不与环境交互的完整框架仍然空缺。

### 6.5 PPO 的复现性陷阱

PPO 文件 332 行，但跑出论文数字需要大量调参。仓库的复现范围只有 CartPole-v1 这个量级的 toy env，Atari / MuJoCo 数字不在范围内——想用它跑 HalfCheetah 是不现实的。

---

## 七、读这本书的最佳顺序

书分三部分 6 章：Part I Foundations（第 1-2 章，RL 是什么、怎么做）、Part II Diving deeper（第 3 章 value functions、第 4 章 policy optimization）、Part III RL at scale（第 5 章 RL×LLMs、第 6 章 AlphaGo Zero）。

建议的读法：

1. **第 1-2 章**（交互环、三类方法）→ 快速过，建立全局视角。
2. **第 3 章**（DP / MC / SARSA / Q-learning，3.8 进神经网络）→ 对照 `tabular.py` 读完，再读 `dqn.py`。
3. **第 4 章**（4.2 SPG / REINFORCE / VPG / GAE，4.3 trust region + PPO）→ 对照 `spg.py` + `reinforce.py` + `vpg.py` + `ppo.py`。
4. **第 5-6 章**（GRPO、AlphaGo Zero）→ 概念级阅读，仓库没有对应实现。
5. `supplementary/` 是 DP 的严格证明，理论派必读，工程派可跳。

每章读完直接跑代码。依赖需要自己装（PyTorch、gymnasium、numpy、tyro、tensorboard，DQN 还额外依赖 cleanrl 的 buffer 工具）：

```bash
pip install torch gymnasium numpy tyro tensorboard

cd algos/value_based
python tabular.py --algo q_learning --env_id FrozenLake-v1

cd ../../algos/policy_based
python reinforce.py --env_id CartPole-v1
python ppo.py --env_id CartPole-v1
```

tensorboard 起来后能看到 return 曲线，对照书里说"应该长什么样"。

---

## 八、为什么这本书值得读

**比起 Sutton & Barto**：后者是 RL 圣经，但没有配套 PyTorch 实现，理论到代码之间隔着一条读者自己搭的桥。Little Book of RL 的每个章节都有对应代码文件，理论和实现 1:1。

**比起 Spinning Up**：OpenAI Spinning Up 也是教学向，代码覆盖 VPG / TRPO / PPO / DDPG / SAC / TD3，但起点就是深度 RL，没有 tabular 部分。Little Book of RL 从查表算法一路讲到 PPO，光谱对入门者更完整。

**比起 CleanRL**：CleanRL 只有实现，没有教科书。Little Book of RL 把实现、教科书 PDF、数学 supplementary 打包进一个仓库，三者互相引用。

一句话：想搞懂 RL 的原理，读 Sutton & Barto；想直接上手调 PPO，读 CleanRL；想沿"公式 ↔ 代码"这条最短路径入门，这本书是当前最少弯路的选择之一。

---

## 九、给作者的反馈（潜在改进点）

仓库质量已经很高，以下改进会让它更完整：

1. continuous action space——加一个 SAC 或 TD3 实现
2. multi-env eval——给 tabular.py 也配上 `SyncVectorEnv` 或批量并行评估
3. reproducibility script——一个 `reproduce_all.sh` 跑完所有算法并出 tensorboard 曲线
4. README 性能表——列出每个算法在 FrozenLake / CartPole 上的最终 return
5. 模型保存与加载——训练好的策略能直接 checkpoint / 恢复

这些都是 nice-to-have，不动摇它作为 RL 入门材料的价值。

---

## 参考资料

- [alxndrTL/little-book-rl](https://github.com/alxndrTL/little-book-rl) — 仓库主页
- [book.pdf](https://github.com/alxndrTL/little-book-rl/blob/main/book.pdf) — 主书
- [supplementary/](https://github.com/alxndrTL/little-book-rl/tree/main/supplementary) — DP 严格证明
- [CleanRL](https://github.com/vwxyzjn/cleanrl) — 实现参考
- [Stable Baselines3](https://stable-baselines3.readthedocs.io/) — 工业级 RL 库
- [Spinning Up](https://spinningup.openai.com/) — OpenAI RL 入门
- [Sutton & Barto - Reinforcement Learning: An Introduction](http://incompleteideas.net/book/the-book.html) — RL 圣经
