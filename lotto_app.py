import streamlit as st
import sqlite3
import pandas as pd
import os
import random

# ==========================================
# 0. 全域設定與側邊欄導覽
# ==========================================
st.set_page_config(page_title="大樂透 AI 預測與分析系統", page_icon="🎯", layout="wide")

DB_NAME = "lotto.db"
MAIN_CSV = "lotto_2007_2026.csv"
EXTRA_CSV = "lotto_extra_2011_2026.csv"

st.sidebar.title("🎯 系統導覽")

# 🌟 新增：核彈級強制同步按鈕
st.sidebar.markdown("---")
if st.sidebar.button("🔄 強制同步最新資料", type="primary", help="上傳新 CSV 檔後請點擊此按鈕"):
    # 1. 清空 Streamlit 記憶體快取
    st.cache_data.clear()
    st.cache_resource.clear()
    # 2. 強制刪除舊的 SQLite 資料庫檔案
    try:
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
    except Exception as e:
        pass
    # 3. 重新載入網頁
    st.success("✅ 系統已重置，正在為您載入最新開獎數據...")
    st.rerun()

st.sidebar.markdown("---")
page = st.sidebar.radio("請選擇功能模組", [
    "🤖 策略選號預測引擎", 
    "📊 常規獎號歷史分析", 
    "🧧 加碼活動數據查詢"
])

# ==========================================
# 1. 系統初始化與資料庫建置
# ==========================================
@st.cache_resource
def init_database():
    """只有在找不到資料庫時，才會讀取 CSV 建立全新資料庫"""
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        
        try:
            # 處理常規大樂透
            if os.path.exists(MAIN_CSV):
                df_main = pd.read_csv(MAIN_CSV)
                df_main['draw_date'] = df_main['draw_date'].astype(str).str.replace('/', '-')
                df_main.to_sql('lotto_history', conn, if_exists='replace', index=False)
                conn.execute('CREATE INDEX IF NOT EXISTS idx_draw_date ON lotto_history(draw_date)')
            
            # 處理加碼大樂透
            if os.path.exists(EXTRA_CSV):
                df_extra = pd.read_csv(EXTRA_CSV)
                df_extra['draw_date'] = df_extra['draw_date'].astype(str).str.replace('/', '-')
                df_extra.to_sql('lotto_bonus_history', conn, if_exists='replace', index=False)
                conn.execute('CREATE INDEX IF NOT EXISTS idx_bonus_period ON lotto_bonus_history(period)')
            
            conn.commit()
        except Exception as e:
            st.sidebar.error(f"資料庫建置發生異常: {e}")
        finally:
            conn.close()

# 確保資料庫存在
init_database()

