# RLlib 最小範例（新 API stack）

環境：Ray `3.0.0.dev0`（nightly）、Python 3.13、torch（CPU）、gymnasium 1.2.2、4 顆 CPU（`nproc` = 4）。
所有指令都在 `~` 執行，先 `source ~/ray-venv/bin/activate`。

> 狀態一覽
> - 範例 1（單智能體 PPO + CartPole）：已實際跑過，4 個 iteration。
> - 範例 2（官方 `multi_agent_cartpole.py`）：一開始缺 `PIL`（Pillow）失敗（第 2 節「遇到的問題：缺 Pillow」），
>   裝好 pillow 12.3.0 之後已實際跑成功，「改哪裡」表 4 條裡 3 條實測，1 條未實測。

---

## 1. 範例 1：`notes/examples/rllib_cartpole.py`

### 怎麼跑

```bash
source ~/ray-venv/bin/activate
cd ~
python /home/user/ray/notes/examples/rllib_cartpole.py
# 可改的參數：--iters --lr --train-batch-size --num-env-runners
```

程式只有四步：`PPOConfig()` 組設定 → `config.build_algo()` 建立 → `algo.train()` 迴圈 → `algo.stop()`。
`build_algo()` 是 repo 裡的實際名稱（`doc/source/rllib/getting-started.md`、`python/ray/rllib/README.md` 都這樣寫）。

結果 dict 的 key 以原始碼為準（`python/ray/rllib/utils/metrics/__init__.py`）：
`ENV_RUNNER_RESULTS = "env_runners"`、`EPISODE_RETURN_MEAN = "episode_return_mean"`，
所以讀法是 `result["env_runners"]["episode_return_mean"]`。

### 實際輸出（預設設定：`num_env_runners=2`、`lr=5e-5`、`train_batch_size_per_learner=4000`）

```
iter 1: episode_return_mean=21.32  time=16.8s
iter 2: episode_return_mean=41.17767441860465  time=16.9s
iter 3: episode_return_mean=61.78201368523949  time=15.5s
iter 4: episode_return_mean=108.88571428571429  time=15.6s
real	1m24.885s
```

（`real` 是整支程式含 Ray 啟動、建 Algorithm、4 個 iteration、結束的時間。每個 iteration 約 15~17 秒，
CartPole 滿分是 500，4 個 iteration 到 100 左右是正常的，目標只是看到分數在上升。）
輸出中還會有一些 `DeprecationWarning: RLModule(config=[RLModuleConfig object]) has been deprecated`，
是 RLlib 內部建 RLModule 的寫法被棄用的警告，不影響執行，不是你的程式寫錯。

### 遇到的問題：dashboard 啟動失敗，卡 60 秒

第一次跑（沒有 `ray.init(include_dashboard=False)`）時，輸出中出現：

```
ERROR services.py:1431 -- Failed to start the dashboard
...
ray.dashboard.utils.FrontendNotFoundError: [Errno 2] Dashboard build directory not found. If installing from source, please follow the additional steps required to build the dashboard(cd python/ray/dashboard/client && npm ci && npm run build): '/root/ray-venv/lib/python3.13/site-packages/ray/dashboard/client/build'
...
INFO trainable.py:154 -- Trainable.setup took 69.674 seconds.
iter 1: episode_return_mean=22.93  time=17.7s
iter 2: episode_return_mean=38.86125  time=14.8s
iter 3: episode_return_mean=55.10263157894737  time=15.5s
iter 4: episode_return_mean=88.56547619047619  time=16.4s
real	2m23.679s
```

原因：這個 Ray 是從原始碼安裝，沒有 build dashboard 前端。訓練本身不受影響，但啟動時白等約 60 秒（總共 2m23s）。
處理：在腳本裡加 `ray.init(include_dashboard=False)`，之後整支程式降到約 1m24s。
有正常安裝 Ray 的環境不需要這行。

### 時間都花在哪？

每個 iteration 約 15 秒，但 `--train-batch-size 1000` 時只要約 4 秒，所以時間主要花在 **Learner 更新**
（PPO 預設 `num_epochs=30`、`minibatch_size=128`，在 CPU 上對 4000 步資料反覆更新），不是環境採樣。
（這是從數字推論，沒有另外用 profiler 驗證。）

