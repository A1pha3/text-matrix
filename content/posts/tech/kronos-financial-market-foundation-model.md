---
github_repo: "shiyu-coder/Kronos"
source_key: "gh:shiyu-coder/Kronos"
title: "Kronos：把 K 线当语言来做的基础模型"
date: "2026-05-14T20:17:49+08:00"
lastmod: 2026-10-03T09:30:00+08:00
categories:
  - "技术笔记"
tags: ["基础模型", "Transformer", "量化金融", "时间序列"]
description: "清华团队的 Kronos 是首个开源的金融 K 线基础模型：分层分词器把 OHLCV 量化为粗细两级 Token，自回归 Transformer 在 45 个交易所、120 亿条 K 线上预训练。本文拆解其分词机制、预训练数据构成、论文基准结果与上手路径。"
slug: kronos-financial-market-foundation-model
---

# Kronos：把 K 线当语言来做的基础模型

通用时间序列基础模型（TSFM）在金融 K 线上一直表现平平，论文摘要里甚至直言它们"常常跑不过非预训练架构"。Kronos 的思路是不跟通用模型硬拼，而是为 K 线专门造一套"语言"：先用分词器把连续的 OHLCV 量化成离散 Token，再用自回归 Transformer 学这套语言的统计规律。预训练语料是 45 个全球交易所、超过 120 亿条 K 线记录。

