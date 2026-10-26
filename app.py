import streamlit as st
import pandas as pd
import random
import os
import threading
import json

# --- 設定 ---
st.set_page_config(page_title="Flashcards", page_icon="📚", layout="centered")

# --- 全体UIのCSSポリッシュ ---
st.markdown("""
<style>
/* --- プレミアムな背景アニメーションとグラスモーフィズム --- */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(-45deg, #e6e9f0, #eef1f5, #d5d9e5, #e0e5ec) !important;
    background-size: 400% 400% !important;
    animation: gradientBG 15s ease infinite !important;
}

@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* メインコンテンツをすりガラス風のカードにする */
[data-testid="stMainBlockContainer"] {
    background: rgba(255, 255, 255, 0.75) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-radius: 24px !important;
    padding: 2rem !important;
    margin: 5rem auto 2rem auto !important;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    max-width: 90% !important;
}

@media (max-width: 768px) {
    [data-testid="stMainBlockContainer"] {
        padding: 1.5rem 1rem !important;
        margin: 4rem auto 1rem auto !important;
        border-radius: 16px !important;
        max-width: 95% !important;
    }
}

/* ヘッダー全体を透明ですりガラス風に戻す */
[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    border-bottom: 1px solid rgba(0,0,0,0.05) !important;
    box-shadow: none !important;
}

/* サイドバーを半透明のすりガラス風にする */
[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.5) !important;
}

/* ヘッダー内のアイコン類の色をダークグレーにする */
[data-testid="stHeader"] svg {
    fill: #334155 !important;
    color: #334155 !important;
}

/* スマホでのサイドバー開閉ボタン（＞）を丸い独立したボタンにして常に目立たせる */
[data-testid="collapsedControl"] {
    transform: scale(1.3) !important;
    transform-origin: center !important;
    background-color: #e2e8f0 !important;
    color: #334155 !important;
    border-radius: 50% !important;
    padding: 6px !important;
    margin: 10px !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    z-index: 999999 !important;
    transition: all 0.2s ease;
}
[data-testid="collapsedControl"]:hover {
    transform: scale(1.4) !important;
    background-color: #cbd5e1 !important;
}

/* プライマリボタンのグラデーションとホバー時の浮き上がり */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ff6b6b, #ff4757) !important;
    border: none !important;
    box-shadow: 0 4px 10px rgba(255, 107, 107, 0.4) !important;
    transition: all 0.2s ease-in-out !important;
    border-radius: 12px !important;
}
div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #ff4757, #ff6b6b) !important;
    box-shadow: 0 6px 15px rgba(255, 107, 107, 0.6) !important;
    transform: translateY(-2px) !important;
}
div.stButton > button[kind="primary"]:active {
    transform: scale(0.95) !important;
}

/* セカンダリボタンのホバーエフェクト */
div.stButton > button[kind="secondary"] {
    border-radius: 12px !important;
    transition: all 0.2s ease-in-out !important;
}
div.stButton > button[kind="secondary"]:hover {
    border-color: #6e8efb !important;
    color: #6e8efb !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 10px rgba(110, 142, 251, 0.2) !important;
}
div.stButton > button[kind="secondary"]:active {
    transform: scale(0.95) !important;
}

/* プログレスバーを白背景でも見えやすくする */
.stProgress > div {
    background-color: #cbd5e1 !important;
    border-radius: 10px !important;
}
.stProgress > div > div > div {
    border-radius: 10px !important;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6) !important;
}

/* 発音ボタンのホバーエフェクト */
span[id^="speaker-icon"]:hover {
    transform: scale(1.1);
    background: #dbe4ff !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}
</style>
""", unsafe_allow_html=True)

# スワイプでサイドバーを開くJS
import streamlit.components.v1 as components
components.html("""
<script>
    var parentDoc = window.parent.document;
    if (!parentDoc.body.hasAttribute('data-swipe-listener')) {
        parentDoc.body.setAttribute('data-swipe-listener', 'true');
        var startX = 0;
        parentDoc.addEventListener('touchstart', function(e) {
            startX = e.changedTouches[0].screenX;
        }, {passive: true});
        parentDoc.addEventListener('touchend', function(e) {
            var endX = e.changedTouches[0].screenX;
            if (startX < 40 && endX > startX + 50) {
                var sidebarBtn = parentDoc.querySelector('[data-testid="collapsedControl"]');
                if (sidebarBtn) sidebarBtn.click();
            }
        }, {passive: true});
    }
</script>
""", height=0, width=0)


