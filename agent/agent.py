from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, ToolMessage
import httpx
from typing import Any, Dict, AsyncIterable, Literal
from pydantic import BaseModel
import os
#from langchain_ollama import OllamaLLM
from langchain_deepseek import ChatDeepSeek
memory = MemorySaver()


@tool
def get_weather_info(
    city: str,
    extensions: str = "base",
    key: str = os.environ.get("AMAP_API_KEY", "您的高德地图API密钥"),
):
    """用于获取城市天气信息。

    参数:
        city: 城市名称或编码，如"北京"或"110000"
        extensions: 气象类型，可选值：base/all，base:返回实况天气，all:返回预报天气
        key: 高德地图API密钥

    返回:
        包含天气数据的字典，或者在请求失败时返回错误信息。
    """    
    try:
        response = httpx.get(
            "https://restapi.amap.com/v3/weather/weatherInfo",
            params={"city": city, "extensions": extensions, "key": key},
        )
        response.raise_for_status()

        data = response.json()
        if data.get("status") != "1":
            return {"error": f"API请求错误: {data.get('info', '未知错误')}"}
        return data
    except httpx.HTTPError as e:
        return {"error": f"API请求失败: {e}"}
    except ValueError:
        return {"error": "API返回的JSON格式无效"}


class ResponseFormat(BaseModel):
    """以此格式回复用户"""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str

class WeatherAgent:

    SYSTEM_INSTRUCTION = (
        "你是一个专门提供天气信息的助手。"
        "你的唯一目的是使用'get_weather_info'工具回答关于天气的问题。"
        "如果用户询问与天气无关的问题，请礼貌地表明你只能提供天气相关的帮助。"
        "不要尝试回答无关问题或将工具用于其他目的。"
        "当用户需要提供更多信息时，将响应状态设置为input_required。"
        "处理请求出错时，将响应状态设置为error。"
        "请求完成时，将响应状态设置为completed。"
    )
     
    def __init__(self):
        self.model = ChatDeepSeek(model="deepseek-chat")
        #self.model = OllamaLLM(model="deepseek-llm:7b")
        self.tools = [get_weather_info]
    
        self.graph = create_react_agent(
            self.model, tools=self.tools, checkpointer=memory, prompt=self.SYSTEM_INSTRUCTION, response_format=ResponseFormat
        )
    
    def invoke(self, query, sessionId) -> str:
        config = {"configurable": {"thread_id": sessionId}}
        self.graph.invoke({"messages": [("user", query)]}, config)        
        return self.get_agent_response(config)

    async def stream(self, query, sessionId) -> AsyncIterable[Dict[str, Any]]:
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": sessionId}}

        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "正在查询天气信息...",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "正在处理天气数据...",
                }            
        
        yield self.get_agent_response(config)

        
    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)        
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(structured_response, ResponseFormat): 
            if structured_response.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured_response.message
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "我们暂时无法处理您的请求，请稍后再试。",
        }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