结果是：零样本设定下，价格序列预测的 RankIC 比最强 TSFM 基线高 93%，比最佳非预训练模型高 87%；波动率预测 MAE 低 9%，合成 K 线的生成保真度高 22%。论文已被 AAAI 2026 接收（[arXiv:2508.02739](https://arxiv.org/abs/2508.02739)），代码 MIT 协议开源，GitHub 39,825 星（2026-10-03 读数）。

值得先知道的现状：仓库最后一次 push 在 2026-04-13，之后近半年没有新提交，也没有任何 tag 或 release——复现实验只能锁 commit（写作时 master 在 `67b630e6`）。这不影响权重可用性，但意味着问题反馈要靠 Issue，跟进节奏要看维护者。

## 系统总览：两级 Token + 一个 Decoder

Kronos 的框架分两阶段，各自独立训练：

| 阶段 | 组件 | 做什么 | 关键设计 |
|------|------|--------|---------|
| 一 | KronosTokenizer | 把每个时间步的 6 维数值（OHLCV + amount）压成离散 Token | 粗（coarse）细（fine）两级 codebook，各 2^10 = 1024 项，联合空间 2^20 |
| 二 | Kronos（decoder-only Transformer） | 在 Token 序列上做自回归预训练 | 每步先预测粗 Token，再以其为条件预测细 Token |

模型家族共四个规模，均可从 Hugging Face 下载（large 除外）：

| 模型 | 分词器 | 上下文 | 层数 / 维度 / 注意力头 | 参数量 | 词表 | 开源 |
|------|--------|--------|----------------------|--------|------|------|
| Kronos-mini | Kronos-Tokenizer-2k | 2048 | 4 / 256 / 4 | 4.1M | 2^20 | ✅ [NeoQuasar/Kronos-mini](https://huggingface.co/NeoQuasar/Kronos-mini) |
| Kronos-small | Kronos-Tokenizer-base | 512 | 8 / 512 / 8 | 24.7M | 2^20 | ✅ [NeoQuasar/Kronos-small](https://huggingface.co/NeoQuasar/Kronos-small) |
| Kronos-base | Kronos-Tokenizer-base | 512 | 12 / 832 / 16 | 102.3M | 2^20 | ✅ [NeoQuasar/Kronos-base](https://huggingface.co/NeoQuasar/Kronos-base) |
| Kronos-large | Kronos-Tokenizer-base | 512 | 18 / 1664 / 32 | 499.2M | 2^20 | ❌ |

两点容易读错的地方。其一，词表不是"2k"：论文 Table 1 明确写 Vocab. 为 2^20（约 105 万种组合），来源是粗细两级 codebook 各 2^10。其二，论文正文只训练了 small/base/large 三个变体（"trained three variants … up to nearly 0.5 billion"），mini 不在论文主表中，是仓库后来单独发布的轻量规格——配套的 Tokenizer-2k 也只有它用（两个分词器的粗细 codebook 完全相同，实际差别在量化分组大小：2k 版 group_size=5，base 版为 4，见两者在 Hugging Face 上的 config.json）。

上下文 512 是有意为之。论文原话：考虑资源限制与实际部署场景，把最大上下文限制在 512 个 Token；任意长的预测视界靠换数据频率实现——1 分钟线看短期，日线看周和月。mini 的 2048 上下文则是面向更长回看窗口的补充选项。

## 分词器：每根 K 线变成两个 Token

分词器本质是一个 Transformer 自编码器，训练目标是重建输入，但用了两个重建损失配合的分层量化：粗 Token 负责主要价格形态，细 Token 编码残差信息。训练时配合熵正则（论文配置 γ=1.1、ζ=0.05）和分组量化（把若干时间步合组计算熵）防止 codebook 塌缩。

预训练时，每个时间步的 Token 被拆成 b_t = [b_t^c, b_t^f]（粗、细两个子 Token），用两个独立的 embedding 层投影后拼接融合进 Transformer。预测目标按链式法则分解：

p(b_t | b_<t) = p(b_t^c | b_<t) · p(b_t^f | b_<t, b_t^c)

也就是先定"轮廓"再补"细节"。这种 coarse-to-fine 的顺序显式建模了多尺度行情动态。消融实验（Table 9）给了一个诚实的注脚：分层损失的重建误差（MAE 0.0785）与标准非分层损失（0.0781）几乎持平，并不更优——分层设计的收益不在重建精度，而在把粗细结构编进 Token 供自回归阶段利用；Transformer 架构本身则明显优于参数量相当的 CNN 对照（0.0916）。另外词表越大，重建质量与预测精度都越好（Figure 6）。

主干的工程细节没有花活：因果自注意力 + RoPE 位置编码 + RMSNorm，和 LLM 的标准配方一致——作者的意图很清楚，就是把 K 线序列当成另一种自然语言，验证语言建模范式能不能直接迁移到金融数据上。

## 预训练数据：45 个交易所、120 亿条 K 线

这是 Kronos 敢自称"基础模型"的底气，也是它和通用 TSFM 拉开差距的地方：

- **股票**：9 个全球交易所——分布内为上海（XSHG）、纳斯达克（XNAS）、日本（XJPX）、印度（XNSE）、韩国（XKRX）、香港（XHKG），分布外为印尼（XIDX）、马来西亚（XKLS）、台湾（XTAI），用于检验跨市场泛化；
- **加密货币**：Binance 全部现货交易对；
- **外汇**：超过 1,000 个货币对；
- **频率**：7 种采样频率，覆盖分钟线到日线。

两个值得注意的处理。一是加密与外汇数据故意去掉了 volume 和 amount，只喂 OHLC 四列——论文用这种"缺模态"设置测试模型对输入维度的鲁棒性，这也是为什么 `KronosPredictor` 允许 volume/amount 缺省填 0。二是原始语料里股票远多于加密、期货和外汇，团队做了数据再平衡，防止小类别欠拟合。数据清洗管线会过滤异常价格尖刺和长期无成交的片段（附录 B）。

## 论文结果怎么读

论文对比了 25 个基线，覆盖四种范式：非预训练全样本模型（iTransformer、PatchTST、DLinear 等）、零样本 TSFM（Chronos、TimesFM、Moirai、Time-MoE 等）、计量波动率模型（GARCH）、生成式时序模型（DiffusionTS）。三组数字对应三类任务，读法各不相同。

**价格序列预测（RankIC +93% / +87%）**。RankIC 衡量预测值与真实收益率横截面排名的相关性，是量化因子评价的标准指标。93% 是相对提升：Kronos 的 RankIC 数值上是最强 TSFM 基线的 1.93 倍——通用 TSFM 在金融数据上的基数本来就低，大倍数有相当部分来自"对手弱"而非自己强；87% 那一档的对手（最佳非预训练模型）基数更高，这个提升幅度更值得看。另外模型规模越大性能越好，验证了时序基础模型的 scaling law。

**波动率预测（MAE −9%）与合成数据生成（保真度 +22%）**。这两项是通用 TSFM 通常不做的任务，Kronos 把它们当作一等公民：生成质量按 diversity / fidelity / usefulness 三个维度评估（Figure 4 展示了 t-SNE 与核密度对比）。这两个数字的绝对基数论文未在正文给出，看完整表需要翻附录 F。

**投资模拟（AER / IR 领先）**。在沪深 300 和中证 800 成分股上，按模型信号选 top-k 股票构建组合做回测，Kronos 的年化超额收益（AER）和信息比率（IR）超过全部基线。注意这是论文自建的模拟环境，交易成本、滑点、市场冲击的建模方式都在附录 D——它证明的是"信号可转化为相对收益"，不等于实盘可复制的绝对收益。

**测试时扩展（test-time scaling）**。`sample_count` 参数允许同一上下文采样多条路径取平均，论文 Figure 7 显示 IC 与 RankIC 随采样路径数一致提升——不重训模型、只多花推理算力就能换更稳的预测。这是概率式生成框架特有的便宜活。

这些数字全部来自论文自述，截至本文写作未见独立第三方复现。把它当作"范式成立的证据"比当作"可直接引用的性能承诺"更稳妥。

## 快速上手

环境要求 Python 3.10+，依赖清单很短（torch ≥ 2.0.0、pandas 2.2.2、einops、safetensors 等，注意 `huggingface_hub` 钉在 0.33.1）：

```bash
pip install -r requirements.txt
```

### 一次完整的预测

```python
from model import Kronos, KronosTokenizer, KronosPredictor

# 1. 加载分词器和模型
tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small")

# 2. 初始化预测器（不传 device 时自动按 cuda -> mps -> cpu 选择）
predictor = KronosPredictor(model, tokenizer, max_context=512)

# 3. 准备数据
import pandas as pd

df = pd.read_csv("./data/XSHG_5min_600977.csv")
df['timestamps'] = pd.to_datetime(df['timestamps'])

lookback = 400
pred_len = 120

x_df = df.loc[:lookback-1, ['open', 'high', 'low', 'close', 'volume', 'amount']]
x_timestamp = df.loc[:lookback-1, 'timestamps']
y_timestamp = df.loc[lookback:lookback+pred_len-1, 'timestamps']

# 4. 生成预测
pred_df = predictor.predict(
    df=x_df,
    x_timestamp=x_timestamp,
    y_timestamp=y_timestamp,
    pred_len=pred_len,
    T=1.0,          # 采样温度
    top_p=0.9,      # Nucleus 采样概率
    sample_count=1  # 采样路径数，多条路径时对结果取平均
)

print(pred_df.head())
```

几个容易踩的点，都来自源码而非文档：

1. **示例数据文件仓库里没有**。README 和 `examples/prediction_example.py` 都引用 `./data/XSHG_5min_600977.csv`，但仓库根本没有 `data/` 目录（2026-10-03 核对 master）——跑官方示例前先自备一份 CSV，至少要有 `timestamps` 与 `open/high/low/close` 五列，volume 和 amount 可选。
2. `predict()` 的完整签名是 `predict(df, x_timestamp, y_timestamp, pred_len, T=1.0, top_k=0, top_p=0.9, sample_count=1, verbose=True)`，`top_k` 默认关闭（0），温度才是主要的随机性旋钮。
3. 返回的 `pred_df` 是以 `y_timestamp` 为索引、含全部六列的 DataFrame——预测的是完整 K 线，不只是收盘价。
4. 温度取值跟任务走：论文附录 E 给的经验值是价格/收益率预测用低温（约 T≈0.6）压随机性，波动率预测和合成生成用更高的温度换多样性；仓库 webui 的推荐档（T 1.2–1.5、top_p 0.95–1.0）偏生成场景。官方 README 示例的 T=1.0 只是中性起点，不是"最优值"。
5. 采样路径数（`sample_count`）越大越稳，代价是推理时间线性变长——这是上文 test-time scaling 的直接应用。

### 批量预测与现成脚本

多标的场景用 `predict_batch`，要求所有序列的 lookback 与 pred_len 一致，volume/amount 缺失自动填 0，GPU 并行处理、每条序列独立做归一化：

```python
pred_df_list = predictor.predict_batch(
    df_list=[df1, df2, df3],
    x_timestamp_list=[x_ts1, x_ts2, x_ts3],
    y_timestamp_list=[y_ts1, y_ts2, y_ts3],
    pred_len=pred_len,
    T=1.0, top_p=0.9, sample_count=1, verbose=True
)
```

不想自己找数据的话，`examples/` 里有一条更顺的路径：`prediction_cn_markets_day.py` 用 akshare 自动拉 A 股日线并完成预测，`python prediction_cn_markets_day.py --symbol 000001` 即可（默认用 Kronos-base，CPU 也能跑），结果输出到 `./outputs/`。同目录还有无成交量版示例（`prediction_wo_vol_example.py`，显式传 `device="cuda:0"`）、批量版和带 GUI 的版本。

仓库还自带一个 Flask 写的本地 Web UI（`webui/` 目录，`python run.py` 启动后访问 localhost:7070）：CSV/Feather 数据上传、400+120 固定窗口滑块、温度与采样参数调节、plotly K 线图对比。模型导入失败时会退回模拟数据演示——看到曲线太"漂亮"先确认模型真的加载了。不想装任何东西，官方还挂着一个 [Live Demo](https://shiyu-coder.github.io/Kronos-demo/)，展示 BTC/USDT 未来 24 小时的预测。

## 微调：两条管线

预训练模型是通用市场的，自己的标的一般要微调。仓库提供两条管线，按数据形态选：

**Qlib 管线（`finetune/`）**——A 股场景，依赖 `pyqlib`（需另装），默认日线数据：

```bash
# 1. 在 finetune/config.py 中改六个路径：qlib_data_path / dataset_path /
#    save_path / backtest_result_path / pretrained_tokenizer_path / pretrained_predictor_path
python finetune/qlib_data_preprocess.py          # 2. 生成 train/val/test 三个 pickle
torchrun --standalone --nproc_per_node=NUM_GPUS finetune/train_tokenizer.py   # 3. 微调分词器
torchrun --standalone --nproc_per_node=NUM_GPUS finetune/train_predictor.py  # 4. 微调预测器
python finetune/qlib_test.py --device cuda:0     # 5. top-K 策略回测 + 累计收益曲线
```

`config.py` 里还有 `instrument`、`train_time_range`、`epochs`、`batch_size` 等参数，用 Comet.ml 记录实验需要把 `use_comet` 置 True，否则置 False。

**CSV 管线（`finetune_csv/`）**——不依赖 Qlib，喂任意 CSV（七列格式，volume/amount 可为 0），YAML 配置，仓库附了一个港股 5 分钟线（阿里 09988）的完整示例与配置文件，推荐用 `train_sequential.py` 一键串完分词器和预测器两阶段。

README 里还有两条必须知道的声明。一是免责声明：微调管线是演示流程用的简化示例，不是生产级量化系统，稳健的量化策略需要组合优化、风险因子中性化等技术才能获得稳定的 alpha。二是在开源项目里相当少见的一条：作者主动声明 `finetune/` 目录里的很多代码注释由 AI 助手（Gemini 2.5 Pro）生成，可能包含不准确之处，建议以代码本身为准——读微调代码时别把注释当文档用。

仓库另带 `tests/test_kronos_regression.py` 回归测试：锁定 Hugging Face 上特定 revision（`901c26c`），用固定输入对比输出的 MSE 期望值（容差 1e-6 量级）。改动推理代码前后跑一遍，能确认没动到数值行为——对金融模型来说，这比单元测试更能说明"改坏了没有"。

## 采用建议

**适合谁**：做因子研究或时序建模、想要一个现成 K 线预训练骨干的人。Kronos 的价值在于零样本可用 + 可微调 + 任务面宽（预测、波动率、生成），从 small 起步在单卡上就能跑（24.7M 参数），base 102M 也只是入门级 GPU 负载。

**不适合谁**：想要"接上就能赚钱"的策略开发者。论文自己的定位是基础模型研究，信号到收益之间还隔着组合构建、风险管理、成本建模整整一层；把 raw prediction 直接当交易信号，是 README 和论文都明确反对的用法。

**风险与边界**：项目近半年无提交、无正式版本号，依赖钉死旧版 `huggingface_hub`，遇到环境冲突要做好自己 patch 的准备；Kronos-large 权重未开源，论文里最大的数字（含 scaling 曲线高端）复现不了；全部基准数字来自论文自述，独立复现尚未见到。回看窗口超过 512 的需求要么换 mini（2048），要么按官方思路换更低频率的数据。

K 线数据的信噪比决定了任何模型的天花板都不会太高，这也是论文 Discussion 一节自己提出的问题——"K 线数据里到底嵌入了多少足以驱动短期价格的信息"。Kronos 的回答是：把这些信息里有结构的部分先抽干净，剩下的交给采样和微调。这个范式能不能在实盘里站住，还要看后续使用者的实证。

## 相关链接

- 论文：<https://arxiv.org/abs/2508.02739>
- GitHub：<https://github.com/shiyu-coder/Kronos>
- Hugging Face：<https://huggingface.co/NeoQuasar/Kronos-small>
- 在线 Demo：<https://shiyu-coder.github.io/Kronos-demo/>

---

*如在研究中使用 Kronos，请引用：*

```bibtex
@misc{shi2025kronos,
  title={Kronos: A Foundation Model for the Language of Financial Markets},
  author={Yu Shi and Zongliang Fu and Shuo Chen and Bohan Zhao and Wei Xu and Changshui Zhang and Jian Li},
  year={2025},
  eprint={2508.02739},
  archivePrefix={arXiv},
  primaryClass={q-fin.ST},
  url={https://arxiv.org/abs/2508.02739},
}
```
