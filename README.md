# 基于 A2A 协议的天气查询代理
本示例展示了一个使用 A2A 协议构建的天气查询代理。它支持多轮对话交互和流式响应，为用户提供实时的天气信息查询服务。

## 工作原理
该代理通过高德地图 API 提供天气信息查询服务。A2A 协议使客户端能够以标准化的方式与代理交互，发送请求并接收实时更新。

```mermaid
sequenceDiagram
    participant Client as A2A 客户端
    participant Server as A2A 服务器
    participant Agent as 天气查询代理
    participant LLM as DeepSeek LLM
    participant API as 高德地图 API

    Client->>Server: 发送带有天气查询的任务
    Server->>Agent: 将查询转发给天气代理
    
    Agent->>LLM: 分析用户查询意图

    alt 完整信息
        LLM->>Agent: 确认信息完整
        Agent->>API: 调用天气查询工具
        API->>Agent: 返回天气数据
        Agent->>LLM: 处理天气数据
        LLM->>Agent: 生成天气回复
        Agent->>Server: 处理数据并返回结果
        Server->>Client: 响应天气信息
    else 不完整信息
        LLM->>Agent: 指出信息不完整
        Agent->>Server: 请求额外输入
        Server->>Client: 状态设置为"需要输入"
        Client->>Server: 发送额外信息
        Server->>Agent: 转发额外信息
        Agent->>LLM: 再次分析用户意图
        LLM->>Agent: 确认信息完整
        Agent->>API: 调用天气查询工具
        API->>Agent: 返回天气数据
        Agent->>LLM: 处理天气数据
        LLM->>Agent: 生成天气回复
        Agent->>Server: 处理数据并返回结果
        Server->>Client: 响应天气信息
    end

    alt 流式响应
        Note over Client,Server: 实时状态更新
        Server->>Client: "正在查询天气信息..."
        Server->>Client: "正在处理天气数据..."
        Server->>Client: 最终结果
    end
```
## 主要特点
- 多轮对话 : 代理可以在需要时请求额外信息
- 实时流式响应 : 在处理过程中提供状态更新
- 推送通知 : 支持基于 webhook 的通知
- 对话记忆 : 在交互过程中维持上下文
- 天气查询工具 : 集成高德地图 API 获取实时天气数据

## 前提条件
- Python 3.13 或更高版本
- UV
- 高德地图 API 密钥