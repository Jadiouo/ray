# Ray 地圖（給第一次接觸 Ray 的人）

> 讀者：會 Python/C++、做機器人的大學生。
> 約定：每個事實後面附（`檔案路徑:行號`）或引原句；「推論：」開頭是我自己的判斷，不是文件原文；找不到就寫「找不到」。
> 所有路徑都相對於 repo 根目錄 `/home/user/ray`。注意：Ray Core 的文件資料夾是 `doc/source/core/`，**不是** `ray-core/`（後者在這個 repo 不存在，`ls doc/source` 可驗證）。

## 1. Ray 是什麼

README 第一句：「Ray is a unified framework for scaling AI and Python applications. Ray consists of a core distributed runtime and a set of AI libraries for simplifying ML compute」（`README.rst:18`）。

- AI 函式庫列表：Data、Train、Tune、RLlib、Serve（`README.rst:27-31`）。
- Core 的三個關鍵抽象：Tasks、Actors、Objects（`README.rst:35-37`）。
- Core 文件：「Ray Core is a distributed computing framework for building and scaling distributed applications. It provides three essential primitives: tasks, actors, and objects.」（`doc/source/core/index.md:21`）
- 推論：可以把 Ray 想成兩層。下層是 Core（分散式執行環境），上層的 Data/Train/Tune/Serve/RLlib 都是用 Core 的 task/actor 組出來的函式庫。依據是 README 說「core distributed runtime and a set of AI libraries」，但「上層函式庫一定建在 Core 之上」這句我沒有逐一在原始碼驗證。

## 2. 元件總表

| 元件 | 解決什麼問題（出處） | Python 程式碼 | 測試 | 官方文件 |
|---|---|---|---|---|
| Core | 把 Python 函式/類別丟到叢集上平行跑。「Ray runs arbitrary functions asynchronously on separate worker processes」（`doc/source/core/key-concepts.md:17`） | `python/ray/`（`remote_function.py`、`actor.py`、`_raylet.pyx`、`_private/`） | `python/ray/tests/`（BUILD：`python/ray/tests/BUILD.bazel`） | `doc/source/core/`（入口 `index.md`、`key-concepts.md`） |
| Data | 「scalable data processing library for AI workloads」，做批次推論、前處理、訓練資料載入（`doc/source/data/index.md:24`） | `python/ray/data/`（`dataset.py`、`read_api.py`、`datasource/`） | `python/ray/data/tests/`、`python/ray/data/tests/unit/` | `doc/source/data/`（`index.md`、`key-concepts.md`） |
| Train | 「scale model training code from a single machine to a cluster of machines in the cloud」（`doc/source/train/train.md:37`） | `python/ray/train/`（新版在 `python/ray/train/v2/`） | `python/ray/train/tests/`、`python/ray/train/v2/tests/` | `doc/source/train/`（入口 `train.md`、`overview.md`） |
| Tune | 「experiment execution and hyperparameter tuning at any scale」（`doc/source/tune/index.md:26`） | `python/ray/tune/`（`tuner.py`、`schedulers/`、`search/`） | `python/ray/tune/tests/` | `doc/source/tune/`（`index.md`、`key-concepts.md`） |
| Serve | 「scalable model serving library for building online inference APIs」（`doc/source/serve/index.md:42`） | `python/ray/serve/`（`api.py`、`deployment.py`、`handle.py`） | `python/ray/serve/tests/`（另有 `python/ray/serve/tests/unit/`） | `doc/source/serve/`（`index.md`、`key-concepts.md`） |
| RLlib | 「open source library for reinforcement learning (RL)... production-grade, scalable, fault-tolerant RL workloads」（`doc/source/rllib/index.md:60`） | `python/ray/rllib/` | 分散在各子資料夾的 `tests/`，例如 `python/ray/rllib/algorithms/ppo/tests`、`python/ray/rllib/env/tests`、`python/ray/rllib/core/rl_module/tests`；`python/ray/rllib/tests` 不存在 | `doc/source/rllib/`（`index.md`、`key-concepts.md`） |
| LLM | 「Ray Serve LLM deploys large language models in production... exposes an OpenAI-compatible API」（`doc/source/serve/llm/index.md:11`）；批次推論見 `doc/source/data/working-with-llms.md:11`（`ray.data.llm`） | `python/ray/llm/`（`_internal/batch`、`_internal/serve`）、`python/ray/serve/llm/`、`python/ray/data/llm.py` | `python/ray/llm/tests/`（BUILD：`python/ray/llm/tests/BUILD.bazel`） | `doc/source/serve/llm/`、`doc/source/data/working-with-llms.md`；`doc/source/llm/` 只有 `doc_code`、`examples` |
| Autoscaler | 「When the resource demands of the Ray workload exceed the current capacity of the cluster, the autoscaler will try to increase the number of worker nodes」（`doc/source/cluster/key-concepts.md:54`） | `python/ray/autoscaler/`（新版 `python/ray/autoscaler/v2/`） | `python/ray/autoscaler/v2/tests/`；v1 專屬測試資料夾：找不到（我沒有去 `python/ray/tests/` 逐檔確認） | `doc/source/cluster/key-concepts.md`、`doc/source/core/internals/autoscaler-v2.md` |
| Dashboard | 「web-based dashboard for monitoring and debugging Ray applications」（`doc/source/ray-observability/getting-started.md:11`） | `python/ray/dashboard/`（`head.py`、`agent.py`、`modules/`） | `python/ray/dashboard/tests/` | `doc/source/ray-observability/getting-started.md` |

