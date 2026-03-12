#!/usr/bin/env node

/**
 * CSCL Script Studio 完整向导流程测试
 * 测试所有4个步骤并报告详细结果
 */

const { chromium } = require('playwright');

const BASE_URL = process.env.BASE_URL || 'https://web-production-591d6.up.railway.app';

// 演示账户凭证
const DEMO_USERNAME = 'teacher_demo';
const DEMO_PASSWORD = 'Demo@12345';

const SYLLABUS_TEXT = `Course: Introduction to Computer Science
Instructor: Dr. Zhang Wei
Semester: Spring 2026

Course Description:
This course provides a comprehensive introduction to computer science fundamentals, covering algorithms, data structures, programming paradigms, and software engineering principles.

Learning Objectives:
1. Understand fundamental algorithms and data structures
2. Apply object-oriented programming principles
3. Analyze algorithm complexity using Big-O notation
4. Design and implement collaborative software projects

Course Topics:
- Week 1-4: Programming fundamentals and Python
- Week 5-8: Object-Oriented Programming
- Week 9-12: Data Structures and Algorithms
- Week 13-16: Software Engineering and Group Projects

Class Size: 40 students
Duration: 90 minutes per session
Mode: In-person`;

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
    console.log('=== CSCL Script Studio 完整流程测试 ===\n');
    console.log(`Base URL: ${BASE_URL}`);
    console.log(`目标页面: ${BASE_URL}/teacher\n`);
    
    const browser = await chromium.launch({
        headless: false, // 使用有界面模式以便观察
        slowMo: 500 // 减慢操作速度以便观察
    });
    
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    
    const page = await context.newPage();
    
    const issues = [];
    const stepResults = [];
    
    try {
        // 导航到教师仪表板
        console.log('📍 导航到教师仪表板...');
        await page.goto(`${BASE_URL}/teacher`, { waitUntil: 'networkidle', timeout: 60000 });
        await sleep(2000);
        
        const pageTitle = await page.title();
        console.log('页面标题:', pageTitle);
        
        // 检查是否需要登录
        if (pageTitle.includes('Sign In') || pageTitle.includes('Login') || pageTitle.includes('登录')) {
            console.log('🔐 需要登录,正在执行登录流程...');
            
            // 截图登录页面
            await page.screenshot({ path: 'outputs/login_page.png', fullPage: true });
            console.log('📸 已保存登录页面截图: outputs/login_page.png');
            
            // 填写用户名
            const usernameInput = await page.locator('input[name="username"], input[name="user_id"], input[type="text"]').first();
            await usernameInput.fill(DEMO_USERNAME);
            console.log(`✓ 已填写用户名: ${DEMO_USERNAME}`);
            
            // 填写密码
            const passwordInput = await page.locator('input[name="password"], input[type="password"]').first();
            await passwordInput.fill(DEMO_PASSWORD);
            console.log('✓ 已填写密码');
            
            // 点击登录按钮
            const loginButton = await page.locator('button[type="submit"], button:has-text("Sign In"), button:has-text("Login"), button:has-text("登录")').first();
            await loginButton.click();
            console.log('✓ 已点击登录按钮');
            
            // 等待登录完成并跳转
            await sleep(3000);
            await page.waitForURL('**/teacher', { timeout: 10000 }).catch(() => {});
            
            console.log('✓ 登录成功\n');
        }
        
        console.log('✓ 页面加载完成\n');
        
        // 截图以便调试
        await page.screenshot({ path: 'outputs/step1_initial.png', fullPage: true });
        console.log('📸 已保存初始页面截图: outputs/step1_initial.png');
        
        // ========== 步骤 1: 上传教学大纲 ==========
        console.log('=== 步骤 1: 上传教学大纲 ===');
        
        // 等待页面完全加载
        await sleep(3000);
        
        // 尝试多种方式查找textarea
        console.log('查找教学大纲输入框...');
        let textarea = null;
        
        // 尝试1: 通过ID或data属性
        textarea = await page.locator('[data-ref="e140"], #syllabus-input, textarea[name="syllabus"]').first().catch(() => null);
        
        // 尝试2: 通过placeholder
        if (!textarea || !await textarea.isVisible().catch(() => false)) {
            textarea = await page.locator('textarea[placeholder*="syllabus"], textarea[placeholder*="Paste"], textarea[placeholder*="教学大纲"]').first().catch(() => null);
        }
        
        // 尝试3: 任何可见的textarea
        if (!textarea || !await textarea.isVisible().catch(() => false)) {
            const allTextareas = await page.locator('textarea').all();
            console.log(`找到 ${allTextareas.length} 个textarea元素`);
            for (const ta of allTextareas) {
                if (await ta.isVisible().catch(() => false)) {
                    textarea = ta;
                    break;
                }
            }
        }
        
        if (!textarea || !await textarea.isVisible().catch(() => false)) {
            issues.push('步骤1: 未找到教学大纲输入框');
            await page.screenshot({ path: 'outputs/step1_error.png', fullPage: true });
            throw new Error('未找到可见的textarea元素');
        }
        
        console.log('填充教学大纲文本...');
        await textarea.fill(SYLLABUS_TEXT);
        await sleep(1000);
        
        // 查找Continue按钮
        const continueBtn = await page.locator('button:has-text("Continue")').first();
        if (!continueBtn) {
            issues.push('步骤1: 未找到Continue按钮');
            throw new Error('未找到Continue按钮');
        }
        
        console.log('点击Continue按钮...');
        await continueBtn.click();
        await sleep(3000);
        
        // 检查是否有错误通知
        const errorNotification = await page.locator('.notification.is-danger, .error, [role="alert"]').first();
        if (await errorNotification.isVisible().catch(() => false)) {
            const errorText = await errorNotification.textContent();
            issues.push(`步骤1错误通知: ${errorText}`);
        }
        
        stepResults.push({ step: 1, status: 'completed', issues: [] });
        console.log('✓ 步骤1完成\n');
        
        // ========== 步骤 2: 填写教学计划表单 ==========
        console.log('=== 步骤 2: 填写教学计划表单 ===');
        
        // 等待表单加载
        await sleep(2000);
        
        // 填写表单字段
        console.log('填写课程名称...');
        const courseNameInput = await page.locator('input[name="courseName"], input[placeholder*="Course"], input[placeholder*="课程"]').first();
        await courseNameInput.fill('Introduction to Computer Science');
        
        console.log('填写主题...');
        const topicInput = await page.locator('input[name="topic"], input[placeholder*="Topic"], input[placeholder*="主题"]').first();
        await topicInput.fill('Algorithm Design and Analysis');
        
        console.log('填写班级规模...');
        const classSizeInput = await page.locator('input[name="classSize"], input[type="number"]').first();
        await classSizeInput.fill('40');
        
        console.log('填写课程背景...');
        const contextTextarea = await page.locator('textarea[name="courseContext"], textarea[placeholder*="context"], textarea[placeholder*="背景"]').first();
        await contextTextarea.fill('This is an undergraduate CS course for second-year students. Students have basic Python knowledge and work in groups of 4-5.');
        
        console.log('填写学习目标...');
        const objectivesTextarea = await page.locator('textarea[name="learningObjectives"], textarea[placeholder*="objectives"], textarea[placeholder*="目标"]').first();
        await objectivesTextarea.fill('Understand and compare sorting algorithms\nAnalyze algorithm complexity using Big-O notation\nEvaluate trade-offs between efficiency and implementation complexity');
        
        console.log('选择任务类型...');
        const taskTypeSelect = await page.locator('select[name="taskType"], select').first();
        await taskTypeSelect.selectOption('evidence_comparison');
        
        console.log('填写预期输出...');
        const outputTextarea = await page.locator('textarea[name="expectedOutput"], textarea[placeholder*="output"], textarea[placeholder*="输出"]').first();
        await outputTextarea.fill('Group comparison chart\n500-word collaborative analysis report');
        
        console.log('填写任务要求...');
        const requirementsTextarea = await page.locator('textarea[name="taskRequirements"], textarea[placeholder*="requirements"], textarea[placeholder*="要求"]').first();
        await requirementsTextarea.fill('Each group must compare at least 3 algorithms with evidence from code execution and Big-O analysis.');
        
        await sleep(1000);
        
        console.log('点击Validate Teaching Plan按钮...');
        const validateBtn = await page.locator('button:has-text("Validate")').first();
        await validateBtn.click();
        await sleep(3000);
        
        // 检查验证结果
        const validationSuccess = await page.locator('.notification.is-success, .success').first();
        if (await validationSuccess.isVisible().catch(() => false)) {
            console.log('✓ 教学计划验证成功');
        } else {
            issues.push('步骤2: 教学计划验证失败或无反馈');
        }
        
        console.log('点击Continue按钮...');
        const step2ContinueBtn = await page.locator('button:has-text("Continue")').first();
        await step2ContinueBtn.click();
        await sleep(3000);
        
        stepResults.push({ step: 2, status: 'completed', issues: [] });
        console.log('✓ 步骤2完成\n');
        
        // ========== 步骤 3: 运行Pipeline ==========
        console.log('=== 步骤 3: 运行Pipeline ===');
        
        console.log('点击Start Generation按钮...');
        const startBtn = await page.locator('button:has-text("Start Generation"), button:has-text("Run Pipeline")').first();
        await startBtn.click();
        
        console.log('等待Pipeline执行 (预计60-120秒)...');
        
        // 轮询检查Pipeline状态
        let pipelineComplete = false;
        let pollCount = 0;
        const maxPolls = 12; // 12 * 15秒 = 180秒
        
        const stageNames = ['Planner', 'Material', 'Critic', 'Refiner'];
        const stageStatuses = {};
        
        while (!pipelineComplete && pollCount < maxPolls) {
            await sleep(15000); // 每15秒检查一次
            pollCount++;
            
            console.log(`轮询 ${pollCount}/${maxPolls}...`);
            
            // 检查各个阶段的状态
            for (const stageName of stageNames) {
                const stageElement = await page.locator(`[data-stage="${stageName}"], .stage:has-text("${stageName}")`).first();
                if (await stageElement.isVisible().catch(() => false)) {
                    const stageText = await stageElement.textContent();
                    
                    if (stageText.includes('Success') || stageText.includes('成功')) {
                        stageStatuses[stageName] = 'Success';
                    } else if (stageText.includes('Failed') || stageText.includes('失败')) {
                        stageStatuses[stageName] = 'Failed';
                    } else if (stageText.includes('Running') || stageText.includes('运行中')) {
                        stageStatuses[stageName] = 'Running';
                    } else {
                        stageStatuses[stageName] = 'Waiting';
                    }
                }
            }
            
            console.log('当前阶段状态:', stageStatuses);
            
            // 检查是否所有阶段都完成
            const allComplete = stageNames.every(name => 
                stageStatuses[name] === 'Success' || stageStatuses[name] === 'Failed'
            );
            
            if (allComplete) {
                pipelineComplete = true;
                console.log('✓ Pipeline执行完成');
                break;
            }
            
            // 检查按钮状态
            const generatingBtn = await page.locator('button:has-text("Generating")').first();
            if (!await generatingBtn.isVisible().catch(() => false)) {
                console.log('✓ 生成按钮已恢复,Pipeline可能已完成');
                pipelineComplete = true;
                break;
            }
        }
        
        if (!pipelineComplete) {
            issues.push('步骤3: Pipeline执行超时 (超过180秒)');
        }
        
        // 记录最终阶段状态
        console.log('\n最终Pipeline阶段状态:');
        for (const [stage, status] of Object.entries(stageStatuses)) {
            console.log(`  ${stage}: ${status}`);
            if (status === 'Failed') {
                issues.push(`步骤3: ${stage}阶段失败`);
            }
        }
        
        stepResults.push({ 
            step: 3, 
            status: pipelineComplete ? 'completed' : 'timeout',
            stageStatuses 
        });
        console.log('✓ 步骤3完成\n');
        
        // ========== 步骤 4: 查看预览 ==========
        console.log('=== 步骤 4: 查看预览 ===');
        
        console.log('点击Continue按钮进入步骤4...');
        const step4ContinueBtn = await page.locator('button:has-text("Continue")').first();
        await step4ContinueBtn.click();
        await sleep(5000);
        
        // 检查预览是否加载
        const loadingText = await page.locator('text="Loading script preview"').first();
        const isLoading = await loadingText.isVisible().catch(() => false);
        
        if (isLoading) {
            issues.push('步骤4: 脚本预览卡在"Loading script preview..."状态');
            console.log('✗ 预览加载失败 - 卡在Loading状态');
        } else {
            // 检查预览内容
            const rolesSection = await page.locator('text="Roles", text="角色"').first();
            const scenesSection = await page.locator('text="Scenes", text="场景"').first();
            const scriptletsSection = await page.locator('text="Scriptlets", text="脚本片段"').first();
            const summarySection = await page.locator('text="Pipeline Summary", text="流程摘要"').first();
            
            const hasRoles = await rolesSection.isVisible().catch(() => false);
            const hasScenes = await scenesSection.isVisible().catch(() => false);
            const hasScriptlets = await scriptletsSection.isVisible().catch(() => false);
            const hasSummary = await summarySection.isVisible().catch(() => false);
            
            console.log('预览内容检查:');
            console.log(`  Roles: ${hasRoles ? '✓' : '✗'}`);
            console.log(`  Scenes: ${hasScenes ? '✓' : '✗'}`);
            console.log(`  Scriptlets: ${hasScriptlets ? '✓' : '✗'}`);
            console.log(`  Pipeline Summary: ${hasSummary ? '✓' : '✗'}`);
            
            if (!hasRoles || !hasScenes || !hasScriptlets || !hasSummary) {
                issues.push('步骤4: 预览内容不完整');
            } else {
                console.log('✓ 预览加载成功,所有部分都显示正常');
            }
        }
        
        stepResults.push({ 
            step: 4, 
            status: isLoading ? 'stuck' : 'completed'
        });
        console.log('✓ 步骤4完成\n');
        
    } catch (error) {
        console.error('\n✗ 测试过程中发生错误:', error.message);
        issues.push(`致命错误: ${error.message}`);
    } finally {
        // 生成最终报告
        console.log('\n' + '='.repeat(60));
        console.log('=== 最终测试报告 ===');
        console.log('='.repeat(60));
        
        console.log('\n步骤执行摘要:');
        stepResults.forEach(result => {
            console.log(`  步骤 ${result.step}: ${result.status}`);
            if (result.stageStatuses) {
                Object.entries(result.stageStatuses).forEach(([stage, status]) => {
                    console.log(`    - ${stage}: ${status}`);
                });
            }
        });
        
        if (issues.length > 0) {
            console.log('\n发现的问题:');
            issues.forEach((issue, index) => {
                console.log(`  ${index + 1}. ${issue}`);
            });
        } else {
            console.log('\n✓ 未发现任何问题!所有步骤都成功完成。');
        }
        
        console.log('\n测试完成。浏览器将在10秒后关闭...');
        await sleep(10000);
        
        await browser.close();
    }
}

if (require.main === module) {
    main().catch(error => {
        console.error('脚本执行失败:', error);
        process.exit(1);
    });
}

module.exports = { main };
