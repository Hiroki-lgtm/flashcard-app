import streamlit as st
import pandas as pd
import random
import os

# --- 設定 ---
st.set_page_config(page_title="Antigravity Flashcards", page_icon="📚", layout="centered")

# --- データ接続の設定 ---
# st-gsheets-connection がインストールされているか確認
try:
    from streamlit_gsheets import GSheetsConnection
    USE_GSHEETS = True
except ImportError:
    USE_GSHEETS = False

CSV_FILE = "words.csv"

# --- セッションステートの初期化 ---
def init_session():
    st.session_state.questions = []
    st.session_state.current_idx = 0
    st.session_state.show_answer = False
    st.session_state.is_learning = False

if "is_learning" not in st.session_state:
    init_session()

# --- データ読み込み ---
def load_data():
    try:
        # スプレッドシートの設定（secrets）が存在する場合はスプレッドシートから読み込む
        if USE_GSHEETS and "connections" in st.secrets and "gsheets" in st.secrets.connections:
            conn = st.connection("gsheets", type=GSheetsConnection)
            # ttl=0 で常に最新のデータを取得
            df = conn.read(ttl=0) 
        else:
            # ローカル環境用: CSVから読み込む
            if not os.path.exists(CSV_FILE):
                return None
            df = pd.read_csv(CSV_FILE)
            
        required_cols = {"ID", "Word", "Meaning", "Mastery", "Rank"}
        if not required_cols.issubset(df.columns):
            st.error(f"データソースに必要なカラムが不足しています。必要: {required_cols}")
            return None
        return df
    except Exception as e:
        st.error(f"データの読み込みエラー: {e}")
        return None

df = load_data()

# --- 関数 ---
def start_learning(ranks, masteries, num_q):
    if df is None:
        return
    
    # フィルタリング
    target_df = df[df["Rank"].isin(ranks) & df["Mastery"].isin(masteries)]
    if target_df.empty:
        st.warning("条件に合致する単語がありません。設定を変更してください。")
        return
    
    # 抽出してシャッフル
    records = target_df.to_dict("records")
    random.shuffle(records)
    
    # 出題数を制限
    st.session_state.questions = records[:num_q]
    st.session_state.current_idx = 0
    st.session_state.show_answer = False
    st.session_state.is_learning = True

def update_mastery(word_id, new_mastery):
    # メモリ上のデータフレームを更新
    idx = df[df["ID"] == word_id].index
    if not idx.empty:
        df.loc[idx, "Mastery"] = new_mastery
        
        # データソースに上書き保存
        try:
            if USE_GSHEETS and "connections" in st.secrets and "gsheets" in st.secrets.connections:
                conn = st.connection("gsheets", type=GSheetsConnection)
                conn.update(data=df) # スプレッドシートを更新
            else:
                df.to_csv(CSV_FILE, index=False) # CSVを更新
        except Exception as e:
            st.error(f"保存エラー: {e}")
    
    # 次の問題へ
    st.session_state.current_idx += 1
    st.session_state.show_answer = False

# --- サイドバー (設定エリア) ---
with st.sidebar:
    st.header("⚙️ 学習設定")
    if df is not None:
        available_ranks = sorted(df["Rank"].dropna().unique().tolist())
        if not available_ranks:
            available_ranks = [1, 2, 3, 4]
            
        selected_ranks = st.multiselect(
            "出題対象の Rank",
            options=available_ranks,
            default=available_ranks
        )
        
        selected_masteries = st.multiselect(
            "出題対象の Mastery",
            options=["A", "B", "C", "D"],
            default=["B", "C", "D"]
        )
        
        num_questions = st.slider("出題数", min_value=5, max_value=100, value=20, step=5)
        
        if st.button("🚀 学習をスタート", use_container_width=True, type="primary"):
            start_learning(selected_ranks, selected_masteries, num_questions)
    else:
        st.warning("データが見つかりません。設定を確認してください。")

# --- メインエリア (フラッシュカード) ---
if not st.session_state.is_learning:
    st.title("📚 英単語フラッシュカード")
    
    # 現在の接続モードを表示
    if USE_GSHEETS and "connections" in st.secrets and "gsheets" in st.secrets.connections:
        st.success("☁️ Googleスプレッドシートと連携しています")
    else:
        st.info("📁 ローカルのCSVファイルで動作しています")

    st.write("👈 サイドバーから出題条件を設定し、「学習をスタート」ボタンを押してください。")
    if df is not None:
        st.write(f"現在の単語登録数: **{len(df)}** 語")
else:
    total_q = len(st.session_state.questions)
    curr_idx = st.session_state.current_idx
    
    if curr_idx >= total_q:
        st.success("🎉 学習完了！ お疲れ様でした！")
        st.balloons()
        if st.button("🔄 設定し直して再スタート", use_container_width=True):
            init_session()
            st.rerun()
    else:
        # 現在の単語データ
        word_data = st.session_state.questions[curr_idx]
        
        # 進捗表示
        st.caption(f"進捗: **{curr_idx + 1} / {total_q}** 問目")
        st.progress((curr_idx) / total_q)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 表面 (Word)
        st.markdown(
            f"<h1 style='text-align: center; font-size: 3.5rem; word-wrap: break-word;'>{word_data['Word']}</h1>", 
            unsafe_allow_html=True
        )
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if not st.session_state.show_answer:
            # 答えを見るボタン
            if st.button("👀 答えを見る", use_container_width=True, type="primary"):
                st.session_state.show_answer = True
                st.rerun()
        else:
            # 裏面 (Meaning)
            st.markdown(
                f"<h2 style='text-align: center; font-size: 2.2rem; color: #ff4b4b; word-wrap: break-word;'>{word_data['Meaning']}</h2>", 
                unsafe_allow_html=True
            )
            
            st.markdown("<hr>", unsafe_allow_html=True)
            st.write("**この単語の定着度はどうでしたか？**")
            
            # 評価ボタン (横並び)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.button("🟦 A (完璧)", use_container_width=True, on_click=update_mastery, args=(word_data["ID"], "A"))
            with col2:
                st.button("🟩 B (だいたい)", use_container_width=True, on_click=update_mastery, args=(word_data["ID"], "B"))
            with col3:
                st.button("🟨 C (うろ覚え)", use_container_width=True, on_click=update_mastery, args=(word_data["ID"], "C"))
            with col4:
                st.button("🟥 D (ダメ)", use_container_width=True, on_click=update_mastery, args=(word_data["ID"], "D"))