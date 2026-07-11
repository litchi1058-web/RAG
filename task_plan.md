# 任务计划：美化 Vue 3 + Element Plus 前端

## 目标
提升 RAG 前端项目视觉质感，保证一致的设计语言，不破坏现有功能。

## 阶段

### Phase 1: 创建全局样式文件
- [x] 创建 `frontend/src/styles/global.css`
  - CSS 自定义变量（--primary, --bg-page, --card-shadow 等）
  - Element Plus 组件覆盖（卡片、表格、标签、按钮、输入框）
  - 过渡动画类（fade-slide, fade）
  - 实用工具类

### Phase 2: 更新 main.js
- [x] 在 `main.js` 中引入全局样式

### Phase 3: 增强 App.vue
- [x] 添加全局 loading 动画
- [x] 添加页面切换过渡动画（router-view 包裹 transition）

### Phase 4: 美化 Dashboard.vue
- [x] 统计卡片增加渐变色顶部装饰条
- [x] 响应式布局（xs:12, md:6）
- [x] ECharts 饼图：按病害类型展示知识分布
- [x] 优化表格：斑马纹、悬停高亮、进度条显示置信度

### Phase 5: 优化 MainLayout.vue
- [x] 侧边栏 logo 区域美化（蓝渐变图标 + 文字）
- [x] 菜单项圆角和高亮样式优化
- [x] 头部增加面包屑导航和全屏按钮
- [x] 用户信息下拉增强

## 文件清单
| 文件 | 操作 |
|------|------|
| frontend/src/styles/global.css | 新建 |
| frontend/src/main.js | 修改 |
| frontend/src/App.vue | 替换 |
| frontend/src/views/Dashboard.vue | 替换 |
| frontend/src/layouts/MainLayout.vue | 替换 |
