// Create screenshot manifest
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, '../outputs/ui');
const MANIFEST_PATH = path.join(OUTPUT_DIR, 'SCREENSHOT_MANIFEST.json');

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

const screenshots = [
    { file: 'home_cscl.png', url: 'http://localhost:5001/' },
    { file: 'teacher_dashboard_cscl.png', url: 'http://localhost:5001/teacher' },
    { file: 'teacher_pipeline_run_cscl.png', url: 'http://localhost:5001/teacher#wizard' },
    { file: 'teacher_quality_report_cscl.png', url: 'http://localhost:5001/teacher#quality-reports' },
    { file: 'student_dashboard_cscl.png', url: 'http://localhost:5001/student' },
    { file: 'student_current_session_cscl.png', url: 'http://localhost:5001/student?script_id=xxx' }
];

const manifest = {
    generated_at: new Date().toISOString(),
    base_url: 'http://localhost:5001',
    screenshots: screenshots.map(s => {
        const filepath = path.join(OUTPUT_DIR, s.file);
        let bytes = 0;
        if (fs.existsSync(filepath)) {
            bytes = fs.statSync(filepath).size;
        }
        return {
            file: s.file,
            bytes: bytes,
            created_at: fs.existsSync(filepath) ? fs.statSync(filepath).mtime.toISOString() : new Date().toISOString(),
            url: s.url
        };
    })
};

fs.writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2));
console.log('✓ Screenshot manifest created:', MANIFEST_PATH);
