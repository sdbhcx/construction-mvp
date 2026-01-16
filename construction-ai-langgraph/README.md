# 🏗️ 施工记录AI服务 - LangChain + LangGraph实现

## 📋 概述

这是一个基于**LangChain**和**LangGraph**构建的现代施工记录AI服务，采用 **智能体（Agent）** 架构，将复杂的施工记录处理任务分解为多个专业化的工作节点，实现**模块化、可观察、可扩展**的多模态处理流水线。

## 🎯 架构优势

* **🧠 智能体协作** ：多个智能体协同工作，各司其职
* **🔄 可视化工作流** ：Graph可视化，易于调试和监控
* **🔧 模块化设计** ：可插拔组件，便于扩展和替换
* **📊 完整可观察性** ：每个步骤都有详细日志和指标
* **⚡ 并行处理** ：支持异步和并发处理

## 🏗️ 系统架构

### 场景一：用户上传新施工记录（自动识别流程）
用户请求（上传图片/PDF）
    ↓
智能体调度器 (Orchestrator)
    ↓
└── 信息抽取智能体 (Information Extraction Agent)
    ├── OCR节点 - 提取文档中所有文本及位置
    ├── 领域NER节点 - 快速从OCR文本中抽取初步实体
    ├── 多模态VLM节点 - 结合原始图片和NER结果进行校验、补全和精炼
    ├── 数据存储节点 - 将JSON结果存入临时数据库
    └── 人工复核节点 - 推送至人工复核队列
        ↓
    复核通过后 → 结构化业务数据库 + 向量数据库索引

### 场景二：用户进行对话查询
用户请求（自然语言提问）
    ↓
智能体调度器 (Orchestrator)
    ↓
└── 问答与查询智能体 (QA Query Agent)
    ├── 意图识别与工具规划节点 - LLM分析问题，判断需要调用哪些工具
    ├── SQL查询节点 - 生成并执行SQL查询
    ├── 向量检索节点 - 在向量库中进行相似性检索
    └── 答案合成节点 - 将结构化数据和文本片段组织成自然语言回答

## 📁 项目结构

construction-ai-langgraph/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py              # 调度器智能体
│   │   ├── information_extraction_agent.py # 信息抽取智能体
│   │   └── qa_query_agent.py            # 问答与查询智能体
│   │
│   ├── graphs/
│   │   ├── __init__.py
│   │   ├── construction_graph.py         # 主工作流图
│   │   ├── information_extraction_graph.py # 信息抽取子图
│   │   └── qa_query_graph.py           # 问答查询子图
│   │
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── input_nodes.py               # 输入处理节点
│   │   ├── ocr_nodes.py                # OCR处理节点
│   │   ├── vlm_nodes.py                # VLM处理节点
│   │   ├── ner_nodes.py                # NER处理节点
│   │   ├── sql_query_nodes.py          # SQL查询节点
│   │   ├── vector_search_nodes.py       # 向量检索节点
│   │   ├── answer_synthesis_nodes.py    # 答案合成节点
│   │   ├── data_storage_nodes.py       # 数据存储节点
│   │   ├── review_nodes.py             # 人工复核节点
│   │   └── output_nodes.py            # 输出节点
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── ocr_tools.py                # OCR工具
│   │   ├── vlm_tools.py                # VLM工具
│   │   ├── ner_tools.py                # NER工具
│   │   ├── sql_tools.py               # SQL查询工具
│   │   ├── vector_tools.py            # 向量检索工具
│   │   └── cache_tools.py            # 缓存工具
│   │
│   ├── chains/
│   │   ├── __init__.py
│   │   ├── extraction_chain.py        # 信息抽取链
│   │   ├── query_chain.py             # 查询处理链
│   │   └── formatting_chain.py        # 格式化链
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── state.py                   # 图状态定义
│   │   ├── messages.py                # 消息定义
│   │   ├── documents.py               # 文档结构
│   │   └── construction_records.py    # 施工记录结构
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── vector_store.py            # 向量存储
│   │   ├── cache_manager.py           # 缓存管理
│   │   └── history_manager.py         # 历史管理
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── metrics.py
│   │   ├── image_utils.py
│   │   └── pdf_utils.py
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py                    # FastAPI应用
│       └── config.py                  # 配置管理
│
├── configs/
│   ├── graph_config.yaml               # 图配置
│   ├── agent_config.yaml               # 智能体配置
│   └── model_config.yaml               # 模型配置
│
├── tests/
│   └── test_graphs.py                # 图测试
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装核心依赖
pip install langchain langgraph langchain-community langchain-openai
pip install paddleocr paddlepaddle
pip install fastapi uvicorn

# 安装其他依赖
pip install -r requirements.txt
```

### 2. 环境配置

```bash
cp .env.example .env
# 编辑.env文件，设置API密钥
```

### 3. 启动服务

```bash
# 开发模式
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload

# 或使用脚本
python scripts/start_server.py
```

## 🎯 优势特点

### 1. **模块化架构**

* 每个处理步骤都是独立的节点
* 可以轻松替换或添加新的处理模块
* 支持A/B测试不同的算法实现

### 2. **可观察性**

* 每个节点都有完整的日志
* 可以跟踪数据的流动路径
* 支持性能指标收集

### 3. **智能路由**

* 根据文档类型自动选择处理路径
* 支持条件分支和循环
* 可以处理异常和重试

### 4. **易于扩展**

* 添加新节点只需要实现节点函数
* 支持自定义工具和智能体
* 可以集成外部服务

### 5. **生产就绪**

* 完整的错误处理
* 支持缓存和重试
* 监控和健康检查
* Docker容器化部署

## 📊 业务流程

### 场景一：施工记录自动识别

1. **用户上传**：通过Web界面上传图片或PDF文件
2. **智能调度**：智能体调度中心接收任务，启动信息抽取智能体
3. **OCR识别**：调用OCR服务，提取文档中所有文本及位置
4. **实体抽取**：调用领域NER模型，快速从OCR文本中抽取初步实体
5. **VLM精炼**：将原始图片和NER结果输入微调后的VLM，进行校验、补全和精炼
6. **临时存储**：将JSON结果存入临时数据库，并推送至人工复核队列
7. **人工复核**：复核通过后，数据进入结构化业务数据库
8. **向量索引**：原始文本和关键信息被索引到向量数据库

### 场景二：智能对话查询

1. **用户提问**：用户在聊天框提问，如"上个月B区有哪些安全隐患？"
2. **意图识别**：智能体调度中心启动问答与查询智能体，进行意图识别与工具规划
3. **SQL查询**：根据意图生成SQL查询，获取结构化数据
4. **向量检索**：如需要，在向量库中进行相似性检索，补充更多细节
5. **答案合成**：LLM将工具返回的结构化数据和文本片段，组织成自然语言回答
6. **返回结果**：将答案返回给用户，并可附上相关图片链接