# --- データ接続の設定 ---
try:
    from streamlit_gsheets import GSheetsConnection
    USE_GSHEETS = True
except ImportError:
    USE_GSHEETS = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "words.csv")
SETTINGS_FILE = os.path.join(BASE_DIR, "user_settings.json")

def load_settings():
    settings = {}
    
    # 1. Googleスプレッドシート連携が有効な場合は Settings シートから取得
    if USE_GSHEETS and "connections" in st.secrets and "gsheets" in st.secrets.connections:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df_set = conn.read(worksheet="Settings", ttl=0)
            if not df_set.empty:
                row = df_set.iloc[0]
                if "rank" in row and pd.notna(row["rank"]):
                    settings["rank_selector"] = [int(x) for x in str(row["rank"]).split(",") if str(x).strip().isdigit()]
                if "start_id" in row and pd.notna(row["start_id"]):
                    settings["start_id"] = int(row["start_id"])
                if "end_id" in row and pd.notna(row["end_id"]):
                    settings["end_id"] = int(row["end_id"])
                if "mastery" in row and pd.notna(row["mastery"]):
                    settings["mastery_selector"] = [str(x).strip() for x in str(row["mastery"]).split(",") if str(x).strip() in ["A", "B", "C", "D"]]
                if "num_q" in row and pd.notna(row["num_q"]):
                    settings["num_q"] = int(row["num_q"])
                return settings
        except Exception:
            pass

    # 2. スプレッドシートから取得できない場合はローカルJSONを参照
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            settings = {}
            
    return settings

def save_settings_bg(settings_dict):
    """バックグラウンドで設定をスプレッドシート / ローカルJSONへ保存"""
    # ローカルJSONへ保存
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings_dict, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # スプレッドシート Settings シートへ保存
    if USE_GSHEETS and "connections" in st.secrets and "gsheets" in st.secrets.connections:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df_set = pd.DataFrame([{
                "rank": ",".join(map(str, settings_dict.get("rank_selector", []))),
                "start_id": settings_dict.get("start_id", 1),
                "end_id": settings_dict.get("end_id", 3800),
                "mastery": ",".join(settings_dict.get("mastery_selector", [])),
                "num_q": settings_dict.get("num_q", 20)
            }])
            conn.update(worksheet="Settings", data=df_set)
        except Exception:
            pass

def save_settings():
    try:
        ranks = [int(x) for x in st.session_state.get("rank_selector", [])]
        masteries = [str(x) for x in st.session_state.get("mastery_selector", [])]
        start_val = int(st.session_state.get("start_id", 1))
        end_val = int(st.session_state.get("end_id", 3800))
        num_q_val = int(st.session_state.get("num_q", 20))
        
        settings = {
            "rank_selector": ranks,
            "start_id": start_val,
            "end_id": end_val,
            "mastery_selector": masteries,
            "num_q": num_q_val
        }
        
        # 非同期で保存を実行してUI操作を軽く保持
        threading.Thread(target=save_settings_bg, args=(settings,)).start()
        
        if hasattr(st, "query_params"):
            if ranks:
                st.query_params["rank"] = ",".join(map(str, ranks))
            if masteries:
                st.query_params["mastery"] = ",".join(masteries)
            st.query_params["start"] = str(start_val)
            st.query_params["end"] = str(end_val)
            st.query_params["num_q"] = str(num_q_val)
    except Exception:
        pass

user_settings = load_settings()

# --- セッションステートの初期化 ---
def init_session():
    st.session_state.questions = []
    st.session_state.current_idx = 0
    st.session_state.show_answer = False
    st.session_state.is_learning = False
    st.session_state.last_action = "start"
    st.session_state.close_sidebar = False
    st.session_state.show_detailed_stats = False

if "is_learning" not in st.session_state:
    init_session()

# --- データ読み込み ---
def load_data():
    if "df" in st.session_state:
        return st.session_state.df

    try:
        if USE_GSHEETS and "connections" in st.secrets and "gsheets" in st.secrets.connections:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(ttl=0) 
        else:
            if not os.path.exists(CSV_FILE):
                return None
            df = pd.read_csv(CSV_FILE)
            
        required_cols = {"ID", "Word", "Meaning", "Mastery", "Rank"}
        if not required_cols.issubset(df.columns):
            st.error(f"データソースに必要なカラムが不足しています。必要: {required_cols}")
            return None
        st.session_state.df = df
        return df
    except Exception as e:
        st.error(f"データの読み込みエラー: {e}")
        return None

