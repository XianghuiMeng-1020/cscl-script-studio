# Commit 1 快速启动指南

## 前置要求

1. Docker Desktop 已安装并运行
2. Python 3.8+（用于生成SECRET_KEY，可选）

## 从零到运行的命令（不超过10条）

```bash
# 1. 进入项目目录
cd /path/to/teacher-in-loop-main

# 2. 创建环境变量文件
cp .env.example .env

# 3. 生成SECRET_KEY（可选但推荐）
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
# 复制输出的SECRET_KEY到.env文件，替换默认值

# 4. 构建并启动服务
docker compose up --build

# 5. 等待服务启动（约10-20秒），看到以下日志表示成功：
#    web_1      | [INFO] Starting gunicorn 21.2.0
#    web_1      | [INFO] Listening at: http://0.0.0.0:5000
#    web_1      | [INFO] Using worker: sync
#    web_1      | [INFO] Booting worker with pid: X

# 6. 验证服务（在另一个终端）
curl http://localhost:5000/
# 应该返回HTML页面

# 7. 初始化演示数据
curl -X POST http://localhost:5000/api/demo/init
# 应该返回: {"message": "Demo data initialized successfully"}

# 8. 访问Web界面
# 浏览器打开: http://localhost:5000/
```

## 成功标志

✅ **服务状态**: `docker compose ps` 显示web和postgres都是"Up"状态  
✅ **Web响应**: `curl http://localhost:5000/` 返回HTML  
✅ **API端点**: `/api/demo/init` 成功创建演示数据  
✅ **页面访问**: `/teacher` 和 `/student` 页面可访问  
✅ **日志输出**: `docker compose logs web` 显示gunicorn日志到stdout

## 验证脚本（自动化）

```bash
# 运行自动化验证脚本
./scripts/verify_commit1.sh
```

## 常用命令

```bash
# 查看日志
docker compose logs -f web

# 停止服务
docker compose down

# 停止并删除数据卷
docker compose down -v

# 重启服务
docker compose restart

# 进入容器（调试用）
docker compose exec web bash
```

## 故障排查

### Docker daemon未运行
```bash
# 错误: Cannot connect to the Docker daemon
# 解决: 启动Docker Desktop
```

### 端口被占用
```bash
# 错误: Bind for 0.0.0.0:5000 failed: port is already allocated
# 解决: 修改.env中的WEB_PORT或停止占用5000端口的进程
lsof -i :5000  # 查看占用进程
```

### 服务启动失败
```bash
# 查看详细日志
docker compose logs web
docker compose logs postgres

# 检查环境变量
docker compose config
```

## 下一步

Commit 1完成后，系统已Docker化且所有配置环境化。  
继续执行Commit 2: 环境变量配置抽象（已在Commit 1中部分完成）。
