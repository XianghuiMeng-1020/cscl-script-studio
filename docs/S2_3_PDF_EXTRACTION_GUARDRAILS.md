# S2.3 PDF 提取防护规则

## 1. 提取方式

- **仅使用 pypdf 页面文本提取**：禁止对原始 bytes 做 decode 或直接读取
- **提取方法**：`pypdf.PdfReader().pages[].extract_text()`

## 2. 二进制标记拦截

若提取文本包含以下任一标记，判定为提取失败，返回 `PDF_PARSE_FAILED`：

| 标记 | 说明 |
|------|------|
| `%PDF-` | PDF 文件头 |
| `xref` | 交叉引用表 |
| `obj` | 对象定义 |
| `endobj` | 对象结束 |
| `stream` | 流开始 |
| `endstream` | 流结束 |
| `N M obj` | 行首的对象编号格式 |

正则表达式：`r'%PDF-|\bxref\b|\bobj\b|\bendobj\b|\bstream\b|\bendstream\b|^\s*\d+\s+\d+\s+obj\b'`

## 3. normalize_text

- 去除控制字符（保留 `\n`、`\t`）
- 合并连续空白
- Unicode 规范化 NFKC
- 去除零宽字符 (U+200B–200D, BOM)

## 4. 错误码

| 错误码 | 条件 |
|--------|------|
| PDF_PARSE_FAILED | 提取文本含二进制标记 |
| EMPTY_EXTRACTED_TEXT | 提取为空 |
| TEXT_TOO_SHORT | 规范化后字符数 < 80 |
| UNSUPPORTED_FILE_TYPE | 不支持的文件类型 |

## 5. 上传成功返回结构

```json
{
  "ok": true,
  "doc_id": "...",
  "detected_type": "pdf|txt|docx",
  "extracted_char_count": 1234,
  "extracted_text_preview": "...前300字符...",
  "extraction_method": "pypdf_page_text|plain_text",
  "warnings": []
}
```
