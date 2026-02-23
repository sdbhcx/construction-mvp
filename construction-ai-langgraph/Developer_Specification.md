# 🏗️ 施工记录智能识别系统 - 开发者规格说明书 (Developer Specification)

## 1. 项目概述

本作为**施工记录智能识别系统**的开发者文档，旨在指导开发团队构建一个基于 **LangGraph + AI Components** 的智能体系统。该系统旨在将非结构化的施工文档（图片、PDF、扫描件）转化为结构化数据，并提供智能查询与分析能力。

本项目已从早期的“固定流水线”架构升级为**自主智能体（Agentic）架构**。系统不再机械地执行 OCR -> NER -> ETL 流程，而是引入了**感知-推理-行动-反思**的决策回路，能够根据文档的复杂度和质量，动态规划处理路径，自我修正错误，并随着使用积累长期记忆。

## 2. 核心特点

1.  **动态决策回路 (Dynamic Decision Loop)**:
    *   通过 `Planner Agent` 动态生成执行计划，而非硬编码流程。
    *   引入 `Critic Agent` 进行结果反思与质量把控，不合格结果会自动触发重试或人工复核。

2.  **多模态融合 (Multi-modal Fusion)**:
    *   结合 OCR (PaddleOCR)、VLM (Qwen-VL) 和 NLP (Qwen-72B) 能力。
    *   支持对文本、表格、手写体、印章等复杂元素的混合识别。

3.  **记忆与持续进化 (Memory & Evolution)**:
    *   **短期记忆**: 维护当前任务的上下文与中间变量。
    *   **长期记忆**: 基于向量数据库 (Milvus/Qdrant) 存储历史成功案例 (Few-shot)，使系统越用越聪明。

4.  **企业级护栏 (Enterprise Guardrails)**:
    *   内置 **策略引擎 (Policy Engine)**，在模型调用前进行预算控制、敏感数据脱敏和合规性检查。
    *   **统一状态管理 (State Store)**，确保分布式环境下的状态一致性与可追溯性。

## 3. 技术选型与理由

### 3.1 核心框架

| 环节 | 选型 | 理由 |
| :--- | :--- | :--- |
| **语言** | Python 3.10+ | AI 生态首选，强类型的支持 (Pydantic) 对构建复杂系统至关重要。 |
| **编排** | **LangGraph** | 相比 LangChain Chain，LangGraph 的图结构原生支持循环（Loop）、分支和状态持久化，完美契合 Agent 的反复推理需求。 |
| **Web** | FastAPI | 高性能异步框架，原生支持 WebSocket (流式输出) 和 OpenAPI 文档生成。 |

### 3.2 AI 模型组件

| 环节 | 选型 | 理由 |
| :--- | :--- | :--- |
| **OCR** | **PaddleOCR v4** | 针对中文场景优化最佳的开源 OCR，支持方向检测和表格结构还原。 |
| **VLM** | **Qwen-VL-Chat** | 通义千问视觉大模型，在中文文档理解（DocVQA）和表格解析上表现优异，且支持本地部署。 |
| **LLM** | **Qwen-72B / GPT-4** | 推理能力强，适合承担 Planner 和 Critic 的逻辑判断角色。 |
| **Embedding** | **BGE-M3** | 多语言、长文本支持极佳的 Embedding 模型，用于向量检索。 |

### 3.3 数据与基础设施

| 环节 | 选型 | 理由 |
| :--- | :--- | :--- |
| **Vector DB** | **Milvus / Qdrant** | 专为向量检索设计，支持海量数据低延迟查询，用于长期记忆库。 |
| **State Store** | **Redis** | 高性能 KV 存储，用于维护 Agent 的瞬时状态 (State Snapshot) 和消息队列。 |
| **Graph DB** | **Neo4j** (可选) | 用于存储项目-人员-文档的实体关系网，辅助推理。 |
| **Container** | Docker + K8s | 标准化交付，便于 GPU 资源的调度与扩缩容。 |

## 4. 系统架构与模块设计

系统采用 **“大脑-身体-工具”** 分层架构：

### 4.1 核心模块 (`src/`)

