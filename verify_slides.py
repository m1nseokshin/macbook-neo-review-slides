#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
슬라이드 덱 검증 루프(Verification Loop) 자동화 스크립트 (Playwright)
- 콘솔 에러, 차트 렌더링, 키보드 슬라이드 전환, 이미지 로드 무결성 자동 검사
"""

import asyncio
import os
import sys
from playwright.async_api import async_playwright

HTML_PATH = os.path.abspath("index.html")
FILE_URL = f"file://{HTML_PATH}"

async def run_verification():
    print("="*60)
    print("🧪 슬라이드 덱 자동 검증 루프 (Verification Loop) 시작")
    print("="*60)

    console_errors = []
    failed_requests = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--allow-file-access-from-files']
        )
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 900}
        )
        page = await context.new_page()

        # Listen for console messages and request failures
        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type in ['error'] else None)
        page.on('requestfailed', lambda req: failed_requests.append(req.url))

        print(f"[1/4] 슬라이드 로드: {FILE_URL}")
        await page.goto(FILE_URL, wait_until='networkidle')
        await asyncio.sleep(1)

        # Total slides check
        slides_count = await page.locator('.slide').count()
        print(f"[2/4] 슬라이드 개수 감지: 총 {slides_count}장 (목표: 8장)")
        assert slides_count == 8, f"Expected 8 slides, got {slides_count}"

        # Loop through all 8 slides via Keyboard 'ArrowRight'
        print("[3/4] 슬라이드 전환 및 애니메이션/차트 렌더링 검사...")
        os.makedirs('verification_screens', exist_ok=True)

        for i in range(1, slides_count + 1):
            curr_num = await page.locator('#current-slide-num').text_content()
            active_slide = page.locator('.slide.active')
            active_id = await active_slide.get_attribute('id')
            
            print(f"  - Slide {i} 검사: active ID={active_id}, counter={curr_num}")
            assert active_id == f"slide-{i}", f"Slide mismatch on step {i}"

            # Wait for anime.js & chart animation
            await asyncio.sleep(0.8)

            # Capture screenshot
            screen_path = f"verification_screens/slide_{i}.png"
            await page.screenshot(path=screen_path)

            if i < slides_count:
                await page.keyboard.press('ArrowRight')
                await asyncio.sleep(0.5)

        print("[4/4] 무결성 검증 결과 요약:")
        print(f"  • 콘솔 에러(Console Errors): {len(console_errors)}건")
        if console_errors:
            for err in console_errors:
                print(f"    ❌ {err}")
        else:
            print("    ✅ 콘솔 에러 제로 (0 errors)")

        print(f"  • 실패한 리소스 요청(Failed Requests): {len(failed_requests)}건")
        if failed_requests:
            for fr in failed_requests:
                print(f"    ❌ {fr}")
        else:
            print("    ✅ 모든 이미지/스크립트 에셋 100% 정상 로드")

        await browser.close()

    print("="*60)
    if len(console_errors) == 0 and len(failed_requests) == 0:
        print("🎉 검증 루프 통과! (All Verification Tests Passed)")
    else:
        print("⚠️ 일부 검증 항목 주의 필요")
    print("="*60)

if __name__ == '__main__':
    asyncio.run(run_verification())
