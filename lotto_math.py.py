import random
import math

def simulate_lotto_sums(num_trials=100000):
    print(f"🚀 正在進行 {num_trials:,} 次大樂透開獎模擬...\n")
    
    sums = []
    # 進行十萬次隨機抽牌
    for _ in range(num_trials):
        # 從 1~49 中抽出 6 個不重複的號碼
        draw = random.sample(range(1, 50), 6)
        sums.append(sum(draw))

    # 1. 統計與計算
    mean = sum(sums) / num_trials
    variance = sum((x - mean) ** 2 for x in sums) / num_trials
    std_dev = math.sqrt(variance)

    # 2. 計算和值落在 120 ~ 180 (黃金區間) 的機率
    target_range_count = sum(1 for x in sums if 120 <= x <= 180)
    prob_in_range = (target_range_count / num_trials) * 100

    # 印出數據結果
    print(f"--- 📊 統計結果分析 ---")
    print(f"✅ 模擬平均和值: {mean:.2f} (純數學理論值: 150.00)")
    print(f"✅ 模擬標準差:   {std_dev:.2f} (純數學理論值: 34.64)")
    print(f"🎯 和值落在 120~180 的機率: {prob_in_range:.2f}%")
    print("\n")

    # 3. 繪製文字版直方圖 (視覺化常態分佈)
    print("--- 📈 和值分佈直方圖 (完美的鐘形曲線) ---")
    distribution = {}
    for s in sums:
        # 將和值以每 10 為一個區間進行分組 (例如 124 屬於 120~129 區間)
        bucket = (s // 10) * 10
        distribution[bucket] = distribution.get(bucket, 0) + 1

    # 印出區間大於等於 60 且小於等於 240 的主要分佈帶
    for bucket in sorted(distribution.keys()):
        if 60 <= bucket <= 240:
            # 依比例轉換為星星符號 (*) 的數量
            bar_length = int((distribution[bucket] / num_trials) * 350)
            print(f"{bucket:3d} ~ {bucket+9:3d} : {'█' * bar_length}")

if __name__ == "__main__":
    simulate_lotto_sums()