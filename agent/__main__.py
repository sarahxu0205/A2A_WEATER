import sys
import os
# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from common.utils.push_notification_auth import PushNotificationSenderAuth
from agent.task_manager import AgentTaskManager  # 修改导入路径
from agent.agent import WeatherAgent  # 修改导入路径
import click
import logging
from dotenv import load_dotenv
import os

# 指定 .env 文件的绝对路径
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10000)
def main(host, port):
    """启动天气查询代理服务器。"""
    try:
        if not os.getenv("AMAP_API_KEY"):
            raise MissingAPIKeyError("未设置 AMAP_API_KEY 环境变量。")

        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skill = AgentSkill(
            id="weather_query",
            name="天气查询工具",
            description="实时获取全国各地天气信息，支持查询当前和未来天气状况",
            tags=["天气查询", "气象信息", "天气预报"],
            examples=["北京今天的天气怎么样", "上海明天的天气预报", "广州未来三天会下雨吗"],
        )
        agent_card = AgentCard(
            name="天气助手",
            description="专业的天气查询助手，可以实时获取全国各地的天气信息和预报",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=WeatherAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=WeatherAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=WeatherAgent(), notification_sender_auth=notification_sender_auth),
            host=host,
            port=port,
        )

        server.app.add_route(
            "/.well-known/jwks.json", notification_sender_auth.handle_jwks_endpoint, methods=["GET"]
        )

        logger.info(f"正在启动服务器，地址：{host}:{port}")
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"错误：{e}")
        exit(1)
    except Exception as e:
        logger.error(f"服务器启动过程中发生错误：{e}")
        exit(1)


if __name__ == "__main__":
    main()
