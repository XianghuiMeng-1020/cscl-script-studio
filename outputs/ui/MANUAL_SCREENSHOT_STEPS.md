# Manual Screenshot Capture Steps

**生成时间**: 2026-02-05  
**原因**: Puppeteer浏览器下载失败（网络连接问题）

---

## 前置条件

1. Docker服务运行正常：
   ```bash
   docker compose ps
   # 应显示 web 和 postgres 容器均为 Up (healthy)
   ```

2. 服务可访问：
   ```bash
   curl http://localhost:5001/api/health
   # 应返回: {"status":"ok",...}
   ```

---

## 截图步骤

### 1. home_cscl.png
- **URL**: http://localhost:5001/
- **保存路径**: `outputs/ui/home_cscl.png`
- **说明**: 首页完整视图，包含Hero、3步流程、角色选择、功能证据、Quick Demo按钮

### 2. teacher_dashboard_cscl.png
- **URL**: http://localhost:5001/teacher
- **保存路径**: `outputs/ui/teacher_dashboard_cscl.png`
- **说明**: Teacher Dashboard，包含统计卡片、今日下一步、最近活动

### 3. teacher_pipeline_run_cscl.png
- **URL**: http://localhost:5001/teacher
- **操作**: 点击"Create New Script Project"按钮，进入向导Step 3（Pipeline Run）
- **保存路径**: `outputs/ui/teacher_pipeline_run_cscl.png`
- **说明**: Pipeline可视化，显示4个阶段（Planner, Material, Critic, Refiner）

### 4. teacher_quality_report_cscl.png
- **URL**: http://localhost:5001/teacher
- **操作**: 点击左侧导航"Quality Reports"，或访问已有script的quality report详情
- **保存路径**: `outputs/ui/teacher_quality_report_cscl.png`
- **说明**: Quality Report详情，显示6维度评估卡片

### 5. student_dashboard_cscl.png
- **URL**: http://localhost:5001/student
- **保存路径**: `outputs/ui/student_dashboard_cscl.png`
- **说明**: Student Dashboard，显示空状态（无script_id时）

### 6. student_current_session_cscl.png
- **URL**: http://localhost:5001/student?script_id=xxx
- **说明**: 使用有效的script_id参数（需要先创建script）
- **保存路径**: `outputs/ui/student_current_session_cscl.png`
- **说明**: Student当前会话视图，显示活动信息、任务、进度

---

## 截图工具推荐

### macOS
- **内置截图**: `Command + Shift + 4`，选择区域
- **全屏截图**: `Command + Shift + 3`
- **浏览器全页截图**: Chrome DevTools > Command + Shift + P > "Capture full size screenshot"

### Chrome DevTools方法（推荐）
1. 打开Chrome DevTools (F12)
2. 按 `Command + Shift + P` (macOS) 或 `Ctrl + Shift + P` (Windows/Linux)
3. 输入 "Capture full size screenshot"
4. 保存到 `outputs/ui/` 目录，命名为对应文件名

---

## 验证步骤

1. 确认6个PNG文件存在：
   ```bash
   ls -lh outputs/ui/*.png
   ```

2. 确认文件大小 > 0：
   ```bash
   for f in outputs/ui/*.png; do echo "$(basename $f): $(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null || echo 0) bytes"; done
   ```

3. 重新生成manifest：
   ```bash
   node scripts/create_manifest.js
   ```

4. 验证manifest中bytes > 0：
   ```bash
   cat outputs/ui/SCREENSHOT_MANIFEST.json | jq '[.screenshots[] | select(.bytes > 0)] | length'
   # 应返回: 6
   ```

---

## 故障排除

### 如果服务不可访问
```bash
# 检查Docker状态
docker compose ps

# 查看日志
docker compose logs web --tail=50

# 重启服务
docker compose restart web
```

### 如果截图工具不可用
- 使用任何截图工具（系统内置、第三方）
- 确保保存为PNG格式
- 确保文件名完全匹配（区分大小写）

---

**状态**: ⚠️ 待手动完成