補充：
- Train 在 `doc/source/train/` 和 `python/ray/train/` 都有 `v2` 相關內容；哪一版是預設，我沒有查，找不到結論。
- RLlib 的 `Algorithm` 是 Tune Trainable 的子類別，所以 RLlib 可以交給 Tune 調參（`doc/source/rllib/key-concepts.md:43`）。

## 3. Ray Core 的三個基本概念

### Task（無狀態函式）
- 原文：「Ray runs arbitrary functions asynchronously on separate worker processes. These asynchronous Ray functions are *tasks*.」（`doc/source/core/key-concepts.md:17`）；也可以指定 CPU/GPU/自訂資源需求（同一行）。
- 白話：在 Python 函式上加 `@ray.remote`，用 `f.remote(...)` 呼叫，它就會在叢集某個 worker 行程上非同步執行。
- 範例出處：`doc/source/core/tasks/index.md:11`（範例程式在 `doc/source/core/doc_code/tasks.py`）；生命週期（定義、呼叫、排程、執行）見 `doc/source/core/internals/task-lifecycle.md`。

### Actor（有狀態的 worker）
- 原文：「An actor is a stateful worker, which you can also think of as a service. When you instantiate an actor, Ray creates a worker for it and schedules the actor's methods on that specific worker.」（`doc/source/core/key-concepts.md:25`）
- 白話：把 class 變成常駐的遠端物件，方法呼叫都送到同一個 worker，所以可以保存狀態（例如機器人模擬器、模型權重）。
- 使用指南：`doc/source/core/actors/index.md`。

### Object（ObjectRef 與 `ray.get`）
- 原文：「These objects are *remote objects* because Ray can store them anywhere in a Ray cluster. You use *object refs* to refer to them. Ray caches remote objects in its distributed shared-memory *object store*, with one object store per node in the cluster.」（`doc/source/core/key-concepts.md:31`）
- 取值：「Call the ray.get() method to fetch the result of a remote object from an object ref. If the current node's object store doesn't contain the object, Ray downloads it.」（`doc/source/core/objects/index.md:55`）
- 白話：`f.remote()` 立刻回傳 `ObjectRef`（像一張取貨單），`ray.get(ref)` 才會等結果並拿回 Python 值。
- 還有第四個概念 placement group（`doc/source/core/key-concepts.md:35-37`），本頁不展開。

## 4. C++ 核心（`src/ray/`）

**只改 Python 的人通常不用碰這裡。** 依據：開發文件把「Python-only development (fast loop, no C++)」列為獨立路線（`doc/source/ray-contribute/development.md:15`），做法是用 `python python/ray/setup-dev.py` 把 pip 安裝的 Python 檔換成本地可編輯版本（`doc/source/ray-contribute/development.md:115-120`）；文件也說只改 Tune/RLlib/Autoscaler 時照這條路，避免漫長的編譯（`doc/source/ray-contribute/development.md:210`）。

