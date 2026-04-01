#!/usr/bin/env python3
"""
验证 Initial Idea 字段是否在 Step 2 表单中可见
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        # 创建输出目录
        output_dir = "outputs/initial_idea_verification"
        os.makedirs(output_dir, exist_ok=True)
        
        print("步骤 1: 访问教师登录页面...")
        await page.goto("https://web-production-591d6.up.railway.app/teacher")
        await page.wait_for_load_state('networkidle')
        await page.screenshot(path=f"{output_dir}/01_login_page.png")
        print("✓ 登录页面加载完成")
        
        print("\n步骤 2: 登录...")
        # 填写登录信息
        await page.fill('input[name="username"]', 'teacher_demo')
        await page.fill('input[name="password"]', 'Demo@12345')
        await page.screenshot(path=f"{output_dir}/02_login_filled.png")
        
        # 点击登录按钮
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        await page.screenshot(path=f"{output_dir}/03_after_login.png")
        print("✓ 登录成功")
        
        print("\n步骤 3: 点击 'New Activity' 按钮...")
        
        # 等待页面稳定
        await asyncio.sleep(3)
        
        # 查找 "New Activity" 按钮
        new_activity_button = page.locator('button:has-text("New Activity")').first
        
        if await new_activity_button.is_visible():
            await new_activity_button.click()
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            await page.screenshot(path=f"{output_dir}/04_step1_page.png")
            print("✓ 进入 Step 1 页面")
        else:
            print("✗ 未找到 'New Activity' 按钮")
            await page.screenshot(path=f"{output_dir}/04_no_button_found.png")
            await browser.close()
            return
        
        print("\n步骤 4: 点击 'Continue' 按钮进入 Step 2...")
        # 等待并点击继续按钮
        continue_button = page.locator('button:has-text("Continue")').first
        if await continue_button.is_visible():
            await continue_button.click()
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            await page.screenshot(path=f"{output_dir}/05_step2_page.png")
            print("✓ 进入 Step 2 页面")
        else:
            print("✗ 未找到 'Continue' 按钮")
            await browser.close()
            return
        
        print("\n步骤 5: 检查 Initial Idea 字段...")
        
        # 截取页面顶部（第一个字段区域）
        await page.screenshot(path=f"{output_dir}/06_step2_top_section.png")
        
        # 检查是否存在 Initial Idea 字段
        initial_idea_checks = {
            'id="specInitialIdea"': False,
            'label包含"初步想法"': False,
            'label包含"initial idea"': False,
            'textarea字段存在': False
        }
        
        # 检查 1: 通过 ID 查找
        initial_idea_by_id = page.locator('#specInitialIdea')
        if await initial_idea_by_id.count() > 0:
            initial_idea_checks['id="specInitialIdea"'] = True
            print("✓ 找到 id='specInitialIdea' 的元素")
            
            # 检查是否可见
            if await initial_idea_by_id.is_visible():
                print("✓ Initial Idea 字段可见")
            else:
                print("✗ Initial Idea 字段存在但不可见")
        else:
            print("✗ 未找到 id='specInitialIdea' 的元素")
        
        # 检查 2: 查找包含"初步想法"的 label
        initial_idea_label_cn = page.locator('label:has-text("初步想法")')
        if await initial_idea_label_cn.count() > 0:
            initial_idea_checks['label包含"初步想法"'] = True
            print("✓ 找到包含'初步想法'的 label")
        else:
            print("✗ 未找到包含'初步想法'的 label")
        
        # 检查 3: 查找包含"initial idea"的 label (不区分大小写)
        initial_idea_label_en = page.locator('label').filter(has_text='initial idea')
        if await initial_idea_label_en.count() > 0:
            initial_idea_checks['label包含"initial idea"'] = True
            print("✓ 找到包含'initial idea'的 label")
        else:
            print("✗ 未找到包含'initial idea'的 label")
        
        # 检查 4: 查找 textarea 字段
        textareas = page.locator('textarea')
        textarea_count = await textareas.count()
        if textarea_count > 0:
            initial_idea_checks['textarea字段存在'] = True
            print(f"✓ 找到 {textarea_count} 个 textarea 字段")
            
            # 列出所有 textarea 的 id 和 name
            for i in range(textarea_count):
                textarea = textareas.nth(i)
                textarea_id = await textarea.get_attribute('id')
                textarea_name = await textarea.get_attribute('name')
                textarea_placeholder = await textarea.get_attribute('placeholder')
                print(f"  Textarea {i+1}: id='{textarea_id}', name='{textarea_name}', placeholder='{textarea_placeholder}'")
        else:
            print("✗ 未找到任何 textarea 字段")
        
        # 获取页面 HTML 以便进一步分析
        page_html = await page.content()
        with open(f"{output_dir}/step2_page_source.html", "w", encoding="utf-8") as f:
            f.write(page_html)
        print(f"\n✓ 页面源代码已保存到 {output_dir}/step2_page_source.html")
        
        # 截取 Initial Idea 字段的特写
        print("\n步骤 6: 截取 Initial Idea 字段...")
        initial_idea_element = page.locator('#specInitialIdea')
        if await initial_idea_element.count() > 0:
            try:
                # 滚动到元素位置
                await initial_idea_element.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                # 截取元素截图
                await initial_idea_element.screenshot(path=f"{output_dir}/07_initial_idea_field.png")
                print("✓ Initial Idea 字段截图已保存")
            except Exception as e:
                print(f"✗ 截图失败: {e}")
                # 尝试截取整个页面
                await page.screenshot(path=f"{output_dir}/07_full_page.png", full_page=True)
                print("✓ 完整页面截图已保存")
        
        # 生成报告
        print("\n" + "="*60)
        print("验证结果总结:")
        print("="*60)
        
        all_passed = all(initial_idea_checks.values())
        
        for check, passed in initial_idea_checks.items():
            status = "✓" if passed else "✗"
            print(f"{status} {check}: {'通过' if passed else '未通过'}")
        
        print("\n" + "="*60)
        if all_passed:
            print("结论: Initial Idea 字段在 Step 2 表单中可见 ✓")
        else:
            print("结论: Initial Idea 字段在 Step 2 表单中不完全可见 ✗")
        print("="*60)
        
        print(f"\n所有截图已保存到: {output_dir}/")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
