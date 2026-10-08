# Ray 入門範例二：Core 與 Data

環境：`~/ray-venv`（Python 3.13、Ray `3.0.0.dev0` nightly、只用 CPU，機器 4 核）。
範例檔都在 `/home/user/ray/notes/examples/`，各 80 行以內。

通用提醒：
- 請在 `/home/user/ray` 以外的目錄執行（例如 `cd ~`），避免 import 到 repo 裡的路徑。
- 範例的 `ray.init(..., include_dashboard=False)` 是我加的，原因見文末「遇到的問題」。
- 下面貼的輸出，Ray 自己印的 `INFO`/`WARNING` 日誌行已用 `grep` 濾掉（只保留範例自己 print 的內容）；未過濾的原始輸出會多出 token 驗證警告、Ray Data 執行計畫等行。

---

## 範例 A：`core_basics.py`（Ray Core）

### 怎麼跑

```bash
source ~/ray-venv/bin/activate && cd ~ && python /home/user/ray/notes/examples/core_basics.py
```

### 實際輸出（成功，整支約 16 秒，其中大部分是 Ray 啟動與關閉）

```
[依序] 結果=[0, 1, 4, 9]，耗時 4.0 秒
[平行] 這是 ObjectRef，不是值： ObjectRef(c2668a65bda616c1ffffffffffffffffffffffff0100000001000000)
[平行] 結果=[0, 1, 4, 9]，耗時 2.0 秒
[put] ref 傳給 task，總和 = 499999500000
[actor] 呼叫三次 incr： [1, 2, 3]
[actor] 再呼叫一次： 4 (接續前面的狀態)
```

（ObjectRef 的那串字每次執行都不同。）

### 每一段在示範什麼

| 段落 | 概念 |
|---|---|
| `ray.init(num_cpus=2)` | 啟動 Ray；`num_cpus` 是「邏輯 CPU 數」，決定最多幾個 task 同時跑 |
| `ray.remote(plain_square)` + `.remote()` | 把函式變成 task。`.remote()` 立刻回傳 ObjectRef，不會等結果，所以能連發很多個 |
| 印 `refs[0]` | ObjectRef 只是「取貨單」，不是值 |
| `ray.get(refs)` | 憑取貨單等結果並取回真正的值 |
| 暖機那行 | 第一次呼叫 task 要先啟動 worker process，先做掉才量得到純平行時間 |
| `ray.put` | 把大物件放進 object store，只傳 ref；ref 當參數傳給 task，task 裡會自動拿到值 |
| `Counter` actor | 加在 class 上的 `@ray.remote`；同一個 actor 的狀態（`self.n`）會跨呼叫保留 |
| `ray.shutdown()` | 關閉 Ray、釋放資源 |

### 改哪裡 → 會看到什麼變化

每一條都實際改過、跑過（改動只在暫存副本上做，原檔不變）。

| 改哪裡 | 實測結果 | 為什麼 |
|---|---|---|
| `NUM_CPUS = 1` | 平行 **4.0 秒**（和依序一樣，沒變快） | 只有 1 個 CPU，task 只能一個接一個跑 |
| `NUM_CPUS = 4` | 平行 **1.0 秒**（依序仍 4.0） | 4 個 task 可以同時跑 |
| `NUM_TASKS = 8`（`NUM_CPUS=2`） | 依序 8.0 秒、平行 **4.0 秒** | 8 個 task、每次同時跑 2 個，要 4 輪 |
| `NUM_TASKS = 2`（`NUM_CPUS=2`） | 依序 2.0 秒、平行 **1.0 秒** | 2 個 task 剛好同時跑完 |

規律：平行時間約等於 `ceil(NUM_TASKS / NUM_CPUS)` 秒。

---

## 範例 B：`data_basics.py`（Ray Data）

### 怎麼跑

```bash
source ~/ray-venv/bin/activate && cd ~ && python /home/user/ray/notes/examples/data_basics.py
```

### 實際輸出（成功，整支約 17 秒；已濾掉 Ray 日誌行）