| 子資料夾 | 一句話 | 依據 |
|---|---|---|
| `src/ray/raylet/` | 每個節點上跑的系統行程，負責排程與物件管理。 | 「A system process that runs on each Ray node. It's responsible for scheduling and object management.」（`doc/source/ray-references/glossary.md:397-399`）；程式有 `node_manager.cc`、`worker_pool.cc`、`scheduling/` |
| `src/ray/gcs/` | GCS（Global Control Service），head node 上的中央 metadata 伺服器。 | 「Centralized metadata server for a Ray cluster. It runs on the Ray head node and has functions like managing node membership and actor directory.」（`doc/source/ray-references/glossary.md:244-246`）；有 `gcs_server.cc`、`gcs_node_manager.cc`、`gcs_job_manager.cc`、`gcs_placement_group_manager.cc` |
| `src/ray/core_worker/` | 每個 driver/worker 行程裡的 C++ 函式庫，提交與執行 task。 | 文件寫 executor 在 `core_worker.cc` 收到 `PushTask` RPC 並執行（`doc/source/core/internals/task-lifecycle.md:67`）。「函式庫形式」是推論：從 `core_worker_process.h` 這類檔名推的，沒有原文 |
| `src/ray/object_manager/` | 推論：節點之間搬運 object store 裡的物件（檔案有 `object_buffer_pool.cc`、`chunk_object_reader.cc`）。object store 本身定義見 `doc/source/ray-references/glossary.md:320-321`；object manager 專屬說明：找不到 |
| `src/ray/pubsub/` | 輕量的 pubsub 模組，把許多長輪詢 gRPC 請求合併成批次，降低記憶體。 | `src/ray/pubsub/README.md:7-30` |
| `src/ray/ray_syncer/` | 推論：節點間同步狀態（檔名 `ray_syncer.cc`、`node_state.cc`）。說明文件：找不到 |
| `src/ray/rpc/` | 推論：gRPC 伺服器/客戶端的共用封裝（`grpc_server.cc`、`grpc_client.h`、`authentication/`）。說明文件：找不到 |
| `src/ray/protobuf/` | RPC 與事件的 `.proto` 定義（`common.proto`、`core_worker.proto`、`autoscaler.proto`…）。這是看檔名，屬推論 |
| `src/ray/design_docs/` | 設計文件：`actor_states.rst`、`id_specification.md`、`task_states.rst`（`ls` 可驗證）。內容我沒細讀 |
| 其他 | `common/`、`util/`、`stats/`、`observability/`、`asio/`、`flatbuffers/`、`raylet_ipc_client/` 等：共用工具與指標，我沒找到統一說明，不猜 |

### Python 怎麼接到 C++
- `python/ray/_raylet.pyx` 是 Cython 檔，開頭有 `# cython:` 指令與 `cimport`（`python/ray/_raylet.pyx:1-7`），全檔 5523 行。
- 它由 Bazel 的 `pyx_library(name = "_raylet", ...)` 編成共享函式庫，輸入含 `python/ray/includes/*.pxd`、`*.pxi`、`_raylet.pyx`（`BUILD.bazel:140-149`）。
- Python 端在 `import ray._raylet` 載入（`python/ray/__init__.py:85`），再從裡面 import 公開符號（`python/ray/__init__.py:87`）。
- 與 C++ core worker 的 Cython 宣告在 `python/ray/includes/libcoreworker.pxd`（檔案存在，內容我沒細讀）。
- 官方的 task 流程文件：Python `remote_function.py` 呼叫 Cython 的 `submit_task`，進入 C++（`doc/source/core/internals/task-lifecycle.md:40`）。
- 推論：只要 `import ray` 能成功，`_raylet` 已經編好，改 Python 檔不需要重編 C++。

## 5. 測試

### 5.1 測試放哪裡
見第 2 節表格的「測試」欄。重點：
- Core 的測試在 `python/ray/tests/`；各函式庫的測試在自己資料夾的 `tests/` 底下。
- RLlib 的測試分散在各子資料夾（如 `python/ray/rllib/algorithms/ppo/tests`）。
- C++ 的測試在各模組自己的 `tests/` 子資料夾，例如 `src/ray/raylet/tests/`、`src/ray/gcs/tests/`、`src/ray/core_worker/tests/`、`src/ray/object_manager/tests/`（`ls` 驗證）。