df = load_data()

# --- バックグラウンド単語データ保存関数 ---
def save_data_bg(df_to_save):
    try:
        if USE_GSHEETS and "connections" in st.secrets and "gsheets" in st.secrets.connections:
            conn = st.connection("gsheets", type=GSheetsConnection)
            conn.update(data=df_to_save)
        else:
            df_to_save.to_csv(CSV_FILE, index=False)
    except Exception as e:
        pass

# --- 関数 ---
def start_learning(target_df, num_q):
    save_settings()
    if target_df.empty:
        st.warning("条件に合致する単語がありません。設定を変更してください。")
        return
    
    records = target_df.to_dict("records")
    random.shuffle(records)
    
    st.session_state.questions = records[:num_q]
    st.session_state.current_idx = 0
    st.session_state.show_answer = False
    st.session_state.is_learning = True
    st.session_state.last_action = "start"
    st.session_state.close_sidebar = True

def go_back():
    if st.session_state.current_idx > 0:
        st.session_state.current_idx -= 1
        st.session_state.show_answer = False
        st.session_state.last_action = "back"

def update_mastery(word_id, action, current_mastery):
    mastery_levels = ["D", "C", "B", "A"]
    new_mastery = current_mastery
    
    if action == "up":
        if current_mastery in mastery_levels:
            current_idx = mastery_levels.index(current_mastery)
            if current_idx < len(mastery_levels) - 1:
                new_mastery = mastery_levels[current_idx + 1]
    
    idx = df[df["ID"] == word_id].index
    if not idx.empty:
        df.loc[idx, "Mastery"] = new_mastery
        st.session_state.df = df
        threading.Thread(target=save_data_bg, args=(df.copy(),)).start()
    
    if st.session_state.current_idx < len(st.session_state.questions):
        st.session_state.questions[st.session_state.current_idx]["session_result"] = action
    
    st.session_state.current_idx += 1
    st.session_state.show_answer = False
    st.session_state.last_action = action