```
筆數 count: 100
欄位 schema:
 Column  Type
------  ----
id      int64
x       double
CSV 內容: [{'id': 0, 'price': 10}, {'id': 1, 'price': 20}, {'id': 2, 'price': 30}, {'id': 3, 'price': 40}, {'id': 4, 'price': 50}]
轉換後 schema:
 Column    Type
------    ----
id        int64
x         double
x_double  double
take(3):
   {'id': 0, 'x': 0.0, 'x_double': 0.0}
   {'id': 1, 'x': 0.5, 'x_double': 1.0}
   {'id': 2, 'x': 1.0, 'x_double': 2.0}
train 筆數: 80，test 筆數: 20
```

### 每一段在示範什麼

| 段落 | 概念 |
|---|---|
| `from_items` | 用 list of dict 在記憶體建小資料，每個 dict 一列 |
| `count()` / `schema()` | 看筆數與欄位型別，先確認資料長得對不對 |
| pandas 寫 CSV → `read_csv` | 讀檔案資料；範例自己帶資料，不用下載 |
| `map_batches(..., batch_format="pandas")` | 一批一批轉換，函式拿到的是 DataFrame，新增 `x_double` 欄位 |
| `take(3)` | 取前 3 列。Ray Data 是 lazy，`take`/`count` 這類動作才會真的執行（所以原始輸出裡每次 take/count 都會出現一段執行計畫日誌） |
| `train_test_split(test_size=0.2)` | 切成 80 / 20。預設不洗牌 |

### 改哪裡 → 會看到什麼變化

| 改哪裡 | 實測結果 | 為什麼 |
|---|---|---|
| `TEST_SIZE = 0.3` | `train 70，test 30` | 測試集占 30% |
| `N = 1000` | `train 800，test 200` | 資料變多，比例不變 |
| `ds.take(3)` 改 `ds.take(5)` | 多印出 id 3、4 兩列（標籤文字還是寫「take(3):」，因為標籤是寫死的字串） | `take(n)` 取前 n 列 |
| `df["x"] * 2` 改 `* 10` | `x_double` 變成 0.0、5.0、10.0 | 轉換函式的計算變了 |
| `train_test_split(..., shuffle=True, seed=1)` | 筆數仍 80/20，但 train 前三列變成 `id` 44、5、27，不再是 0、1、2 | 先全域洗牌再切 |
| `batch_format="pandas"` 改 `"numpy"` | **沒有變化**，輸出與原本相同 | numpy 格式的 batch 是 dict（欄位名對應陣列），`batch["x_double"] = batch["x"] * 2` 這句剛好也能運作；但 `df` 就不是 DataFrame 了，若用 pandas 專屬方法（如 `df.assign`）會出錯（此點**未實測**） |

---

## 遇到的問題與怎麼修

1. **儀表板啟動失敗，`ray.init()` 卡約 60 秒**。第一次跑（沒有 `include_dashboard=False`）整支花了 1 分 15 秒，日誌出現
   `FrontendNotFoundError: Dashboard build directory not found ... site-packages/ray/dashboard/client/build`。
   原因（已查證）：nightly wheel 本身有編好的前端（`site-packages/ray/dashboard.bak/client/build` 存在），但 `setup-dev.py` 把 `ray/dashboard` 換成指向 repo 的 symlink，而 repo 裡的 `python/ray/dashboard/client/build` 不存在（前端要另外用 npm 編）。修法二選一：(a) `ray.init(..., include_dashboard=False)`，範例採用這個，整支降到約 16 秒；(b) 照 `doc/source/ray-contribute/development.md` 第 126 行，用 `python python/ray/setup-dev.py -y --skip dashboard` 不連結 dashboard。一般 pip 安裝的 Ray 不需要這個參數。
2. **平行計時偏高**。第一次版本平行是 2.8 秒（預期 2.0），因為第一次呼叫 task 要啟動 worker。修法：計時前先用空 task 暖機，之後穩定量到 2.0 秒。
3. **依序對照組原本寫得很彆扭**（用 list comprehension 加 `if time.sleep(1) is None`），改成一般函式 `plain_square`，再用 `ray.remote(plain_square)` 包成 task，兩邊用同一個函式比較。
4. 日誌裡的 `Token authentication is enabled` 警告是 nightly 的預設行為，不影響執行，沒有處理。
5. 時間數字是單次量測，你自己跑可能差 0.1 秒左右。

## 未實測的項目

- 範例 B 表格最後一列中「用 pandas 專屬方法在 numpy batch 上會出錯」這句推論：**未實測**（其餘各列皆已實測）。
- 範例 A、範例 B 表格其餘各條皆已實際修改並執行。
