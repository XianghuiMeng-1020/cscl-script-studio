# CSCL Script Studio - 前端设计系统

**版本**: 1.0.0  
**更新日期**: 2026-02-05  
**产品名称**: CSCL Script Studio  
**副标题**: Collaborative Learning Activity Generator

---

## 1. 品牌标识

### 1.1 Logo设计方向

提供三个方向供选择（最终实现其一）：

#### 方向A：三人环形协作 + 对话气泡
- **语义**: 多人协作 + 结构化对话
- **视觉**: 三个圆形节点环形排列，中心有对话气泡
- **适用**: 强调协作与交流

#### 方向B：节点网络 + 剧本页角
- **语义**: 结构化流程 + 脚本化活动
- **视觉**: 节点网络图，右下角有折角（剧本页）
- **适用**: 强调流程与结构

#### 方向C：双人协作手势 + 时间线
- **语义**: 协作 + 时间序列
- **视觉**: 两个手势图标，下方有时间线
- **适用**: 强调协作与时间流程

**技术要求**:
- 纯矢量、扁平化
- 单色或双色（Primary + Accent）
- 16/24/32/64 px 可读
- favicon 与 sidebar logo 都可用

### 1.2 产品命名

- **主名称**: CSCL Script Studio
- **副标题**: Collaborative Learning Activity Generator
- **简称**: Script Studio

---

## 2. 配色系统（Design Tokens）

### 2.1 主色调（禁止AI典型紫蓝）

```css
/* Primary - 深青 */
--color-primary: #1F6F78;
--color-primary-hover: #195B62;
--color-primary-light: #2A8A94;
--color-primary-dark: #0F4A50;

/* Secondary - 柔和绿 */
--color-secondary: #2E8B57;
--color-secondary-hover: #256A42;
--color-secondary-light: #3BA66B;

/* Accent - 暖金（少量用于强调） */
--color-accent: #C08A3E;
--color-accent-hover: #A6752F;

/* Background */
--color-bg-primary: #F7F9F8;
--color-bg-surface: #FFFFFF;
--color-bg-surface-hover: #F0F3F2;

/* Border */
--color-border: #DDE5E3;
--color-border-hover: #C8D4D0;

/* Text */
--color-text-primary: #1F2933;
--color-text-secondary: #52606D;
--color-text-muted: #7A8A99;
--color-text-inverse: #FFFFFF;

/* Status */
--color-success: #2F855A;
--color-success-bg: #D1FAE5;
--color-warning: #B7791F;
--color-warning-bg: #FEF3C7;
--color-error: #C53030;
--color-error-bg: #FEE2E2;
--color-info: #1F6F78;
--color-info-bg: #E0F2F1;
```

### 2.2 使用规范

- **Primary**: 主按钮、链接、重要强调
- **Secondary**: 次要操作、辅助信息
- **Accent**: 少量用于高亮、徽章、特殊提示
- **禁止**: 蓝紫霓虹、渐变炫光、悬浮发光、过度拟物

---

## 3. 字体与排版

### 3.1 字体族

```css
/* 英文 */
font-family: 'Inter', 'Source Sans Pro', -apple-system, BlinkMacSystemFont, sans-serif;

/* 中文 */
font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;

/* 等宽数字（用于指标） */
font-variant-numeric: tabular-nums;
```

### 3.2 字重与行高

```css
/* 标题 */
--font-weight-heading: 600;
--line-height-heading: 1.4;

/* 正文 */
--font-weight-body: 400;
--font-weight-body-medium: 500;
--line-height-body: 1.65;

/* 每行长度 */
max-width: 60-80 字符（ch）
```

### 3.3 字号层级

```css
--font-size-xs: 0.75rem;    /* 12px - 辅助信息 */
--font-size-sm: 0.875rem;   /* 14px - 次要文本 */
--font-size-base: 1rem;     /* 16px - 正文 */
--font-size-lg: 1.125rem;   /* 18px - 强调文本 */
--font-size-xl: 1.25rem;    /* 20px - 小标题 */
--font-size-2xl: 1.5rem;   /* 24px - 中标题 */
--font-size-3xl: 1.875rem; /* 30px - 大标题 */
--font-size-4xl: 2.25rem;  /* 36px - Hero标题 */
```

---

