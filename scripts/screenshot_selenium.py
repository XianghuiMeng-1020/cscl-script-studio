#!/usr/bin/env python3
"""Screenshot script using Selenium"""
import os
import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5001')
OUTPUT_DIR = Path(__file__).parent.parent / 'outputs' / 'ui'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def take_screenshot(driver, url, filename):
    """Take a screenshot of a URL"""
    print(f"Taking screenshot: {filename}...")
    try:
        driver.get(url)
        # Wait for page to load
        time.sleep(3)
        
        filepath = OUTPUT_DIR / filename
        driver.save_screenshot(str(filepath))
        
        size = filepath.stat().st_size
        print(f"✓ {filename} ({size / 1024:.2f} KB)")
        return {'filepath': str(filepath), 'size': size, 'success': True, 'url': url}
    except Exception as e:
        print(f"✗ Failed to screenshot {filename}: {e}")
        return {'filepath': None, 'size': 0, 'success': False, 'url': url}

def main():
    print('Starting screenshot capture with Selenium...')
    print(f"Base URL: {BASE_URL}")
    print(f"Output directory: {OUTPUT_DIR}\n")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Failed to start Chrome: {e}")
        print("Trying with system Chrome...")
        # Try to use system Chrome
        chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e2:
            print(f"Failed to start system Chrome: {e2}")
            print("Please install ChromeDriver or ensure Chrome is available")
            return []
    
    screenshots = [
        {'url': f'{BASE_URL}/', 'filename': 'home_cscl.png', 'name': 'Home Page'},
        {'url': f'{BASE_URL}/teacher', 'filename': 'teacher_dashboard_cscl.png', 'name': 'Teacher Dashboard'},
        {'url': f'{BASE_URL}/student', 'filename': 'student_dashboard_cscl.png', 'name': 'Student Dashboard'},
        {'url': f'{BASE_URL}/teacher', 'filename': 'teacher_pipeline_run_cscl.png', 'name': 'Teacher Pipeline Run'},
        {'url': f'{BASE_URL}/teacher', 'filename': 'teacher_quality_report_cscl.png', 'name': 'Teacher Quality Report'},
        {'url': f'{BASE_URL}/student', 'filename': 'student_current_session_cscl.png', 'name': 'Student Current Session'},
    ]
    
    results = []
    for shot in screenshots:
        result = take_screenshot(driver, shot['url'], shot['filename'])
        results.append({
            'name': shot['name'],
            'filename': shot['filename'],
            **result
        })
    
    driver.quit()
    
    print('\n=== Screenshot Summary ===')
    for r in results:
        status = '✓' if r['success'] else '✗'
        size_info = f" ({r['size'] / 1024:.2f} KB)" if r['success'] else ' (failed)'
        print(f"{status} {r['name']}: {r['filename']}{size_info}")
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n{success_count}/{len(results)} screenshots captured successfully.")
    
    return results

if __name__ == '__main__':
    main()
