#!/usr/bin/env python3
"""Debug script to inspect roadmap.sh page structure."""

from playwright.sync_api import sync_playwright
import time

print("Inspecting roadmap.sh page structure...")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox'
        ]
    )
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ignore_https_errors=True
    )
    page = context.new_page()
    page.set_default_timeout(60000)
    
    print("Navigating to roadmap.sh/engineering-manager...")
    try:
        page.goto("https://roadmap.sh/engineering-manager", wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"Navigation error: {e}")
        print("Trying to continue anyway...")
    
    print("Waiting for page to load...")
    time.sleep(3)
    
    print("\nPage title:", page.title())
    print("URL:", page.url)
    
    # Check for various elements
    print("\n--- Looking for common elements ---")
    
    selectors_to_check = [
        "svg",
        "canvas",
        "[class*='roadmap']",
        "[class*='renderer']",
        "[id*='roadmap']",
        "[data-renderer-id]",
        "main",
        "article",
        "#roadmap-content",
        ".roadmap-container",
    ]
    
    for selector in selectors_to_check:
        try:
            elements = page.query_selector_all(selector)
            if elements:
                print(f"✓ Found {len(elements)} element(s) with selector: {selector}")
        except:
            pass
    
    # Get page HTML structure
    print("\n--- Body class names ---")
    body_classes = page.evaluate("document.body.className")
    print(body_classes)
    
    print("\n--- Main element IDs ---")
    ids = page.evaluate("""
        Array.from(document.querySelectorAll('[id]'))
            .map(el => el.id)
            .slice(0, 20)
    """)
    print(ids)
    
    print("\n--- Saving screenshot for inspection ---")
    try:
        page.screenshot(path="output/debug_screenshot.png", full_page=True)
        print("Screenshot saved to output/debug_screenshot.png")
    except Exception as e:
        print(f"Screenshot error: {e}")
    
    context.close()
    browser.close()
    print("\n✅ Debug complete!")

