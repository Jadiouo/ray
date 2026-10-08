# 學習紀錄與觀察筆記

這份是「一路上看到的事」的流水帳，之後問問題時從這裡開始找。
標記方式：**[已查證]** 有親自確認，附出處；**[推論]** 還沒確認；**[待查]** 還沒處理的問題。

## 筆記索引

| 檔案 | 內容 |
|---|---|
| `00-session-log.md` | 本檔：環境、觀察、待查問題 |
| `01-ray-map.md` | Ray 地圖：元件、路徑、測試慣例 |
| `02-examples-core-data.md` | Ray Core / Ray Data 範例與「改哪裡」表 |
| `03-examples-rllib.md` | RLlib CartPole、多智能體範例、API stack 結構 |
| `04-contribution-flow.md` | 貢獻流程：PR、lint、測試、CI |
| `05-issues.md` | 第 3 階段 issue 分析 |

## 環境（每次開新 session 都要重做）

雲端容器會被回收，`~/ray-venv` 不會保留。要重建的話，在 repo 根目錄依序執行：

```bash
python3 -m venv ~/ray-venv && source ~/ray-venv/bin/activate
python -m pip install --upgrade pip wheel
# wheel 檔名的 cp313 要對應 python --version
pip install -U "ray[default] @ https://s3-us-west-2.amazonaws.com/ray-wheels/latest/ray-3.0.0.dev0-cp313-cp313-manylinux2014_x86_64.whl"
python python/ray/setup-dev.py -y          # 或加 --skip dashboard，見下方觀察 1
pip install "numpy>=1.20" "pandas>=2.2.3" "pyarrow>=17.0.0" fsspec pytest pytest-asyncio pytest-aiohttp
pip install "tensorboardX>=1.9" dm_tree "gymnasium==1.2.2" lz4 "ormsgpack>=1.7.0" scipy pillow torch
```

- 先確認 `python -c "import ray; print(ray.__commit__)"` 和 `git rev-parse HEAD` 差不多。差太多的話，repo 的 Python 和 wheel 的 C++ 可能對不上。**[已查證]** 2026-10-08 兩者都是 `0fe2388`。
- 設好 symlink 之後**不要** `pip install -U ray` 或 `pip uninstall ray`（`doc/source/ray-contribute/development.md:131`）。
- 網路政策擋掉 `download.pytorch.org`，所以 torch 從 PyPI 安裝，會多裝約 3 GB 的 CUDA 函式庫，但只用 CPU 也能正常執行。

## 觀察

### 1. `ray.init()` 白等約 60 秒（dashboard 前端不存在）[已查證]
- 現象：日誌出現 `FrontendNotFoundError: Dashboard build directory not found ... site-packages/ray/dashboard/client/build`。
- 原因：wheel 原本有 `dashboard/client/build`（備份在 `site-packages/ray/dashboard.bak/client/build`），但 `setup-dev.py` 把 `ray/dashboard` 換成指向 repo 的 symlink，而 repo 沒有編好的前端。
- 解法：`ray.init(include_dashboard=False)`，或 `setup-dev.py -y --skip dashboard`（`development.md:126`）。
- [推論] 第 0 階段 `test_train_test_split` 跑了 72 秒，大部分是在等這個。

### 2. RLlib 載入任何演算法都需要 Pillow [已查證]，可能是上游問題 [推論]
- import 鏈：`ray/tune/registry.py _has_rllib_trainable` → `ray/rllib/__init__.py:35 _register_all`（註冊**所有**演算法）→ `rllib/algorithms/registry.py:32 _import_dreamerv3` → `dreamerv3/utils/summaries.py:14` → `dreamerv3/utils/debugging.py:4 from PIL import Image, ImageDraw`。
- `python/setup.py` 的 `rllib` extra（約第 333–340 行）沒有列 pillow。
- [推論] 照 `python/ray/rllib/README.md` 的 `pip install "ray[rllib]" torch` 安裝，用 `get_trainable_cls` 或 Tune 時可能也會遇到。
- [待查] 在乾淨環境重現；上游有沒有人回報過；修法是把 import 移進函式裡（lazy import），還是把 pillow 加進 extra。

### 3. 官方範例的命令列參數會蓋掉腳本裡寫死的設定 [已查證]
- `python/ray/rllib/examples/utils.py:520-521`：`run_rllib_example_script_experiment` 會用 `--num-envs-per-env-runner` 等參數重設 config，而且是在腳本設定好 `base_config` 之後才執行。

### 4. 文件路徑和印象不同 [已查證]
- 開發文件是 `doc/source/ray-contribute/development.md`（不是 `.rst`）；`doc/AGENTS.md` 規定新文件一律用 MyST Markdown。
- Ray Core 的文件在 `doc/source/core/`，不是 `ray-core/`。
- `python/ray/rllib/tests` 不存在；RLlib 的測試分散在各子資料夾的 `tests/` 裡。

