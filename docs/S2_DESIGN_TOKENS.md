# S2 设计令牌文档

**版本**: S2重构版  
**日期**: 2026-02-05

本文档定义S2重构后的设计令牌（Design Tokens），锁定视觉系统。

---

## 1. 配色系统（锁定）

### 1.1 主色板

| 用途 | 颜色值 | CSS变量 | 说明 |
|------|--------|---------|------|
| 主文本/深色背景 | `#050C12` | `--text-dark` | 深蓝黑，用于标题和主要文本 |
| 浅背景/分区 | `#B5D5DA` | `--bg-light` | 浅青蓝，用于背景和分区 |
| 主操作强调 | `#58C0DB` | `--primary-color` | 亮青色，用于主按钮和强调 |
| 次强调/hover | `#166DA6` | `--secondary-color` | 深蓝色，用于hover和次要操作 |
| 标题/导航 | `#063467` | `--nav-color` | 深蓝，用于导航和标题背景 |

### 1.2 配色原则

- ✅ **禁止使用**: 紫色系、霓虹渐变、发光效果
- ✅ **要求**: 高对比、低饱和、留白充分
- ✅ **限制**: 每屏最多一个主按钮色

---

## 2. CSS变量映射

### 2.1 文本颜色

```css
--text-primary: #050C12;      /* 主文本 */
--text-secondary: rgba(5, 12, 18, 0.7);  /* 次要文本 */
--text-muted: rgba(5, 12, 18, 0.5);      /* 弱化文本 */
--text-inverse: #FFFFFF;      /* 反色文本（深色背景上） */
```

### 2.2 背景颜色

```css
--bg-primary: #B5D5DA;        /* 主背景 */
--bg-surface: #FFFFFF;        /* 卡片/表面背景 */
--bg-surface-hover: rgba(181, 213, 218, 0.3);  /* 悬停背景 */
```

### 2.3 主色系统

```css
--primary-color: #58C0DB;     /* 主操作色 */
--primary-dark: #166DA6;      /* 主色深色变体 */
--primary-hover: #166DA6;     /* 主色悬停 */
--primary-light: #58C0DB;     /* 主色浅色变体 */

--secondary-color: #166DA6;   /* 次强调色 */
--secondary-light: #58C0DB;   /* 次色浅色变体 */
--secondary-hover: #063467;   /* 次色悬停 */
```

### 2.4 状态颜色

```css
--success-color: #2F855A;     /* 成功（绿色系，保持兼容） */
--warning-color: #B7791F;     /* 警告（黄色系，保持兼容） */
--error-color: #C53030;       /* 错误（红色系，保持兼容） */
--info-color: #58C0DB;        /* 信息（使用主色） */
```

---

## 3. 渐变系统

### 3.1 允许的渐变

```css
--gradient-primary: linear-gradient(135deg, #58C0DB 0%, #166DA6 100%);
--gradient-secondary: linear-gradient(135deg, #166DA6 0%, #063467 100%);
--gradient-dark: linear-gradient(135deg, #050C12 0%, #063467 100%);
--gradient-hero: linear-gradient(135deg, #050C12 0%, #063467 50%, #166DA6 100%);
```

### 3.2 使用原则

- **克制使用**: 仅用于Hero区域和特殊强调
- **禁止**: 霓虹色、紫色系渐变
- **方向**: 135deg（左上到右下）

---

## 4. 阴影系统

### 4.1 阴影定义

```css
--shadow-sm: 0 1px 2px 0 rgba(5, 12, 18, 0.05);
--shadow-md: 0 2px 4px 0 rgba(5, 12, 18, 0.08);
--shadow-lg: 0 4px 8px 0 rgba(5, 12, 18, 0.1);
--shadow-none: none;
```

### 4.2 使用原则

- **极轻**: 仅用于浮层和卡片
- **颜色**: 使用`--text-dark`的透明度
- **禁止**: 彩色阴影、发光效果

---

## 5. 圆角系统

```css
--radius-sm: 6px;    /* 小元素（标签、徽章） */
--radius-md: 10px;   /* 按钮、输入框 */
--radius-lg: 12px;   /* 卡片 */
--radius-xl: 16px;   /* 大卡片、模态框 */
--radius-full: 9999px;  /* 圆形（头像、徽章） */
```

---

## 6. 间距系统

```css
--spacing-xs: 0.25rem;   /* 4px */
--spacing-sm: 0.5rem;    /* 8px */
--spacing-md: 1rem;      /* 16px */
--spacing-lg: 1.5rem;    /* 24px */
--spacing-xl: 2rem;      /* 32px */
--spacing-2xl: 3rem;     /* 48px */
```

---

## 7. 字体系统

### 7.1 字体族

```css
--font-family-en: 'Inter', 'Source Sans Pro', -apple-system, BlinkMacSystemFont, sans-serif;
--font-family-cn: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
```

### 7.2 字重

```css
--font-weight-heading: 600;      /* 标题 */
--font-weight-body: 400;         /* 正文 */
--font-weight-body-medium: 500;  /* 正文强调 */
```

### 7.3 行高

```css
--line-height-heading: 1.4;   /* 标题 */
--line-height-body: 1.65;     /* 正文 */
```

---

## 8. 过渡动画

```css
--transition-fast: 150ms;
--transition-base: 250ms;
--transition-slow: 350ms;

--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
```

---

## 9. Logo规范

### 9.1 Logo方向

**主题**: 协作学习 + 活动编排

**元素**:
- 3人协作节点（圆形）
- 连接路径（线条）
- 流程页角（路径元素）

### 9.2 版本要求

- **扁平风格**: 无渐变、无阴影
- **单色版本**: 使用`--primary-color`
- **双色版本**: `--primary-color` + `--text-dark`
- **SVG格式**: 矢量，可缩放

### 9.3 禁止元素

- ❌ 学术帽图标
- ❌ AI风格图标
- ❌ 紫色/霓虹色
- ❌ 发光效果

---

## 10. 图标使用规范

### 10.1 语义化图标

| 功能 | 图标 | Font Awesome类 |
|------|------|---------------|
| 教师 | `fa-chalkboard-teacher` | 黑板+教师 |
| 学生 | `fa-users` | 用户组 |
| 协作活动 | `fa-project-diagram` | 流程图 |
| 上传 | `fa-file-upload` | 文件上传 |
| 检查 | `fa-check-circle` | 检查圈 |
| 生成 | `fa-cogs` | 齿轮 |
| 发布 | `fa-rocket` | 火箭 |

### 10.2 图标颜色

- **主操作**: `--primary-color` (#58C0DB)
- **次要操作**: `--secondary-color` (#166DA6)
- **文本图标**: `--text-secondary`

---

## 11. 按钮系统

### 11.1 主按钮

```css
.btn-primary {
    background: var(--primary-color);
    color: var(--text-inverse);
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: var(--radius-md);
    font-weight: 600;
}

.btn-primary:hover {
    background: var(--primary-dark);
}
```

### 11.2 次按钮

```css
.btn-secondary {
    background: transparent;
    color: var(--primary-color);
    border: 2px solid var(--primary-color);
    padding: 0.75rem 1.5rem;
    border-radius: var(--radius-md);
    font-weight: 600;
}

.btn-secondary:hover {
    background: var(--primary-color);
    color: var(--text-inverse);
}
```

---

## 12. 更新记录

- 2026-02-05: S2重构版本创建，配色系统锁定
