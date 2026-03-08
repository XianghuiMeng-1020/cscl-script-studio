// Screenshot script using Playwright (more reliable than Puppeteer)
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = process.env.BASE_URL || 'http://localhost:5001';
const OUTPUT_DIR = path.join(__dirname, '../outputs/ui');

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function takeScreenshot(page, url, filename, options = {}) {
    console.log(`Taking screenshot: ${filename}...`);
    try {
        await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(2000); // Wait for animations
        
        const filepath = path.join(OUTPUT_DIR, filename);
        await page.screenshot({
            path: filepath,
            fullPage: options.fullPage !== false,
            ...options
        });
        
        const stats = fs.statSync(filepath);
        console.log(`✓ ${filename} (${(stats.size / 1024).toFixed(2)} KB)`);
        return { filepath, size: stats.size, success: true, url };
    } catch (error) {
        console.error(`✗ Failed to screenshot ${filename}:`, error.message);
        return { filepath: null, size: 0, success: false, url };
    }
}

async function main() {
    console.log('Starting screenshot capture with Playwright...');
    console.log(`Base URL: ${BASE_URL}`);
    console.log(`Output directory: ${OUTPUT_DIR}\n`);
    
    const browser = await chromium.launch({
        headless: true
    });
    
    const page = await browser.newPage();
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    const screenshots = [
        { url: `${BASE_URL}/`, filename: 'home_cscl.png', name: 'Home Page' },
        { url: `${BASE_URL}/teacher`, filename: 'teacher_dashboard_cscl.png', name: 'Teacher Dashboard' },
        { url: `${BASE_URL}/student`, filename: 'student_dashboard_cscl.png', name: 'Student Dashboard' }
    ];
    
    const results = [];
    
    // Basic screenshots
    for (const shot of screenshots) {
        const result = await takeScreenshot(page, shot.url, shot.filename);
        results.push({
            name: shot.name,
            filename: shot.filename,
            ...result
        });
    }
    
    // Pipeline and Quality Report screenshots (same as teacher dashboard for now)
    console.log('\nCapturing Pipeline and Quality Report screenshots...');
    const pipelineResult = await takeScreenshot(page, `${BASE_URL}/teacher`, 'teacher_pipeline_run_cscl.png');
    results.push({
        name: 'Teacher Pipeline Run',
        filename: 'teacher_pipeline_run_cscl.png',
        ...pipelineResult
    });
    
    const qualityResult = await takeScreenshot(page, `${BASE_URL}/teacher`, 'teacher_quality_report_cscl.png');
    results.push({
        name: 'Teacher Quality Report',
        filename: 'teacher_quality_report_cscl.png',
        ...qualityResult
    });
    
    // Student current session
    const studentSessionResult = await takeScreenshot(page, `${BASE_URL}/student`, 'student_current_session_cscl.png');
    results.push({
        name: 'Student Current Session',
        filename: 'student_current_session_cscl.png',
        ...studentSessionResult
    });
    
    await browser.close();
    
    console.log('\n=== Screenshot Summary ===');
    results.forEach(r => {
        console.log(`${r.success ? '✓' : '✗'} ${r.name}: ${r.filename}${r.success ? ` (${(r.size / 1024).toFixed(2)} KB)` : ' (failed)'}`);
    });
    
    const successCount = results.filter(r => r.success).length;
    console.log(`\n${successCount}/${results.length} screenshots captured successfully.`);
    
    return results;
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = { takeScreenshot, main };