### 5.2 命名習慣
- Python：`test_*.py`，例如 `python/ray/data/tests/test_arrow_block.py`；Data 的 BUILD 用 `glob(["tests/unit/**/test_*.py"])`（`python/ray/data/BUILD.bazel:32`）。
- C++：`*_test.cc` 放在 `tests/`，例如 `src/ray/gcs/tests/gcs_node_manager_test.cc`、`src/ray/core_worker/tests/reference_counter_test.cc`。
- 例外（推論：不是慣例的反例，只是要小心）：`src/ray/` 底下共 191 個 `*_test.cc`，其中有些不在 `tests/` 裡，如 `src/ray/gcs/leader_election/leader_elector_test.cc`。所以「都在 tests/」不是百分之百。
- C++ 的 Bazel 目標用 `ray_cc_test(name = "wait_manager_test", ...)`（`src/ray/raylet/tests/BUILD.bazel:20-21`）。

### 5.3 Ray Data：`tests/unit/` 與 `tests/` 的差別
- `unit/README.md`：「This directory contains unit tests that do not depend on distributed infrastructure or external dependencies.」（`python/ray/data/tests/unit/README.md:3`）
- 要求：Fast（毫秒級）、Isolated（不依賴 Ray runtime、外部服務、檔案 I/O）、Deterministic（無隨機或時間行為）（`python/ray/data/tests/unit/README.md:5-10`）。
- 禁止：初始化 Ray、`time.sleep()`、外部服務、網路（`python/ray/data/tests/unit/README.md:12-17`）。
- 強制方式：該資料夾的 `conftest.py` 用 autouse fixture 讓 `ray.init` 和 `time.sleep` 直接 raise（`python/ray/data/tests/unit/conftest.py:7-27`，README 對應 `README.md:20-24`）。
- 「如果需要這些就搬到主測試資料夾」（`python/ray/data/tests/unit/README.md:26`）。貢獻指南也說「Put unit tests in `python/ray/data/tests/unit`」（`doc/source/data/contributing/how-to-write-tests.md:25`）。
- 所以：`tests/` 是會啟動 Ray 的整合型測試，`tests/unit/` 是不能啟動 Ray 的快速測試。「`tests/` 是整合型」是推論，依據是 unit 的規則與 `tests/conftest.py` 會 import Ray 的 fixture（`python/ray/data/tests/conftest.py:29`）。

### 5.4 測試怎麼進 CI（Bazel `py_test_module_list`）
- 定義：`bazel/python.bzl:73` 的 `py_test_module_list(files, size, deps, ...)`，對 `files` 裡每個檔案產生一個 `native.py_test`（`name` 是去掉 `.py` 的檔名，`main`/`srcs` 是該檔）（`bazel/python.bzl:73-86`）。
- Data 有自己的包裝：`python/ray/data/test.bzl:26` 的 `py_test_module_list`，會合併 env 後再呼叫原版（`python/ray/data/test.bzl:26-28`）。
- 使用例子（Data unit）：`python/ray/data/BUILD.bazel:30-41`，`size = "small"`、`files = glob(["tests/unit/**/test_*.py"])`、tags 含 `team:data`。
- 使用例子（Core）：`python/ray/tests/BUILD.bazel:34-` 的 `size = "medium"`，`files = [ "test_actor_cancel.py", ... ]` 手動列檔。
- 推論：新增一個 `test_xxx.py` 後，如果它不被某個 glob 涵蓋，就要自己加進 BUILD.bazel 的 `files` 清單，否則 CI 不會跑它。依據是 Core 用手動列表；各資料夾實際規則我沒有逐一驗證。
- 也有其他 BUILD 直接用 `py_test(...)`（`python/ray/train/BUILD.bazel:53` 起）；Train 的 BUILD 只 load 了 `py_library, py_test` 和 `doctest`（`python/ray/train/BUILD.bazel:1-2`），沒有 load `py_test_module_list`。

### 5.5 pytest 預設 timeout
- `pytest.ini:12-13`：「Default to 3 min timeout for all individual pytest. timeout = 180」。
- `AGENTS.md` 也寫「The default test timeout is 180s (`pytest.ini`)」。
- 同檔另有 `filterwarnings = error`（`pytest.ini:3-10`，但後面 `ignore:.*:` 把所有警告又忽略掉）與 `asyncio_mode = auto`（`pytest.ini:15-16`）。