### 改哪裡 → 會看到什麼（範例 1，全部實測，各跑 4 個 iteration）

| 改哪裡 | 指令 | 實測結果 | 觀察 |
|---|---|---|---|
| 基準（不改；跑兩次看雜訊） | （無參數）| 第 4 次 return 108.9 / 118.0；每 iter 約 15~17 s；整支 1m23~1m25s | 同樣設定兩次，return 差約 10，所以小差異不要過度解讀 |
| `lr` 5e-5 → 1e-3 | `--lr 0.001` | return 19.8 → 55.1 → 193.8 → 271.5；每 iter 約 15 s | 學習率大 20 倍，進步明顯變快；時間幾乎不變（lr 不影響計算量）|
| `train_batch_size_per_learner` 4000 → 1000 | `--train-batch-size 1000` | return 20.9 → 31.6 → 39.3 → 88.5；每 iter 約 4 s；整支 34 s | 每 iter 變快約 4 倍（資料少 4 倍），但每 iter 看到的資料少，return 的進步也比較慢 |
| `num_env_runners` 2 → 1 | `--num-env-runners 1` | 每 iter 約 19.5~21 s；return 最終 105.9；整支 1m39s | 採樣只剩一個 worker，每 iter 約慢 4 秒（約 +25%）|
| `num_env_runners` 2 → 3 | `--num-env-runners 3` | 每 iter 15.4~18.3 s；return 最終 102.9；整支 1m26s | 沒有變快：4 顆 CPU 被 3 個 EnvRunner + driver 佔滿，而瓶頸又在 Learner |

提醒：`num_env_runners` 再加大，在這台 4 顆 CPU 的機器上沒有幫助（也可能因為 CPU 不夠而卡住，這部分未測）。
各 return 數字是單次、單一 seed 的結果，只能看趨勢。

---

## 2. 範例 2：官方多智能體範例 `multi_agent_cartpole.py`

檔案：`python/ray/rllib/examples/multi_agent/multi_agent_cartpole.py`（不複製，直接跑）。

### 先看有哪些參數

讀 `python/ray/rllib/examples/utils.py` 的 `add_rllib_example_script_args`，這次會用到的：

| 參數 | 意義 |
|---|---|
| `--num-agents` | 0（預設）= 單智能體；> 0 = 多智能體，環境複製 n 份，每個 agent 各自獨立 |
| `--stop-iters` | 訓練幾個 iteration（此檔預設 200）|
| `--num-env-runners` | 平行 EnvRunner 數量 |
| `--stop-reward` / `--stop-timesteps` | 其他停止條件（此檔預設 600.0 / 100000）|
| `--no-tune` | 不透過 Tune，直接 build_algo 訓練（除錯用）|
| 其他 | `--algo`、`--num-envs-per-env-runner`、`--num-learners`、`--evaluation-*`、`--as-test` 等 |

### 怎麼跑

```bash
source ~/ray-venv/bin/activate
cd ~
python /home/user/ray/python/ray/rllib/examples/multi_agent/multi_agent_cartpole.py \
    --num-agents=2 --stop-iters=2 --num-env-runners=2
```

### 實際結果（裝好 Pillow 後）

指令：`--num-agents=2 --stop-iters=2 --num-env-runners=2`（4 顆 CPU，`num_env_runners=2`）。
這個腳本預設用 Tune 執行（沒加 `--no-tune`），所以輸出是 Tune 的狀態表。節錄最後的部分：

```
Trial PPO_env_eb9f9_00000 reported env_runners/episode_len_mean=39.86558139534884,num_env_steps_sampled_lifetime=8042.0,env_runners/episode_return_mean=61.02093023255814 with parameters=...
== Status ==
Logical resource usage: 3.0/4 CPUs, 0/0 GPUs
+---------------------+------------+-----------------+--------+------------------+------+-------------------+-------------+-------------+
| Trial name          | status     | loc             |   iter |   total time (s) |   ts |   combined return |   return p0 |   return p1 |
| PPO_env_eb9f9_00000 | TERMINATED | 192.0.2.2:16180 |      2 |          42.2918 | 8042 |           61.0209 |      28.194 |      32.827 |
+---------------------+------------+-----------------+--------+------------------+------+-------------------+-------------+-------------+
2026-10-08 05:06:40,815	INFO tune.py:1039 -- Total run time: 54.61 seconds (54.17 seconds for the tuning loop).
real	2m5.395s
```

