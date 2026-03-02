# 可观测性与追踪 (Observability & Tracing)

## 1. 追踪工具选型

为了全面监控 Agent 的执行过程和 AI 模型的调用情况，系统集成多层次的追踪方案：

| 追踪层级 | 选型工具 | 主要功能 | 优势 |
| :--- | :--- | :--- | :--- |
| **LLM 调用追踪** | **Langfuse** (主要) / LangSmith (备选) | 记录每次 LLM 调用的 Prompt、Response、Token 消耗、延迟、成本 | LLM 原生集成，中国可访问，支持本地部署 |
| **分布式追踪** | **OpenTelemetry + Jaeger** | 追踪请求跨多个服务的完整链路 | 开源、供应商无关、云原生 |
| **应用性能监控** | **Prometheus + Grafana** | 系统级别的指标收集和可视化（CPU、内存、GPU、吞吐量等） | 业界标准，与 K8s 深度集成 |
| **日志聚合** | **ELK Stack** (Elasticsearch + Logstash + Kibana) | 集中式日志收集、搜索、分析 | 功能完善，搜索能力强 |

## 2. 追踪架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (FastAPI)                      │
│  ┌────────────────────────────────────────────────────┐ │
│  │         LangGraph Agent 执行                       │ │
│  │  (Coordinator → Planner → Executor → Critic)      │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  追踪层 (Tracing Layer)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ LangSmith    │  │ Langfuse SDK │  │ OpenTelemetry│ │
│  │ Callback     │  │ Callback     │  │ Instrumentation  │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ↓                ↓                   ↓         │
│  ┌──────────────────────────────────────────────────┐ │
│  │    统一的 Tracing Context（ThreadLocal/AsyncLocal) │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│               数据收集与存储层                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Langfuse │  │  Jaeger  │  │Prometheus│  │ ELK    │ │
│  │ Backend  │  │ Backend  │  │ Backend  │  │        │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│               可视化与分析层                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Langfuse │  │ Jaeger UI│  │ Grafana  │  │ Kibana │ │
│  │ Dashboard│  │ UI       │  │ Dashboards  │        │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 3. 追踪指标体系

### 3.1 LLM 调用追踪（Langfuse）

**记录的关键指标**：
```python
class LLMCallTrace:
    # 调用标识
    trace_id: str  # 全局唯一追踪ID
    span_id: str   # 本次 LLM 调用的 Span ID
    parent_span_id: Optional[str]  # 父 Span ID
    
    # 模型信息
    model: str  # "gpt-4", "qwen-72b" 等
    provider: str  # "openai", "aliyun" 等
    
    # Prompt 相关
    prompt_template: str  # Prompt 模板
    input_variables: Dict[str, Any]  # 模板变量
    final_prompt: str  # 最终发送的 Prompt
    prompt_tokens: int  # Prompt token 数
    
    # Response 相关
    response: str  # 完整响应
    completion_tokens: int  # Completion token 数
    total_tokens: int  # 总 token 数
    
    # 性能指标
    start_time: datetime  # 调用开始时间
    end_time: datetime  # 调用结束时间
    latency_ms: float  # 总延迟（毫秒）
    
    # 成本计算
    cost_usd: float  # 本次调用的成本（美元）
    
    # 质量指标
    temperature: float  # 采样温度
    top_p: float  # Top-P 采样参数
    max_tokens: int  # 最大输出 token 数
    
    # 错误信息
    error: Optional[str]  # 错误信息（如有）
    error_type: Optional[str]  # 错误类型
```

### 3.2 工具调用追踪

**记录的关键指标**：
```python
class ToolCallTrace:
    # 工具信息
    tool_name: str  # "OCRTool", "VectorSearchTool" 等
    tool_version: str  # 工具版本
    
    # 输入
    input_args: Dict[str, Any]  # 工具输入参数
    input_size: int  # 输入大小（如文件大小、字符数）
    
    # 输出
    output: Any  # 工具输出
    output_size: int  # 输出大小
    output_format: str  # 输出格式（json、text 等）
    
    # 性能
    start_time: datetime
    end_time: datetime
    latency_ms: float  # 执行延迟
    
    # 资源消耗
    cpu_usage: float  # CPU 使用百分比
    memory_usage: float  # 内存使用（MB）
    gpu_memory: Optional[float]  # GPU 显存使用（MB）
    
    # 结果质量
    success: bool  # 是否成功
    error: Optional[str]  # 错误信息
    confidence: Optional[float]  # 置信度分数
```

