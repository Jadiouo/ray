# Ray 貢獻流程（給第一次參與大型開源專案的人）

> 範圍：只改 Python、不編譯 C++。每個事實都附出處（`檔案:行號`）。
> 「推論：」開頭是我自己的判斷，不是文件原文。「找不到（查過：…）」代表 repo 內沒有明講。
> 以下路徑都相對於 `/home/user/ray`；`getting-involved.md` 等指 `doc/source/ray-contribute/` 底下的檔案。

## 0. 全流程一覽

改程式 -> 本機跑相關測試 -> `pre-commit` lint -> `git commit -s` -> 開 PR（填模板）-> Buildkite 跑 microcheck -> reviewer/assignee 審 -> committer 加 `go` 跑完整測試 -> 合併（全部 commit 會被 squash，`getting-involved.md:114`）。

## 1. PR 標題、描述、模板

**PR 模板（三個欄位）**（`.github/PULL_REQUEST_TEMPLATE.md:1-15`）：
- `## Description`：「Briefly describe what this PR accomplishes and why it's needed.」（`.github/PULL_REQUEST_TEMPLATE.md:9`）
- `## Related issues`：用 "Fixes #1234"、"Closes #1234" 或 "Related to #1234" 連結（同檔第 12 行）
- `## Additional information`：選填，實作細節、API 變更、用法範例、截圖（同檔第 15 行）
- 模板開頭有「Remove these instructions before submitting your PR」（第 4 行），送出前要把引言說明刪掉。
- 「Mark as draft if you want early feedback」（第 6 行）：想先要回饋可以先開 draft。

**標題格式**：
- 找不到明文規定（查過：`CONTRIBUTING.rst`、`AGENTS.md`、`getting-involved.md`、`.github/PULL_REQUEST_TEMPLATE.md`、`.github/workflows/*`、`docs.md`）。沒有「合法前綴清單」。
- 只找到旁證：(a) issue 模板標題是 `"[<Ray component: Core|RLlib|etc...>] "`（`.github/ISSUE_TEMPLATE/bug-report.yml:2`，這是 issue，不是 PR）；(b) 文件 cherry-pick PR 標題是 `[cherry-pick][X.Y.Z][docs] ...`（`docs.md:452`）；(c) 某個 skill 建議 `[doc] Soft-wrap prose in <area>`（`doc/.claude/skills/ray-soft-wrap/SKILL.md:84`）。
- 推論：實務上 PR 標題習慣用 `[Data]`、`[Core]`、`[Serve]`、`[doc]` 這類元件前綴，但 repo 內沒有文件規定，開 PR 前請看 `gh pr list --repo ray-project/ray --state merged` 上同元件的標題模仿。
- 有一條審查規則會檢查標題太籠統：標題如 "fix bug"、"update"、"changes" 會被提醒（`src/ray/.cursor/BUGBOT.md:14-18`）。

**描述要寫什麼**：同一個規則要求描述說明「這解決什麼問題、怎麼解決」，各一句即可；也可補充為何重要、為何選此做法（`src/ray/.cursor/BUGBOT.md:16-28`）。空白或只剩模板文字會被提醒（同檔第 16 行）。
推論：`.cursor/BUGBOT.md` 是給自動審查機器人的規則，不是人類貢獻指南，但它反映維護者期待。

**AGENTS.md 對 AI 協助 PR 的額外要求**（`AGENTS.md`）：
- 違反政策的 PR 可能被直接關閉（第 3-4 行）。
- 開 PR 前查重複：`gh issue view <n> --repo ray-project/ray --comments`、`gh pr list --repo ray-project/ray --state open --search "..."`（第 15-24 行）；已有 PR 就去留言，不要再開（第 26-27 行）。
- 不開瑣碎 PR（單一 typo、單一風格調整等），除非和實質工作綁在一起或先和維護者協調（第 33-36 行）。
- 純 AI 代理 PR 不允許；人類提交者必須理解並能捍衛每一行，且要在本機跑過相關測試（第 40-43 行）。
- PR 描述必須寫明三件事：為何不是重複工作、跑了哪些測試指令與結果、有使用 AI 協助（第 44-47 行）。
- 若是重複、瑣碎、或人無法測試/捍衛，就不要開 PR（第 49-53 行）。
- 推論：大學生第一個 PR 若是單純修一個 typo，依 `AGENTS.md:33-36` 不適合單獨開；這條是寫給 AI 輔助貢獻的，但精神值得所有人遵守。

