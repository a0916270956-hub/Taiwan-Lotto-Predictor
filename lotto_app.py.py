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
        st.info("🔄 系統首次啟動，正在為您自動建置大樂透資料庫，請稍候...")
        conn = sqlite3.connect(DB_NAME)
        
        try:
            # 處理常規大樂透
            df_main = pd.read_csv(MAIN_CSV)
            df_main.to_sql('lotto_history', conn, if_exists='replace', index=False)
            conn.execute('CREATE INDEX idx_draw_date ON lotto_history(draw_date)')
            
            # 處理加碼大樂透
            df_extra = pd.read_csv(EXTRA_CSV)
            df_extra.to_sql('lotto_bonus_history', conn, if_exists='replace', index=False)
            conn.execute('CREATE INDEX idx_bonus_period ON lotto_bonus_history(period)')
            
            conn.commit()
            st.success("✅ 資料庫建置完成！")
        except Exception as e:
            st.error(f"❌ 資料庫建置失敗，請確認 CSV 檔案是否在同一個資料夾。錯誤: {e}")
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
    df = load_data("SELECT num1, num2, num3, num4, num5, num6 FROM lotto_history")
    all_nums = pd.concat([df['num1'], df['num2'], df['num3'], df['num4'], df['num5'], df['num6']])
    freq = all_nums.value_counts().reset_index()
    freq.columns = ['number', 'count']
    return freq.sort_values(by='count', ascending=False)

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
hot_numbers = freq_df.head(15)['number'].tolist()  # 前 15 大熱門
cold_numbers = freq_df.tail(15)['number'].tolist() # 最後 15 大冷門

# ------------------------------------------
# 模組 A：策略選號預測引擎
# ------------------------------------------
if page == "🤖 策略選號預測引擎":
    st.title("🤖 大樂透策略選號預測引擎")
    st.markdown("結合歷史數據庫 (`2007-2026`)，提供多種統計策略為您生成下一期的推薦號碼。")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ 參數設定")
        strategy = st.selectbox("請選擇預測策略：", [
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
                if strategy == "均衡演算法 (熱門+冷門+隨機)":
                    # 2熱 + 2冷 + 2隨機
                    picks = random.sample(hot_numbers, 2) + random.sample(cold_numbers, 2)
                    while len(picks) < 6:
                        n = random.randint(1, 49)
                        if n not in picks: picks.append(n)
                
                elif strategy == "追熱牌策略 (從最常開出號碼挑選)":
                    picks = random.sample(hot_numbers, 6)
                
                elif strategy == "搏冷門策略 (從最少開出號碼挑選)":
                    picks = random.sample(cold_numbers, 6)
                    
                else: # 純隨機
                    picks = random.sample(range(1, 50), 6)
                
                picks.sort()
                # 視覺化顯示號碼
                html_balls = "".join([f"<span style='display:inline-block; width:40px; height:40px; line-height:40px; text-align:center; background-color:#ffcc00; color:#333; border-radius:50%; margin-right:10px; font-weight:bold; font-size:18px; box-shadow: 2px 2px 5px rgba(0,0,0,0.2);'>{n:02d}</span>" for n in picks])
                st.markdown(f"<div style='margin-bottom:15px; padding:15px; background-color:#f8f9fa; border-radius:10px; border-left:5px solid #ffcc00;'>組別 {i+1}:<br><br>{html_balls}</div>", unsafe_allow_html=True)
            
            st.info("💡 貼心提醒：大樂透為獨立隨機機率，本系統依歷史統計提供選號靈感，請理性投注。")

# ------------------------------------------
# 模組 B：常規獎號歷史分析
# ------------------------------------------
elif page == "📊 常規獎號歷史分析":
    st.title("📊 常規大樂透歷史分析 (2007-2026)")
    df_main = load_data("SELECT * FROM lotto_history ORDER BY draw_date DESC")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("總收錄期數", f"{len(df_main)} 期")
    c2.metric("最熱門號碼", f"{freq_df.iloc[0]['number']:02d} ({freq_df.iloc[0]['count']}次)")
    c3.metric("最冷門號碼", f"{freq_df.iloc[-1]['number']:02d} ({freq_df.iloc[-1]['count']}次)")
    
    st.subheader("📈 歷年號碼開出頻率分佈圖")
    chart_data = freq_df.sort_values(by='number').set_index('number')
    st.bar_chart(chart_data)
    
    st.subheader("📋 原始開獎紀錄")
    st.dataframe(df_main, use_container_width=True)

# ------------------------------------------
# 模組 C：加碼活動數據查詢
# ------------------------------------------
elif page == "🧧 加碼活動數據查詢":
    st.title("🧧 加碼活動數據查詢 (2011-2026)")
    df_bonus = load_data("SELECT * FROM lotto_bonus_history ORDER BY draw_date DESC")
    
    events = df_bonus['bonus_name'].unique().tolist()
    selected_event = st.selectbox("📌 請選擇加碼活動：", events)
    
    filtered_df = df_bonus[df_bonus['bonus_name'] == selected_event]
    st.metric(f"共開出組數", f"{len(filtered_df)} 組")
    
    st.dataframe(filtered_df.dropna(axis=1, how='all'), use_container_width=True, height=500)