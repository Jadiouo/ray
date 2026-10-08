"""Ray Core 入門：task、ObjectRef、ray.put、actor。

執行方式（請在 /home/user/ray 以外的目錄）：
    source ~/ray-venv/bin/activate && cd ~ && python /home/user/ray/notes/examples/core_basics.py
"""
import time

import ray

# 想玩玩看就改這兩個數字（為什麼放最上面：學生不用在程式裡找）
NUM_CPUS = 2   # 告訴 Ray 這台機器「有幾顆 CPU 可用」，決定最多幾個 task 同時跑
NUM_TASKS = 4  # 一次發出幾個 task

# 為什麼要 ray.init：啟動（或連上）Ray 執行環境，之後 @ray.remote 才有地方跑。
# include_dashboard=False：這個環境的 nightly 沒有網頁儀表板的前端檔，不關掉會卡約 60 秒；
# 正常安裝的 Ray 不需要這個參數。
ray.init(num_cpus=NUM_CPUS, include_dashboard=False)


# ---- 1. Task：把普通函式加上 @ray.remote，就變成可以丟到別的 process 跑的 task ----
def plain_square(x):
    time.sleep(1)  # 假裝這是很耗時的工作
    return x * x


# 為什麼這樣寫：同一個函式，普通呼叫是依序跑；包成 remote 才是 task。方便公平比較。
slow_square = ray.remote(plain_square)  # 等同於在函式上面加 @ray.remote


# 對照組：普通 Python 依序執行。為什麼要比：這樣才看得出 Ray 省了多少時間。
t0 = time.time()
serial = [plain_square(x) for x in range(NUM_TASKS)]
print(f"[依序] 結果={serial}，耗時 {time.time() - t0:.1f} 秒")

# 暖機：第一次呼叫 task 時 Ray 要先啟動 worker process，會讓計時多出 1~2 秒。
# 先跑空 task 把 worker 叫起來，後面量到的才是「純平行」的時間。
ray.get([ray.remote(lambda: None).remote() for _ in range(NUM_CPUS)])

# 為什麼用 .remote()：它「立刻回傳」不會等結果，所以可以連續發出很多個呼叫。
t0 = time.time()
refs = [slow_square.remote(x) for x in range(NUM_TASKS)]
print("[平行] 這是 ObjectRef，不是值：", refs[0])  # 只是「取貨單」

# 為什麼用 ray.get：憑「取貨單」等工作完成並拿回真正的值。
print(f"[平行] 結果={ray.get(refs)}，耗時 {time.time() - t0:.1f} 秒")

# ---- 2. ray.put：把大物件放進共用的 object store，只傳 ref，不用每次複製整份 ----
big = list(range(1_000_000))
big_ref = ray.put(big)


@ray.remote
def total(data):
    # 為什麼這裡 data 已經是 list：ref 當作參數傳給 task 時，Ray 會自動幫你取值
    return sum(data)


print("[put] ref 傳給 task，總和 =", ray.get(total.remote(big_ref)))


# ---- 3. Actor：@ray.remote 加在 class 上，會在一個專屬 process 裡長期活著、保有狀態 ----
@ray.remote
class Counter:
    def __init__(self):
        self.n = 0  # 狀態存在 actor 自己的 process 裡

    def incr(self):
        self.n += 1
        return self.n


counter = Counter.remote()  # 建立 actor
# 為什麼同一個 actor 的結果會累加：每次呼叫都送到同一個 process，n 沒有被重置。
print("[actor] 呼叫三次 incr：", ray.get([counter.incr.remote() for _ in range(3)]))
print("[actor] 再呼叫一次：", ray.get(counter.incr.remote()), "(接續前面的狀態)")

# 為什麼要 shutdown：關掉 Ray 並釋放 process 與記憶體。
ray.shutdown()
