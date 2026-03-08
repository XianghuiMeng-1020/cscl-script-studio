#!/usr/bin/env node
/**
 * S2.14.2 minimal frontend interaction smoke: /teacher
 * - Open /teacher (login if redirected)
 * - Click 开始导入 -> expect wizard or feedback
 * - Click 确认目标 -> expect feedback
 * - Click 开始生成 -> expect feedback
 * Exit 0 if all pass, 1 otherwise.
 */
const { chromium } = require('playwright');
const BASE_URL = process.env.BASE_URL || 'http://localhost:5001';

async function main() {
    let passed = 0;
    let failed = 0;
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    page.on('console', msg => {
        const t = msg.text();
        if (t.indexOf('[teacher]') !== -1) console.log('  [page]', t);
    });

    try {
        await page.goto(BASE_URL + '/teacher', { waitUntil: 'domcontentloaded', timeout: 15000 });
        await page.waitForTimeout(1500);

        const url = page.url();
        if (url.indexOf('/login') !== -1) {
            await page.fill('input[name="username"], input#username, input[type="text"]', 'teacher_demo');
            await page.fill('input[name="password"], input#password, input[type="password"]', 'Demo@12345');
            await page.click('button[type="submit"], input[type="submit"], .btn-primary');
            await page.waitForTimeout(2000);
            await page.goto(BASE_URL + '/teacher', { waitUntil: 'domcontentloaded', timeout: 10000 });
            await page.waitForTimeout(1000);
        }

        const teacherUrl = page.url();
        if (teacherUrl.indexOf('/teacher') === -1) {
            console.error('FAIL: did not reach /teacher, current url:', teacherUrl);
            failed++;
        } else {
            passed++;
            console.log('OK: reached /teacher');
        }

        const clickAndCheck = async (label, selector, check) => {
            try {
                const el = await page.$(selector);
                if (!el) {
                    console.error('FAIL: button not found:', label, selector);
                    failed++;
                    return;
                }
                await el.click();
                await page.waitForTimeout(800);
                const ok = await check(page);
                if (ok) {
                    console.log('OK:', label, '- feedback seen');
                    passed++;
                } else {
                    console.error('FAIL:', label, '- no expected feedback');
                    failed++;
                }
            } catch (e) {
                console.error('FAIL:', label, e.message);
                failed++;
            }
        };

        await clickAndCheck(
            '开始导入',
            '[data-action="import-outline"], .btn-import, #btnImport',
            async (p) => {
                const wizard = await p.$('.wizard-container, #wizardView.active, .wizard-step-content.active');
                const notif = await p.$('.notification.show');
                return !!(wizard || notif);
            }
        );

        await page.goto(BASE_URL + '/teacher', { waitUntil: 'domcontentloaded', timeout: 10000 });
        await page.waitForTimeout(500);

        await clickAndCheck(
            '确认目标',
            '[data-action="validate-goals"], .btn-validate, #btnValidate',
            async (p) => {
                const wizard = await p.$('.wizard-container .wizard-step-content.active, #wizardView.active');
                const notif = await p.$('.notification.show');
                return !!(wizard || notif);
            }
        );

        await page.goto(BASE_URL + '/teacher', { waitUntil: 'domcontentloaded', timeout: 10000 });
        await page.waitForTimeout(500);

        await clickAndCheck(
            '开始生成',
            '[data-action="run-pipeline"], .btn-generate, #btnGenerate',
            async (p) => {
                const wizard = await p.$('.wizard-container .wizard-step-content.active, #wizardView.active');
                const notif = await p.$('.notification.show');
                return !!(wizard || notif);
            }
        );

        const navItem = await page.$('.nav-item[data-view="spec-validation"]');
        if (navItem) {
            await navItem.click();
            await page.waitForTimeout(500);
            const specView = await page.$('#specValidationView.active');
            if (specView) {
                console.log('OK: nav 教学目标检查 -> panel switched');
                passed++;
            } else {
                console.error('FAIL: nav 教学目标检查 did not switch panel');
                failed++;
            }
        } else {
            console.error('FAIL: nav .nav-item[data-view="spec-validation"] not found');
            failed++;
        }
    } catch (err) {
        console.error('Smoke error:', err.message);
        failed++;
    } finally {
        await browser.close();
    }

    console.log('\nResult: passed=' + passed + ', failed=' + failed);
    process.exit(failed > 0 ? 1 : 0);
}

main();
