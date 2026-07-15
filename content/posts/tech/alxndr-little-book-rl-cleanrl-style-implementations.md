---
title: "The Little Book of RL：从零到 PPO 的 CleanRL 风格实现解析"
date: 2026-07-15T21:27:31+08:00
lastmod: 2026-07-15T21:27:31+08:00
draft: false
slug: alxndr-little-book-rl-cleanrl-style-implementations
description: "alxndrTL/little-book-rl 仓库深度拆解——一本配套 PyTorch 实现的小型强化学习书，覆盖 tabular MC / SARSA / Q-learning / n-step SARSA / SARSA(λ) / REINFORCE / VPG / SPG / PPO 全套算法。"
categories:
  - tech
tags:
  - Reinforcement Learning
  - PyTorch
  - PPO
  - CleanRL
  - cn-doc-writer
  - alxndrTL
---

# The Little Book of RL：从零到 PPO 的 CleanRL 风格实现解析

> 仓库：[alxndrTL/little-book-rl](https://github.com/alxndrTL/little-book-rl)
> 配套书 PDF：[book.pdf](https://github.com/alxndrTL/little-book-rl/blob/main/book.pdf) — 21MB / V1 (June 2026)
> 作者：[Thomas Lew](https://github.com/alxndrTL) / 471 stars / CC BY-SA 4.0 (non-commercial)
> 配套实现：6 个文件，~80KB，覆盖 9 个 RL 算法

这是一本**短小但完整的强化学习入门书**，加上一份"教学优先"的 PyTorch 实现。**作者 Thomas Lew 在 README 里写明**：书的目的是"从基础到应用算法的 RL 入门"，**代码是把书里讲到的算法全部实现一遍**。

下面把这本书的实现层拆给你看。

---

## 一、整体结构

仓库分四个部分：

| 路径 | 内容 | 用途 |
|---|---|---|
| `book.pdf` | 书的主文件 | 21MB 完整正文（V1 June 2026） |
| `algos/value_based/` | 基于价值函数的方法 | tabular.py + dqn.py |
| `algos/policy_based/` | 基于策略梯度的方法 | reinforce.py + spg.py + vpg.py + ppo.py |
| `supplementary/` | 动态规划的严格证明 | 2021 年写的补充材料 |

配套实现覆盖 **10 个算法**：

```
tabular  : MC, SARSA, Q-learning, n-step SARSA, SARSA(λ)   (5)
value    : DQN                                            (1)
policy   : REINFORCE, VPG, SPG, PPO                       (4)
```

**没有写**的有：A2C / SAC / TD3 / DDPG / 模型方法（model-based）。这本书明确说是"入门到应用"，所以刻意停在 PPO。

---

## 二、tabular.py：一个文件覆盖 5 个 tabular 算法

这是仓库里最有教学价值的文件——**5 个 on-policy / off-policy / n-step / eligibility trace 算法全在一个 300 行的 Python 文件里**。

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

每个字段下面用 docstring 写文档，tyro 自动生成 `--help`。这是 **CleanRL 风格的核心**：用 `tyro` 替代 `argparse`，让 dataclass 直接当 CLI schema。

### 2.2 5 个算法的核心 update 对比

每个算法一个 `run_episode_*` 函数。**把它们放一起看更新公式**：

| 算法 | Target | 更新 |
|---|---|---|
| **MC** | $G_t = \sum_{k=t}^{T-1} \gamma^{k-t} r_k$ | $Q[s,a] \mathrel{+}= \alpha (G_t - Q[s,a])$ |
| **SARSA** | $r + \gamma Q[s',a']$ | $Q[s,a] \mathrel{+}= \alpha (r + \gamma Q[s',a'] - Q[s,a])$ |
| **Q-learning** | $r + \gamma \max_{a'} Q[s',a']$ | $Q[s,a] \mathrel{+}= \alpha (r + \gamma \max Q[s',a'] - Q[s,a])$ |
| **n-step SARSA** | $\sum_{j=\tau}^{\tau+n-1} \gamma^{j-\tau} r_j + \gamma^n Q[s_{\tau+n}, a_{\tau+n}]$ | 同上模板 |
| **SARSA(λ)** | $r + \gamma Q[s',a'] - Q[s,a]$ | $Q \mathrel{+}= \alpha \delta E$, $E \mathrel{*}= \gamma \lambda$ |

**所有 on-policy + off-policy + n-step + eligibility trace 算法共享同一个 update 模板**（TD error × eligibility / 折扣回报）。把 5 个 update 公式并排放，立刻能看出**为什么 tabular RL 算法这么少**——它们本质上是**一个模板的不同填空**。

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
        ...
```

**这是 Sutton & Barto §12.7 的 1-for-1 实现**。两个关键点：

1. **eligibility trace $E[s,a]$ 跟 $Q[s,a]$ 同 shape**，每次访问累加（accumulating）或覆盖（replacing）。
2. **TD error $\delta$ 算出来后 broadcast 到整个 $Q$**：`Q += alpha * delta * E`——这意味着**所有曾经访问过的 state-action 都会被更新**，强度按 trace 衰减。

### 2.4 epsilon schedule 用线性衰减

```python
def linear_schedule(start_e: float, end_e: float, duration: float, t: int) -> float:
    slope = (end_e - start_e) / duration
    return max(end_e, start_e + slope * t)
```

跟 CleanRL DQN 一样的 ε 线性衰减：`start=1.0 → end=0.05`，`exploration_fraction=0.5` 表示在前 50% 训练步衰减完。

---

## 三、policy_based/：4 个策略梯度算法

### 3.1 REINFORCE（最基础的策略梯度）

```python
def reward_to_go(rewards, gamma):
    """G_t = sum_{k=t}^{T-1} gamma^{k-t} r_k"""
    G = np.zeros(len(rewards), dtype=np.float32)
    running = 0.0
    for t in reversed(range(len(rewards))):
        running = rewards[t] + gamma * running
        G[t] = running
    return G
```

这是**反向算 reward-to-go**——比正向循环 O(n²) 节省到 O(n)。然后：

```python
# REINFORCE loss:
# ∇J(θ) ≈ (1/N) Σ_n Σ_t ∇log π_θ(a_{n,t}|s_{n,t}) G_{n,t}
loss = -(log_probs * returns).mean()
```

注意 **negative**——PyTorch 的 optimizer 只能 minimize，所以策略梯度 maximize 期望回报 ↔ minimize negative expected return。

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

**没有 critic**——纯 actor-only。这是 REINFORCE 的标志。`std=0.01` 的小初始化是为了**初始策略接近 uniform**（low entropy 反而会让 loss 跳得厉害）。

### 3.2 PPO（仓库里最复杂的文件）

PPO 文件 333 行，是所有算法里最长的。它的注释把"书里没讲但实现里要做的事"全部列出来：

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

这一段注释是仓库**最有价值的部分**——它把"理论 → 工程"的 gap 显式标出来。**作者明确说代码基于 CleanRL 的 PPO**，所以读这本书的 PPO 实现 ≈ 读 CleanRL 的 PPO 实现 + 一份"理论教学"。

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

注意：
- critic 输出 std=1.0（小 std 让 critic 初始值偏小），actor 输出 std=0.01（小 std 让 actor 初始 logits 偏小 → uniform policy）。
- `get_action_and_value` **一次 forward 拿四个东西**（action、log_prob、entropy、value），节省算力。

#### B. 核心 PPO 损失（论文原版）

```python
# PPO clipped surrogate:
# L_clip(θ) = E[ min(r_t(θ) A_t, clip(r_t(θ), 1-ε, 1+ε) A_t) ]
new_log_prob = probs.log_prob(batched_actions)
log_ratio = new_log_prob - b_old_log_probs
ratio = log_ratio.exp()

adv = b_advantages
if args.norm_adv:
    adv = (adv - adv.mean()) / (adv.std() + 1e-8)

# unclipped
pg_loss1 = -adv * ratio
# clipped
pg_loss2 = -adv * torch.clamp(ratio, 1 - args.clip_coef, 1 + args.clip_coef)
pg_loss = torch.max(pg_loss1, pg_loss2).mean()
```

`clip_coef=0.2` 是 PPO 论文的默认。`torch.max(pg_loss1, pg_loss2).mean()` 是**取两个 loss 中较大的那个**——这是 PPO "悲观主义"的精髓：**clipped 后变差的更新就直接不用**。

#### C. Value loss（clipped 版）

```python
# value loss with clipping
newvalue = new_values
if args.clip_vloss:
    vf_loss1 = (newvalue - b_returns).pow(2)
    vf_loss2 = (torch.clamp(newvalue, b_values - args.clip_coef, b_values + args.clip_coef) - b_returns).pow(2)
    vf_loss = 0.5 * torch.max(vf_loss1, vf_loss2).mean()
else:
    vf_loss = 0.5 * (newvalue - b_returns).pow(2).mean()
```

`clip_vloss=True` 是 PPO 的稳定技巧——**不让 critic 更新太剧烈**，跟 policy clipping 同理。

#### D. GAE（Generalized Advantage Estimation）

PPO 注释里说 GAE "explained in the book"。仓库代码里的 GAE 计算：

```python
with torch.no_grad():
    advantages = torch.zeros_like(rewards)
    lastgaelam = 0
    for t in reversed(range(args.num_steps)):
        if t == args.num_steps - 1:
            nextnonterminal = 1.0 - next_done
            nextvalues = next_value
        else:
            nextnonterminal = 1.0 - dones[t + 1]
            nextvalues = values[t + 1]
        delta = rewards[t] + args.gamma * nextvalues * nextnonterminal - values[t]
        lastgaelam = delta + args.gamma * args.gae_lambda * nextnonterminal * lastgaelam
        advantages[t] = lastgaelam
returns = advantages + values
```

GAE 把 **TD(0) / TD(1) / TD(∞) ... TD(n)** 的 advantage 估计**用 λ 加权**插值，平衡 bias / variance。`gae_lambda=0.95` 是常用默认。

### 3.4 与 CleanRL 的关系

PPO 文件的开头写了：

> copied here for the sake of completeness, original code at: https://github.com/vwxyzjn/cleanrl/

所以这份 PPO 实现**几乎是 CleanRL PPO 的 1-for-1 移植**。两个值得记的事实：

1. **CleanRL 是社区公认的"教学优先 + 工程正确"RL 实现范式**——单文件、易读、可执行、有 tensorboard / wandb 集成。
2. **Little Book of RL 把 CleanRL 当作实现参考**说明 CleanRL 风格正在成为 RL 入门的**事实标准**——跟 PyTorch 官方 tutorial、Stable Baselines3 并列。

---

## 四、10 个算法的演进关系

把仓库里 10 个算法按"理论血缘"画一张图：

```
value-based          policy-based
─────────            ────────────
MC ─┐                REINFORCE ──┐
SARSA ─┐             VPG ────────┤
Q-learning ─┤        SPG ────────┤
n-step SARSA ─┤      PPO ────────┘
SARSA(λ) ──┘
DQN ────────┘
```

观察：

- **tabular 5 算法全部共享 update 模板**（TD error + 各种 target 形式）。
- **policy-based 4 算法共享 actor-only → actor-critic 的演进**：REINFORCE（pure actor）→ VPG（add baseline）→ SPG（stochastic）→ PPO（clipped + GAE）。
- **DQN 是 tabular Q-learning 的非线性推广**（同样的 update 公式 + 神经网络逼近 + experience replay）。
- **PPO 是 REINFORCE 的"加约束"版本**（trust region + clipped surrogate）。

**理解这张图 = 理解现代 RL 算法的骨架**。

---

## 五、这本书没讲的事（工程坑）

仓库代码 + 注释暴露了几个**RL 入门书一般不讲但工程必踩**的坑：

### 5.1 初始化方差

```python
layer_init(nn.Linear(64, envs.single_action_space.n), std=0.01)
```

actor 输出层 std=0.01（小），critic 输出层 std=1.0（默认）。**这是 CleanRL 的隐性约定**——小 std 让初始策略接近 uniform（高熵），避免 early-stage collapse；大 std 让 critic 输出范围大一些，方便训练。

### 5.2 vectorized env

所有 policy-based 文件都用 `gym.vector.SyncVectorEnv`，**多个 env 并行采样**。这在论文里通常一句"parallel rollout"带过，**但在工程上是 PPO 跑 CartPole 的关键**——单 env 数据采样太慢，PPO 根本跑不动。

### 5.3 步数 vs trajectory 计数

PPO 注释明确说：

> collection is done with a fixed number of steps per environment, instead of a fixed number of complete trajectories (discussed in the book)

REINFORCE 用 `num_trajectories`（固定 trajectory 数），PPO 用 `num_steps`（固定步数）。**这是 on-policy 算法的一个工程分叉**——trajectory-based 适合 short episodes，step-based 适合 long episodes。

### 5.4 entropy bonus

PPO 注释：

> entropy loss penalizes low entropy policies, thus encourages exploration

`ent_coef=0.01` 是熵正则的权重——**给策略加一个"不要太确定"的奖励**。没有这个，policy gradient 在收敛后期很容易 collapse 到 greedy policy。

### 5.5 LR annealing + grad clip

PPO 用 `anneal_lr=True`（学习率随训练线性衰减）和 `max_grad_norm=0.5`（梯度范数截断）。**这两个不是 PPO 论文的硬性要求**，但在 long training run 里是**防止后期震荡 + early collapse 的工程保险**。

### 5.6 target_kl 早停

```python
if args.target_kl is not None:
    if approx_kl > args.target_kl:
        break
```

如果新旧策略的 KL 散度超过 `target_kl`，**提前停止当前 update**。这是 PPO "trust region" 思想的具体落地——不要让单次更新走太远。

---

## 六、这本书的局限（写给认真学 RL 的人）

把仓库读完，下面这些**没教**的要知道：

### 6.1 没有 continuous action space

所有算法都假设 `gym.spaces.Discrete`（用 `Categorical` distribution）。**SAC / TD3 / DDPG 这类连续动作算法完全没提**。如果你的任务是 robotics / 自动控制，需要补这一块。

### 6.2 没有 model-based 方法

MCTS / 世界模型 / Dreamer 这些都没提。**model-based 是 RL 的另一个半壁江山**，这本书完全没碰。

### 6.3 没有 multi-agent / hierarchical

multi-agent RL 和 hierarchical RL（Options / Feudal Networks）都没提。这是工业 RL（推荐系统、运筹优化）的常见范式。

### 6.4 没有 offline RL / imitation learning

BC / IRL / CQL / IQL 这些都没提。如果你的数据是 fixed dataset（没有环境交互），需要补 offline RL。

### 6.5 PPO 的复现性陷阱

PPO 文件 333 行，**但跑出论文数字需要大量调参**。仓库只给了 CartPole-v1 这种 toy env 的复现。**Atari / MuJoCo 数字不在仓库范围内**——所以"用这份代码跑 HalfCheetah" 是不现实的。

---

## 七、读这本书的最佳顺序

如果你是 RL 入门，按下面顺序读：

1. **读 book.pdf 前 4 章**（tabular / DP / MC / TD）→ 对应 `tabular.py` 完整读完
2. **读 book.pdf 第 5 章**（function approximation）→ 跳到 `dqn.py`
3. **读 book.pdf 第 6 章**（policy gradient）→ 对应 `reinforce.py` + `vpg.py` + `spg.py`
4. **读 book.pdf 第 7 章**（TRPO / PPO）→ 对应 `ppo.py`
5. **supplementary/** 是 DP 的严格数学证明，**选择性读**（理论派必读，工程派可跳）

每章读完**直接跑代码**：

```bash
cd algos/value_based
python tabular.py --algo q_learning --env_id FrozenLake-v1

cd ../../algos/policy_based
python reinforce.py --env_id CartPole-v1
python ppo.py --env_id CartPole-v1
```

tensorboard 起来后**能看到 return 曲线**，对照书里讲"应该长什么样"。

---

## 八、为什么这本书值得读

**比起 Sutton & Barto**：Sutton & Barto 是 RL 圣经，但**没有配套 PyTorch 实现**——理论扎实但工程断层。Little Book of RL 是**理论 + 实现 1:1 对应**，每个章节都有对应代码文件。

**比起 Spinning Up**：OpenAI Spinning Up 也是教学向，但只覆盖 VPG / TRPO / PPO / DDPG / SAC / TD3，**没有 tabular 部分**。Little Book of RL 覆盖**从 tabular 到 PPO 的完整光谱**，对入门者更友好。

**比起 CleanRL**：CleanRL 是"工程实现"，**没有理论教科书**。Little Book of RL 把**实现 + 教科书 PDF + 数学 supplementary 打包成一个仓库**，是**目前最完整的 RL 入门包之一**。

---

## 九、给作者的反馈（潜在改进点）

虽然仓库质量已经很高，下面这些改进会让它更完整：

1. **continuous action space**——加 SAC 或 TD3 一个实现
2. **multi-env eval**——给 tabular.py 也加 `SyncVectorEnv`
3. **reproducibility script**——一个 `reproduce_all.sh` 跑完所有算法 + tensorboard
4. **README 性能表**——列出每个算法在 FrozenLake / CartPole 上的最终 return
5. **Hugging Face integration**——`from_pretrained` 直接加载训练好的模型

这些都是 nice-to-have，**不影响这是一本非常优秀的 RL 入门资源**。

---

## 参考资料

- [alxndrTL/little-book-rl](https://github.com/alxndrTL/little-book-rl) — 仓库主页
- [book.pdf](https://github.com/alxndrTL/little-book-rl/blob/main/book.pdf) — 主书
- [supplementary/](https://github.com/alxndrTL/little-book-rl/tree/main/supplementary) — DP 严格证明
- [CleanRL](https://github.com/vwxyzjn/cleanrl) — 实现参考
- [Stable Baselines3](https://stable-baselines3.readthedocs.io/) — 工业级 RL 库
- [Spinning Up](https://spinningup.openai.com/) — OpenAI RL 入门
- [Sutton & Barto - Reinforcement Learning: An Introduction](http://incompleteideas.net/book/the-book.html) — RL 圣经

> 本文由钳岳星君基于 alxndrTL/little-book-rl 仓库深度拆解，使用 cn-doc-writer 技能优化、去除 AI 味道。所有算法 update 公式均来自仓库代码与 Sutton & Barto 教科书；所有"工程坑"来自仓库注释（"Few implementation details not described in the book" 段落）。