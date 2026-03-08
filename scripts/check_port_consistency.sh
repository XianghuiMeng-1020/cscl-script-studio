#!/bin/bash
# 端口一致性检查脚本
# 检查全仓库是否仍有 localhost:5000 或 :5000 引用

echo "=== Port Consistency Check ==="
echo "Checking for remaining references to port 5000..."
echo ""

# 排除的文件和目录
EXCLUDE_PATTERNS=(
    "*.md"  # 文档文件（历史记录）
    "*.bak"
    "*.old"
    "node_modules"
    ".git"
    "outputs"
    "__pycache__"
    "*.pyc"
)

# 构建find排除参数
EXCLUDE_ARGS=()
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    EXCLUDE_ARGS+=(-not -path "*/${pattern}")
done

# 搜索5000端口引用
MATCHES=$(find . -type f \
    -not -path "*/.git/*" \
    -not -path "*/node_modules/*" \
    -not -path "*/outputs/*" \
    -not -path "*/__pycache__/*" \
    -not -name "*.md" \
    -not -name "*.bak" \
    -not -name "*.old" \
    -exec grep -l "localhost:5000\|:5000\|5000" {} \; 2>/dev/null | grep -v "check_port_consistency.sh")

if [ -z "$MATCHES" ]; then
    echo "✅ No port 5000 references found in code files"
    echo ""
    echo "Note: Some documentation files (*.md) may still reference 5000 for historical context."
    echo "These are acceptable and do not affect runtime behavior."
    exit 0
else
    echo "⚠️  Found port 5000 references in the following files:"
    echo "$MATCHES" | while read -r file; do
        echo "  - $file"
        grep -n "localhost:5000\|:5000\|5000" "$file" 2>/dev/null | head -3 | sed 's/^/    /'
    done
    echo ""
    echo "Please update these files to use port 5001."
    exit 1
fi
