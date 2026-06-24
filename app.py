import streamlit as st
import pandas as pd
import random
import os
import threading

# --- 設定 ---
st.set_page_config(page_title="Flashcards", page_icon="📚", layout="centered")

# --- 全体UIのCSSポリッシュ ---
st.markdown("""
<style>
/* --- プレミアムな背景アニメーションとグラスモーフィズム --- */
[data-testid="stAppViewContainer"] {
    /* 視認性を高めるため、クリーンでクールなシルバー系・アイスブルー系の背景グラデーション */
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
    /* 文字が見えやすいように少し白を強めに */
    background: rgba(255, 255, 255, 0.75) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-radius: 24px !important;
    padding: 2rem !important;
    /* ヘッダーとの被りを防ぐため上部マージンを確保 */
    margin: 5rem auto 2rem auto !important;
    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.8) !important;
    max-width: 90% !important;
}

@media (max-width: 768px) {
    [data-testid="stMainBlockContainer"] {
        padding: 1.5rem 1rem !important;
        /* スマホでも上部の被りを防ぐ */
        margin: 4rem auto 1rem auto !important;
        border-radius: 16px !important;
        max-width: 95% !important;
    }
}

/* ヘッダー全体（サイドバー展開ボタンやGitHubアイコンがある行）を透明ですりガラス風に戻す */
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

/* ヘッダー内のアイコン類の色をダークグレーにする（白背景で見えるように） */
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

/* プライマリボタン（スタート、できた等）のグラデーションとホバー時の浮き上がり */
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

/* セカンダリボタン（もう一度、前に戻る等）のホバーエフェクト */
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
    background-color: #cbd5e1 !important; /* 未完了部分をはっきりしたグレーに */
    border-radius: 10px !important;
}
.stProgress > div > div > div {
    border-radius: 10px !important;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6) !important; /* 濃い青〜紫のグラデーションでコントラスト強化 */
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
            // 左端(40px以内)から50px以上右へスワイプした場合
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

CSV_FILE = "words.csv"

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
    
    # 今回の学習での結果を記録
    if st.session_state.current_idx < len(st.session_state.questions):
        st.session_state.questions[st.session_state.current_idx]["session_result"] = action
    
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
                    <th class="left-side">問題</th>
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
        if "rank_selector" not in st.session_state:
            st.session_state.rank_selector = available_ranks
            
        if hasattr(st, "pills"):
            selected_ranks = st.pills("Rank", options=available_ranks, selection_mode="multi", label_visibility="collapsed", key="rank_selector", on_change=update_id_range)
        else:
            selected_ranks = st.multiselect("Rank", options=available_ranks, label_visibility="collapsed", key="rank_selector", on_change=update_id_range)

        st.write("**IDの範囲を指定**")
        col1, col2 = st.columns(2)
        with col1:
            start_id = st.number_input("開始 ID", min_value=min_id, max_value=max_id, key="start_id")
        with col2:
            end_id = st.number_input("終了 ID", min_value=min_id, max_value=max_id, key="end_id")

        st.write("**出題対象の Mastery**")
        mastery_options = ["A", "B", "C", "D"]
        if "mastery_selector" not in st.session_state:
            st.session_state.mastery_selector = ["B", "C", "D"]
            
        if hasattr(st, "pills"):
            selected_masteries = st.pills("Mastery", options=mastery_options, selection_mode="multi", label_visibility="collapsed", key="mastery_selector")
        else:
            selected_masteries = st.multiselect("Mastery", options=mastery_options, label_visibility="collapsed", key="mastery_selector")
        
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
                st.session_state.num_q = min(20, max_q)
                
            def dec_q():
                st.session_state.num_q = max(1, st.session_state.num_q - 10)
            def inc_q():
                st.session_state.num_q = min(max_q, st.session_state.num_q + 10)
                
            st.write("**今回の出題数**")
            col_q1, col_q2, col_q3 = st.columns([1, 2, 1])
            with col_q1:
                st.button("<<", on_click=dec_q, use_container_width=True)
            with col_q2:
                num_questions = st.number_input("出題数", min_value=1, max_value=max_q, key="num_q", label_visibility="collapsed")
            with col_q3:
                st.button(">>", on_click=inc_q, use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
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
            
        else:
            st.warning("条件に合致する単語がありません。")
            
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
            # Pandasのスタイルを使って表示を調整
            df_res = pd.DataFrame(results_data)
            st.dataframe(
                df_res,
                use_container_width=True,
                hide_index=True
            )
            
        st.markdown("<br>", unsafe_allow_html=True)
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
        </style>
        """
        
        # 単語が途中で改行されないよう、フォントサイズを動的調整しつつ word-break を keep-all に
        # ReactによるDOM要素の再利用を防ぎ、毎回アニメーションと裏返り状態をリセットするためにタグを切り替える
        container_tag = "div" if curr_idx % 2 == 0 else "section"
        
        # 発音記号が存在する場合のみ表示用のHTMLを生成する
        pronunciation = str(word_data.get('Pronunciation', ''))
        pronunciation_html = ""
        if pronunciation and pronunciation.lower() != 'nan':
            # Markdownのコードブロックと誤認識されないよう、余分なスペースや改行を入れない
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
        
        # 音声発音用のJSを親フレームに注入
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
                    // 機械音声特有の不自然さや、速度変更による歪み（気持ち悪さ）を完全に排除するため、
                    // 人間の肉声が録音された高品質な辞書音声API（アメリカ英語）を利用してMP3を再生する
                    var text = encodeURIComponent({word_js});
                    var url = "https://dict.youdao.com/dictvoice?audio=" + text + "&type=2";
                    var audio = new Audio(url);
                    audio.play().catch(function(e) {{
                        // 万が一ネットワーク等の理由で再生できなかった場合のフォールバック（自然な標準速度）
                        var msg = new SpeechSynthesisUtterance({word_js});
                        msg.lang = 'en-US';
                        msg.rate = 1.0;
                        window.speechSynthesis.speak(msg);
                    }});
                }};
            }}
            
            // スマホでのページ拡大縮小（ズーム）を禁止
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
