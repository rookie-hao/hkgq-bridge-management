# 港澳台侨管库系统

基于 Vue + Flask 前后端分离的港澳台侨事务管理系统，支持人员信息、政策文件、活动管理等功能。

## 技术栈

### 前端
- Vue 2.6 + Vue Router + Vuex
- Element UI 组件库
- Axios HTTP 客户端
- ECharts 数据可视化

### 后端
- Python Flask
- PyMySQL 数据库驱动
- PyJWT 身份认证
- MySQL 数据库

## 功能模块

| 模块 | 功能 |
|------|------|
| 📊 仪表盘 | 系统概览、统计卡片、数据图表 |
| 👤 人员管理 | 港澳台侨人员信息增删改查、搜索筛选 |
| 📄 政策文件 | 政策文件管理、分类筛选、状态管理 |
| 🎉 活动管理 | 活动/会议管理、类型筛选、状态追踪 |
| ⚙️ 用户管理 | 系统用户管理、角色权限控制（admin/user） |

## 快速开始

### 环境要求
- Node.js >= 12
- Python >= 3.7
- MySQL >= 5.7

### 后端启动

```bash
cd hkgq-bridge-management
pip install -r requirements.txt

# 修改 config.py 中的数据库配置
# MYSQL_HOST = 'localhost'
# MYSQL_USER = 'root'
# MYSQL_PASSWORD = 'your_password'
# MYSQL_DB = 'hkgq_management'

python app.py
```

后端运行在 `http://localhost:5000`

### 前端启动

```bash
npm install
npm run dev
```

前端运行在 `http://localhost:9528`

### 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | 111111 | 管理员 |
| test | 111111 | 普通用户 |

## API 接口

### 认证相关
- `POST /vue-admin-template/user/login` - 登录
- `POST /vue-admin-template/user/logout` - 登出
- `GET /vue-admin-template/user/info` - 获取用户信息

### 人员管理
- `GET /vue-admin-template/personnel/list` - 人员列表
- `GET /vue-admin-template/personnel/detail` - 人员详情
- `POST /vue-admin-template/personnel/create` - 新增人员
- `POST /vue-admin-template/personnel/update` - 更新人员
- `POST /vue-admin-template/personnel/delete` - 删除人员

### 政策文件
- `GET /vue-admin-template/policy/list` - 政策列表
- `GET /vue-admin-template/policy/detail` - 政策详情
- `POST /vue-admin-template/policy/create` - 新增政策
- `POST /vue-admin-template/policy/update` - 更新政策
- `POST /vue-admin-template/policy/delete` - 删除政策

### 活动管理
- `GET /vue-admin-template/activity/list` - 活动列表
- `GET /vue-admin-template/activity/detail` - 活动详情
- `POST /vue-admin-template/activity/create` - 新增活动
- `POST /vue-admin-template/activity/update` - 更新活动
- `POST /vue-admin-template/activity/delete` - 删除活动

### 统计看板
- `GET /vue-admin-template/dashboard/overview` - 概览统计
- `GET /vue-admin-template/dashboard/region-stats` - 地区分布统计
- `GET /vue-admin-template/dashboard/policy-stats` - 政策分类统计
- `GET /vue-admin-template/dashboard/activity-stats` - 活动类型统计

## 项目结构

```
├── app.py                 # Flask 后端主文件
├── models.py              # 数据模型
├── config.py              # 配置文件
├── requirements.txt       # Python 依赖
├── src/                   # 前端源码
│   ├── api/               # API 请求模块
│   ├── components/        # 公共组件
│   ├── icons/             # SVG 图标
│   ├── layout/            # 页面布局
│   ├── router/            # 路由配置
│   ├── store/             # Vuex 状态管理
│   ├── styles/            # 全局样式
│   ├── utils/             # 工具函数
│   └── views/             # 页面组件
├── public/                # 静态资源
├── package.json           # 前端依赖
└── vue.config.js          # Vue 配置
```

## License

MIT
