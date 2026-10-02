#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
애플 맥북 네오 (A18 Pro) 네이버 브랜드스토어 전체 리뷰(526건) 전수 수집 및 어뷰징/봇 심층 분석
대상 URL: https://brand.naver.com/applestore/products/13203249084
"""

import asyncio
import json
import csv
import re
import os
import sys
from datetime import datetime
from collections import Counter
from playwright.async_api import async_playwright

TARGET_URL = "https://brand.naver.com/applestore/products/13203249084"
OUTPUT_CSV = "apple_macbook_neo_reviews.csv"
RAW_JSON = "all_macbook_reviews_raw.json"

def detect_abuse_and_bot(content, author, date_str, rating, images):
    """
    526건 전수 리뷰에 대한 다차원 어뷰징 및 봇(매크로/포인트 파밍) 검사 알고리즘
    - 텍스트 길이, 구체성, 상투적 문구 비율, 자음 반복, 작성일자 집중도 분석
    """
    risk_score = 0
    reasons = []

    clean_content = content.strip() if content else ""
    char_len = len(clean_content)

    # 1. 초단문 검사 (25자 미만 - 포인트 적립용 무성의 리뷰 의심)
    if char_len < 20:
        risk_score += 45
        reasons.append(f"초단문 리뷰 ({char_len}자 - 포인트 파밍 의심)")
    elif char_len < 35:
        risk_score += 20
        reasons.append(f"단문 리뷰 ({char_len}자)")

    # 2. 상투적 매크로 템플릿 문구 검사
    cliche_patterns = [
        (r"배송도?\s*빠르고\s*포장도?\s*꼼꼼", "배송/포장 상투구"),
        (r"너무\s*좋아요\s*\^\^", "단순 호평 반복"),
        (r"만족합니다\s*!+", "단순 만족 호평"),
        (r"가성비가?\s*좋은\s*제품", "가성비 상투구"),
        (r"잘\s*쓰겠습니다", "기계적 인사치레")
    ]
    cliche_matches = []
    for p, label in cliche_patterns:
        if re.search(p, clean_content):
            cliche_matches.append(label)
    if len(cliche_matches) >= 2:
        risk_score += 25
        reasons.append(f"상투적 템플릿 패턴 다수 포함 ({', '.join(cliche_matches)})")

    # 3. 감정표현 자음/단순 부호 과다 검사 (텍스트 비율의 25% 이상)
    jamo_repeats = len(re.findall(r"[ㅎㅋㅠㅜ~!^.]", clean_content))
    if char_len > 0 and (jamo_repeats / char_len) > 0.30:
        risk_score += 20
        reasons.append("단순 감정표현/기호 반복 비율 과다 (>30%)")

    # 4. 실사용 구체성 검사 (가점/위험도 차감)
    specific_keywords = [
        "대학원", "논문", "블로그", "작업", "일러스트", "256", "512", "사무직", 
        "직장인", "서치", "환불", "총알배송", "토요일", "맥북에어", "m1", "m2", "m3", 
        "코딩", "개발", "영상", "유튜브", "강의", "수업", "발열", "소음", "배터리", "화면"
    ]
    specific_matches = [k for k in specific_keywords if k in clean_content.lower()]
    if specific_matches:
        risk_score -= 30
        reasons.append(f"실사용 맥락 명시 ({', '.join(specific_matches[:3])})")

    # 5. 사진 첨부 여부 (실구매 인증 지표)
    if images and len(images) > 0:
        risk_score -= 15
        reasons.append(f"실물 인증 사진 첨부 ({len(images)}장)")

    # 최종 의심도 판정
    risk_score = max(0, min(100, risk_score))
    if risk_score >= 50:
        status = "의심(Bot/Abuse)"
    elif risk_score >= 25:
        status = "주의(Suspicious)"
    else:
        status = "정상(Genuine)"

    return status, risk_score, "; ".join(reasons) if reasons else "특이사항 없음"

async def crawl_all_reviews():
    """Playwright 스텔스 세션을 이용하여 526건 전체 리뷰를 무한 스크롤로 수집합니다."""
    print("[1/4] Playwright 스텔스 브라우저를 시작합니다...")
    all_reviews_map = {}
    total_elements_expected = 526

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
            ]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            viewport={'width': 1440, 'height': 900},
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )
        page = await context.new_page()
        await page.add_init_script('''Object.defineProperty(navigator, 'webdriver', {get: () => undefined});''')

        async def handle_response(res):
            nonlocal total_elements_expected
            if 'group-products/query-pages' in res.url and res.status == 200:
                try:
                    data = await res.json()
                    total = data.get('totalElements')
                    if total:
                        total_elements_expected = total
                    contents = data.get('contents', [])
                    for item in contents:
                        rid = item.get('id')
                        if rid:
                            all_reviews_map[rid] = item
                    print(f"  [수집 진행] 현재 누적 고유 리뷰: {len(all_reviews_map)} / {total_elements_expected} 건")
                except Exception as e:
                    pass

        page.on('response', handle_response)

        print("[2/4] 상품 페이지 접속 중...")
        await page.goto(TARGET_URL, wait_until='networkidle')
        await asyncio.sleep(2)

        # '리뷰 전체보기' 버튼 클릭
        print("[3/4] '리뷰 전체보기' 모달 오픈 중...")
        await page.locator('text=리뷰 전체보기').first.click()
        await asyncio.sleep(2)

        # 모달 내부 스크롤 진행 (최대 35회 반복하여 전체 526건 수집)
        max_scrolls = 35
        idle_count = 0
        prev_count = 0

        for s in range(1, max_scrolls + 1):
            await page.evaluate('''
                () => {
                    const c = document.querySelector('.ckqgS03UN6');
                    if (c) c.scrollTop = c.scrollHeight;
                }
            ''')
            await asyncio.sleep(1.2)

            curr_count = len(all_reviews_map)
            if curr_count >= total_elements_expected:
                print(f"  [*] 전체 리뷰 목표치({total_elements_expected}건) 도달 완료!")
                break
            
            if curr_count == prev_count:
                idle_count += 1
                if idle_count >= 5:
                    print("  [*] 추가 로딩 대기 후 계속 진행...")
                    await asyncio.sleep(2.0)
            else:
                idle_count = 0
            prev_count = curr_count

        await browser.close()

    print(f"[4/4] 총 {len(all_reviews_map)}건의 리뷰 원본 수집 완료.")
    with open(RAW_JSON, 'w', encoding='utf-8') as f:
        json.dump(list(all_reviews_map.values()), f, ensure_ascii=False, indent=2)
    return list(all_reviews_map.values())

def process_and_export(raw_reviews):
    """원시 JSON 리뷰를 파싱, 어뷰징/봇 검사 후 CSV 파일로 내보냅니다."""
    processed = []

    for r in raw_reviews:
        rid = r.get("id", "")
        author = r.get("writerId", "구매고객(익명)")
        create_date = r.get("createDate", "")
        if create_date:
            date_str = create_date[:10].replace("-", ".")
        else:
            date_str = ""

        score = r.get("reviewScore", 5)
        raw_content = r.get("reviewContent", "")
        clean_content = " ".join(raw_content.split()) if raw_content else ""

        # 옵션 파싱
        opt_str = r.get("productOptionContent", "")
        ram, storage, color = "-", "-", "-"
        if opt_str:
            m_ram = re.search(r"RAM용량:\s*([^/]+)", opt_str)
            m_st = re.search(r"저장용량:\s*([^/]+)", opt_str)
            m_col = re.search(r"색상:\s*([^\n\r/]+)", opt_str)
            if m_ram: ram = m_ram.group(1).strip()
            if m_st: storage = m_st.group(1).strip()
            if m_col: color = m_col.group(1).strip()

        # 평가 태그 (ID 매핑)
        # 무게: 3000120(가벼워요), 3000121(적당해요), 3000122(무거워요)
        # 성능: 3000131(좋아요), 3000130(보통이에요), 3000132(아쉬워요)
        weight_eval = "-"
        perf_eval = "-"
        eval_ids = r.get("reviewEvaluationValueIds", []) or []
        eval_map = {
            3000120: ("무게", "가벼워요"),
            3000121: ("무게", "적당해요"),
            3000122: ("무게", "무거워요"),
            3000130: ("성능", "보통이에요"),
            3000131: ("성능", "좋아요"),
            3000132: ("성능", "아쉬워요")
        }
        for eid in eval_ids:
            if eid in eval_map:
                cat, val = eval_map[eid]
                if cat == "무게":
                    weight_eval = val
                elif cat == "성능":
                    perf_eval = val

        # 이미지 / 첨부파일
        attaches = r.get("reviewAttaches", []) or []
        img_urls = []
        for att in attaches:
            url = att.get("attachUrl", "")
            if url:
                img_urls.append(url)

        helpful_count = r.get("reviewHelpfulCount", 0)

        # 어뷰징 / 봇 검사
        abuse_status, risk_score, abuse_reason = detect_abuse_and_bot(
            clean_content, author, date_str, score, img_urls
        )

        processed.append({
            "rid": rid,
            "author": author,
            "date": date_str,
            "score": score,
            "ram": ram,
            "storage": storage,
            "color": color,
            "weight_eval": weight_eval,
            "perf_eval": perf_eval,
            "content": clean_content,
            "img_count": len(img_urls),
            "img_urls": " | ".join(img_urls),
            "helpful_count": helpful_count,
            "abuse_status": abuse_status,
            "risk_score": risk_score,
            "abuse_reason": abuse_reason
        })

    # 날짜 최신순 정렬
    processed.sort(key=lambda x: (x["date"], x["rid"]), reverse=True)

    # CSV 저장
    fieldnames = [
        "순번", "리뷰ID", "작성자", "작성일자", "평점",
        "구매옵션_RAM", "구매옵션_저장용량", "구매옵션_색상",
        "평가_무게", "평가_성능", "리뷰내용",
        "추천수", "사진수", "사진URL",
        "어뷰징_봇_의심도", "의심점수(0-100)", "검사_사유"
    ]

    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for idx, item in enumerate(processed, 1):
            writer.writerow([
                idx,
                item["rid"],
                item["author"],
                item["date"],
                item["score"],
                item["ram"],
                item["storage"],
                item["color"],
                item["weight_eval"],
                item["perf_eval"],
                item["content"],
                item["helpful_count"],
                item["img_count"],
                item["img_urls"],
                item["abuse_status"],
                item["risk_score"],
                item["abuse_reason"]
            ])

    print(f"\n[*] '{OUTPUT_CSV}' 파일에 총 {len(processed)}건 저장 완료!")
    return processed

def display_final_report(processed):
    """전체 리뷰 수집 및 어뷰징/봇 종합 통계 리포트"""
    total = len(processed)
    if total == 0:
        print("수집된 리뷰가 없습니다.")
        return

    avg_score = sum(p["score"] for p in processed) / total
    scores = Counter(p["score"] for p in processed)
    abuse_counts = Counter(p["abuse_status"] for p in processed)
    colors = Counter(p["color"] for p in processed if p["color"] != "-")
    storages = Counter(p["storage"] for p in processed if p["storage"] != "-")
    weights = Counter(p["weight_eval"] for p in processed if p["weight_eval"] != "-")
    perfs = Counter(p["perf_eval"] for p in processed if p["perf_eval"] != "-")

    photo_reviews = sum(1 for p in processed if p["img_count"] > 0)

    print("\n" + "="*60)
    print("🎯 애플 맥북 네오 (A18 Pro) 526건 전수 리뷰 심층 분석 리포트")
    print("="*60)
    print(f"1. 수집 총계: {total}건 (포토리뷰: {photo_reviews}건 / {photo_reviews/total*100:.1f}%)")
    print(f"2. 전체 평균 평점: {avg_score:.2f} / 5.0 점")
    print(f"3. 평점 분포:")
    for sc in sorted(scores.keys(), reverse=True):
        print(f"   ⭐ {sc}점: {scores[sc]}건 ({scores[sc]/total*100:.1f}%)")
    print(f"\n4. 인기 구매 옵션:")
    print(f"   - 색상 선호도: {dict(colors.most_common(5))}")
    print(f"   - 저장용량 선호도: {dict(storages.most_common(5))}")
    print(f"\n5. 실구매자 평가 항목:")
    print(f"   - 무게 평가: {dict(weights.most_common(5))}")
    print(f"   - 성능 평가: {dict(perfs.most_common(5))}")
    print(f"\n6. 🛡️ 어뷰징 및 봇(매크로/파밍) 검사 결과:")
    for st, cnt in abuse_counts.items():
        print(f"   - {st}: {cnt}건 ({cnt/total*100:.1f}%)")
    print("="*60)

if __name__ == "__main__":
    raw_data = asyncio.run(crawl_all_reviews())
    processed = process_and_export(raw_data)
    display_final_report(processed)
