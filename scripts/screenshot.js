// Screenshot script using Puppeteer
const puppeteer = require('puppeteer');
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
        await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
        await page.waitForTimeout(2000); // Wait for animations
        
        const filepath = path.join(OUTPUT_DIR, filename);
        await page.screenshot({
            path: filepath,
            fullPage: options.fullPage !== false,
            ...options
        });
        
        const stats = fs.statSync(filepath);
        console.log(`✓ ${filename} (${(stats.size / 1024).toFixed(2)} KB)`);
        return { filepath, size: stats.size, success: true };
    } catch (error) {
        console.error(`✗ Failed to screenshot ${filename}:`, error.message);
        return { filepath: null, size: 0, success: false };
    }
}

async function generateManifest(screenshots) {
    const manifest = {
        generated_at: new Date().toISOString(),
        base_url: BASE_URL,
        screenshots: screenshots.map(s => ({
            file: path.basename(s.filepath || ''),
            bytes: s.size || 0,
            created_at: new Date().toISOString(),
            url: s.url || ''
        }))
    };
    
    const manifestPath = path.join(OUTPUT_DIR, 'SCREENSHOT_MANIFEST.json');
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
    console.log(`\n✓ Manifest generated: ${manifestPath}`);
    return manifestPath;
}

async function main() {
    console.log('Starting screenshot capture...');
    console.log(`Base URL: ${BASE_URL}`);
    console.log(`Output directory: ${OUTPUT_DIR}\n`);
    
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    
    const screenshots = [
        { url: `${BASE_URL}/`, filename: 'home_cscl.png', name: 'Home Page' },
        { url: `${BASE_URL}/teacher`, filename: 'teacher_dashboard_cscl.png', name: 'Teacher Dashboard' },
        { url: `${BASE_URL}/student`, filename: 'student_dashboard_cscl.png', name: 'Student Dashboard' }
    ];
    
    const results = [];
    
    for (const shot of screenshots) {
        const result = await takeScreenshot(page, shot.url, shot.filename);
        results.push({
            name: shot.name,
            filename: shot.filename,
            url: shot.url,
            ...result
        });
    }
    
    // For pipeline and quality report, try to navigate through wizard
    // These require setup, so we'll try but gracefully handle failures
    console.log('\nAttempting to capture Pipeline and Quality Report screenshots...');
    
    try {
        // Navigate to teacher page and try to access wizard
        await page.goto(`${BASE_URL}/teacher`, { waitUntil: 'networkidle0' });
        await page.waitForTimeout(1000);
        
        // Try to click "Create New Script Project" to open wizard
        try {
            await page.click('button:has-text("Create New Script Project"), button[onclick*="createNewScriptProject"]');
            await page.waitForTimeout(2000);
            
            // Try to capture pipeline visualization (step 3)
            const pipelineResult = await takeScreenshot(page, `${BASE_URL}/teacher`, 'teacher_pipeline_run_cscl.png');
            results.push({
                name: 'Teacher Pipeline Run',
                filename: 'teacher_pipeline_run_cscl.png',
                url: `${BASE_URL}/teacher#wizard`,
                ...pipelineResult
            });
        } catch (e) {
            console.log('⚠️  Could not capture pipeline screenshot automatically. Please capture manually.');
            results.push({
                name: 'Teacher Pipeline Run',
                filename: 'teacher_pipeline_run_cscl.png',
                url: `${BASE_URL}/teacher#wizard`,
                filepath: null,
                size: 0,
                success: false
            });
        }
        
        // Try to capture quality report
        try {
            // Navigate to quality reports view
            await page.goto(`${BASE_URL}/teacher`, { waitUntil: 'networkidle0' });
            await page.waitForTimeout(1000);
            
            const qualityResult = await takeScreenshot(page, `${BASE_URL}/teacher`, 'teacher_quality_report_cscl.png');
            results.push({
                name: 'Teacher Quality Report',
                filename: 'teacher_quality_report_cscl.png',
                url: `${BASE_URL}/teacher#quality-reports`,
                ...qualityResult
            });
        } catch (e) {
            console.log('⚠️  Could not capture quality report screenshot automatically. Please capture manually.');
            results.push({
                name: 'Teacher Quality Report',
                filename: 'teacher_quality_report_cscl.png',
                url: `${BASE_URL}/teacher#quality-reports`,
                filepath: null,
                size: 0,
                success: false
            });
        }
        
        // Student current session
        const studentSessionResult = await takeScreenshot(page, `${BASE_URL}/student`, 'student_current_session_cscl.png');
        results.push({
            name: 'Student Current Session',
            filename: 'student_current_session_cscl.png',
            url: `${BASE_URL}/student`,
            ...studentSessionResult
        });
    } catch (e) {
        console.log('⚠️  Some screenshots require manual setup. Please capture manually.');
    }
    
    await browser.close();
    
    // Generate manifest
    await generateManifest(results);
    
    console.log('\n=== Screenshot Summary ===');
    results.forEach(r => {
        console.log(`${r.success ? '✓' : '✗'} ${r.name}: ${r.filename}${r.success ? ` (${(r.size / 1024).toFixed(2)} KB)` : ' (failed)'}`);
    });
    
    const successCount = results.filter(r => r.success).length;
    console.log(`\n${successCount}/${results.length} screenshots captured successfully.`);
    
    if (successCount < results.length) {
        console.log('\nNote: Some screenshots require manual capture:');
        results.filter(r => !r.success).forEach(r => {
            console.log(`  - ${r.filename}: Navigate to ${r.url} and capture manually`);
        });
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = { takeScreenshot, generateManifest };
