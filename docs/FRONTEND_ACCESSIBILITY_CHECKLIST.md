# CSCL Script Studio - 前端可访问性检查清单

**版本**: 1.0.0  
**更新日期**: 2026-02-05

---

## 1. 键盘可操作性

### 1.1 所有交互元素可键盘访问
- [ ] 所有按钮可通过 Tab 键访问
- [ ] 所有链接可通过 Tab 键访问
- [ ] 所有表单输入可通过 Tab 键访问
- [ ] 所有下拉菜单可通过键盘操作
- [ ] 所有模态框可通过 Esc 关闭

### 1.2 Tab顺序合理
- [ ] Tab顺序遵循视觉流（从上到下，从左到右）
- [ ] 跳过隐藏元素
- [ ] 模态框内Tab循环（不跳出模态框）

### 1.3 快捷键支持
- [ ] Enter键提交表单
- [ ] Esc键关闭模态框
- [ ] 箭头键导航列表/菜单

---

## 2. 焦点态清晰

### 2.1 可见焦点指示器
- [ ] 所有可聚焦元素有清晰的焦点边框
- [ ] 焦点颜色对比度≥3:1
- [ ] 焦点样式不依赖颜色 alone

### 2.2 焦点管理
- [ ] 模态框打开时焦点移至模态框
- [ ] 模态框关闭时焦点返回触发元素
- [ ] 动态内容更新时焦点管理合理

---

## 3. 对比度满足标准

### 3.1 文本对比度
- [ ] 正文文本对比度≥4.5:1
- [ ] 大文本（18px+）对比度≥3:1
- [ ] 图标对比度≥3:1

### 3.2 非文本对比度
- [ ] 按钮边框对比度≥3:1
- [ ] 表单输入边框对比度≥3:1
- [ ] 图表数据点对比度≥3:1

---

## 4. ARIA标签覆盖

### 4.1 核心控件
- [ ] 所有按钮有 `aria-label` 或可见文本
- [ ] 所有图标按钮有 `aria-label`
- [ ] 所有表单输入有 `aria-label` 或 `<label>`
- [ ] 所有链接有描述性文本

### 4.2 状态和属性
- [ ] 加载状态有 `aria-live="polite"`
- [ ] 错误消息有 `role="alert"`
- [ ] 折叠内容有 `aria-expanded`
- [ ] 必填字段有 `aria-required="true"`

### 4.3 区域标识
- [ ] 主要区域有 `role="main"`
- [ ] 导航有 `role="navigation"`
- [ ] 表单有 `role="form"`
- [ ] 模态框有 `role="dialog"` 和 `aria-modal="true"`

---

## 5. 表单可访问性

### 5.1 标签关联
- [ ] 所有输入有 `<label>` 或 `aria-labelledby`
- [ ] 标签与输入正确关联（`for` 或 `id`）
- [ ] 占位符不作为唯一标签

### 5.2 错误处理
- [ ] 错误消息有 `role="alert"`
- [ ] 错误字段有 `aria-invalid="true"`
- [ ] 错误消息通过 `aria-describedby` 关联到字段

### 5.3 帮助文本
- [ ] 帮助文本通过 `aria-describedby` 关联
- [ ] 必填字段有 `aria-required="true"`
- [ ] 字段格式要求清晰说明

---

## 6. 图像和媒体

### 6.1 替代文本
- [ ] 所有信息图像有 `alt` 文本
- [ ] 装饰图像有 `alt=""`
- [ ] 图标有 `aria-label` 或文本替代

### 6.2 图表和数据可视化
- [ ] 图表有文本描述或 `aria-label`
- [ ] 数据表格有 `<caption>`
- [ ] 复杂图表有详细描述

---

## 7. 颜色和视觉

### 7.1 不依赖颜色
- [ ] 错误状态不只用红色（有图标或文字）
- [ ] 成功状态不只用绿色（有图标或文字）
- [ ] 链接不只用颜色区分（有下划线或图标）

### 7.2 动画和闪烁
- [ ] 无闪烁内容（符合WCAG 2.1）
- [ ] 动画可暂停（`prefers-reduced-motion`）
- [ ] 加载动画有 `aria-live="polite"`

---

## 8. 响应式设计