## 4. 组件风格

### 4.1 圆角

```css
--radius-sm: 6px;   /* 小元素 */
--radius-md: 10px;  /* 按钮、输入框 */
--radius-lg: 12px;  /* 卡片 */
--radius-xl: 16px;  /* 大卡片、模态框 */
--radius-full: 9999px; /* 圆形 */
```

### 4.2 阴影

```css
/* 极轻阴影，只用于浮层 */
--shadow-sm: 0 1px 2px 0 rgba(31, 45, 51, 0.05);
--shadow-md: 0 2px 4px 0 rgba(31, 45, 51, 0.08);
--shadow-lg: 0 4px 8px 0 rgba(31, 45, 51, 0.1);
--shadow-none: none; /* 默认无阴影 */
```

### 4.3 卡片

```css
/* 白底 + 细边框，避免厚重阴影 */
.card {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
}
```

### 4.4 按钮

```css
/* 主按钮 - 实心 */
.btn-primary {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  font-weight: 600;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

/* 次按钮 - 描边 */
.btn-secondary {
  background: transparent;
  color: var(--color-primary);
  border: 2px solid var(--color-primary);
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  font-weight: 600;
}

.btn-secondary:hover {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

/* 文本按钮 */
.btn-text {
  background: transparent;
  color: var(--color-primary);
  border: none;
  padding: 0.5rem 1rem;
  font-weight: 500;
}
```

### 4.5 图标

```css
/* 线性风格，统一 1.75px stroke */
.icon {
  stroke-width: 1.75px;
  fill: none;
}

/* Font Awesome 图标大小 */
.icon-sm: 1rem;   /* 16px */
.icon-md: 1.25rem; /* 20px */
.icon-lg: 1.5rem;  /* 24px */
.icon-xl: 2rem;    /* 32px */
```

---

## 5. 间距系统

```css
--spacing-xs: 0.25rem;  /* 4px */
--spacing-sm: 0.5rem;   /* 8px */
--spacing-md: 1rem;    /* 16px */
--spacing-lg: 1.5rem;  /* 24px */
--spacing-xl: 2rem;    /* 32px */
--spacing-2xl: 3rem;   /* 48px */
--spacing-3xl: 4rem;   /* 64px */
```

---

## 6. 动画与过渡

### 6.1 过渡时间

```css
--transition-fast: 150ms;
--transition-base: 250ms;
--transition-slow: 350ms;
```

### 6.2 缓动函数

```css
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
```

### 6.3 动画原则

- **克制**: 避免花哨动画
- **功能优先**: 动画服务于交互反馈
- **性能**: 使用 transform 和 opacity

---

## 7. 响应式断点

```css
/* Desktop First */
--breakpoint-sm: 640px;   /* Tablet */
--breakpoint-md: 768px;   /* Small Desktop */
--breakpoint-lg: 1024px;  /* Desktop */
--breakpoint-xl: 1280px;  /* Large Desktop */
--breakpoint-2xl: 1536px; /* Extra Large */

/* 关键流程在 1366x768 无折叠灾难 */
```

---

## 8. 可访问性

### 8.1 对比度

- **正文**: 至少 4.5:1
- **大文本**: 至少 3:1
- **交互元素**: 至少 3:1

### 8.2 焦点态

```css
.focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

### 8.3 ARIA标签

- 所有核心控件必须有 `aria-label`
- 表单字段必须有 `aria-describedby`（错误提示）
- 状态变化必须有 `aria-live`

---

## 9. 视觉克制原则

1. **留白充分**: 卡片间距至少 1.5rem
2. **层级清晰**: 使用字号、字重、颜色建立层级
3. **对比适中**: 避免高对比度造成视觉疲劳
4. **不用花哨动画**: 仅使用必要的过渡效果

---

## 10. 实施检查清单

- [ ] Logo 已替换（3个方向选1）
- [ ] 配色已更新为深青+柔和绿+暖金
- [ ] 字体已设置为 Inter/Noto Sans SC
- [ ] 圆角统一为 10-12px
- [ ] 阴影已移除或极轻
- [ ] 按钮主次清晰
- [ ] 图标统一为线性风格
- [ ] 响应式断点已测试
- [ ] 可访问性已验证
- [ ] 无AI典型紫蓝配色