## 2. DCO sign-off

- 要：「Every commit needs that trailer to pass the Developer Certificate of Origin (DCO) check.」（`getting-involved.md:111`）。`AGENTS.md:74-82` 也說所有 commit 都要 sign-off，用 `git commit -s -m "..."`。
- 怎麼加：`git commit -s`（`getting-involved.md:111`；`publishing-examples.md:70`）。
- 自動加：跑 `setup_hooks.sh`，它把 `ci/lint/pre-push` 與 `ci/lint/prepare-commit-msg` 連結進 `.git/hooks`（`setup_hooks.sh:13-14`）。`prepare-commit-msg` 會用 `git interpret-trailers` 加 `Signed-off-by: <user.name> <user.email>`，且 `user.name`/`user.email` 沒設會報錯退出（`ci/lint/prepare-commit-msg:7-23`）。
- 忘了加怎麼補：找不到（查過：`getting-involved.md`、`CONTRIBUTING.rst`、`development.md`、`AGENTS.md`、`.github/` 全部、`ci.md`）。
  - 推論：最後一個 commit 用 `git commit --amend -s --no-edit`；多個 commit 用 `git rebase --signoff <base>` 後 force-push。文件只有 cherry-pick 版本：`git cherry-pick -x --signoff`（`docs.md:453`）。
  - 注意：`getting-involved.md:114` 說合併衝突時用 `git pull . upstream/master`、「Don't use rebase」，所以改寫歷史前建議先問 reviewer。
- DCO 檢查本身的設定（如 DCO GitHub App）：找不到（查過：`.github/` 下只有 `CODEOWNERS`、`ISSUE_TEMPLATE/`、`PULL_REQUEST_TEMPLATE.md`、`dependabot.yml`、4 個 workflow，沒有 DCO 設定）。

## 3. Lint 與格式化

文件說的：
- 風格：Python 遵循 Black code style，import 遵循 PEP8；但「more important for code to be in a locally consistent style」（`getting-involved.md:175`）。
- 裝 lint 依賴：`pip install -c python/requirements_compiled.txt -r python/requirements/lint-requirements.txt`（`getting-involved.md:265`）。
- 指定版本：`pip install -U pre-commit==3.5.0`（`getting-involved.md:273`）；`python/requirements/lint-requirements.txt:3` 也是 `pre-commit==3.5.0`。
- 設定檔：`.pre-commit-config.yaml` 設定所有 lint/格式檢查（`development.md:435`）。裡面的 ruff 是 `v0.8.4`（第 45 行）、black 是 `22.10.0`（第 95 行）。
- 只檢查自己改的檔案：`pre-commit run --files $(git diff --name-only HEAD)`；不加 `--files` 只會檢查 staged 檔案（`.claude/skills/lint/SKILL.md:11,14`）。
- 只跑 ruff 全部檔案：`pre-commit run ruff -a`（`getting-involved.md:275`）。
- 暫時略過：`git commit -n`（`development.md:442-446`）。
- 沒放進 pre-commit 的檢查（Python README、bazel format、clang-tidy）：`getting-involved.md:287-306`。純 Python 改動通常用不到。
- CI 端：`lint: pre_commit` 步驟執行 `./ci/lint/lint.sh pre_commit`（`.buildkite/lint.rayci.yml:88-96`），內容是 `pre-commit run "$HOOK" --all-files --show-diff-on-failure`（`ci/lint/lint.sh:47`）。`ci.md:85` 也說 pre_commit 跑 `--all-files`。
- 純文件（`.md`/`.rst`/圖片）PR 不跑大部分 lint（`ci.md:79-89`）。

