# 快速启动命令（可直接复制）

## macOS zsh 一键启动

```bash
# ============================================
# 1. 启动服务
# ============================================
cd /Users/mrealsalvatore/Desktop/teacher-in-loop-main && \
docker compose down -v && \
docker compose up --build -d && \
echo "Waiting 30 seconds for services to start..." && \
sleep 30

# ============================================
# 2. 初始化Demo数据
# ============================================
curl -X POST http://localhost:5001/api/demo/init

# ============================================
# 3. 健康检查
# ============================================
curl http://localhost:5001/api/health

# ============================================
# 4. 页面检查（应全部返回200）
# ============================================
echo "Testing pages..." && \
curl -s -o /dev/null -w "Home: %{http_code}\n" http://localhost:5001/ && \
curl -s -o /dev/null -w "Teacher: %{http_code}\n" http://localhost:5001/teacher && \
curl -s -o /dev/null -w "Student: %{http_code}\n" http://localhost:5001/student

# ============================================
# 5. API联调测试
# ============================================
./scripts/test_api.sh

# ============================================
# 6. 打开浏览器访问
# ============================================
open http://localhost:5001
```

## 关键API测试命令

```bash
# Spec Validation (公开端点)
curl -X POST http://localhost:5001/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "course": "CS101",
    "topic": "Algorithmic Fairness",
    "duration_minutes": 90,
    "mode": "Sync",
    "class_size": 30,
    "learning_objectives": ["Explain fairness metrics"],
    "task_type": "debate"
  }' | jq
```

## 演示流程

1. **访问首页**: http://localhost:5001
2. **点击"Quick Demo Syllabus"** → 自动跳转并填充
3. **验证Spec** → 点击"Validate Spec"
4. **运行Pipeline** → 点击"Run Pipeline"，观察4阶段进度
5. **查看Quality Report** → 点击"View Quality Report"
6. **切换到Student** → 访问 http://localhost:5001/student

---

**总演示时间**: 5-6分钟
