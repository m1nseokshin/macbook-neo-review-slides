#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
애플 맥북 네오 526건 전수 리뷰 데이터 시각화 차트 생성 스크립트 (Matplotlib)
- 다크 글래스모피즘 테마에 맞춘 애플 프리미엄 스타일 차트 에셋 3종 생성
"""

import os
import json
import csv
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# Set Korean Font & Dark Aesthetics
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

BG_COLOR = '#0f111a'
CARD_BG = '#161926'
TEXT_COLOR = '#f8fafc'
MUTED_COLOR = '#94a3b8'
CITRUS = '#fcd34d'
BLUE = '#38bdf8'
INDIGO = '#818cf8'
PURPLE = '#c084fc'
ROSE = '#fb7185'
GREEN = '#4ade80'

os.makedirs('assets', exist_ok=True)

def load_reviews():
    with open('apple_macbook_neo_reviews.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader)

def create_timeline_chart(reviews):
    """1. 월별 리뷰 등록 추이 및 누적 성장 곡선 (듀얼 축 차트)"""
    dates = []
    for r in reviews:
        d_str = r['작성일자']
        if d_str:
            try:
                dates.append(datetime.strptime(d_str, '%Y.%m.%d'))
            except:
                pass
    dates.sort()

    # Group by month (2026.03 ~ 2026.09)
    month_counts = Counter(d.strftime('%Y-%m') for d in dates)
    sorted_months = sorted(month_counts.keys())
    counts = [month_counts[m] for m in sorted_months]
    cumulative = np.cumsum(counts)

    fig, ax1 = plt.subplots(figsize=(10, 4.5), facecolor=BG_COLOR)
    ax1.set_facecolor(CARD_BG)

    # Bar chart for monthly new reviews
    bars = ax1.bar(sorted_months, counts, color=BLUE, alpha=0.75, width=0.45, label='월별 신규 리뷰 수')
    ax1.set_ylabel('신규 등록 건수 (건)', color=BLUE, fontsize=11, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=BLUE)
    ax1.tick_params(axis='x', labelcolor=TEXT_COLOR, rotation=15)
    ax1.grid(color='#ffffff', alpha=0.08, linestyle='--', linewidth=0.8, axis='y')

    # Add count text on top of bars
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  
                    textcoords="offset points",
                    ha='center', va='bottom', color=TEXT_COLOR, fontsize=10, fontweight='bold')

    # Line chart on secondary axis for cumulative
    ax2 = ax1.twinx()
    ax2.plot(sorted_months, cumulative, color=CITRUS, marker='o', linewidth=3, markersize=8, label='누적 리뷰 추이')
    ax2.set_ylabel('누적 리뷰 수 (건)', color=CITRUS, fontsize=11, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=CITRUS)

    # Title & aesthetics
    plt.title('맥북 네오 월별 리뷰 등록 추이 (2026.03 ~ 2026.09)', color=TEXT_COLOR, fontsize=14, fontweight='bold', pad=15)
    for spine in ax1.spines.values():
        spine.set_color('#ffffff22')
    for spine in ax2.spines.values():
        spine.set_color('#ffffff22')

    plt.tight_layout()
    out_path = 'assets/chart_timeline.png'
    plt.savefig(out_path, dpi=300, facecolor=BG_COLOR)
    plt.close()
    print(f"[*] '{out_path}' 생성 완료")

def create_abuse_radar_chart(reviews):
    """2. 어뷰징/봇 탐지 요인별 진단 히트맵 및 위험도 세부 분석"""
    statuses = Counter(r['어뷰징_봇_의심도'] for r in reviews)
    labels = ['정상 (Genuine)', '주의 (포인트파밍)', '의심 (Bot/매크로)']
    values = [statuses.get(k, 0) for k in ['정상(Genuine)', '주의(Suspicious)', '의심(Bot/Abuse)']]
    colors = [GREEN, CITRUS, ROSE]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), facecolor=BG_COLOR)
    ax1.set_facecolor(CARD_BG)
    ax2.set_facecolor(CARD_BG)

    # Left: Donut Chart
    wedges, texts, autotexts = ax1.pie(values, labels=labels, autopct='%1.1f%%',
                                      startangle=140, colors=colors,
                                      wedgeprops=dict(width=0.4, edgecolor=BG_COLOR, linewidth=2),
                                      textprops=dict(color=TEXT_COLOR, fontsize=10, fontweight='bold'))
    for autotext in autotexts:
        autotext.set_color('#000000')
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')
    ax1.set_title('어뷰징/봇 위험도 분류', color=TEXT_COLOR, fontsize=13, fontweight='bold', pad=10)

    # Right: Text Length vs Risk Distribution
    text_lens = [len(r['리뷰내용']) for r in reviews]
    risk_scores = [int(r['의심점수(0-100)']) for r in reviews]

    scatter = ax2.scatter(text_lens, risk_scores, c=risk_scores, cmap='coolwarm', alpha=0.65, edgecolors='none', s=40)
    ax2.set_xlabel('리뷰 글자 수 (자)', color=MUTED_COLOR, fontsize=10)
    ax2.set_ylabel('위험 점수 (0-100)', color=MUTED_COLOR, fontsize=10)
    ax2.set_title('글자 수 대비 어뷰징 위험도 상관관계', color=TEXT_COLOR, fontsize=13, fontweight='bold', pad=10)
    ax2.tick_params(colors=MUTED_COLOR)
    ax2.grid(color='#ffffff', alpha=0.08, linestyle='--')
    for spine in ax2.spines.values():
        spine.set_color('#ffffff22')

    # Add reference zone
    ax2.axvspan(0, 20, color='red', alpha=0.1, label='초단문 파밍 구간 (<20자)')
    ax2.legend(facecolor=CARD_BG, edgecolor='#ffffff22', labelcolor=TEXT_COLOR, fontsize=9)

    plt.tight_layout()
    out_path = 'assets/chart_abuse_analysis.png'
    plt.savefig(out_path, dpi=300, facecolor=BG_COLOR)
    plt.close()
    print(f"[*] '{out_path}' 생성 완료")

def create_color_storage_cross_chart(reviews):
    """3. 색상과 용량의 크로스 결합 매트릭스 차트"""
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
    bars = ax.barh(y_pos, counts, color=PURPLE, alpha=0.8, height=0.55)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=TEXT_COLOR, fontsize=10, fontweight='bold')
    ax.invert_yaxis()
    ax.set_xlabel('선택 구매자 수 (명)', color=MUTED_COLOR, fontsize=10)
    ax.tick_params(colors=MUTED_COLOR)
    ax.grid(color='#ffffff', alpha=0.08, linestyle='--', axis='x')
    for spine in ax.spines.values():
        spine.set_color('#ffffff22')

    for bar in bars:
        width = bar.get_width()
        ax.annotate(f'{width}명',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0),
                    textcoords="offset points",
                    ha='left', va='center', color=CITRUS, fontsize=10, fontweight='bold')

    plt.title('인기 구매 조합 Top 8 (색상 x 저장용량)', color=TEXT_COLOR, fontsize=14, fontweight='bold', pad=15)
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
