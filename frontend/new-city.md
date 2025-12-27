# 添加新城市指南

## 概述
本指南说明如何向地铁寻路应用添加新城市。

## 前置条件

### 1. 数据文件准备
确保以下数据文件已准备好：

**后端数据文件**（位于 `backend/` 目录）：
- `stations_coordinates_{city_code}.json` - 城市地铁站点坐标数据
  - 必须包含 `stations` 和 `lines` 两个主要字段
  - 每个站点包含：`x`, `y` 坐标，`lines` 线路数组
  - 每条线路包含：`color`（颜色），`stations`（站点数组），可选 `is_loop`（是否环线）

**前端 Logo 文件**（位于 `frontend/src/assets/` 目录）：
- `{city_code}-logo.svg` 或 `.png` - 城市标识图标
  - 支持 SVG 或 PNG 格式（PNG 需要透明底）
  - 建议尺寸：约 5x5（显示）到 10x10（标题）像素

### 2. 城市代码约定
使用城市拼音首字母作为城市代码：
- 深圳：sz
- 上海：sh
- 北京：bj
- 广州：gz
- 武汉：wh
- 长沙：cs

## 修改步骤

### 步骤 1：修改前端文件

#### 1.1 `frontend/src/App.vue`

**添加 Logo 导入**：
```javascript
// 在 import 区域添加（约第 119-123 行）
import {cityCode}Logo from '@/assets/{city_code}-logo.{ext}'
```

**更新城市数据**（约第 140-155 行）：
```javascript
const cityKeys = ['sz', 'sh', 'bj', 'gz', 'wh', 'cs', '{city_code}']
const cityNames = {
  // ... 现有城市 ...
  '{city_code}': '{城市中文名}'
}
const cityLogos = {
  // ... 现有城市 ...
  '{city_code}': {cityCode}Logo
}
```

**注意**：将新城市代码插入到适当的位置，保持城市顺序合理。

#### 1.2 `frontend/src/stores/game.js`

**添加城市配置**（约第 5-30 行的 CITY_CONFIG 对象）：
```javascript
const CITY_CONFIG = {
  // ... 现有城市 ...
  '{city_code}': {
    name: '{城市中文名}',
    title: '{城市中文名}地铁寻路挑战',
    subtitle: '找出两个站点之间的最短路径',
  }
}
```

#### 1.3 `frontend/src/main.js`

**添加路由配置**（约第 8-41 行的 routes 数组）：
```javascript
routes: [
  // ... 现有路由 ...
  {
    path: '/{city_code}',
    component: App,
    props: { city: '{city_code}' }
  },
  // ... 其他路由 ...
]
```

### 步骤 2：修改后端文件

#### 2.1 `backend/app/routers/metro.py`

**更新数据文件映射**（约第 22-37 行）：
```python
CITY_DATA_FILES = {
    # ... 现有城市 ...
    "{city_code}": "stations_coordinates_{city_code}.json",   # {English Name}
}

CITY_NAMES = {
    # ... 现有城市 ...
    "{city_code}": "{城市中文名}",
}
```

#### 2.2 `backend/app/main.py`

**更新 API 信息**（约第 5-9 行）：
```python
app = FastAPI(
    title="地铁寻路游戏 API",
    description="地铁最短路径查找和验证 API（支持深圳、上海、北京、广州、武汉、长沙、{城市中文名}）",
    version="1.3.0"
)
```

**更新支持的城市列表**（约第 23-30 行）：
```python
@app.get("/")
async def root():
    return {
        "message": "地铁寻路游戏 API",
        "docs": "/docs",
        "version": "1.3.0",
        "supported_cities": ["sz", "sh", "bj", "gz", "wh", "cs", "{city_code}"]
    }
```
