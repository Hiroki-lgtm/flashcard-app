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
