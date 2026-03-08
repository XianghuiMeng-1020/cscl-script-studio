# API错误代码矩阵 - 前端展示文案映射

**版本**: 1.0.0  
**更新日期**: 2026-02-05

---

## 错误代码映射表

| HTTP状态码 | 错误代码 | 前端展示文案 | 用户操作建议 |
|-----------|---------|-------------|-------------|
| 401 | AUTH_REQUIRED | 请先登录 | 点击登录按钮或联系管理员 |
| 403 | PERMISSION_DENIED | 当前角色无权限 | 联系管理员获取相应角色权限 |
| 404 | SCRIPT_NOT_FOUND | 资源不存在或尚未创建 | 检查资源ID或创建新资源 |
| 404 | REVISION_NOT_FOUND | 修订记录不存在 | 检查修订ID |
| 400 | MISSING_BODY | 请求数据缺失 | 检查表单是否完整填写 |
| 400 | MISSING_SPEC | spec字段必填 | 请填写Pedagogical Spec |
| 400 | MISSING_REQUIRED_FIELDS | 必填字段缺失 | 请检查表单必填项 |
| 422 | VALIDATION_FAILED | 输入不完整，请检查表单 | 查看详细错误信息并修正 |
| 422 | INVALID_SPEC | Spec验证失败 | 查看验证结果并修正问题 |
| 422 | INVALID_DECISION_TYPE | 无效的决策类型 | 检查决策类型参数 |
| 422 | INVALID_TARGET_TYPE | 无效的目标类型 | 检查目标类型参数 |
| 422 | INVALID_SOURCE_STAGE | 无效的源阶段 | 检查源阶段参数 |
| 422 | INVALID_CONFIDENCE | 置信度必须在1-5之间 | 修正置信度值 |
| 422 | INVALID_TIME_FORMAT | 时间格式错误 | 使用ISO 8601格式 |
| 415 | UNSUPPORTED_FILE_TYPE | 不支持的文件类型 | 使用支持的格式（.txt, .md, .pdf） |
| 422 | PDF_PARSE_FAILED | PDF解析失败 | 检查PDF是否损坏或加密，尝试其他格式 |
| 422 | TEXT_TOO_SHORT | 提取的文本过短 | 确保文件包含足够的文本内容（至少80字符） |
| 422 | EMPTY_EXTRACTED_TEXT | 无法提取文本 | 可能是扫描版PDF，尝试OCR或手动输入 |
| 400 | EXTRACTION_FAILED | 文件处理失败 | 检查文件格式或联系技术支持 |
| 500 | INTERNAL_ERROR | 服务器内部错误 | 稍后重试或联系技术支持 |
| 500 | REPORT_GENERATION_FAILED | 质量报告生成失败 | 稍后重试 |
| 503 | PROVIDER_KEY_MISSING | 服务暂不可用，可先使用mock | 配置LLM Provider或使用Mock模式 |
| 503 | PROVIDER_ERROR | AI服务暂不可用 | 稍后重试或使用Mock模式 |

---

## 前端错误处理实现

### JavaScript错误处理函数

```javascript
function handleApiError(response, errorData) {
    const status = response.status;
    const code = errorData.code || 'UNKNOWN_ERROR';
    
    let message = 'An error occurred';
    let action = 'Please try again later';
    
    switch(status) {
        case 401:
            message = '请先登录';
            action = 'Please login first';
            break;
        case 403:
            message = '当前角色无权限';
            action = 'Current role has no permission';
            break;
        case 404:
            message = '资源不存在或尚未创建';
            action = 'Resource not found or not yet created';
            break;
        case 422:
            message = '输入不完整，请检查表单';
            action = 'Input incomplete, please check the form';
            break;
        case 503:
            message = '服务暂不可用，可先使用mock';
            action = 'Service temporarily unavailable. You can use mock mode for testing.';
            break;
        default:
            message = errorData.error || 'An error occurred';
    }
    
    showNotification(`${message}. ${action}`, status >= 500 ? 'error' : 'warning');
    return { message, action, status, code };
}
```

---

## 错误展示规范

### 通知样式
- **401/403**: 红色错误通知，显示"请先登录"或"当前角色无权限"
- **404**: 黄色警告通知，显示"资源不存在或尚未创建"
- **422**: 黄色警告通知，显示具体验证错误列表
- **503**: 蓝色信息通知，显示"服务暂不可用，可先使用mock"

### 表单错误
- 字段级错误：在字段下方显示红色错误文本
- 表单级错误：在表单顶部显示错误摘要
- 验证错误：显示具体问题列表

### 空状态错误
- 404错误：显示"资源不存在" + 创建按钮
- 权限错误：显示"无权限访问" + 联系管理员提示

---

## 错误代码详细说明

### 认证相关（401）
- **AUTH_REQUIRED**: 需要登录才能访问此资源
- **前端处理**: 显示登录提示，可跳转到登录页面

### 权限相关（403）
- **PERMISSION_DENIED**: 当前用户角色无权限
- **前端处理**: 显示权限提示，说明所需角色

### 资源相关（404）
- **SCRIPT_NOT_FOUND**: 脚本项目不存在
- **REVISION_NOT_FOUND**: 修订记录不存在
- **前端处理**: 显示"资源不存在"，提供创建新资源的选项

### 验证相关（422）
- **VALIDATION_FAILED**: Spec验证失败
- **INVALID_SPEC**: Spec格式或内容无效
- **PDF_PARSE_FAILED**: PDF解析失败
- **TEXT_TOO_SHORT**: 提取的文本过短
- **EMPTY_EXTRACTED_TEXT**: 无法提取文本
- **前端处理**: 显示详细错误列表，高亮问题字段

### 文件提取相关（415/422）
- **UNSUPPORTED_FILE_TYPE**: 不支持的文件类型（415）
- **PDF_PARSE_FAILED**: PDF解析失败（422）
- **TEXT_TOO_SHORT**: 提取的文本过短（422）
- **EMPTY_EXTRACTED_TEXT**: 无法提取文本（422）
- **EXTRACTION_FAILED**: 文件处理失败（400）
- **前端处理**: 显示明确的错误信息和操作建议

### 服务相关（503）
- **PROVIDER_KEY_MISSING**: LLM Provider未配置
- **PROVIDER_ERROR**: AI服务错误
- **前端处理**: 显示服务不可用提示，提供Mock模式选项

---

## 实施检查清单

- [x] 401错误处理实现
- [x] 403错误处理实现
- [x] 404错误处理实现
- [x] 422错误处理实现
- [x] 503错误处理实现
- [x] 错误通知样式统一
- [x] 表单错误显示实现
- [x] 空状态错误处理实现