```text
src/
├── agents/             # [大脑] 智能体逻辑
│   ├── coordinator.py  # 总控：任务分发与预算控制
│   ├── planner.py      # 规划：生成 DAG 执行计划 (ReAct/Plan-and-Solve)
│   ├── executor.py     # 执行：调度工具，处理异常
│   ├── critic.py       # 反思：结果校验，质量打分
│   └── writer.py       # 写作：报表与文档生成
├── core/               # [神经系统] 基础设施
│   ├── state.py        # 统一状态定义 (TaskState)
│   ├── memory.py       # 记忆管理 (Short/Long-term)
│   └── policy.py       # 策略引擎 (Budget, Guardrails)
├── tools/              # [手] 原子能力封装
│   ├── vision/         # OCRTool, VLMTool
│   ├── data/           # SQLTool, VectorSearchTool
│   └── file/           # PDFParser, ExcelWriter
└── schemas/            # 数据协议 (Pydantic Models)
```

### 4.2 关键交互流程

1.  **感知 (Input)**: 如果是复杂 PDF，先通过 Layout Analysis 拆解。
2.  **记忆 (Recall)**: Planner 根据任务目标，从 Memory Store 检索“相似文档的处理经验”。
3.  **规划 (Plan)**: 生成初步步骤，例如 `[OCR -> 表格提取 -> 规则校验]`。
4.  **行动 (Act)**: Executor 依次调用工具。每次调用前，Policy Engine 检查预算。
5.  **反思 (Critique)**: Critic 检查提取结果。如果置信度低，指示 Planner 插入“人工复核”或“切换模型”步骤。

### 4.3 智能体角色详解

#### 4.3.1 Coordinator Agent (总控智能体)
**职责**: 类似于交响乐团的指挥或公司的项目经理。它不直接干活（不跑 OCR，不写 SQL），而是负责**接待、分诊、风控和兜底**。

**核心功能**:
1.  **意图识别与路由**: 基于用户指令和输入类型，将任务分发至不同流水线：
    *   **Extraction Routing (单据提取)**: 处理上传的图片/PDF，目标是结构化入库。
    *   **QA Routing (智能问答)**: 处理自然语言提问（如“查询某工地隐患”），目标是检索并生成答案。
    *   **Report Routing (报表生成)**: 处理复杂聚合请求（如“生成本月安全隐患周报”）。Coordinator 会启动一个并行工作流：
        *   调用 `SQLTool` 统计隐患数量与类型分布。
        *   调用 `VectorSearchTool` 检索典型隐患照片。
        *   最后由 `Writer Agent` 汇总生成图文并茂的 PDF/Markdown 报告。
    *   **Command Routing (系统指令)**: 处理运维与配置类指令（如“将阈值调整为0.8”或“清除OCR缓存”）。Coordinator 会进行严格的**权限校验**，直接调用 `SystemTool` 或 `AdminAPI` 执行操作，并记录审计日志。
2.  **资源与权限门禁**: 检查用户是否有权操作该项目，项目余额是否由足，预估任务复杂度。
3.  **异常熔断与降级**: 当子 Agent（如 Planner）陷入死循环或耗时过长时，强制介入终止，并返回友好的降级回复。
4.  **人机交互管理**: 决定何时打断流程请求人工确认（Human-in-the-loop）。

**交互示例**:

> **场景**: 用户上传了一份模糊的《2026年2月施工现场隐患排查表.jpg》，并备注“急需提取隐患项”。

1.  **接收请求**: Coordinator 收到图片和 Prompt。
2.  **前置检查 (Pre-check)**:
    *   *Policy Check*: 用户是“项目经理”，权限通过。
    *   *Budget Check*: 图片预估 Token 消耗 0.05 USD，项目余额充足。
3.  **意图路由 (Routing)**:
    *   识别为 `Extraction Task`（提取任务）。
    *   而不是 `QA Task`（检索任务）或 `Report Task`（报表）。
    *   初始化 `TaskState`，标记 `priority=High`（因为用户说了“急需”）。
4.  **委托 (Delegate)**: 将状态传递给 `Planner Agent`，指令：“处理这个图片，专注提取隐患项”。
5.  **监控 (Monitor)**:
    *   如果 `Planner` 反馈图片太模糊无法处理，`Coordinator` 不会直接崩溃，而是请求用户：“图片清晰度不足，请重新上传或手动输入关键信息”。

#### 4.3.2 Writer Agent (文书智能体)
**职责**: 专注于“输出表达”。将结构化数据、图片和分析结论转化为人类可读的高质量文档（如周报 HTML、PDF 或 Markdown 摘要）。

**核心功能**:
1.  **数据可视化**: 调用绘图工具（Matplotlib/Echarts）将统计数据转化为图表。
2.  **排版渲染**: 根据模板（Jinja2）生成标准格式的报告。
3.  **摘要生成**: 对长篇幅的施工日志进行润色和总结。

## 5. 测试方案