怎麼讀：第 1 個 iteration 後 `combined return` 45.45（p0 24.23、p1 21.22），第 2 個 iteration 後 61.02（p0 28.19、p1 32.83）；
`combined return` 是所有 agent 的 return 加總（`--num-agents` 的說明就是這樣寫的），`return p0 / p1` 是各 policy 的。
`ts` 是累計採樣的環境步數（8042）。耗時：Tune 迴圈 54 秒（2 個 iteration 共 42.3 秒），整支指令 2m5s。

**dashboard 卡 60 秒**：輸出裡同樣出現 `Failed to start the dashboard ... FrontendNotFoundError`（原因同第 1 節）。
整支 2m5s 比 Tune 迴圈的 54 秒多出約 70 秒，大部分是這個 dashboard 逾時加上 Ray 啟動。
這是本機從原始碼安裝造成的，沒有修改官方範例檔，註明即可。

### 遇到的問題：缺 Pillow

第一次跑同一個指令，7 秒內失敗：

```
Traceback (most recent call last):
  File "/home/user/ray/python/ray/rllib/examples/multi_agent/multi_agent_cartpole.py", line 51, in <module>
    get_trainable_cls(args.algo)
  ...
  File "/root/ray-venv/lib/python3.13/site-packages/ray/rllib/algorithms/registry.py", line 32, in _import_dreamerv3
    import ray.rllib.algorithms.dreamerv3 as dreamerv3
  ...
  File "/root/ray-venv/lib/python3.13/site-packages/ray/rllib/algorithms/dreamerv3/utils/debugging.py", line 4, in <module>
    from PIL import Image, ImageDraw
ModuleNotFoundError: No module named 'PIL'

real	0m6.950s
```

- 實際 import 鏈：`ray/tune/registry.py` 的 `_has_rllib_trainable` → `ray/rllib/__init__.py:35` `_register_all`
  → `algorithms/registry.py:32` `_import_dreamerv3` → `dreamerv3/utils/summaries.py:14`
  → `dreamerv3/utils/debugging.py:4` `from PIL import Image, ImageDraw`。
  也就是 `get_trainable_cls("PPO")` 會先註冊**所有**演算法，即使只用 PPO 也會被 DreamerV3 的 import 擋住。
- 已查證：`python/setup.py` 的 `rllib` extra（約第 333–340 行）只列了 `tune` extra、`dm_tree`、`gymnasium==1.2.2`、`lz4`、`ormsgpack`、`pyyaml`、`scipy`，**沒有 pillow**（`grep -i pillow python/setup.py` 無結果）。
- 推論（未驗證）：照 README 的 `pip install "ray[rllib]" torch` 安裝，可能也會遇到這個錯誤。尚未查上游有沒有人回報，也沒有在乾淨環境重現。
- 解法：`pip install pillow`。已由人在 `~/ray-venv` 安裝 pillow 12.3.0，之後同一指令即可跑通（見上）。

### 補充：不靠官方範例，直接實測環境（這一段有跑）

`MultiAgentCartPole` 不需要 PIL，可以單獨 import 並手動操作。這個小實驗只驗證環境的資料格式，**不是**官方範例的結果：

```python
from ray.rllib.examples.envs.classes.multi_agent import MultiAgentCartPole
env = MultiAgentCartPole({"num_agents": 2})
obs, info = env.reset(seed=0)
env.step({0: 0, 1: 1})
```

實際輸出：

