"""RLlib 最小範例：PPO + CartPole-v1（新 API stack）。

執行方式（在 ~ 執行，不要在 repo 目錄裡跑）：
    source ~/ray-venv/bin/activate
    python /home/user/ray/notes/examples/rllib_cartpole.py
    # 想改參數：
    python /home/user/ray/notes/examples/rllib_cartpole.py --lr 0.001 --num-env-runners 1

目標是「看懂結構」，不是訓練到好，所以只跑幾個 iteration。
"""
import argparse
import time

import ray
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.utils.metrics import ENV_RUNNER_RESULTS, EPISODE_RETURN_MEAN

# 為什麼用常數而不是直接寫字串？
# 結果 dict 的 key 是 RLlib 內部定義的（ray/rllib/utils/metrics/__init__.py），
# 用常數可以避免打錯字，版本改名時也比較容易發現。
# 實際取值：ENV_RUNNER_RESULTS == "env_runners"、EPISODE_RETURN_MEAN == "episode_return_mean"

parser = argparse.ArgumentParser()
parser.add_argument("--iters", type=int, default=4)  # 訓練幾個 iteration
parser.add_argument("--lr", type=float, default=5e-5)  # 學習率（PPO 預設 5e-5）
parser.add_argument("--train-batch-size", type=int, default=4000)  # 每次更新用幾步資料
parser.add_argument("--num-env-runners", type=int, default=2)  # 平行採樣的 worker 數
args = parser.parse_args()

# 這台機器是從原始碼安裝，沒有 build dashboard 前端，啟動 dashboard 會失敗並卡約 60 秒
# （錯誤不致命，但很浪費時間），所以關掉。有正常安裝的環境可以拿掉這行。
ray.init(include_dashboard=False)

# Config 只是「設定表」，這裡還沒有啟動任何東西。
# 用鏈式呼叫，每個方法管一類設定：environment / env_runners / training。
config = (
    PPOConfig()
    # 要訓練的環境，字串會交給 gymnasium.make()
    .environment("CartPole-v1")
    # EnvRunner = 負責跟環境互動、收集資料的 Ray actor。
    # 這台機器有 4 顆 CPU：每個 EnvRunner 佔 1 顆，driver（跑 Learner）佔 1 顆，
    # 所以最多開 2~3 個，超過會因為 CPU 不夠而卡住。
    .env_runners(num_env_runners=args.num_env_runners)
    # 訓練相關超參數。新 API stack 用 train_batch_size_per_learner
    .training(lr=args.lr, train_batch_size_per_learner=args.train_batch_size)
)

# build_algo() 才真的啟動 Ray、建立 EnvRunner 與 Learner。
algo = config.build_algo()

for i in range(args.iters):
    t0 = time.time()
    # train() = 一個 iteration：EnvRunner 採樣 -> Learner 更新 -> 同步權重回 EnvRunner
    result = algo.train()
    dt = time.time() - t0
    # 結果是巢狀 dict：result["env_runners"]["episode_return_mean"]
    # 第一個 iteration 可能還沒有任何完成的 episode，所以用 .get 避免 KeyError
    ret = result[ENV_RUNNER_RESULTS].get(EPISODE_RETURN_MEAN)
    print(f"iter {i + 1}: episode_return_mean={ret}  time={dt:.1f}s")

# 釋放 EnvRunner / Learner 等 actor，不然程式結束前資源不會歸還
algo.stop()
