from agent.gateway_agent import GatewayAgent, CONFIG

# 创建GatewayAgent实例，传入配置
agent = GatewayAgent(CONFIG)

# 启动服务
agent.start()