### 5.1 单元测试 (Unit Test)
*   **工具层**: 针对 `OCRTool`、`SQLTool` 编写 Mock 测试，验证输入输出格式的一致性。
*   **逻辑层**: 测试 `PolicyEngine` 的拦截逻辑（如超过预算是否报错）。

### 5.2 集成测试 (Integration Test)
*   **模拟回路**: 构造虚拟的 Tool Output，测试 `Planner -> Executor -> Critic` 的状态流转是否闭环。
*   **并发测试**: 使用 `Locust` 模拟 50+ 并发请求，验证 Redis 状态锁和消息队列的稳定性。

### 5.3 评估测试 (Evals)
*   建立 **Golden Dataset**（包含 100 份标注好的典型施工文档）。
*   主要指标：
    *   **字段准确率**: 提取字段与真值的匹配度。
    *   **Planner 成功率**: 生成的计划是否逻辑通顺且可执行。
    *   **幻觉率**: Critic 是否能识别出模型编造的数据。

## 6. 项目排期与跟踪

### 阶段一：基础设施与工具化 (Week 1-2)
*目标：完成基础组件封装，实现工具的标准化调用。*

| 任务编号 | 任务名称 | 状态 | 完成日期 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| T1-01 | **环境搭建** | To Do | 2026-02-25 | 初始化 Poetry, Docker, Pre-commit |
| T1-02 | **状态定义 (State Schema)** | To Do | 2026-02-26 | 定义 `TaskState` 和 `PlanStep` |
| T1-03 | **工具封装: OCR/VLM** | To Do | 2026-02-28 | 封装 PaddleOCR/Qwen-VL 为 LangChain Tool |
| T1-04 | **工具封装: Storage** | To Do | 2026-03-01 | 封装 MinIO 和 PostgreSQL 交互 |

### 阶段二：智能体核心逻辑 (Week 3-4)
*目标：实现 Planner/Executor/Critic 三大核心智能体。*

| 任务编号 | 任务名称 | 状态 | 完成日期 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| T2-01 | **Planner Agent 开发** | To Do | 2026-03-05 | 实现基于 LLM 的计划生成 |
| T2-02 | **Executor Agent 开发** | To Do | 2026-03-08 | 实现工具调度与错误重试 |
| T2-03 | **Critic Agent 开发** | To Do | 2026-03-12 | 实现基于规则+LLM 的评分逻辑 |
| T2-04 | **LangGraph 流程编排** | To Do | 2026-03-15 | 串联 Agent，跑通“即使”循环 |

### 阶段三：记忆与策略 (Week 5)
*目标：引入长期记忆与策略控制，提升系统稳健性。*

| 任务编号 | 任务名称 | 状态 | 完成日期 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| T3-01 | **Policy Engine 实现** | To Do | 2026-03-18 | 预算控制、敏感词过滤 |
| T3-02 | **Memory Store 集成** | To Do | 2026-03-21 | 接入 Milvus，实现 RAG 检索 |
| T3-03 | **Prompt 调优** | To Do | 2026-03-23 | 优化 Few-shot 效果 |

### 阶段四：联调与交付 (Week 6)
*目标：端到端测试，性能优化与文档交付。*

| 任务编号 | 任务名称 | 状态 | 完成日期 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| T4-01 | **Evals 数据集构建** | To Do | 2026-03-25 | 准备 Golden Data |
| T4-02 | **性能压测** | To Do | 2026-03-28 | 优化并发吞吐量 |
| T4-03 | **UI 对接** | To Do | 2026-03-31 | 前端展示 Trace 和中间状态 |

## 7. 可扩展性与未来展望

### 7.1 可扩展性设计
*   **工具热插拔**: 新增工具（如“工程图纸CAD解析”）不仅需要编写代码，只需在 `ToolRegistry` 并更新 `tools_description`，Planner 即可感知并使用。
*   **多模型路由**: 支持通过配置切换底层 LLM（如从 Qwen-72B 切换到 GPT-4o），以适应不同成本/精度需求的任务。

### 7.2 未来规划
*   **多智能体协作 (MARL)**: 引入“专家会诊”模式，让结构工程师Agent、预算员Agent共同审核一份复杂文档。
*   **端侧轻量化**: 将 OCR 和轻量级 VLM 蒸馏后部署在边缘设备（如施工现场的手持终端），实现离线初步识别。
*   **主动学习 (Active Learning)**: 将人工修正后的数据自动加入训练集，定期微调 LoRA 模型，实现“越用越懂业务”。