文件之間不一致（我發現的）：
1. `pre-commit` 版本：`getting-involved.md:273` 與 `lint-requirements.txt:3` 釘 3.5.0；`development.md:421,438` 與 `lint/SKILL.md:19` 沒釘版本（SKILL 有 `-c python/requirements_compiled.txt`，該檔第 1612 行釘 `pre-commit==3.5.0`，所以推論：加 `-c` 的話結果也是 3.5.0；`development.md:438` 的裸 `pip install pre-commit` 則不保證）。
2. `getting-involved.md:175` 說用 Black，但 `.pre-commit-config.yaml` 同時有 ruff 與 black 兩套 hook（第 44-48、94-97 行）。以 pre-commit 實際跑的為準。

**實際操作紀錄**（日期 2026-10-08，環境：`~/ray-venv`，Python 3.13.16）：

```bash
source ~/ray-venv/bin/activate
pip install -U pre-commit==3.5.0      # 約 1.9 秒；pre-commit 3.5.0 裝好
cd /home/user/ray
time pre-commit run --files python/ray/data/dataset.py
```
- 沒有執行 `pre-commit install`（會改 `.git/hooks`）。
- 耗時 `real 2m37s`。第一次跑會為各 hook 下載並建立環境（輸出一堆 `[INFO] Initializing/Installing environment for https://github.com/...`），所以慢；推論：之後重跑會快很多（hook 環境有快取）。網路沒有被擋。
- 結果（節錄，其餘為 Skipped：`no files to check`）：

```
trim trailing whitespace........Passed
fix end of files................Passed
check for added large files.....Passed
check python ast................Passed
ruff............................Passed   (出現兩次，兩個 ruff hook)
pydoclint.......................Passed
black...........................Passed
use logger.warning(.............Passed
check for not-real mock methods.Passed
Check for Ray docstyle violations.Passed
Check for Ray import order violations.Passed
Check that links to files on Ray's master branch resolve.Passed
```
- 沒有 hook 自動修改檔案：跑完 `git status --short` 為空，不需要 `git checkout --`。

## 4. 只跑跟自己改動有關的測試

文件說的：
- 先裝測試依賴：`pip install -c python/requirements_compiled.txt -r python/requirements/test-requirements.txt`（`getting-involved.md:140`；`development.md:428`）。Ray Data/ML 的需求檔在 `python/requirements/`（`development.md:431`）。
- 整套太大，只跑相關檔案：`python -m pytest -v -s python/ray/tests/test_basic.py`（`getting-involved.md:145-149`），並註解「Directly calling `pytest -v ...` may lose import paths」（第 148 行）。
- 單一測試：`python -m pytest -v -s test_file.py::name_of_the_test`（`getting-involved.md:156`）。
- `-k` 關鍵字篩選：repo 文件沒有講解（查過：`getting-involved.md`、`development.md`、`testing-tips.md`），但是本篇實測用了（見下）。這是 pytest 本身功能，推論：`-k` 是子字串比對，會連名字相近的測試一起選到。
- 預設單一測試逾時 180 秒（`AGENTS.md:64`；`pytest.ini:12-13`）。
- 新功能或修 bug 要加測試，放在 `ray/python/ray/tests/` 相關檔案（`getting-involved.md:112`）。Ray Data 的測試則必須放 `python/ray/data/tests/`，否則 pre-commit hook 失敗（`.pre-commit-config.yaml:220-225`）。

`testing-tips.md` 的四個建議：
1. `ray.init(num_cpus=2)` 固定資源量，避免 CI 核心少造成 flaky（`testing-tips.md:15-25`）。
2. 盡量共用 Ray cluster（`setUpClass`/`tearDownClass`），啟停一次約 5 秒；但設環境變數或 process 全域狀態時不安全（`testing-tips.md:27-64`）。
3. 用 `ray.cluster_utils.Cluster` 模擬多節點（`testing-tips.md:69` 起）。
4. 用 pytest-xdist 平行跑要小心，服務同時啟動容易逾時、造成 flaky（`testing-tips.md:130-132`）。

