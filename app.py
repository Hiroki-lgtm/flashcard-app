import streamlit as st
import pandas as pd
import random
import os
import threading

# --- 設定 ---
st.set_page_config(page_title="Flashcards", page_icon="📚", layout="centered")

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
    st.session_state.last_action = "start"
    st.session_state.close_sidebar = False

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

# --- バックグラウンド保存関数 ---
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
                # 定着度を1段階上げる（D->C, C->B, B->A, A->A）
                new_mastery = mastery_levels[current_idx + 1]
    # action == "keep" の場合はそのまま
    
    idx = df[df["ID"] == word_id].index
    if not idx.empty:
        df.loc[idx, "Mastery"] = new_mastery
        st.session_state.df = df
        
        # バックグラウンドで非同期に保存処理を実行（UIをブロックしないため）
        threading.Thread(target=save_data_bg, args=(df.copy(),)).start()
    
    st.session_state.current_idx += 1
    st.session_state.show_answer = False
    st.session_state.last_action = action

def generate_html_export(target_df, num_questions):
    export_df = target_df.sample(frac=1).head(num_questions)
    
    # PDF出力用のHTML文字列を生成
    html_content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>単語テスト</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; table-layout: fixed; }
            th, td { padding: 15px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f2f2f2; }
            .left-side { width: 50%; border-right: 2px dashed #000; }
            .right-side { width: 50%; padding-left: 20px; }
            .word { font-size: 1.2em; font-weight: bold; display: inline-block; width: 45%; }
            .answer-box { display: inline-block; width: 50%; border-bottom: 1px solid #333; height: 1.5em; vertical-align: bottom; }
            @media print {
                .no-print { display: none; }
                table { page-break-inside: auto; }
                tr { page-break-inside: avoid; page-break-after: auto; }
            }
        </style>
    </head>
    <body>
        <div class="no-print" style="margin-bottom: 20px; padding: 15px; background-color: #e7f3fe; border-left: 6px solid #2196F3;">
            <strong>💡 このページをPDFとして保存する方法：</strong><br>
            下のボタンを押すと印刷画面が開きます。送信先（プリンター）を「PDFに保存」に変更して「保存」を押してください。<br>
            <button onclick="window.print()" style="margin-top: 15px; padding: 10px 20px; cursor: pointer; background-color: #4CAF50; color: white; border: none; border-radius: 5px; font-weight: bold;">🖨️ PDF保存 / 印刷画面を開く</button>
        </div>
        <h2>📚 単語テスト (""" + str(num_questions) + """問)</h2>
        <table>
            <thead>
                <tr>
                    <th class="left-side">問題 (ここを谷折り 👉)</th>
                    <th class="right-side">答え</th>
                </tr>
            </thead>
            <tbody>
    """
    for _, row in export_df.iterrows():
        html_content += f"""
                <tr>
                    <td class="left-side">
                        <span class="word"><small style="color: #777; font-size: 0.75em; margin-right: 8px;">[{row['ID']}]</small>{row['Word']}</span>
                        <span class="answer-box"></span>
                    </td>
                    <td class="right-side">
                        {row['Meaning']}
                    </td>
                </tr>"""
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    return html_content

# --- サイドバー (設定エリア) ---
with st.sidebar:
    st.header("⚙️ 学習設定")
    
    if df is not None:
        min_id = int(df["ID"].min())
        max_id = int(df["ID"].max())
        
        if "start_id" not in st.session_state:
            st.session_state.start_id = min_id
        if "end_id" not in st.session_state:
            st.session_state.end_id = max_id
            
        def update_id_range():
            selected = st.session_state.get("rank_selector", [])
            if selected:
                rank_df = df[df["Rank"].isin(selected)]
                if not rank_df.empty:
                    st.session_state.start_id = int(rank_df["ID"].min())
                    st.session_state.end_id = int(rank_df["ID"].max())

        available_ranks = sorted(df["Rank"].dropna().unique().tolist())
        if not available_ranks:
            available_ranks = [1, 2, 3, 4]
            
        st.write("**出題対象の Rank**")
        if hasattr(st, "pills"):
            selected_ranks = st.pills("Rank", options=available_ranks, default=available_ranks, selection_mode="multi", label_visibility="collapsed", key="rank_selector", on_change=update_id_range)
        else:
            selected_ranks = st.multiselect("Rank", options=available_ranks, default=available_ranks, label_visibility="collapsed", key="rank_selector", on_change=update_id_range)

        st.write("**IDの範囲を指定**")
        col1, col2 = st.columns(2)
        with col1:
            start_id = st.number_input("開始 ID", min_value=min_id, max_value=max_id, key="start_id")
        with col2:
            end_id = st.number_input("終了 ID", min_value=min_id, max_value=max_id, key="end_id")

        st.write("**出題対象の Mastery**")
        mastery_options = ["A", "B", "C", "D"]
        default_mastery = ["B", "C", "D"]
        if hasattr(st, "pills"):
            selected_masteries = st.pills("Mastery", options=mastery_options, default=default_mastery, selection_mode="multi", label_visibility="collapsed")
        else:
            selected_masteries = st.multiselect("Mastery", options=mastery_options, default=default_mastery, label_visibility="collapsed")
        
        st.markdown("---")
        
        target_df = df[
            (df["ID"] >= min(start_id, end_id)) & 
            (df["ID"] <= max(start_id, end_id)) & 
            (df["Rank"].isin(selected_ranks)) & 
            (df["Mastery"].isin(selected_masteries))
        ]
        
        if not target_df.empty:
            st.info(f"対象の単語数: **{len(target_df)}** 語")
            max_q = min(200, len(target_df))
            num_questions = st.number_input("今回の出題数 (最大200)", min_value=1, max_value=max_q, value=min(20, max_q))
            
            if st.button("🚀 学習をスタート", use_container_width=True, type="primary"):
                start_learning(target_df, num_questions)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # HTML出力（PDF用）ボタン
            html_string = generate_html_export(target_df, num_questions)
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
        
        mastered = count_A + count_B
        progress_pct = int((mastered / total_words) * 100) if total_words > 0 else 0
        
        st.markdown("### 📊 現在の学習ダッシュボード")
        
        st.markdown(f"**マスター率 (A + B): <span style='color: #4CAF50; font-size: 1.2rem;'>{progress_pct}%</span>**", unsafe_allow_html=True)
        st.progress(progress_pct / 100.0)
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🟦 A (完璧)", f"{count_A} 語")
        col2.metric("🟩 B (だいたい)", f"{count_B} 語")
        col3.metric("🟨 C (うろ覚え)", f"{count_C} 語")
        col4.metric("🟥 D (ダメ)", f"{count_D} 語")
        
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
        st.success("学習完了！")
        st.balloons()
        if st.button("🔄 設定し直して再スタート", use_container_width=True, type="primary"):
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
        
        # ポップな単語カードデザイン (タップで裏返るCSSアニメーション)
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
        .flip-instruction {{
            font-size: 0.9rem;
            color: #888;
            text-align: center;
            margin-top: 10px;
            display: block;
        }}
        </style>
        """
        
        # 単語が途中で改行されないよう、フォントサイズを動的調整しつつ word-break を keep-all に
        card_html = f"""
        {css}
        <div class="flip-card-container">
            <label style="display:block; width:100%; height:100%; margin:0;">
                <input type="checkbox" class="flip-toggle" id="flip_{curr_idx}">
                <div class="flip-card-inner">
                    <div class="flip-card-front">
                        <h1 style='font-size: clamp(2rem, 8vw, 4rem); margin: 0; word-break: keep-all; overflow-wrap: normal; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); padding: 0 20px;'>{word_data['Word']}</h1>
                    </div>
                    <div class="flip-card-back">
                        <h2 style='font-size: clamp(1.5rem, 6vw, 2.5rem); margin: 0; word-break: keep-all; overflow-wrap: normal; padding: 0 20px;'>{word_data['Meaning']}</h2>
                    </div>
                </div>
            </label>
        </div>
        <span class="flip-instruction">タップして裏返す</span>
        <!-- 強制的にチェックボックスを外すハック -->
        <img src="data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==" onload="var cb=document.getElementById('flip_{curr_idx}'); if(cb) cb.checked=false;" style="display:none;">
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("👈 もう一度", use_container_width=True, on_click=update_mastery, args=(word_data["ID"], "keep", word_data["Mastery"]))
        with col2:
            st.button("できた 👉", use_container_width=True, type="primary", on_click=update_mastery, args=(word_data["ID"], "up", word_data["Mastery"]))
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("↩️ 前に戻る", use_container_width=True, on_click=go_back, disabled=(curr_idx == 0))