# ==========================================
# 2. 共用資料讀取函數 (🌟 拔除快取封印，確保每次拿最新資料)
# ==========================================
def load_data(query):
    """直接對 SQL 下指令，不使用記憶體快取"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_number_frequencies():
    """計算所有號碼的歷史出現頻率"""
    try:
        df = load_data("SELECT num1, num2, num3, num4, num5, num6 FROM lotto_history")
        all_nums = pd.concat([df['num1'], df['num2'], df['num3'], df['num4'], df['num5'], df['num6']])
        freq = all_nums.value_counts().reset_index()
        freq.columns = ['number', 'count']
        freq['number'] = freq['number'].astype(int)
        return freq.sort_values(by='count', ascending=False)
    except Exception:
        return pd.DataFrame({'number': list(range(1, 50)), 'count': [0]*49})

# 取得最新頻率數據
freq_df = get_number_frequencies()
if not freq_df.empty and freq_df['count'].sum() > 0:
    hot_numbers = freq_df.head(15)['number'].tolist()  
    cold_numbers = freq_df.tail(15)['number'].tolist() 
else:
    hot_numbers = list(range(1, 16))
    cold_numbers = list(range(35, 50))

# ------------------------------------------
# 模組 A：策略選號預測引擎
# ------------------------------------------
if page == "🤖 策略選號預測引擎":
    st.title("🤖 大樂透策略選號預測引擎")
    st.markdown("結合歷史大數據庫 (`2007-2026`)，提供多種統計與資料科學策略為您生成下一期的推薦號碼。")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ 參數設定")
        strategy = st.selectbox("請選擇預測策略：", [
            "歷史機率加權演算法 (依統計機率分配權重)", 
            "高期望值與常態分佈過濾法 (資料科學推薦)",
            "均衡演算法 (熱門+冷門+隨機)", 
            "追熱牌策略 (從最常開出號碼挑選)", 
            "搏冷門策略 (從最少開出號碼挑選)", 
            "純粹隨機 (完全靠電腦運氣)"
        ])
        generate_count = st.slider("產生組數：", 1, 10, 3)
        generate_btn = st.button("🚀 立即預測產生號碼", type="primary")
        
    with col2:
        st.subheader("🎟️ 系統推薦獎號")
        if generate_btn:
            for i in range(generate_count):
                picks = []
                
                # --- 策略 1: 歷史機率加權演算法 (統計概率) ---
                if strategy == "歷史機率加權演算法 (依統計機率分配權重)":
                    pool = freq_df['number'].tolist()
                    weights = freq_df['count'].tolist()
                    
                    if sum(weights) == 0:
                        weights = [1] * len(pool)
                        
                    temp_picks = set()
                    while len(temp_picks) < 6:
                        choice = random.choices(pool, weights=weights, k=1)[0]
                        temp_picks.add(choice)
                    picks = sorted(list(temp_picks))

                # --- 策略 2: 高期望值與常態分佈過濾法 ---
                elif strategy == "高期望值與常態分佈過濾法 (資料科學推薦)":
                    valid_picks = False
                    attempts = 0
                    pool = list(range(1, 32)) + list(range(32, 50)) * 2 
                    
                    while not valid_picks and attempts < 1000:
                        attempts += 1
                        temp_picks = []
                        while len(temp_picks) < 6:
                            new_num = random.choice(pool)
                            if new_num not in temp_picks:
                                temp_picks.append(new_num)
                        
                        temp_picks.sort()
                        total_sum = sum(temp_picks)
                        odds = sum(1 for n in temp_picks if n % 2 != 0)
                        
                        if 120 <= total_sum <= 180 and (odds in [2, 3, 4]):
                            picks = temp_picks
                            valid_picks = True
                            
                    if not valid_picks:
                        picks = random.sample(range(1, 50), 6)

                # --- 策略 3: 均衡演算法 ---
                elif strategy == "均衡演算法 (熱門+冷門+隨機)":
                    picks = random.sample(hot_numbers, 2) + random.sample(cold_numbers, 2)
                    while len(picks) < 6:
                        n = random.randint(1, 49)
                        if n not in picks: picks.append(n)
                
                # --- 策略 4: 追熱牌 ---
                elif strategy == "追熱牌策略 (從最常開出號碼挑選)":
                    picks = random.sample(hot_numbers, 6)
                
                # --- 策略 5: 搏冷門 ---
                elif strategy == "搏冷門策略 (從最少開出號碼挑選)":
                    picks = random.sample(cold_numbers, 6)
                    
                # --- 策略 6: 純隨機 ---
                else: 
                    picks = random.sample(range(1, 50), 6)
                
                picks.sort()
                
                # 視覺化模擬彩球
                html_balls = "".join([
                    f"<span style='display:inline-block; width:45px; height:45px; line-height:45px; "
                    f"text-align:center; background-color:#ffcc00; color:#333; border-radius:50%; "
                    f"margin-right:12px; font-weight:bold; font-size:20px; "
                    f"box-shadow: 2px 2px 5px rgba(0,0,0,0.3);'>{int(n):02d}</span>" 
                    for n in picks
                ])
                
                metrics_html = ""
                if strategy == "高期望值與常態分佈過濾法 (資料科學推薦)":
                    odds_cnt = sum(1 for n in picks if n % 2 != 0)
                    metrics_html = f"<div style='margin-top:10px; font-size:14px; color:#555;'>" \
                                   f"📊 指標分析 ➔ 和值: <b>{sum(picks)}</b> | 奇偶比: <b>{odds_cnt}:{6-odds_cnt}</b>" \
                                   f"</div>"
                elif strategy == "歷史機率加權演算法 (依統計機率分配權重)":
                    total_hist_count = sum([freq_df[freq_df['number'] == n]['count'].values[0] for n in picks if n in freq_df['number'].values])
                    metrics_html = f"<div style='margin-top:10px; font-size:14px; color:#555;'>" \
                                   f"📈 機率權重 ➔ 歷史總計開出: <b>{total_hist_count}</b> 次 (偏向高機率熱門區間)" \
                                   f"</div>"

                st.markdown(
                    f"<div style='margin-bottom:20px; padding:20px; background-color:#f8f9fa; "
                    f"border-radius:12px; border-left:6px solid #ffcc00;'>"
                    f"<div style='color:#666; font-size:14px; margin-bottom:8px;'>組合 {i+1}</div>"
                    f"{html_balls}{metrics_html}"
                    f"</div>", 
                    unsafe_allow_html=True
                )
            
            st.info("💡 貼心提醒：大樂透每次搖獎皆為獨立隨機事件。本系統依歷史統計與資料科學期望值提供選號靈感，請理性投注。")

# ------------------------------------------
# 模組 B：常規獎號歷史分析
# ------------------------------------------
elif page == "📊 常規獎號歷史分析":
    st.title("📊 常規大樂透歷史分析 (2007-2026)")
    
    try:
        df_main = load_data("SELECT * FROM lotto_history ORDER BY draw_date DESC")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("總收錄期數", f"{len(df_main)} 期")
        
        if not freq_df.empty and freq_df['count'].sum() > 0:
            c2.metric("最熱門號碼", f"{int(freq_df.iloc[0]['number']):02d} ({int(freq_df.iloc[0]['count'])}次)")
            c3.metric("最冷門號碼", f"{int(freq_df.iloc[-1]['number']):02d} ({int(freq_df.iloc[-1]['count'])}次)")
        
        st.subheader("📈 歷年號碼開出頻率分佈圖")
        chart_data = freq_df.sort_values(by='number').set_index('number')
        st.bar_chart(chart_data)
        
        st.subheader("📋 原始開獎紀錄")
        st.dataframe(df_main, use_container_width=True)
    except Exception as e:
        st.warning(f"⚠️ 讀取歷史數據庫時發生未知錯誤。詳細資訊: {e}")

# ------------------------------------------
# 模組 C：加碼活動數據查詢
# ------------------------------------------
elif page == "🧧 加碼活動數據查詢":
    st.title("🧧 加碼活動數據查詢 (2011-2026)")
    
    try:
        df_bonus = load_data("SELECT * FROM lotto_bonus_history ORDER BY draw_date DESC")
        
        if not df_bonus.empty:
            events = df_bonus['bonus_name'].unique().tolist()
            selected_event = st.selectbox("📌 請選擇加碼活動：", events)
            
            filtered_df = df_bonus[df_bonus['bonus_name'] == selected_event]
            st.metric(f"共開出組數", f"{len(filtered_df)} 組")
            
            display_df = filtered_df.dropna(axis=1, how='all')
            
            # 清理浮點數型態，格式化號碼顯示
            for col in display_df.columns:
                if col.startswith('num'):
                    display_df[col] = display_df[col].apply(lambda x: f"{int(x):02d}" if pd.notnull(x) and str(x).replace('.0','').isdigit() else "")
                    
            st.dataframe(display_df, use_container_width=True, height=500)
        else:
            st.info("資料庫中目前沒有加碼活動資料。")
    except Exception as e:
        st.warning(f"⚠️ 讀取加碼數據庫時發生未知錯誤。詳細資訊: {e}")