```
agents: [0, 1]
obs: {0: array([ 0.01369617, -0.02302133, -0.04590265, -0.04834723], dtype=float32), 1: array([ 0.01369617, -0.02302133, -0.04590265, -0.04834723], dtype=float32)}
rew: {0: 1.0, 1: 1.0}
terminated: {0: False, 1: False, '__all__': False}
truncated: {0: False, 1: False, '__all__': False}
action_spaces: {0: Discrete(2), 1: Discrete(2)}
```

### MultiAgentCartPole 的定義與三個概念

定義位置：`python/ray/rllib/examples/envs/classes/multi_agent/__init__.py`：
`MultiAgentCartPole = make_multi_agent("CartPole-v1")`；`make_multi_agent` 在 `python/ray/rllib/env/multi_agent_env.py`。
它就是把 n 個獨立的 `CartPole-v1` 疊在一起，包成一個 `MultiAgentEnv`，各個 agent 其實互不影響。

**agent id 是什麼？**
一個 agent 的名字（dict 的 key）。在 `make_multi_agent` 裡是整數 `0, 1, ..., n-1`（上面輸出的 `agents: [0, 1]`）。
別的環境可以用字串，例如 `"robot_0"`。多機器人時，每台機器人就是一個 agent id。

**obs / action / reward 為什麼是 dict？**
因為每一步不是只有一個人在看、在動、在拿分數，而是每個 agent 各一份，用 agent id 當 key 才能對應：
`obs = {0: obs_0, 1: obs_1}`，`step({0: a0, 1: a1})`，`rew = {0: r0, 1: r1}`。
也因為各 agent 不一定每步都出現（有的死掉、有的還活著），dict 可以只放「這一步有東西的 agent」。
`terminated` / `truncated` 多了一個特殊 key `"__all__"`，代表整個 episode 是否結束（見 `multi_agent_env.py` 內 `step()`）。
這就是和單智能體 gymnasium 介面最大的差別。

**policy_mapping_fn 在做什麼？**
決定「哪個 agent 用哪一個 policy（RLModule）來決定動作、並用它的資料來訓練」。官方範例裡：

```python
base_config.multi_agent(
    policies={f"p{i}" for i in range(args.num_agents)},   # {"p0", "p1"}：兩個獨立的 policy
    policy_mapping_fn=lambda aid, *a, **kw: f"p{aid}",    # agent 0 -> "p0"，agent 1 -> "p1"
)
```

這樣每個 agent 有自己的網路、各學各的。若把函式改成永遠回傳同一個名字（例如 `"shared"`），
所有 agent 就共用同一個 policy（parameter sharing）。這是之後做多機器人強化學習最常調整的地方。
（這段是讀程式碼的說明，沒有實測不同 mapping 的結果。）

### 改哪裡 → 會看到什麼（範例 2）

基準：`--num-agents=2 --stop-iters=2 --num-env-runners=2`，Tune 迴圈 54.6 s、整支 2m5s、combined return 61.0（p0 28.2、p1 32.8）、ts 8042。
以下都只改一個地方，各跑一次（單次單 seed，只看趨勢）。

| 改哪裡 | 指令 | 實測結果 | 觀察 |
|---|---|---|---|
| `--num-agents` 2 → 4 | `--num-agents=4 --stop-iters=2 --num-env-runners=2` | iter 2；2 個 iteration 共 73.1 s（基準 42.3 s）；Tune 迴圈 86.7 s；整支 2m38s；ts 8040；combined return 115.96（p0..p3 = 34.3 / 27.0 / 28.7 / 26.0）| 表多了 p2、p3 兩個 policy。combined return 是 4 個 agent 加總，所以數字變大不代表學得更好，單一 agent 約 26~34，和 2 agent 時差不多。時間變長（約 +70%），因為 batch 裡每個 agent 都要各自更新 |
| `--num-env-runners` 2 → 1 | `--num-agents=2 --stop-iters=2 --num-env-runners=1` | 2 個 iteration 共 47.9 s（基準 42.3 s）；Tune 迴圈 60.5 s；整支 2m11s；ts 8019；combined return 65.2（31.99 / 33.23）| 少一個採樣 worker，稍慢（約 +13%）。差距不大，因為 Learner 更新佔多數時間 |
| `--stop-iters` 2 → 4 | `--num-agents=2 --stop-iters=4 --num-env-runners=2` | 4 個 iteration 共 89.0 s；Tune 迴圈 104.5 s；整支 2m56s；ts 16055；combined return 137.5（73.8 / 63.6）| 訓練越久分數越高（61.0 → 137.5），每 iteration 約 22 s，時間大致隨 iteration 數線性增加 |
| `--num-envs-per-env-runner`（官方範例寫死 20，這裡覆蓋成 5）| `--num-agents=2 --stop-iters=2 --num-env-runners=2 --num-envs-per-env-runner=5` | 2 個 iteration 共 51.1 s；Tune 迴圈 66.6 s；整支 2m19s；ts 8009；combined return 68.2（33.5 / 34.7）| 沒有明顯差別，只是稍慢（每個 EnvRunner 同時跑的環境變少，推論 batch 變小；這個原因是推測，未驗證）。**注意**：這條不是原先預計的 `policy_mapping_fn`，是改用命令列可直接改的參數取代 |
| `policy_mapping_fn` 改成全部對到同一個 policy | （要改程式；官方檔不能改、也不複製）| **未實測** | — |