**Ray Data `tests/unit/` 與 `tests/` 的差別**：
- `tests/unit/` 只放純 Python 邏輯的測試：不能初始化 Ray runtime、不能 `time.sleep()`、不依賴外部服務/檔案系統/網路（`python/ray/data/tests/unit/README.md:3-18`）。
- 由 `python/ray/data/tests/unit/conftest.py` 強制：呼叫 `ray.init()` 與 `time.sleep()` 會報錯（README 第 22-24 行；conftest 第 6-12 行有 `disallow_ray_init`）。
- 審查規則同樣寫明：不得使用 `ray_start_` 開頭的 fixture、不得呼叫需要 cluster 的 `ray.*`（`src/ray/.cursor/BUGBOT.md:34-39`）；需要 cluster 的測試放上層 `tests/`。反過來，頂層測試若其實是純邏輯，會被建議搬到 `tests/unit/`（同檔第 44-46 行）。
- 上層 `python/ray/data/tests/` 才是用 `ray_start_regular_shared_2_cpus` 之類 fixture 啟動 Ray 的整合測試（見 `test_split.py:746`）。

**範例：改了 `dataset.py` 的 `train_test_split`（定義在 `python/ray/data/dataset.py:3176`）**

```bash
grep -rln "train_test_split" python/ray/data/tests
grep -n "def test.*train_test_split" python/ray/data/tests/test_split.py
```
- 含此字串的測試檔：`test_split.py`、`test_dynamic_block_split.py`、`datasource/test_huggingface.py`、`test_execution_optimizer_integrations.py`。主要的是 `python/ray/data/tests/test_split.py`。
- 直接測 `train_test_split` 的：`test_train_test_split`（第 746 行）、`test_train_test_split_stratified`（781）、`test_train_test_split_shuffle_stratify_error`（812）、`test_train_test_split_stratified_imbalanced`（829）。
- 另有 `test_streaming_train_test_split_hash/random/wrong_params`（890/908/938）測的是另一個方法 `streaming_train_test_split`，但 `-k train_test_split` 會一起選到（子字串）。若只想跑前四個，推論：可用 `-k "test_train_test_split"`。

實跑：
```bash
cd /home/user/ray && source ~/ray-venv/bin/activate
python -m pytest -q python/ray/data/tests/test_split.py -k train_test_split
```
結果：`4 failed, 11 passed, 411 deselected in 155.49s (0:02:35)`（整體 `real 2m38s`）。
失敗的是：`test_train_test_split`、`test_streaming_train_test_split_hash`、`test_streaming_train_test_split_random[None]`、`[42]`。
- 一個失敗的訊息：`assert [0, 1, 4, 5, 6, 7] == [0, 1, 2, 3, 4, 5]`（`test_train_test_split`）。
- 另一個失敗訊息：`ImportError: Dataset.join depends on 'polars', but Ray Data couldn't import it. Install it by running 'pip install polars'`。
- 路徑注意（已查證）：traceback 顯示 `/root/ray-venv/lib/python3.13/site-packages/ray/...`，但 `site-packages/ray/data` 本身是 `setup-dev.py` 建的 symlink，指向 `/home/user/ray/python/ray/data`（`ls -l` 可見；`python -c "import ray.data, os; print(os.path.realpath(ray.data.__file__))"` 會印出 repo 路徑）。所以測試跑的**就是** repo 原始碼。wheel 的 `ray.__commit__` 和 repo HEAD 也同為 `0fe2388`，不是版本不一致。
- 失敗原因：3 個 `streaming_train_test_split` 是缺 `polars`（環境問題，`pip install polars` 可解）。`test_train_test_split` 單獨跑會通過（`::test_train_test_split`，68 秒），用 `-k train_test_split` 一起跑才失敗；原因是測試沒有設定 `preserve_order`，區塊順序看運氣（flaky test），見 `00-session-log.md` 觀察 7。教訓：本機測試失敗時，先單獨跑、多跑幾次，分清楚是你的改動造成的、環境問題，還是原本就不穩定。

## 5. CI

