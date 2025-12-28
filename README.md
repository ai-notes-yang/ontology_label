# 本体数据标注平台

用于检查和标注招聘业务中本体建设过程中每一步输出的数据内容的标注平台。

## 功能特点

- **多步骤支持**: 支持数据清洗、原子意图拆解、Object建模、Action建模、三元组创建五个步骤
- **当前已实现**: 原子意图拆解步骤的完整功能
- **核对功能**: 支持通过、需修改、删除、待定四种核对结果
- **分页浏览**: 支持自定义每页显示数量，快速翻页和页码跳转
- **文件管理**: 支持上传、查看、删除JSON文件

## 技术栈

### 后端
- Python 3.8+
- Flask 3.0
- SQLite
- Flask-SQLAlchemy

### 前端
- React 18
- Axios
- CSS3 (自定义主题)

## 项目结构

```
ontology_review_system/
├── backend/
│   ├── app.py           # Flask主应用
│   ├── config.py        # 配置文件
│   ├── models.py        # 数据库模型
│   ├── logger.py        # 日志配置
│   ├── uploads/         # 上传文件存储
│   ├── logs/            # 日志文件
│   │   └── app.log      # 应用日志
│   └── data/            # SQLite数据库
│       └── ontology_review.db
├── frontend/
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── App.js       # 主组件
│       ├── App.css      # 样式文件
│       ├── index.js
│       └── index.css
├── requirements.txt     # Python依赖
├── start.sh            # 启动脚本
└── README.md
```

## 快速开始

### 方式一：使用启动脚本 (推荐)

```bash
chmod +x start.sh
./start.sh
```

### 方式二：手动启动

#### 1. 启动后端

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建必要目录
mkdir -p backend/uploads backend/logs backend/data

# 启动后端服务
cd backend
python app.py
```

后端服务将在 http://localhost:5001 启动

#### 2. 启动前端

```bash
cd frontend
npm install
npm start
```

前端服务将在 http://localhost:3000 启动

## API 接口

### 步骤类型
- `GET /api/step-types` - 获取所有步骤类型

### 文件管理
- `GET /api/files` - 获取已上传文件列表
- `POST /api/upload` - 上传JSON文件
- `DELETE /api/files/<id>` - 删除文件
- `GET /api/files/<id>/export` - 导出核对后的文件

### 意图管理
- `GET /api/intents` - 获取意图列表（分页）
- `GET /api/intents/<id>` - 获取意图详情
- `POST /api/intents/<id>/review` - 提交核对结果
- `POST /api/intents/<id>/pass` - 直接通过

## JSON文件格式

上传的JSON文件应符合以下格式：

```json
{
  "metadata": {
    "source_file": "文件名.json",
    "created_at": "2024-12-23",
    "total_items": 60,
    "judgement_options": ["通过", "需修改", "删除", "待定"]
  },
  "Stage_1_xxx": [
    {
      "id": "INT-S1-001",
      "category": "Fact",
      "original_comment": "意图描述内容",
      "judgement": "",
      "judged_by": "",
      "modified_content": "",
      "judge_date": ""
    }
  ]
}
```

## 日志

应用日志保存在 `backend/logs/app.log`，记录所有操作和错误信息，便于调试问题。

## 许可证

MIT License

