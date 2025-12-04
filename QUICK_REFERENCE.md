# 快速参考指南

本文档提供深圳地铁寻路游戏的快速参考信息。

---

## 🚀 快速启动

### 一键启动（推荐）
```bash
./start.sh
```

### 手动启动
```bash
# 终端 1 - 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 终端 2 - 启动前端
cd frontend
npm install
npm run dev
```

### 访问地址
- 🎮 前端应用: http://localhost:5173
- 📚 API 文档: http://localhost:8000/docs
- 🔧 后端 API: http://localhost:8000

---

## 🎮 游戏流程

```
1. 选择线路 → 2. 设定起终点 → 3. 输入路径 → 4. 查看结果
   (多选)        (手动/随机)       (逐站添加)      (验证答案)
```

---

## 📋 功能清单

### 基础功能
- ✅ 线路选择（支持多选）
- ✅ 起终点设置（手动输入/随机生成）
- ✅ 路径输入（逐站添加）
- ✅ 路径验证（合法性检查）
- ✅ 结果展示（所有最短路径）

### 优化功能
- ✅ 线路锁定（游戏中禁止修改）
- ✅ 成本提示（显示大致站数）
- ✅ 详细错误提示（中文说明）
- ✅ 查看答案（可选显示）
- ✅ 换乘标注（橙色高亮）

---

## 🎯 成本计算

| 项目 | 成本 |
|------|------|
| 经过一站 | +1 |
| 换乘一次 | +2.5 |

**示例**：
- 罗湖 → 国贸 → 老街 = 2 站 = 成本 2
- 罗湖 → 国贸 → 老街(换乘) → 大剧院 = 3 站 + 1 换乘 = 成本 5.5

---

## ❌ 错误类型

| 错误 | 说明 | 示例 |
|------|------|------|
| 起点错误 | 路径起点不匹配 | 应该从"罗湖"开始，但你从"国贸"开始 |
| 终点错误 | 路径终点不匹配 | 应该到"世界之窗"，但你到了"大剧院" |
| 站点不存在 | 站点不在所选线路中 | "市民中心"不在1号线中 |
| 站点不相邻 | 两站之间没有直接连接 | "罗湖"和"世界之窗"不相邻 |
| 路径不是最短 | 成本高于最短路径 | 你的成本15.5，最短12.5 |

---

## 🔑 快捷操作

### 线路选择
- **全选**: 点击"全选"按钮
- **清空**: 点击"清空"按钮
- **单选**: 点击对应线路复选框

### 起终点设置
- **随机生成**: 点击"🎲 随机生成起终点"
- **手动输入**: 在输入框中输入站名
- **开始游戏**: 点击"▶️ 开始游戏"

### 路径输入
- **添加站点**: 输入站名后点击"添加"或按 Enter
- **删除站点**: 点击站点旁的"×"按钮
- **清空路径**: 点击"清空"按钮
- **提交答案**: 点击"提交答案"按钮

### 结果查看
- **查看答案**: 点击"👁️ 查看正确答案"（答错时）
- **再来一局**: 点击"🔄 再来一局"（保持线路和起终点）
- **返回首页**: 点击"🏠 返回首页"（重新开始）

---

## 📊 API 端点速查

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/lines` | 获取所有线路 |
| GET | `/api/lines/{line}/stations` | 获取线路站点 |
| GET | `/api/stations` | 获取所有站点 |
| POST | `/api/game/random-stations` | 随机生成起终点 |
| POST | `/api/game/calculate-path` | 计算最短路径 |
| POST | `/api/game/validate-path` | 验证用户路径 |

---

## 🎨 UI 状态

### 游戏状态
- **setup**: 初始状态，选择线路和起终点
- **playing**: 游戏中，输入路径
- **result**: 结果展示

### 视觉反馈
- 🟢 **绿色**: 答对了
- 🟡 **黄色**: 路径合法但不是最短
- 🔴 **红色**: 路径不合法
- 🟠 **橙色**: 换乘站标注

---

## 🔧 开发命令

### 后端
```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload

# 启动生产服务器
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端
```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

---

## 📁 项目结构速查

```
sz-metro/
├── backend/
│   ├── app/
│   │   ├── services/          # 业务逻辑
│   │   │   ├── metro_network.py    # 地铁网络
│   │   │   ├── path_finder.py      # 路径查找
│   │   │   └── path_validator.py   # 路径验证
│   │   ├── routers/
│   │   │   └── metro.py            # API 路由
│   │   ├── models.py               # 数据模型
│   │   └── main.py                 # 应用入口
│   └── lines.json                  # 地铁数据
│
├── frontend/
│   ├── src/
│   │   ├── components/        # Vue 组件
│   │   │   ├── LineSelector.vue      # 线路选择
│   │   │   ├── StationSelector.vue   # 起终点设置
│   │   │   ├── PathInput.vue         # 路径输入
│   │   │   └── GameResult.vue        # 结果展示
│   │   ├── stores/
│   │   │   └── game.js              # 状态管理
│   │   ├── services/
│   │   │   └── api.js               # API 封装
│   │   └── App.vue                  # 主应用
│   └── vite.config.js               # Vite 配置
│
└── 文档/
    ├── README.md                    # 项目说明
    ├── CHANGELOG.md                 # 开发日志
    ├── TESTING.md                   # 测试指南
    ├── OPTIMIZATION_SUMMARY.md      # 优化总结
    └── QUICK_REFERENCE.md           # 本文档
```

---

## 🐛 常见问题

### 1. 前端启动失败
**问题**: `Failed to load PostCSS config`
**解决**: 确保 `postcss.config.js` 使用 ES 模块语法（`export default`）

### 2. 后端无法连接
**问题**: 前端无法访问后端 API
**解决**: 检查后端是否在 8000 端口运行，检查 CORS 配置

### 3. 线路数据加载失败
**问题**: 无法读取 `lines.json`
**解决**: 确保 `backend/lines.json` 文件存在且格式正确

### 4. 路径验证失败
**问题**: 明明是正确的路径却提示错误
**解决**: 检查站点名称是否完全匹配（包括空格）

---

## 📞 获取帮助

- 📖 查看 [README.md](./README.md) 了解项目详情
- 🧪 查看 [TESTING.md](./TESTING.md) 了解测试方法
- 📊 查看 [OPTIMIZATION_SUMMARY.md](./OPTIMIZATION_SUMMARY.md) 了解优化内容
- 📝 查看 [CHANGELOG.md](./CHANGELOG.md) 了解开发历史
- 🔧 访问 http://localhost:8000/docs 查看 API 文档

---

## 🎉 快速提示

- 💡 **新手建议**: 先选择 1-2 条线路，从简单的起终点开始
- 🎯 **进阶挑战**: 选择多条线路，尝试需要换乘的路径
- 🚀 **高手模式**: 选择所有线路，挑战复杂的换乘路径
- 📊 **学习模式**: 先查看答案，学习最短路径的规律

---

**祝你游戏愉快！🎮**
