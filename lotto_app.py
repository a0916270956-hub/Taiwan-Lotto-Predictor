import streamlit as st
import sqlite3
import pandas as pd
import os
import random

# ==========================================
# 1. 系統初始化與資料庫建置 (自動化)
# ==========================================
DB_NAME = "lotto.db"
MAIN_CSV = "lotto_2007_2026.csv"
EXTRA_CSV = "lotto_extra_2011_2026.csv"

@st.cache_resource
def init_database():
    """如果資料庫不存在，則自動讀取 CSV 建立資料庫"""
    if not os.path.exists(DB_NAME):
        st.info("🔄 系統首次啟動或雲端重啟，正在為您自動建置大樂透資料庫，請稍候...")
        conn = sqlite3.connect(DB_NAME)
        
        try:
            # 處理常規大樂透
            if os.path.exists(MAIN_CSV):
                df_main = pd.read_csv(MAIN_CSV)
                df_main.to_sql('lotto_history', conn, if_exists='replace', index=False)
                conn.execute('CREATE INDEX idx_draw_date ON lotto_history(draw_date)')
            
            # 處理加碼大樂透
            if os.path.exists(EXTRA_CSV):
                df_extra = pd.read_csv(EXTRA_CSV)
                df_extra.to_sql('lotto_bonus_history', conn, if_exists='replace', index=False)
                conn.execute('CREATE INDEX idx_bonus_period ON lotto_bonus_history(period)')
            
            conn.commit()
            st.success("✅ 資料庫建置完成！")
        except Exception as e:
            st.error(f"❌ 資料庫建置失敗，錯誤: {e}")
        finally:
            conn.close()

# 執行初始化
init_database()

# ==========================================
# 2. 共用資料讀取函數
# ==========================================
@st.cache_data
def load_data(query):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

@st.cache_data
def get_number_frequencies():
    """計算所有號碼的歷史出現頻率"""
    try:
        df = load_data("SELECT num1, num2, num3, num4, num5, num6 FROM lotto_history")
        all_nums = pd.concat([df['num1'], df['num2'], df['num3'], df['num4'], df['num5'], df['num6']])
        freq = all_nums.value_counts().reset_index()
        freq.columns = ['number', 'count']
        
        # 強制將號碼轉換為整數 (避免 pandas 在合併時將其轉為浮點數導致後續格式化報錯)
        freq['number'] = freq['number'].astype(int)
        
        return freq.sort_values(by='count', ascending=False)
    except Exception:
        # 避免資料庫尚未完全建置時引發錯誤
        return pd.DataFrame({'number': list(range(1, 50)), 'count': [0]*49})

# ==========================================
# 3. 網頁介面設計與路由
# ==========================================
st.set_page_config(page_title="大樂透 AI 預測與分析系統", page_icon="🎯", layout="wide")

st.sidebar.title("🎯 系統導覽")
page = st.sidebar.radio("請選擇功能模組", [
    "🤖 策略選號預測引擎", 
    "📊 常規獎號歷史分析", 
    "🧧 加碼活動數據查詢"
])

# 取得頻率資料供後續使用
freq_df = get_number_frequencies()
if not freq_df.empty and freq_df['count'].sum() > 0:
    hot_numbers = freq_df.head(15)['number'].tolist()  # 前 15 大熱門
    cold_numbers = freq_df.tail(15)['number'].tolist() # 最後 15 大冷門
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
                
                # --- 策略 1: 高期望值與常態分佈過濾法 ---
                if strategy == "高期望值與常態分佈過濾法 (資料科學推薦)":
                    valid_picks = False
                    attempts = 0
                    # 偏好大於 31 的號碼 (避開生日陷阱，大號碼權重加倍)
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
                        
                        # 嚴格過濾：和值介於 120~180，且奇偶比為 2:4, 3:3 或 4:2
                        if 120 <= total_sum <= 180 and (odds in [2, 3, 4]):
                            picks = temp_picks
                            valid_picks = True
                            
                    # 若極端情況下 1000 次都沒配出來，則給予隨機
                    if not valid_picks:
                        picks = random.sample(range(1, 50), 6)

                # --- 策略 2: 均衡演算法 ---
                elif strategy == "均衡演算法 (熱門+冷門+隨機)":
                    picks = random.sample(hot_numbers, 2) + random.sample(cold_numbers, 2)
                    while len(picks) < 6:
                        n = random.randint(1, 49)
                        if n not in picks: picks.append(n)
                
                # --- 策略 3: 追熱牌 ---
                elif strategy == "追熱牌策略 (從最常開出號碼挑選)":
                    picks = random.sample(hot_numbers, 6)
                
                # --- 策略 4: 搏冷門 ---
                elif strategy == "搏冷門策略 (從最少開出號碼挑選)":
                    picks = random.sample(cold_numbers, 6)
                    
                # --- 策略 5: 純隨機 ---
                else: 
                    picks = random.sample(range(1, 50), 6)
                
                picks.sort()
                
                # 視覺化顯示號碼 (仿真實彩球)
                html_balls = "".join([
                    f"<span style='display:inline-block; width:45px; height:45px; line-height:45px; "
                    f"text-align:center; background-color:#ffcc00; color:#333; border-radius:50%; "
                    f"margin-right:12px; font-weight:bold; font-size:20px; "
                    f"box-shadow: 2px 2px 5px rgba(0,0,0,0.3);'>{int(n):02d}</span>" 
                    for n in picks
                ])
                
                # 附加數據科學指標顯示
                metrics_html = ""
                if strategy == "高期望值與常態分佈過濾法 (資料科學推薦)":
                    odds_cnt = sum(1 for n in picks if n % 2 != 0)
                    metrics_html = f"<div style='margin-top:10px; font-size:14px; color:#555;'>" \
                                   f"📊 指標分析 ➔ 和值: <b>{sum(picks)}</b> | 奇偶比: <b>{odds_cnt}:{6-odds_cnt}</b>" \
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
        
        # 這裡已經加入了 int() 強制轉型，徹底解決 ValueError 的問題！
        c2.metric("最熱門號碼", f"{int(freq_df.iloc[0]['number']):02d} ({int(freq_df.iloc[0]['count'])}次)")
        c3.metric("最冷門號碼", f"{int(freq_df.iloc[-1]['number']):02d} ({int(freq_df.iloc[-1]['count'])}次)")
        
        st.subheader("📈 歷年號碼開出頻率分佈圖")
        chart_data = freq_df.sort_values(by='number').set_index('number')
        st.bar_chart(chart_data)
        
        st.subheader("📋 原始開獎紀錄")
        st.dataframe(df_main, use_container_width=True)
    except Exception as e:
        st.warning(f"⚠️ 尚未讀取到資料，請確認資料庫是否建置成功。錯誤訊息: {e}")

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
            
            # 清除全部都是 NaN (空值) 的欄位以保持版面乾淨
            display_df = filtered_df.dropna(axis=1, how='all')
            
            # 強制將號碼轉為沒有小數點的格式顯示
            for col in display_df.columns:
                if col.startswith('num'):
                    display_df[col] = display_df[col].apply(lambda x: f"{int(x):02d}" if pd.notnull(x) else "")
                    
            st.dataframe(display_df, use_container_width=True, height=500)
        else:
            st.info("資料庫中目前沒有加碼活動資料。")
    except Exception as e:
        st.warning(f"⚠️ 尚未讀取到加碼資料，請確認資料庫是否建置成功。錯誤訊息: {e}")