# --- サイドバー (設定エリア) ---
with st.sidebar:
    st.header("⚙️ 学習設定")
    
    if df is not None:
        min_id = int(df["ID"].min())
        max_id = int(df["ID"].max())
        available_ranks = [int(r) for r in sorted(df["Rank"].dropna().unique().tolist())]
        if not available_ranks:
            available_ranks = [1, 2, 3, 4]
            
        # 1. Rank の初期化
        if "rank_selector" not in st.session_state:
            saved_ranks = user_settings.get("rank_selector")
            if saved_ranks is not None:
                valid_ranks = [int(r) for r in saved_ranks if int(r) in available_ranks]
                st.session_state.rank_selector = valid_ranks if valid_ranks else available_ranks
            else:
                st.session_state.rank_selector = available_ranks

        # 2. 開始 ID・終了 ID の初期化
        if "start_id" not in st.session_state:
            saved_start = user_settings.get("start_id")
            if saved_start is not None:
                st.session_state.start_id = max(min_id, min(max_id, int(saved_start)))
            else:
                st.session_state.start_id = min_id
                
        if "end_id" not in st.session_state:
            saved_end = user_settings.get("end_id")
            if saved_end is not None:
                st.session_state.end_id = max(min_id, min(max_id, int(saved_end)))
            else:
                st.session_state.end_id = max_id

        st.write("**出題対象の Rank**")
        def on_rank_change():
            save_settings()
            
        if hasattr(st, "pills"):
            selected_ranks = st.pills("Rank", options=available_ranks, selection_mode="multi", label_visibility="collapsed", key="rank_selector", on_change=on_rank_change)
        else:
            selected_ranks = st.multiselect("Rank", options=available_ranks, label_visibility="collapsed", key="rank_selector", on_change=on_rank_change)

        st.write("**IDの範囲を指定**")
        col1, col2 = st.columns(2)
        with col1:
            start_id = st.number_input("開始 ID", min_value=min_id, max_value=max_id, key="start_id", on_change=save_settings)
        with col2:
            end_id = st.number_input("終了 ID", min_value=min_id, max_value=max_id, key="end_id", on_change=save_settings)

        st.write("**出題対象の Mastery**")
        mastery_options = ["A", "B", "C", "D"]
        if "mastery_selector" not in st.session_state:
            saved_masteries = user_settings.get("mastery_selector")
            if saved_masteries is not None:
                valid_m = [str(m) for m in saved_masteries if str(m) in mastery_options]
                st.session_state.mastery_selector = valid_m if valid_m else ["B", "C", "D"]
            else:
                st.session_state.mastery_selector = ["B", "C", "D"]
            
        if hasattr(st, "pills"):
            selected_masteries = st.pills("Mastery", options=mastery_options, selection_mode="multi", label_visibility="collapsed", key="mastery_selector", on_change=save_settings)
        else:
            selected_masteries = st.multiselect("Mastery", options=mastery_options, label_visibility="collapsed", key="mastery_selector", on_change=save_settings)
        
        st.markdown("---")
        
        target_df = df[
            (df["ID"] >= min(start_id, end_id)) & 
            (df["ID"] <= max(start_id, end_id)) & 
            (df["Rank"].isin(selected_ranks)) & 
            (df["Mastery"].isin(selected_masteries))
        ]
        
        if not target_df.empty:
            max_q = min(200, len(target_df))
            if "num_q" not in st.session_state:
                saved_num_q = user_settings.get("num_q", 20)
                try:
                    st.session_state.num_q = min(max_q, max(1, int(saved_num_q)))
                except Exception:
                    st.session_state.num_q = min(20, max_q)
            else:
                if st.session_state.num_q > max_q:
                    st.session_state.num_q = max_q
                elif st.session_state.num_q < 1:
                    st.session_state.num_q = 1

            def dec_q_10():
                st.session_state.num_q = max(1, st.session_state.num_q - 10)
                save_settings()
            def dec_q_1():
                st.session_state.num_q = max(1, st.session_state.num_q - 1)
                save_settings()
            def inc_q_1():
                st.session_state.num_q = min(max_q, st.session_state.num_q + 1)
                save_settings()
            def inc_q_10():
                st.session_state.num_q = min(max_q, st.session_state.num_q + 10)
                save_settings()
            def on_num_q_change():
                save_settings()
                
            st.write("**今回の出題数**")
            st.markdown("""
            <style>
            div[data-testid="stButton"] button p {
                text-align: center !important;
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                margin: 0 !important;
                width: 100% !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            col_q1, col_q2, col_q3 = st.columns([1, 4, 1])
            with col_q1:
                st.button("◀", on_click=dec_q_10, use_container_width=True)
            with col_q2:
                num_questions = st.number_input("出題数", min_value=1, max_value=max_q, step=1, key="num_q", label_visibility="collapsed", on_change=on_num_q_change)
            with col_q3:
                st.button("▶", on_click=inc_q_10, use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 学習をスタート", use_container_width=True, type="primary"):
                start_learning(target_df, st.session_state.num_q)
        else:
            st.warning("条件に合致する単語がありません。")
            
        save_settings()
            
    else:
        st.warning("データが見つかりません。設定を確認してください。")

# --- メインエリア (フラッシュカード) ---
if not st.session_state.is_learning:
    if st.session_state.get("show_detailed_stats", False):
        st.markdown("<h2 style='text-align: center; color: #4CAF50;'>📈 ランク別 詳細データ</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        if df is not None:
            stats_df = pd.crosstab(df['Rank'], df['Mastery'])
            for col in ['A', 'B', 'C', 'D']:
                if col not in stats_df.columns:
                    stats_df[col] = 0
            
            stats_df = stats_df[['A', 'B', 'C', 'D']]
            stats_df['合計'] = stats_df.sum(axis=1)
            stats_df = stats_df.reset_index()
            
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔙 ホームに戻る", use_container_width=True):
            st.session_state.show_detailed_stats = False
            st.rerun()
            
    else:
        st.markdown("<h1 style='text-align: center; color: #FF4B4B; font-size: 3rem;'>TOEFL iBT 3800</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #555;'>目指せスコアアップ！🚀</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        if df is not None:
            total_words = len(df)
            mastery_counts = df["Mastery"].value_counts()
            count_A = mastery_counts.get("A", 0)
            count_B = mastery_counts.get("B", 0)
            count_C = mastery_counts.get("C", 0)
            count_D = mastery_counts.get("D", 0)
            
            mastered = count_A
            progress_pct = int((mastered / total_words) * 100) if total_words > 0 else 0
            
            st.markdown("### 📊 現在の学習ダッシュボード")
            
            st.markdown(f"**マスター率 (A): <span style='color: #4CAF50; font-size: 1.2rem;'>{progress_pct}%</span>**", unsafe_allow_html=True)
            st.progress(progress_pct / 100.0)
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🟦 A (完璧)", f"{count_A} 語")
            col2.metric("🟩 B (だいたい)", f"{count_B} 語")
            col3.metric("🟨 C (うろ覚え)", f"{count_C} 語")
            col4.metric("🟥 D (ダメ)", f"{count_D} 語")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📈 ランク別の詳細データを見る", use_container_width=True):
                st.session_state.show_detailed_stats = True
                st.rerun()
                
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("💡 **使い方:** 左のサイドバー（⚙️ 学習設定）から学習する条件を選んで、**「🚀 学習をスタート」**を押してください！")
        else:
            st.warning("データが見つかりません。")
            
    st.markdown("<br><br>", unsafe_allow_html=True)
    if USE_GSHEETS and "connections" in st.secrets and "gsheets" in st.secrets.connections:
        st.caption("☁️ データソース: Googleスプレッドシート連携中")
    else:
        st.caption("📁 データソース: ローカルCSVファイル")

else:
    if st.session_state.get("close_sidebar", False):
        import streamlit.components.v1 as components
        components.html("""
        <script>
            const btn1 = window.parent.document.querySelector('button[kind="headerNoPadding"]');
            if (btn1) { btn1.click(); }
            const btn2 = window.parent.document.querySelector('[data-testid="collapsedControl"]');
            if (btn2) { btn2.click(); }
            const btn3 = window.parent.document.querySelector('button[aria-label="Collapse sidebar"]');
            if (btn3) { btn3.click(); }
        </script>
        """, height=0, width=0)
        st.session_state.close_sidebar = False

    total_q = len(st.session_state.questions)
    curr_idx = st.session_state.current_idx
    
    if curr_idx >= total_q:
        st.success("🎉 学習完了！お疲れ様でした！")
        st.balloons()
        
        st.markdown("### 📝 今回の学習結果")
        results_data = []
        for q in st.session_state.questions:
            res = q.get("session_result", "未回答")
            mark = "✅ できた" if res == "up" else ("🔄 もう一度" if res == "keep" else "未回答")
            results_data.append({
                "単語": q["Word"],
                "意味": q["Meaning"],
                "結果": mark
            })
        
        if results_data:
            df_res = pd.DataFrame(results_data)
            st.dataframe(
                df_res,
                use_container_width=True,
                hide_index=True
            )
            
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔁 同じ設定でもう一度", use_container_width=True, type="primary"):
                start_learning(target_df, st.session_state.get("num_q", 20))
                st.rerun()
        with col2:
            if st.button("🔄 設定し直して再スタート", use_container_width=True):
                init_session()
                st.rerun()
    else:
        word_data = st.session_state.questions[curr_idx]
        
        st.caption(f"🚀 進捗: **{curr_idx + 1} / {total_q}** 問目")
        st.progress((curr_idx) / total_q)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        last_action = st.session_state.get("last_action", "start")
        if last_action == "up":
            anim_css = "animation: enterFromLeft 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;"
        elif last_action == "keep":
            anim_css = "animation: enterFromRight 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;"
        elif last_action == "back":
            anim_css = "animation: enterFromLeft 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;"
        else:
            anim_css = "animation: popIn 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;"
        
        css = f"""
        <style>
        @keyframes enterFromRight {{
            from {{ transform: translateX(100vw); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        @keyframes enterFromLeft {{
            from {{ transform: translateX(-100vw); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        @keyframes popIn {{
            from {{ transform: scale(0.8); opacity: 0; }}
            to {{ transform: scale(1); opacity: 1; }}
        }}
        .flip-card-container {{
            perspective: 1000px;
            width: 100%;
            margin-bottom: 20px;
            {anim_css}
        }}
        .flip-card-inner {{
            position: relative;
            width: 100%;
            height: 300px;
            text-align: center;
            transition: transform 0.6s;
            transform-style: preserve-3d;
            cursor: pointer;
        }}
        input[type=checkbox].flip-toggle {{
            display: none;
        }}
        input[type=checkbox].flip-toggle:checked + .flip-card-inner {{
            transform: rotateY(180deg);
        }}
        .flip-card-front, .flip-card-back {{
            position: absolute;
            width: 100%;
            height: 100%;
            -webkit-backface-visibility: hidden;
            backface-visibility: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 20px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }}
        .flip-card-front {{
            background: linear-gradient(135deg, #6e8efb, #a777e3);
            color: white;
        }}
        .flip-card-back {{
            background-color: #fff0f5;
            color: #d63031;
            transform: rotateY(180deg);
            border: 3px dashed #ff6b6b;
            box-sizing: border-box;
            padding: 20px;
        }}
        </style>
        """
        
        container_tag = "div" if curr_idx % 2 == 0 else "section"
        
        pronunciation = str(word_data.get('Pronunciation', ''))
        pronunciation_html = ""
        if pronunciation and pronunciation.lower() != 'nan':
            pronunciation_html = f'<div style="background-color: #f1f5f9; color: #475569; padding: 10px 24px; border-radius: 12px; margin-bottom: 12px; font-family: \'Lucida Sans Unicode\', \'Segoe UI\', \'Helvetica Neue\', Helvetica, Arial, sans-serif; font-size: 1.4rem; font-weight: 500; display: inline-block; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); letter-spacing: 1.5px;">{pronunciation}</div><br>'
        
        card_html = f"""
{css}
<{container_tag} class="flip-card-container">
    <label style="display:block; width:100%; height:100%; margin:0;">
        <input type="checkbox" class="flip-toggle" id="flip_{curr_idx}">
        <div class="flip-card-inner">
            <div class="flip-card-front">
                <h1 style='font-size: clamp(2.5rem, 10vw, 5rem); margin: 0; word-break: keep-all; overflow-wrap: normal; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); padding: 0 20px;'>{word_data['Word']}</h1>
            </div>
            <div class="flip-card-back">
                <h2 style='font-size: clamp(1.5rem, 6vw, 2.5rem); margin: 0; word-break: normal; overflow-wrap: break-word; padding: 0 20px;'>{word_data['Meaning']}</h2>
            </div>
        </div>
    </label>
</{container_tag}>
<div style="text-align: center; margin-top: 10px;">
{pronunciation_html}
<span id="speaker-icon-{curr_idx}" style="cursor: pointer; font-size: 1.1rem; color: #6e8efb; font-weight: bold; padding: 8px 16px; border-radius: 8px; background: #e0e7ff; display: inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.05); transition: all 0.2s;">🔊 発音を聴く</span>
</div>
"""
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        import json
        import streamlit.components.v1 as components
        word_js = json.dumps(word_data['Word'])
        components.html(f"""
        <script>
            var parentDoc = window.parent.document;
            var speakerBtn = parentDoc.getElementById('speaker-icon-{curr_idx}');
            if (speakerBtn && !speakerBtn.hasAttribute('data-has-listener')) {{
                speakerBtn.setAttribute('data-has-listener', 'true');
                speakerBtn.onclick = function() {{
                    var text = encodeURIComponent({word_js});
                    var url = "https://dict.youdao.com/dictvoice?audio=" + text + "&type=2";
                    var audio = new Audio(url);
                    audio.play().catch(function(e) {{
                        var msg = new SpeechSynthesisUtterance({word_js});
                        msg.lang = 'en-US';
                        msg.rate = 1.0;
                        window.speechSynthesis.speak(msg);
                    }});
                }};
            }}
            
            var meta = parentDoc.querySelector('meta[name="viewport"]');
            if (!meta) {{
                meta = parentDoc.createElement('meta');
                meta.name = "viewport";
                parentDoc.head.appendChild(meta);
            }}
            meta.content = "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no";
        </script>
        """, height=0, width=0)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("👈 もう一度", use_container_width=True, on_click=update_mastery, args=(word_data["ID"], "keep", word_data["Mastery"]))
        with col2:
            st.button("できた 👉", use_container_width=True, type="primary", on_click=update_mastery, args=(word_data["ID"], "up", word_data["Mastery"]))
            
        st.markdown("<br>", unsafe_allow_html=True)
        col_bottom1, col_bottom2 = st.columns(2)
        with col_bottom1:
            st.button("↩️ 前に戻る", use_container_width=True, on_click=go_back, disabled=(curr_idx == 0))
        with col_bottom2:
            if st.button("🏠 ホームに戻る", use_container_width=True):
                init_session()
                st.rerun()