- 系統：Buildkite（`getting-involved.md:310`）；流程定義在 `.buildkite/*.rayci.yml`，由 rayci 產生並執行（`.buildkite/README.md:5-7`）。
- PR 上預設跑 `microcheck`：每次 commit 預設執行；目標是用約 10% 的完整測試量抓到約 90% 的 bug；比完整測試快約兩倍、便宜約一半（`ci.md:13-15`）。
- microcheck 怎麼挑測試：新增或修改的測試一定包含（`ci.md:17`）。可在 commit message 本文（第二行以後）加 `@microcheck TEST_TARGET01 TEST_TARGET02 ...` 手動加測試（`ci.md:18-30`）。除此之外，挑選演算法細節：找不到（查過：`ci.md`、`.buildkite/README.md`、`.buildkite/lint.rayci.yml` 只提到 microcheck 有寫死的 `tag:lint` 選擇器，第 48、62 行）。
- 結果呈現：綠勾或紅叉，GitHub UI 有各測試狀態摘要（`ci.md:32`）。
- 合併前跑完整測試：「the full test suite must pass before a PR can merge. Adding the `go` label triggers the full suite」（`ci.md:36`）。
- 外部貢獻者：「adding the `go` label and enabling auto-merge both require write access, so a committer runs the full suite and merges」（`ci.md:40`）；reviewer 審外部 PR 時會幫他們加 `go`（`ci.md:38`）。所以誰能加：有 write access 的 committer。
- 啟用 auto-merge 時 workflow 自動加 `go`（`.github/workflows/on_auto_merge.yaml:1-19`）；新 push 會取消 auto-merge（`ci.md:38`；`.github/workflows/on_pull_request_synchronized.yml:1-10`）。
- 文件 PR：`docs-go` label 可跳過各函式庫的文件範例測試，同樣需要 write access（`ci.md:93`）。
- `test.rules.txt` 如何把改動檔案對應到測試：
  - 規則檔把路徑對應到 tag：`dir/` 或檔案或 fnmatch 樣式，`@ tag1 tag2` 發出 tag，沒有 tag 的規則是略過規則，`;` 分隔規則（`.buildkite/test.rules.txt:6-13`）。
  - 依檔案順序比對，第一個命中的規則勝出（`.buildkite/test.rules.txt:21-23`）。
  - 例：`python/ray/data/` 等路徑 -> `@ data`（`.buildkite/test.rules.txt:123-129`）；結尾 `*` 萬用規則會把未命中的改動擴散成全套（第 736-740 行；`.buildkite/README.md:13`）。
  - tag 再由 rayci 對應到 `.buildkite/data.rayci.yml` 等檔案中的 step（`.buildkite/README.md:15`）。
  - 權威的評估器在 repo 外，`ci/pipeline/determine_tests_to_run.py` 只是參考實作（`.buildkite/test.rules.txt:28-31`）。
  - 另有 `always.rules.txt` 一律套用（`.buildkite/README.md:12`）。
  - 推論：改 `python/ray/data/dataset.py` 會觸發 `data` tag 的測試步驟。
- CI 失敗時外部貢獻者怎麼看 log：沒有明文指引（查過：`getting-involved.md`、`ci.md`、`CONTRIBUTING.rst`、`testing-tips.md`、`agent-development.md`）。
  - 有的資訊：PR 的 GitHub 檢查會顯示狀態摘要（`ci.md:32`）；Buildkite 專案頁 <https://buildkite.com/ray-project/>（`getting-involved.md:310`）。
  - 若失敗似乎和你無關，查已知 flaky 測試：<https://flakey-tests.ray.io/>（`getting-involved.md:321`）。
  - 用指令抓 log 的 skill `/fetch-buildkite-logs` 需要 Buildkite API token，權限 `read_builds`、`read_build_logs`、`read_artifacts`（`doc/source/ray-contribute/agent-development.md:89-100`；`.claude/skills/fetch-buildkite-logs/SKILL.md:57`）。
  - 推論：外部貢獻者可能沒有 Buildkite 組織帳號，點 PR 檢查的 Details 連結能否看 log，文件沒寫，請以實際 PR 畫面為準，看不到就在 PR 留言請 reviewer 協助。
- 文件 PR 另有 Read the Docs 檢查 `docs/readthedocs.com:anyscale-ray`，任何 Sphinx warning 都會失敗（`ci.md:48`）。

