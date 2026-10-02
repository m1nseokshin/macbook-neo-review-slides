#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
애플 맥북 네오 526건 전수 리뷰 데이터 시각화 차트 생성 스크립트 (Matplotlib)
- 화이트 톤 + 난색 프라이머리 (#FF5B00) 클린 미니멀 스타일
- 스트로크 최소화, 이모지 배제, 모던 타이포그래피
"""

import os
import json
import csv
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# Set Korean Font & White Clean Aesthetics
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# White & Warm Primary Palette
BG_COLOR = '#ffffff'
CARD_BG = '#ffffff'
TEXT_MAIN = '#111827'
TEXT_MUTED = '#6b7280'
BORDER_COLOR = '#e5e7eb'

# Warm Primary (난색 계열)
PRIMARY_WARM = '#ff5b00'       # Deep Warm Coral Orange
PRIMARY_WARM_LIGHT = '#ff8a3d'
WARM_SUBTLE = '#fff7ed'
ACCENT_GRAY = '#9ca3af'
SOFT_GRAY = '#e5e7eb'

os.makedirs('assets', exist_ok=True)

def load_reviews():
    with open('apple_macbook_neo_reviews.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)

def create_timeline_chart(reviews):
    """1. 월별 리뷰 등록 추이 및 누적 성장 곡선 (화이트 톤)"""
    dates = []
    for r in reviews:
        d_str = r['작성일자']
        if d_str:
            try:
                dates.append(datetime.strptime(d_str, '%Y.%m.%d'))
            except:
                pass
    dates.sort()

    month_counts = Counter(d.strftime('%Y-%m') for d in dates)
    sorted_months = sorted(month_counts.keys())
    counts = [month_counts[m] for m in sorted_months]
    cumulative = np.cumsum(counts)

    fig, ax1 = plt.subplots(figsize=(10, 4.5), facecolor=BG_COLOR)
    ax1.set_facecolor(CARD_BG)

    # Bar chart (Soft Warm Tone)
    bars = ax1.bar(sorted_months, counts, color='#fed7aa', edgecolor='none', width=0.45, label='월별 신규 리뷰 수')
    ax1.set_ylabel('신규 등록 건수 (건)', color=TEXT_MUTED, fontsize=10, fontweight='medium')
    ax1.tick_params(axis='y', labelcolor=TEXT_MUTED)
    ax1.tick_params(axis='x', labelcolor=TEXT_MAIN, rotation=0)
    ax1.grid(color='#f1f5f9', linestyle='-', linewidth=1, axis='y')

    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha='center', va='bottom', color=TEXT_MAIN, fontsize=10, fontweight='bold')

    # Line chart on secondary axis for cumulative (Primary Warm)
    ax2 = ax1.twinx()
    ax2.plot(sorted_months, cumulative, color=PRIMARY_WARM, marker='o', linewidth=2.5, markersize=7, label='누적 리뷰 추이')
    ax2.set_ylabel('누적 리뷰 수 (건)', color=PRIMARY_WARM, fontsize=10, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=PRIMARY_WARM)

    # Remove all spines (No strokes)
    for spine in ax1.spines.values():
        spine.set_visible(False)
    for spine in ax2.spines.values():
        spine.set_visible(False)

    plt.title('맥북 네오 월별 리뷰 등록 및 누적 성장 추이 (2026.03 ~ 2026.09)', color=TEXT_MAIN, fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    out_path = 'assets/chart_timeline.png'
    plt.savefig(out_path, dpi=300, facecolor=BG_COLOR)
    plt.close()
    print(f"[*] '{out_path}' 생성 완료")

def create_abuse_radar_chart(reviews):
    """2. 어뷰징/봇 탐지 요인별 진단 및 위험도 분석 (화이트 톤)"""
    statuses = Counter(r['어뷰징_봇_의심도'] for r in reviews)
    labels = ['정상 (Genuine)', '주의 (단문 파밍)', '의심 (Bot/매크로)']
    values = [statuses.get(k, 0) for k in ['정상(Genuine)', '주의(Suspicious)', '의심(Bot/Abuse)']]
    colors = ['#10b981', '#f59e0b', PRIMARY_WARM]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), facecolor=BG_COLOR)
    ax1.set_facecolor(CARD_BG)
    ax2.set_facecolor(CARD_BG)

    # Left: Donut Chart
    wedges, texts, autotexts = ax1.pie(values, labels=labels, autopct='%1.1f%%',
                                      startangle=140, colors=colors,
                                      wedgeprops=dict(width=0.38, edgecolor=BG_COLOR, linewidth=3),
                                      textprops=dict(color=TEXT_MAIN, fontsize=10, fontweight='bold'))
    for autotext in autotexts:
        autotext.set_color('#ffffff')
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')
    ax1.set_title('어뷰징 및 봇 탐지 비율', color=TEXT_MAIN, fontsize=12, fontweight='bold', pad=10)

    # Right: Text Length vs Risk Distribution
    text_lens = [len(r['리뷰내용']) for r in reviews]
    risk_scores = [int(r['의심점수(0-100)']) for r in reviews]

    scatter = ax2.scatter(text_lens, risk_scores, c=risk_scores, cmap='Oranges', alpha=0.7, edgecolors='none', s=45)
    ax2.set_xlabel('리뷰 글자 수 (자)', color=TEXT_MUTED, fontsize=10)
    ax2.set_ylabel('위험 점수 (0-100)', color=TEXT_MUTED, fontsize=10)
    ax2.set_title('글자 수 대비 어뷰징 위험도 분포', color=TEXT_MAIN, fontsize=12, fontweight='bold', pad=10)
    ax2.tick_params(colors=TEXT_MUTED)
    ax2.grid(color='#f1f5f9', linestyle='-', linewidth=1)
    
    # Remove all spines
    for spine in ax1.spines.values():
        spine.set_visible(False)
    for spine in ax2.spines.values():
        spine.set_visible(False)

    ax2.axvspan(0, 20, color='#fee2e2', alpha=0.5, label='초단문 구간 (<20자)')
    ax2.legend(facecolor=BG_COLOR, edgecolor='none', labelcolor=TEXT_MAIN, fontsize=9)

    plt.tight_layout()
    out_path = 'assets/chart_abuse_analysis.png'
    plt.savefig(out_path, dpi=300, facecolor=BG_COLOR)
    plt.close()
    print(f"[*] '{out_path}' 생성 완료")

def create_color_storage_cross_chart(reviews):
    """3. 색상과 용량의 크로스 결합 매트릭스 차트 (화이트 톤)"""
    combos = Counter()
    for r in reviews:
        col = r['구매옵션_색상']
        st = r['구매옵션_저장용량']
        if col != '-' and st != '-':
            combos[f"{col} + {st}"] += 1

    top_combos = combos.most_common(8)
    labels = [k for k, v in top_combos]
    counts = [v for k, v in top_combos]

    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor=BG_COLOR)
    ax.set_facecolor(CARD_BG)

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, counts, color=PRIMARY_WARM_LIGHT, alpha=0.85, height=0.55, edgecolor='none')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=TEXT_MAIN, fontsize=10, fontweight='medium')
    ax.invert_yaxis()
    ax.set_xlabel('선택 구매자 수 (명)', color=TEXT_MUTED, fontsize=10)
    ax.tick_params(colors=TEXT_MUTED)
    ax.grid(color='#f1f5f9', linestyle='-', linewidth=1, axis='x')

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    for bar in bars:
        width = bar.get_width()
        ax.annotate(f'{width}명',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(6, 0),
                    textcoords="offset points",
                    ha='left', va='center', color=PRIMARY_WARM, fontsize=10, fontweight='bold')

    plt.title('인기 구매 옵션 조합 Top 8 (색상 x 저장용량)', color=TEXT_MAIN, fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()
    out_path = 'assets/chart_combos.png'
    plt.savefig(out_path, dpi=300, facecolor=BG_COLOR)
    plt.close()
    print(f"[*] '{out_path}' 생성 완료")

if __name__ == '__main__':
    revs = load_reviews()
    create_timeline_chart(revs)
    create_abuse_radar_chart(revs)
    create_color_storage_cross_chart(revs)