### 5. Ray Data 測試分兩種 [已查證]
- `python/ray/data/tests/unit/`：不啟動 Ray，要求毫秒級；`conftest.py` 會擋 `ray.init()` 和 `time.sleep()`（`tests/unit/README.md`）。
- `python/ray/data/tests/`：需要 Ray 叢集的測試，常用 fixture 是 `ray_start_regular_shared_2_cpus`（`python/ray/tests/conftest.py:676`）。
- 所有 pytest 預設 timeout 180 秒（`pytest.ini:12-13`）。

### 6. RLlib 效能觀察（4 CPU 的雲端容器，只能當參考）
- CartPole PPO 每個 iteration 約 16 秒，時間主要花在 Learner 更新，不在採樣（subagent 的觀察，[推論]）。
- `num_env_runners` 從 2 改成 3 沒有變快；`train_batch_size=1000` 時每個 iteration 降到約 4 秒。

### 7. `test_train_test_split` 結果看運氣：測試沒有固定區塊順序 [已查證]
- 現象：用 `-k train_test_split` 跑，3 次都失敗，`assert [0, 1, 4, 5, 6, 7] == [0, 1, 2, 3, 4, 5]`；單獨跑 2 次都通過。
- 根本原因：
  - 不 shuffle 時，`train_test_split` 會呼叫 `split_at_indices`，依照區塊**到達的順序**切出前 N 列（`python/ray/data/dataset.py:3063` `bundle: RefBundle = self._execute()`）。
  - `preserve_order` 預設是 `False`（`python/ray/data/_internal/execution/interfaces/execution_options.py:411`）。`range(8)` 分成 4 個區塊，哪個先讀完就排在前面。
  - 官方文件寫明預設不保證順序（`doc/source/data/performance-tips.md:360`、`doc/source/data/shuffling-data.md:151`）。
  - 同一個測試檔裡，其他依賴順序的測試都有設 `preserve_order = True`（`test_split.py:201,267,298`），只有 `test_train_test_split`（`:746`）沒設。
  - docstring 裡同一個範例在 CI 跑 doctest 時是穩定的，因為 doctest 外掛會先設 `preserve_order = True`（`python/ray/data/tests/doctest_pytest_plugin.py:43`）。
- 證明（subagent 的實驗，我審過）：用 pytest 外掛攔截後，失敗時的區塊順序是 `[[0,1],[4,5],[6,7],[2,3]]`，切出前 6 列剛好得到 `[0,1,4,5,6,7]`。強制設 `preserve_order=True` 時 2/2 通過，不設時 2/2 失敗。
- 判斷：**測試不穩定（flaky test）**，不是 Ray 的執行錯誤，也不是本機環境的問題。
- [推論] 可能的修法：在測試裡加 `DataContext.get_current().execution_options.preserve_order = True`，或改成跟順序無關的斷言（例如比較 `sorted(...)` 和筆數）。
- [推論] docstring 範例看起來像在保證順序，但一般使用者預設拿不到這個順序。這可能算文件不清楚的地方。
- [待查] 上游有沒有人回報過這個 flaky test；它在 CI 是不是真的會失敗（https://flakey-tests.ray.io/ 可查）。這和 #66472（大小算錯）是不同的問題，大小是對的。

### 8. 跑 Ray Data 的完整測試需要 polars [已查證]
- `test_streaming_train_test_split_*` 用到 `Dataset.join`，錯誤訊息：`ImportError: Dataset.join depends on 'polars'... pip install polars`。目前 venv 沒有裝。

### 9. 貢獻文件之間不一致 [已查證]（細節見 `04-contribution-flow.md`）
- 合併前的 label：`CONTRIBUTING.rst:42`、`getting-involved.md:125` 寫 `test-ok`；`ci.md:36-40` 寫 `go`，而且外部貢獻者沒有權限加，要由 committer 加。[推論] 以 `ci.md` 為準。
- 新測試放哪裡：`getting-involved.md:112` 寫 `python/ray/tests/`，但 Ray Data 的 pre-commit 規定要放 `python/ray/data/tests/`（`.pre-commit-config.yaml:225`）。
- pre-commit 3.5.0 第一次跑 `pre-commit run --files <檔案>` 要約 2.5 分鐘建立 hook 環境，之後就快了。

## 待查問題清單
- [ ] 觀察 2：Pillow 問題上游有沒有人回報（第 3 階段一起查）
- [x] 觀察 7：根本原因找到了（測試沒有固定區塊順序）
- [ ] 觀察 7：查上游有沒有人回報，以及 flakey-tests.ray.io 的紀錄
- [x] 三個 issue 的狀態：#66472 已經有 PR #66499；#66077 和 #65759 的留言讀不到（見 `05-issues.md`）

## 進度
- 2026-10-08 第 0 階段：環境建好，`test_train_test_split` 通過
- 2026-10-08 第 1 階段：地圖與 Core/Data/RLlib 範例完成，推到 `lex/notes`
- 2026-10-08 第 2 階段：貢獻流程筆記完成（`04-contribution-flow.md`）；觀察 7 已找到原因
- 2026-10-08 第 3 階段：GitHub API 讀不到 ray-project/ray 的留言，等使用者貼上 issue 內容