文件之間不一致：
3. 合併前的 label：`CONTRIBUTING.rst:42` 與 `getting-involved.md:125` 寫「作者在 build 成功後加 `test-ok` label」；`ci.md:36-40` 與 `publishing-examples.md:71` 寫要 `go` label，且外部貢獻者不能自己加。推論：`ci.md` 較新較詳細，`test-ok` 可能過時，但我沒有證據證明，請向 reviewer 確認。
4. `getting-involved.md:112` 說新測試放 `ray/python/ray/tests/`，但 Ray Data 規定必須放 `python/ray/data/tests/`（`.pre-commit-config.yaml:225`）。以各元件自己的 tests 目錄為準。

## 6. Review 流程

- 誰 review：非 ray-project 組織成員的 PR 會「shortly」有 assignee，assignee 會積極互動（`CONTRIBUTING.rst:48`；`getting-involved.md:130`）。組織成員則自己在 `assignee` 欄位加 reviewer（`getting-involved.md:121`）。
- CODEOWNERS：`.github/CODEOWNERS`。例：`/python/ray/data/` -> `@ray-project/ray-data`（第 67 行）、`/python/ray/` 預設 -> `@ray-project/ray-core`（第 33 行）、`/doc/`（第 25 行）。規則是 last-match-wins（第 21 行）。每個 PR 都會通知 CODEOWNERS（`AGENTS.md:6`）。
- 流程：assignee 審後若需要修改會加 `@author-action-required`；你修完要移除該 label（`getting-involved.md:122-123`）。核可後 committer 合併（第 126 行）。
- 沒回應怎麼辦：「Actively ping assignees after you address your comments!」（`getting-involved.md:131`；`CONTRIBUTING.rst:49`）；「Be sure to ping them if the pull request is getting stale」（`getting-involved.md:115`）。沒有指定「幾天」才算沒回應（找不到，查過：`CONTRIBUTING.rst`、`getting-involved.md`）。
- 自動 stale：PR 14 天沒活動被標 `stale`，再 14 天沒活動就關閉；留任何留言就會移除 stale label（`.github/workflows/stale_pull_request.yaml:27,30,48-49`）。有 `unstale`、`release-blocker` 等 label 的不會被標（第 57-60 行）。
- PR 要保持小：找不到明文規定（查過：`CONTRIBUTING.rst`、`AGENTS.md`、`getting-involved.md`、`development.md`、`involvement.md`）。
  - 相關旁證：`getting-involved.md:135` 說本機先跑測試是為了「reduce reviewers' burden and speed up the review process」；`AGENTS.md:6-9` 強調維護者注意力有限。
  - 推論：一個 PR 做一件事，較容易被審。
- 衝突處理：用 `git pull . upstream/master`，不要 rebase（`getting-involved.md:114`）。
- 想找題目：`good-first-issue`、`contribution-welcome` label（`getting-involved.md:62-63`）。

## 7. 從改程式到 PR 的檢查清單

1. 查有沒有人做過：`gh pr list --repo ray-project/ray --state open --search "<關鍵字>"`（`AGENTS.md:23-24`）
2. 設定 Python-only 開發環境：`python python/ray/setup-dev.py`（`development.md:120`）；確認 `python -c "import ray; print(ray.__file__)"`
3. 改程式，並在對應元件的 tests 目錄補測試（`getting-involved.md:112`）
4. 跑相關測試：`python -m pytest -v -s python/ray/data/tests/test_split.py::test_train_test_split`（`getting-involved.md:156`）
5. 裝 lint 工具：`pip install -c python/requirements_compiled.txt -r python/requirements/lint-requirements.txt`（`getting-involved.md:265`）
6. 只 lint 自己改的檔案：`pre-commit run --files $(git diff --name-only HEAD)`（`lint/SKILL.md:11`）
7. 合併最新 master：`git pull . upstream/master`（`getting-involved.md:105-108`、`114`）
8. 簽署 commit：`git commit -s -m "[Data] ..."`（`getting-involved.md:111`；標題前綴為推論）
9. 開 PR，照模板填 Description / Related issues / Additional information，刪掉模板說明（`.github/PULL_REQUEST_TEMPLATE.md:4`）；若有 AI 協助，寫明三項（`AGENTS.md:44-47`）
10. 等 microcheck；有人 review 後立即回覆並 ping assignee，請 committer 加 `go`（`ci.md:36-40`；`getting-involved.md:131`）