### 5.6 常見 fixture
- `ray_start_regular_shared`：定義在 `python/ray/tests/conftest.py:668-673`，scope 是 `module`，用 `_ray_start(**param)` 啟動一個 Ray。
- `ray_start_regular_shared_2_cpus`：定義在 `python/ray/tests/conftest.py:675-680`，同樣 `module` scope，`num_cpus=2`。
- 同檔還有 `ray_start_regular`（`python/ray/tests/conftest.py:652`）。它是預設（function）scope 的 `@pytest.fixture`，註解寫「will start ray with 1 cpu」（`python/ray/tests/conftest.py:649-652`）。
- Data 的 `python/ray/data/tests/conftest.py:29-30` 用 `from ray.tests.conftest import *` 重用這些 fixture，所以 Data 測試能直接用。
- 其他函式庫（Train/Tune/Serve）是否也這樣共用：找不到，我只確認了 Data。
- 推論：「shared」代表同一個測試檔（module）內共用一個 Ray 叢集，比每個測試重啟快。依據是 `scope="module"`。

## 6. 之後想做多機器人 RL：RLlib 先看哪些資料夾

先讀 `doc/source/rllib/key-concepts.md`（Algorithm、EnvRunner、Learner、RLModule 的整體架構，`doc/source/rllib/key-concepts.md:11`、`:30-34`）。

| 資料夾 | 一句話 |
|---|---|
| `python/ray/rllib/algorithms/` | 演算法實作與設定，含 `algorithm.py`、`algorithm_config.py`，及 `ppo/`、`appo/`、`impala/`、`dqn/`、`sac/` 等。核心類別是 `Algorithm`，每種演算法有對應的 `AlgorithmConfig`（`doc/source/rllib/key-concepts.md:32`）。 |
| `python/ray/rllib/env/` | 環境與取樣：`multi_agent_env.py`、`multi_agent_env_runner.py`、`multi_agent_episode.py`、`external/`（外部模擬器）。文件：「In a multi-agent environment, multiple "agents" act simultaneously, in a turn-based sequence, or through an arbitrary combination of both.」（`doc/source/rllib/multi-agent-envs.md:11`） |
| `python/ray/rllib/examples/multi_agent/` | 多智能體範例：`multi_agent_cartpole.py`、`multi_agent_pendulum.py`、`pettingzoo_independent_learning.py`、`pettingzoo_parameter_sharing.py`、`shared_encoder_cartpole.py`、`self_play_with_open_spiel.py`（`ls` 驗證）。 |
| `python/ray/rllib/core/rl_module/` | RLModule 是模型類別：「you write custom models, including complex multi-network setups often found in multi-agent or model-based algorithms」（`doc/source/rllib/rl-modules.md:11`）；`multi_rl_module.py` 看起來是多個模組的容器（推論：依檔名）。 |
| `python/ray/rllib/core/learner/` | 負責用資料更新模型的 Learner（文件：`doc/source/rllib/learner.md`；內容我沒細讀）。 |
| `python/ray/rllib/examples/envs/` | 環境範例，如 `agents_act_in_sequence.py`、`agents_act_simultaneously.py`（對應「輪流行動」與「同時行動」兩種多智能體模式，後者說法為推論）。 |
| `python/ray/rllib/examples/rl_modules/` | 自訂 RLModule 範例資料夾（`ls` 驗證存在，內容我沒讀）。 |

- 推論：機器人通常有自己的模擬器，可能需要外部環境接入；`doc/source/rllib/external-envs.md` 與 `python/ray/rllib/env/external/` 存在，但是否適合你的模擬器，我沒有評估。
- 推論：建議閱讀順序是 key-concepts → multi-agent-envs → rl-modules → `examples/multi_agent/` 跑一個範例。這是我的建議，不是文件規定。
- RLlib 文件提到機器人是使用領域之一（`doc/source/rllib/index.md` 的 verticals 段落，約 `:62`），行號我沒精確核對。

## 7. 這份地圖沒查證的地方（誠實清單）
- Train v2 與 v1 哪個是預設：找不到結論。
- object_manager、ray_syncer、rpc 的官方說明：找不到，上表標為推論。
- Autoscaler v1 專屬測試路徑：找不到。
- 沒有實際執行任何測試或建置，所有內容來自讀檔與 `ls`。
