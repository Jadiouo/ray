# 第 3 階段：Issue 分析

查詢日期：2026-10-08。

## 讀取限制
- 這個 session 的 GitHub API 權限只開到 `jadiouo/ray`，讀 `ray-project/ray` 的 issue 會被拒絕（GitHub 工具和 REST API 都是 403）。
- 可以用的管道：
  - (a) WebFetch 讀公開網頁。交回來的是小模型的**摘要，不是原文**；**看不到留言**，頁面顯示要登入才能參與討論。
  - (b) git 唯讀抓取 PR 的 ref（`refs/pull/N/head`），這是原文，可以信任。
- 所以「有沒有人認領」目前**無法判斷**，需要人工去看留言。

## 三個先前看過的 issue：最新狀態

| Issue | 標題 | 狀態／標籤（WebFetch 摘要） | 有沒有人在做 |
|---|---|---|---|
| #66472 | train_test_split 浮點截斷導致大小算錯、stratify 可能產生空的測試集 | Open；bug, community-backlog, data, stability, triage | **[已查證] 已經有修正 PR #66499**：作者 ege-arhan，2026-09-25 送出，只改 `python/ray/data/dataset.py`（+63/−7），commit 訊息寫明兩個問題都修了。依社群習慣，**這題不要再做** |
| #66077 | [Data] Raise a descriptive error when a partition value cannot be cast | Open；bug, community-backlog, data, triage, usability；沒有指派人，沒有關聯的 PR | **使用者確認：已經有人在做**（2026-10-08），不考慮 |
| #65759 | [Data] Add HDF5 datasource support | Open；community-backlog, data, usability；沒有指派人，沒有關聯的 PR；本文提到可以參考 PR #63821（`read_lerobot`）的寫法 | 使用者貼了一則留言：有人提供用 `read_binary_files`/`from_items` + h5py 代用的寫法，並說「happy to help test if you open a PR」。[推論] 留言者沒有要自己做。其他留言未知。完整分析見 `06-issue-65759.md` |

- [推論] 這三題的標籤都**沒有** `good-first-issue`，而是 `community-backlog`。goodfirstissue.org 收錄它們，可能是因為它用的篩選標準不同。
- 注意 #66077 和 #66472 都有 `triage` 標籤。[推論] 這代表維護者還沒分類完成。依社群習慣，可能要先留言詢問維護者再動手。

## 目前 open 的 `good-first-issue`（WebFetch，第 1 頁，共 71 個）

和 Ray Data 相關的：

| Issue | 標題 | 開立日期 | 留言數 |
|---|---|---|---|
| #65129 | write_lance is incompatible with PyLance 6.x (removed `storage_options_provider`) | 2026-07-30 | 4 |
| #64880 | Unity Catalog Delta Table Reads Won't Work with GCP Databricks | 2026-07-20 | 6 |
| #60935 | Profile the vLLM engine in data LLM release benchmarks | 2026-02-10 | 8 |
| #58674 | Ray Data Compute Expressions | 2025-11-16 | 14 |
| #57825 | DAG inconsistency in `Operator._apply_transform` when partial transformation occurs | 2025-10-16 | 9 |
| #57729 | map_batches fails with asyncio.run() in func and chaining with async actor | 2025-10-15 | 11 |

- 第 1 頁**沒有** RLlib 的 good-first-issue；第 2、3 頁還沒看。
- [推論] 留言數多、開立很久的 issue（例如 #58674 有 14 則留言），很可能已經有人在做，或在等維護者決定。

## 自己找到、還沒查上游的候選（見 `00-session-log.md`）
- 觀察 7：`test_train_test_split` 是不穩定的測試（沒有設定 `preserve_order`）。根本原因已經查證。
- 觀察 2：RLlib 的 `rllib` extra 沒有列 pillow，但載入演算法時一定要用到它。
