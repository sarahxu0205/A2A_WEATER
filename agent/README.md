# 天气查询服务器
基于 A2A 协议的天气查询代理，支持多轮对话交互和流式响应，为用户提供实时的天气信息查询服务。

## 工作原理
该代理通过高德地图 API 提供天气信息查询服务。A2A 协议使客户端能够以标准化的方式与代理交互，发送请求并接收实时更新。

## 主要特点
- 多轮对话 ：代理可以在需要时请求额外信息
- 实时流式响应 ：在处理过程中提供状态更新
- 推送通知 ：支持基于 webhook 的通知
- 对话记忆 ：在交互过程中维持上下文
- 天气查询工具 ：集成高德地图 API 获取实时天气数据
- 大语言模型 ：使用 DeepSeek LLM 作为核心推理引擎，提供智能对话能力

## 前提条件
- Python 3.12 或更高版本
- UV 包管理工具
- 高德地图 API 密钥（需要设置为环境变量 AMAP_API_KEY ）
- DeepSeek API 密钥（如果使用 DeepSeek 云服务，需要设置为环境变量 DEEPSEEK_API_KEY）

## 安装依赖
使用 UV 安装项目依赖：

```bash
cd agent
uv pip install -e .
 ```

## 运行天气查询服务器
1. 首先，确保设置了高德地图 API 密钥环境变量：
export AMAP_API_KEY="您的高德地图API密钥"

2. 启动服务器：
cd agent
python -m agent --host localhost --port 10000

默认情况下，服务器将在 localhost:10000 上运行。

## API 使用
服务器启动后，可以通过以下端点访问：

- 代理卡片信息： GET http://localhost:10000/
- 发送任务： POST http://localhost:10000/
- 流式响应： POST http://localhost:10000/

## 示例查询
服务器支持以下类型的天气查询：
- "北京今天的天气怎么样"
- "上海明天的天气预报"
- "广州未来三天会下雨吗"

## 项目结构
- agent.py ：天气查询代理的核心实现，集成 DeepSeek LLM 模型
- task_manager.py ：处理任务请求和响应
- __main__.py ：服务器启动入口