### 8.1 移动端可访问性
- [ ] 触摸目标≥44x44px
- [ ] 文本大小可缩放（不截断）
- [ ] 横向滚动最小化

### 8.2 视口和缩放
- [ ] 支持200%缩放无水平滚动
- [ ] 关键功能在缩放后仍可用
- [ ] 移动端布局合理

---

## 9. 语义HTML

### 9.1 正确使用HTML元素
- [ ] 使用 `<button>` 而非 `<div>` 做按钮
- [ ] 使用 `<nav>` 做导航
- [ ] 使用 `<main>` 做主要内容
- [ ] 使用 `<header>` 和 `<footer>`
- [ ] 使用正确的标题层级（h1-h6）

### 9.2 列表和表格
- [ ] 列表使用 `<ul>` 或 `<ol>`
- [ ] 表格使用 `<table>` 和正确结构
- [ ] 表格有 `<thead>` 和 `<tbody>`

---

## 10. 屏幕阅读器支持

### 10.1 页面结构
- [ ] 有清晰的页面标题（`<title>`）
- [ ] 有跳过链接（Skip to main content）
- [ ] 主要内容有 `role="main"`

### 10.2 动态内容
- [ ] 动态更新有 `aria-live`
- [ ] 状态变化有通知
- [ ] 加载状态有说明

---

## 11. 测试工具

### 11.1 自动化测试
- [ ] 使用 axe DevTools 扫描
- [ ] 使用 WAVE 检查
- [ ] 使用 Lighthouse 可访问性审计

### 11.2 手动测试
- [ ] 仅用键盘导航测试
- [ ] 使用屏幕阅读器测试（NVDA/JAWS/VoiceOver）
- [ ] 高对比度模式测试
- [ ] 缩放测试（200%）

---

## 12. 具体页面检查

### 12.1 首页（/）
- [ ] Hero区域有清晰的标题和描述
- [ ] 角色选择卡片可键盘访问
- [ ] 主按钮有清晰的标签
- [ ] Demo按钮有说明

### 12.2 Teacher Dashboard
- [ ] 侧边栏导航可键盘访问
- [ ] 统计卡片有语义结构
- [ ] 快速操作按钮有标签
- [ ] 最近活动列表可键盘导航

### 12.3 Pipeline可视化
- [ ] 阶段状态有文本说明
- [ ] 进度条有 `aria-valuenow`
- [ ] 错误消息有 `role="alert"`
- [ ] 技术信息可复制（键盘操作）

### 12.4 Quality Report
- [ ] 分数有文本说明
- [ ] 证据链接可键盘访问
- [ ] 改进建议清晰可读
- [ ] 图表有文本替代

### 12.5 Student Dashboard
- [ ] 当前活动信息清晰
- [ ] 任务卡可键盘操作
- [ ] 示例句框可复制（键盘）
- [ ] 协作提示可读

---

## 13. 常见问题修复

### 13.1 按钮
```html
<!-- ❌ 错误 -->
<div onclick="submit()">Submit</div>

<!-- ✅ 正确 -->
<button type="button" onclick="submit()">Submit</button>
```

### 13.2 表单
```html
<!-- ❌ 错误 -->
<input type="text" placeholder="Enter name" />

<!-- ✅ 正确 -->
<label for="name">Name</label>
<input type="text" id="name" aria-required="true" />
```

### 13.3 图标按钮
```html
<!-- ❌ 错误 -->
<i class="fas fa-trash" onclick="delete()"></i>

<!-- ✅ 正确 -->
<button type="button" aria-label="Delete item" onclick="delete()">
  <i class="fas fa-trash" aria-hidden="true"></i>
</button>
```

---

## 14. 实施检查清单

- [ ] 所有页面通过键盘导航测试
- [ ] 所有表单通过可访问性检查
- [ ] 所有图像有替代文本
- [ ] 所有动态内容有ARIA标签
- [ ] 对比度满足WCAG AA标准
- [ ] 屏幕阅读器测试通过
- [ ] 移动端触摸目标≥44px
- [ ] 支持200%缩放
- [ ] 无闪烁内容
- [ ] 语义HTML正确使用

---

## 15. 参考资源

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [axe DevTools](https://www.deque.com/axe/devtools/)
