"""Ray Data 入門：建資料、讀 CSV、map_batches、切 train/test。

執行方式（請在 /home/user/ray 以外的目錄）：
    source ~/ray-venv/bin/activate && cd ~ && python /home/user/ray/notes/examples/data_basics.py
"""
import os
import tempfile

import pandas as pd
import ray

N = 100          # 資料筆數
TEST_SIZE = 0.2  # 測試集比例

# num_cpus=2：Ray Data 的各個步驟會變成 task 並行，所以也要先 init 並限制 CPU。
# include_dashboard=False：此環境的 nightly 缺少儀表板前端檔，不關會卡約 60 秒（正常安裝不需要）。
ray.init(num_cpus=2, include_dashboard=False)

# ---- 1. 從記憶體建資料 ----
# 為什麼用 from_items：最快的方式做出一份小資料；list of dict，每個 dict 是一列，key 是欄位名。
ds = ray.data.from_items([{"id": i, "x": i * 0.5} for i in range(N)])
print("筆數 count:", ds.count())
print("欄位 schema:\n", ds.schema())  # 為什麼印 schema：確認欄位名和型別是不是你預期的

# ---- 2. 讀 CSV ----
# 為什麼先用 pandas 寫檔：這樣範例自己帶資料，不用另外下載。
tmp_dir = tempfile.mkdtemp()  # 暫存資料夾，作業系統之後會清掉
csv_path = os.path.join(tmp_dir, "small.csv")
pd.DataFrame({"id": range(5), "price": [10, 20, 30, 40, 50]}).to_csv(csv_path, index=False)
csv_ds = ray.data.read_csv(csv_path)  # 傳資料夾或檔案路徑都可以，也可以傳多個檔案的 list
print("CSV 內容:", csv_ds.take_all())

# ---- 3. map_batches：一批一批轉換，比逐列 map 快 ----
def add_double(df: pd.DataFrame) -> pd.DataFrame:
    # 為什麼 batch_format="pandas"：下面傳進來的 df 就是 DataFrame，用熟悉的 pandas 語法就好。
    df["x_double"] = df["x"] * 2  # 新增一個欄位
    return df  # 一定要回傳 DataFrame（或 dict / table）

ds = ds.map_batches(add_double, batch_format="pandas")
# 為什麼轉換後才印：Ray Data 是 lazy（延遲執行），真的要用結果時（take/count）才會跑。
print("轉換後 schema:\n", ds.schema())
print("take(3):")
for row in ds.take(3):  # take(n) 回傳前 n 列，每列是 dict
    print("  ", row)

# ---- 4. 切 train / test ----
# 為什麼用 train_test_split：機器學習要留一部分資料不參與訓練，用來驗證模型。
# 它預設不洗牌（前 80% 是 train、後 20% 是 test）；資料若有排序，記得加 shuffle=True, seed=42。
train, test = ds.train_test_split(test_size=TEST_SIZE)
print(f"train 筆數: {train.count()}，test 筆數: {test.count()}")

ray.shutdown()
