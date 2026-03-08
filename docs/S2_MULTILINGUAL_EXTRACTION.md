# S2 多语言文本提取文档

**版本**: S2重构版  
**日期**: 2026-02-05

本文档描述S2重构后的多语言文本提取实现。

---

## 1. 支持的语言与编码

### 1.1 编码支持

| 语言 | 编码 | 优先级 |
|------|------|--------|
| English | UTF-8, UTF-8-sig, Latin-1 | 1, 2, 5 |
| 简体中文 | UTF-8, UTF-8-sig, GBK | 1, 2, 3 |
| 繁體中文 | UTF-8, UTF-8-sig, Big5 | 1, 2, 4 |

### 1.2 编码检测顺序

```python
encodings = ['utf-8', 'utf-8-sig', 'gbk', 'big5', 'latin-1']
```

**策略**: 按顺序尝试，第一个成功即使用

---

## 2. 文本清理流程

### 2.1 Unicode规范化

```python
text = unicodedata.normalize('NFKC', text)
```

**NFKC**: Compatibility decomposition + Composition
- 统一全角/半角字符
- 统一兼容字符变体

### 2.2 控制字符处理

**保留**:
- `\n` (换行)
- `\t` (制表符)

**移除**:
- 所有其他控制字符（C0, C1）
- Zero-width字符（\u200b-\u200d, \ufeff）

### 2.3 空白字符规范化

```python
# 多个空格/制表符 → 单个空格
text = re.sub(r'[ \t]+', ' ', text)

# 多个换行 → 双换行
text = re.sub(r'\n{3,}', '\n\n', text)
```

---

## 3. 文件类型支持

### 3.1 当前支持

| 类型 | 扩展名 | 状态 |
|------|--------|------|
| 纯文本 | .txt | ✅ 完全支持 |
| Markdown | .md | ✅ 完全支持 |

### 3.2 暂不支持（明确提示）

| 类型 | 扩展名 | 错误消息 |
|------|--------|---------|
| PDF | .pdf | "PDF解析暂未支持。请上传 .txt 或 .md 文件，或先将PDF内容复制为文本后粘贴上传。" |
| Word | .docx | "DOCX解析暂未支持。请将文档另存为 .txt 或 .md 格式后上传，或复制内容后使用粘贴上传功能。" |

---

## 4. 粘贴上传处理

### 4.1 流程

1. 用户粘贴文本到文本域
2. 前端发送JSON: `{text: "...", title: "..."}`
3. 后端调用`upload_text_document()`
4. 文本清理（`clean_text()`）
5. 验证长度（>= 10字符）
6. 分块存储

### 4.2 清理保证

- 粘贴文本同样经过`clean_text()`处理
- 确保UTF-8统一
- 控制字符清洗
- 空白规范化

---

## 5. 错误处理

### 5.1 编码错误

**场景**: 文件编码不在支持列表中

**处理**:
```python
raise ValueError(
    f"无法解码文件，尝试的编码：{', '.join(encodings)}。"
    f"请确保文件为UTF-8、GBK或Big5编码。"
)
```

### 5.2 文件类型错误

**场景**: 不支持的文件类型（PDF/DOCX）

**处理**:
```python
raise ValueError(
    "PDF解析暂未支持。请上传 .txt 或 .md 文件，"
    "或先将PDF内容复制为文本后粘贴上传。"
)
```

### 5.3 文本过短

**场景**: 清理后文本 < 10字符

**处理**:
```python
return {
    'error': '文本内容过短（至少10个字符）。'
             '请提供有效的课程大纲内容。'
}
```

---

## 6. 测试样例

### 6.1 English样例

**文件**: `test_en.txt`
```
Introduction to Data Science

This course covers fundamental concepts in data science,
including data collection, analysis, and visualization.

Learning Objectives:
- Understand data science workflow
- Apply statistical methods
- Create visualizations
```

**预期结果**: 成功提取，UTF-8编码

### 6.2 简体中文样例

**文件**: `test_zh_cn.txt` (GBK编码)
```
数据科学导论

本课程涵盖数据科学的基础概念，
包括数据收集、分析和可视化。

学习目标：
- 理解数据科学工作流程
- 应用统计方法
- 创建可视化
```

**预期结果**: 成功提取，GBK→UTF-8转换

### 6.3 繁體中文样例

**文件**: `test_zh_tw.txt` (Big5编码)
```
資料科學導論

本課程涵蓋資料科學的基礎概念，
包括資料收集、分析和視覺化。

學習目標：
- 理解資料科學工作流程
- 應用統計方法
- 創建視覺化
```

**预期结果**: 成功提取，Big5→UTF-8转换

---

## 7. 实现细节

### 7.1 代码位置

- **服务类**: `app/services/document_service.py`
- **清理函数**: `clean_text()`
- **提取函数**: `extract_text_from_file()`
- **上传函数**: `upload_text_document()`

### 7.2 关键方法

```python
def clean_text(self, text: str) -> str:
    """清理文本：UTF-8规范化、控制字符移除、空白规范化"""
    # Unicode规范化
    text = unicodedata.normalize('NFKC', text)
    # 移除控制字符（保留\n\t）
    text = ''.join(char for char in text 
                   if unicodedata.category(char)[0] != 'C' 
                   or char in '\n\t')
    # 规范化空白
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 移除零宽字符
    text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
    return text.strip()
```

---

## 8. 性能考虑

### 8.1 文件大小限制

- **最大文件**: 10MB
- **分块大小**: 500字符/块

### 8.2 处理时间

- **小文件** (< 100KB): < 1秒
- **中文件** (100KB - 1MB): 1-5秒
- **大文件** (1MB - 10MB): 5-30秒

---

## 9. 未来扩展

### 9.1 计划支持

- PDF解析（PyPDF2/pdfplumber）
- DOCX解析（python-docx）
- 图片OCR（可选）

### 9.2 编码扩展

- UTF-16 (LE/BE)
- Shift-JIS (日文)
- EUC-KR (韩文)

---

## 10. 更新记录

- 2026-02-05: S2重构版本创建，多语言支持实现