已查證會生效：官方範例最後呼叫的 `run_rllib_example_script_experiment`（`python/ray/rllib/examples/utils.py:380`）在第 520–521 行寫著 `if args.num_envs_per_env_runner is not None: config.env_runners(num_envs_per_env_runner=args.num_envs_per_env_runner)`，它在腳本寫死 20 之後才執行，所以命令列的 5 會蓋掉 20。

---

## 3. RLlib 新 API stack 結構

路徑都相對於 `python/ray/rllib/`。

```
Algorithm（執行整個實驗：train() / save / evaluate）             algorithms/ (algorithm.py, algorithm_config.py, ppo/)
│   由 AlgorithmConfig（PPOConfig 等）建立：config.build_algo()
│
├── EnvRunnerGroup ── n 個 EnvRunner（Ray actor，負責「收資料」） env/ (env_runner_group.py, env_runner.py)
│     ├─ SingleAgentEnvRunner / MultiAgentEnvRunner               env/single_agent_env_runner.py, env/multi_agent_env_runner.py
│     ├─ 跟環境互動：gymnasium env / MultiAgentEnv                 env/ (multi_agent_env.py)
│     ├─ 產出 Episode（SingleAgentEpisode / MultiAgentEpisode）     env/single_agent_episode.py, env/multi_agent_episode.py
│     ├─ 用 RLModule（inference-only 副本）算動作                   core/rl_module/
│     └─ connectors：env_to_module（obs -> 模型輸入）、module_to_env（模型輸出 -> action）
│                                                                  connectors/env_to_module/, connectors/module_to_env/
│
└── LearnerGroup ── m 個 Learner（負責「更新模型」）              core/learner/ (learner_group.py, learner.py)
      ├─ connectors：learner pipeline（episodes -> train batch）     connectors/learner/
      ├─ 算 loss、梯度、optimizer 更新                              core/learner/learner.py（PPO 的在 algorithms/ppo/）
      └─ 持有 RLModule（完整版，含 value function）                 core/rl_module/
            └─ 多智能體時是 MultiRLModule（包多個 RLModule）         core/rl_module/multi_rl_module.py

一個 train() = EnvRunner 採樣 -> episodes -> Learner connector 組 batch -> Learner 更新 RLModule -> 權重同步回 EnvRunner
```

對應到範例 1 的設定：`.env_runners(num_env_runners=2)` 控制 EnvRunnerGroup 大小；
`.training(lr=..., train_batch_size_per_learner=...)` 控制 Learner 端；
connectors 與 RLModule 這次都用預設值（沒有寫任何一行）。
（以上結構來自 `doc/source/rllib/key-concepts.md` 與實際資料夾；`ls` 確認過路徑存在。）

---

## 4. 下一步建議

1. 範例 1 試著把 `.environment("CartPole-v1")` 換成自己的機器人環境（gymnasium 介面）。
2. 之後做多機器人，從 `MultiAgentEnv` 開始（`env/multi_agent_env.py`），並設計 `policy_mapping_fn`。
