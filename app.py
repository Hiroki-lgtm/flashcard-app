import streamlit as st
import pandas as pd
import random
import os

# --- 設定 ---
st.set_page_config(page_title="Antigravity Flashcards", page_icon="📚", layout="centered")

# --- データ接続の設定 ---
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
        return df
    except Exception as e:
        st.error(f"データの読み込みエラー: {e}")
        return None

df = load_data()

# --- 関数 ---
def start_learning(target_df, num_q):
    if target_df.empty:
        st.warning("条件に合致する単語がありません。設定を変更してください。")
        return
    
    records = target_df.to_dict("records")
    random.shuffle(records)
    
    st.session_state.questions = records[:num_q]
    st.session_state.current_idx = 0
    st.session_state.show_answer = False
    st.session_state.is_learning = True

def update_mastery(word_id, new_mastery):
    idx = df[df["ID"] == word_id].index
    if not idx.empty:
        df.loc[idx, "Mastery"] = new_mastery
        try:
            if USE_GSHEETS and "connections" in st.secrets and "gsheets" in st.secrets.connections:
                conn = st.connection("gsheets", type=GSheetsConnection)
                conn.update(data=df)
            else:
                df.to_csv(CSV_FILE, index=False)
        except Exception as e:
            st.error(f"保存エラー: {e}")
    
    st.session_state.current_idx += 1
    st.session_state.show_answer = False

def generate_html_export(target_df):
    # PDF出力用のHTML文字列を生成
    html_content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>単語リスト</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background-color: #f2f2f2; }
            @media print {
                .no-print { display: none; }
            }
        </style>
    </head>
    <body>
        <div class="no-print" style="margin-bottom: 20px; padding: 15px; background-color: #e7f3fe; border-left: 6px solid #2196F3;">
            <strong>💡 このページをPDFとして保存する方法：</strong><br>
            下のボタンを押すと印刷画面が開きます。送信先（プリンター）を「PDFに保存」に変更して「保存」を押してください。<br>
            <button onclick="window.print()" style="margin-top: 15px; padding: 10px 20px; cursor: pointer; background-color: #4CAF50; color: white; border: none; border-radius: 5px; font-weight: bold;">🖨️ PDF保存 / 印刷画面を開く</button>
        </div>
        <h2>📚 指定範囲の単語リスト</h2>
        <table>
            <tr><th>ID</th><th>英単語 (Word)</th><th>意味 (Meaning)</th><th>Rank</th><th>Mastery</th></tr>
    """
    for _, row in target_df.iterrows():
        html_content += f"<tr><td>{row['ID']}</td><td><strong>{row['Word']}</strong></td><td>{row['Meaning']}</td><td>{row['Rank']}</td><td>{row['Mastery']}</td></tr>"
    html_content += """
        </table>
    </body>
    </html>
    """
    return html_content

# --- サイドバー (設定エリア) ---
with st.sidebar:
    st.header("⚙️ 学習設定")
    
    if df is not None:
        # モード選択
        mode = st.radio("学習モード", ["🎯 条件で絞り込む", "🔢 番号（ID）で指定する"])
        
        target_df = pd.DataFrame()
        st.markdown("---")
        
        if mode == "🎯 条件で絞り込む":
            available_ranks = sorted(df["Rank"].dropna().unique().tolist())
            if not available_ranks:
                available_ranks = [1, 2, 3, 4]
            
            st.write("**出題対象の Rank**")
            # 新しいUI (pills) が使えるかチェック
            if hasattr(st, "pills"):
                selected_ranks = st.pills("Rank", options=available_ranks, default=available_ranks, selection_mode="multi", label_visibility="collapsed")
            else:
                cols = st.columns(len(available_ranks))
                selected_ranks = []
                for i, rank in enumerate(available_ranks):
                    if cols[i % len(cols)].checkbox(f"R{rank}", value=True):
                        selected_ranks.append(rank)

            st.write("**出題対象の Mastery**")
            mastery_options = ["A", "B", "C", "D"]
            default_mastery = ["B", "C", "D"]
            if hasattr(st, "pills"):
                selected_masteries = st.pills("Mastery", options=mastery_options, default=default_mastery, selection_mode="multi", label_visibility="collapsed")
            else:
                cols = st.columns(4)
                selected_masteries = []
                for i, m in enumerate(mastery_options):
                    if cols[i].checkbox(m, value=(m in default_mastery)):
                        selected_masteries.append(m)
            
            target_df = df[df["Rank"].isin(selected_ranks) & df["Mastery"].isin(selected_masteries)]
            
        else:
            # 番号（ID）で指定するモード
            min_id = int(df["ID"].min())
            max_id = int(df["ID"].max())
            
            st.write("**IDの範囲を指定**")
            col1, col2 = st.columns(2)
            with col1:
                start_id = st.number_input("開始 ID", min_value=min_id, max_value=max_id, value=min_id)
            with col2:
                end_id = st.number_input("終了 ID", min_value=start_id, max_value=max_id, value=max_id)
                
            target_df = df[(df["ID"] >= start_id) & (df["ID"] <= end_id)]

        st.markdown("---")
        
        if not target_df.empty:
            st.info(f"対象の単語数: **{len(target_df)}** 語")
            num_questions = st.slider("今回の出題数", min_value=1, max_value=len(target_df), value=min(20, len(target_df)))
            
            if st.button("🚀 学習をスタート", use_container_width=True, type="primary"):
                start_learning(target_df, num_questions)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # HTML出力（PDF用）ボタン
            html_string = generate_html_export(target_df)
            st.download_button(
                label="📄 この範囲のリストを保存 (PDF用)",
                data=html_string,
                file_name="flashcards_list.html",
                mime="text/html",
                use_container_width=True
            )
            st.caption("※ダウンロードしたファイルを開き、**「印刷 → PDFに保存」**を選ぶことで綺麗なPDFとして保存できます。")
        else:
            st.warning("条件に合致する単語がありません。")
            
    else:
        st.warning("データが見つかりません。設定を確認してください。")

# --- メインエリア (フラッシュカード) ---
if not st.session_state.is_learning:
    st.title("📚 英単語フラッシュカード")
    
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
        word_data = st.session_state.questions[curr_idx]
        
        st.caption(f"進捗: **{curr_idx + 1} / {total_q}** 問目")
        st.progress((curr_idx) / total_q)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown(
            f"<h1 style='text-align: center; font-size: 3.5rem; word-wrap: break-word;'>{word_data['Word']}</h1>", 
            unsafe_allow_html=True
        )
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if not st.session_state.show_answer:
            if st.button("👀 答えを見る", use_container_width=True, type="primary"):
                st.session_state.show_answer = True
                st.rerun()
        else:
            st.markdown(
                f"<h2 style='text-align: center; font-size: 2.2rem; color: #ff4b4b; word-wrap: break-word;'>{word_data['Meaning']}</h2>", 
                unsafe_allow_html=True
            )
            st.markdown("<hr>", unsafe_allow_html=True)
            st.write("**この単語の定着度はどうでしたか？**")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.button("🟦 A (完璧)", use_container_width=True, on_click=update_mastery, args=(word_data["ID"], "A"))
            with col2:
                st.button("🟩 B (だいたい)", use_container_width=True, on_click=update_mastery, args=(word_data["ID"], "B"))
            with col3:
                st.button("🟨 C (うろ覚え)", use_container_width=True, on_click=update_mastery, args=(word_data["ID"], "C"))
            with col4:
                st.button("🟥 D (ダメ)", use_container_width=True, on_click=update_mastery, args=(word_data["ID"], "D"))