### 3.3 Agent 执行追踪

**记录的关键指标**：
```python
class AgentExecutionTrace:
    # 任务信息
    task_id: str  # 任务全局唯一ID
    agent_name: str  # "Planner", "Executor", "Critic" 等
    
    # 执行过程
    state_before: Dict[str, Any]  # Agent 执行前的状态
    state_after: Dict[str, Any]  # Agent 执行后的状态
    actions_taken: List[str]  # 该 Agent 执行的操作列表
    
    # 性能
    start_time: datetime
    end_time: datetime
    total_duration_ms: float  # 总执行时间
    
    # 决策信息
    decision_reasoning: str  # Agent 的决策推理过程
    next_node: str  # 下一个要执行的 Node
    
    # 成本与资源
    total_llm_calls: int  # LLM 调用次数
    total_tokens_used: int  # 总 Token 消耗
    total_cost_usd: float  # 总成本
```

### 3.4 端到端请求追踪

**完整的请求生命周期追踪**：
```python
class RequestTrace:
    # 请求标识
    request_id: str  # 全局唯一请求ID
    trace_id: str  # 追踪ID（与 OpenTelemetry 对齐）
    session_id: str  # 用户会话ID
    user_id: str  # 用户ID
    
    # 请求信息
    request_type: str  # "upload", "query", "report" 等
    timestamp: datetime  # 请求时间
    
    # 执行链路
    graph_execution: Dict  # 完整的 LangGraph 执行记录
    {
        "total_duration_ms": 5000,
        "nodes_executed": [
            {"name": "Coordinator", "duration_ms": 100},
            {"name": "Planner", "duration_ms": 500},
            {"name": "Executor", "duration_ms": 3500},
            {"name": "Critic", "duration_ms": 500},
            {"name": "Writer", "duration_ms": 400}
        ],
        "edges_traversed": [
            {"from": "Coordinator", "to": "Planner"},
            {"from": "Planner", "to": "Executor"},
            {"from": "Executor", "to": "Critic"},
            {"from": "Critic", "to": "Writer"}
        ]
    }
    
    # 资源消耗
    total_tokens: int
    total_cost_usd: float
    peak_memory_mb: float
    
    # 质量指标
    success: bool
    final_confidence: float
    
    # 错误追踪
    errors: List[Dict]  # 执行过程中发生的所有错误
```

## 4. 集成实现方案

### 4.1 Langfuse 集成（LLM 调用追踪）

```python
# 在 FastAPI 应用启动时初始化
from langfuse import Langfuse

langfuse_client = Langfuse(
    public_key="pk_...",
    secret_key="sk_...",
    host="https://cloud.langfuse.com"  # 或本地部署地址
)

# 在 LangChain 中使用 Callback
from langfuse.callback import CallbackHandler

callback_handler = CallbackHandler(
    user_id="user_123",
    session_id="session_456",
    public_key="pk_...",
    secret_key="sk_..."
)

# 在 LLM 调用时传入 callback
response = llm.invoke(
    prompt,
    callbacks=[callback_handler]
)
```

### 4.2 OpenTelemetry 集成（分布式追踪）

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# 初始化 Jaeger Exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

# 配置 Tracer Provider
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# 在应用中使用
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_document") as span:
    span.set_attribute("document_id", doc_id)
    span.set_attribute("user_id", user_id)
    
    # 执行业务逻辑
    result = await process_document(doc_id)
    
    span.set_attribute("result_confidence", result["confidence"])
```

### 4.3 Prometheus 监控集成

```python
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
llm_calls_total = Counter(
    'llm_calls_total',
    'Total number of LLM calls',
    ['model', 'status']
)

llm_latency = Histogram(
    'llm_latency_seconds',
    'LLM call latency',
    ['model'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
)

llm_tokens = Counter(
    'llm_tokens_total',
    'Total tokens used',
    ['model', 'type']  # type: prompt, completion, total
)

# 在 Agent 执行时收集指标
llm_calls_total.labels(model="qwen-72b", status="success").inc()
llm_latency.labels(model="qwen-72b").observe(latency_seconds)
llm_tokens.labels(model="qwen-72b", type="prompt").inc(prompt_tokens)
```

## 5. 可视化与分析

### 5.1 Langfuse Dashboard

Langfuse 提供内置的 Web Dashboard，可以：
- **实时监控**：查看正在执行的 LLM 调用
- **成本分析**：按模型、用户、日期维度聚合成本
- **性能分析**：追踪延迟、Token 使用趋势
- **错误追踪**：快速定位和分析错误
- **用户行为**：分析用户的查询模式

### 5.2 Jaeger UI

查看分布式追踪的完整链路：
- **服务拓扑**：可视化微服务之间的调用关系
- **跨度分析**：分析单个请求的完整执行路径
- **性能瓶颈**：识别慢查询和瓶颈服务

### 5.3 Grafana Dashboards

自定义仪表板展示关键指标：
- **系统健康度**：CPU、内存、GPU 使用率
- **吞吐量与延迟**：P50, P95, P99 延迟分布
- **成本追踪**：实时 Token 和 API 成本统计
- **模型性能对比**：不同模型的准确率、成本对比

## 6. 追踪数据的应用场景

### 6.1 成本优化

通过追踪数据识别：
- 哪些任务消耗 Token 最多？可以优化 Prompt？
- 哪些模型的成本效益比最优？应该默认选用哪个模型？
- 是否存在重复的 API 调用可以通过缓存优化？

### 6.2 性能优化

通过追踪数据识别：
- 哪个 Agent Node 的执行时间最长？是否存在瓶颈？
- 重试次数是否过多？是否应该调整快速失败阈值？
- GPU 利用率是否充分？是否需要增加并发？

### 6.3 质量监控

通过追踪数据监控：
- 识别识别准确率下降的模式（如特定文档类型）
- 追踪人工复核率的变化趋势
- 分析不同模型的置信度分布

### 6.4 故障诊断

通过追踪数据快速定位：
- 特定用户的请求为什么失败？
- 特定时段的错误率为什么升高？
- 集成的第三方服务是否存在问题？

## 7. 部署与配置

### 7.1 Docker Compose 部署

```yaml
version: '3.8'

services:
  # Jaeger 全栈（All-in-One）
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "6831:6831/udp"  # Jaeger agent
      - "16686:16686"    # Jaeger UI
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

  # Langfuse (可选本地部署)
  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3001:3000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/langfuse
      - NEXTAUTH_SECRET=your-secret

volumes:
  prometheus_data:
  grafana_data:
```

### 7.2 应用配置

```python
# config/observability.py
from pydantic import BaseSettings

class ObservabilityConfig(BaseSettings):
    # Langfuse 配置
    langfuse_enabled: bool = True
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str = "https://cloud.langfuse.com"
    
    # Jaeger 配置
    jaeger_enabled: bool = True
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831
    
    # Prometheus 配置
    prometheus_enabled: bool = True
    prometheus_port: int = 8000
    
    # 采样率
    trace_sample_rate: float = 1.0  # 100% 采样
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

## 8. 最佳实践

1. **结构化日志**：使用 JSON 格式的结构化日志，便于 ELK 分析
2. **标准化追踪 ID**：确保所有日志和追踪数据都包含统一的 `trace_id`
3. **关键路径追踪**：优先追踪关键业务路径（如 LLM 调用）
4. **隐私保护**：脱敏敏感数据（如用户输入、API 密钥）再发送到追踪系统
5. **告警规则**：基于追踪数据设定告警（如错误率、延迟超过阈值）
6. **定期审查**：定期审查追踪数据，识别优化机会
