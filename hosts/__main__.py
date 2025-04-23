import asyncclick as click
import asyncio
import base64
import os
import urllib
import sys
from uuid import uuid4

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.client import A2AClient, A2ACardResolver
from common.types import TaskState, Task, TextPart, FilePart, FileContent
from common.utils.push_notification_auth import PushNotificationReceiverAuth
from hosts.push_notification_listener import PushNotificationListener


@click.command()
@click.option("--agent", default="http://localhost:10000")
@click.option("--session", default=0)
@click.option("--history", default=False)
@click.option("--use_push_notifications", default=False)
@click.option("--push_notification_receiver", default="http://localhost:5000")
async def cli(agent, session, history, use_push_notifications: bool, push_notification_receiver: str):
    card_resolver = A2ACardResolver(agent)
    card = card_resolver.get_agent_card()

    print("======= 天气Agent卡片信息 ========")
    print(card.model_dump_json(exclude_none=True))

    notif_receiver_parsed = urllib.parse.urlparse(push_notification_receiver)
    notification_receiver_host = notif_receiver_parsed.hostname
    notification_receiver_port = notif_receiver_parsed.port

    if use_push_notifications:
        notification_receiver_auth = PushNotificationReceiverAuth()
        await notification_receiver_auth.load_jwks(f"{agent}/.well-known/jwks.json")

        push_notification_listener = PushNotificationListener(
            host = notification_receiver_host,
            port = notification_receiver_port,
            notification_receiver_auth=notification_receiver_auth,
        )
        push_notification_listener.start()
        
    client = A2AClient(agent_card=card)
    if session == 0:
        sessionId = uuid4().hex
    else:
        sessionId = session

    continue_loop = True
    streaming = card.capabilities.streaming

    while continue_loop:
        taskId = uuid4().hex
        print("=========  开始新的天气查询任务 ======== ")
        continue_loop = await completeTask(client, streaming, use_push_notifications, notification_receiver_host, notification_receiver_port, taskId, sessionId)

        if history and continue_loop:
            print("========= 历史记录 ======== ")
            task_response = await client.get_task({"id": taskId, "historyLength": 10})
            print(task_response.model_dump_json(include={"result": {"history": True}}))

async def completeTask(client: A2AClient, streaming, use_push_notifications: bool, notification_receiver_host: str, notification_receiver_port: int, taskId, sessionId):
    prompt = click.prompt(
        "\n请输入您想查询的天气信息 (:q 或 quit 退出)"
    )
    if prompt == ":q" or prompt == "quit":
        return False
    
    message = {
        "role": "user",
        "parts": [
            {
                "type": "text",
                "text": prompt,
            }
        ]
    }
    
    file_path = click.prompt(
        "选择要附加的文件路径？（按回车跳过）",
        default="",
        show_default=False,
    )
    if file_path and file_path.strip() != "":
        with open(file_path, "rb") as f:
            file_content = base64.b64encode(f.read()).decode('utf-8')
            file_name = os.path.basename(file_path)
        
        message["parts"].append(
            {
                "type": "file",
                "file": {
                    "name": file_name,
                    "bytes": file_content,
                }
            }
        )
 
    payload = {
        "id": taskId,
        "sessionId": sessionId,
        "acceptedOutputModes": ["text"],
        "message": message,
    }

    if use_push_notifications:
        payload["pushNotification"] = {
            "url": f"http://{notification_receiver_host}:{notification_receiver_port}/notify",            
            "authentication": {
                "schemes": ["bearer"],
            },
        }

    taskResult = None
    if streaming:
        response_stream = client.send_task_streaming(payload)
        async for result in response_stream:
            print(f"流式响应 => {result.model_dump_json(exclude_none=True)}")
        taskResult = await client.get_task({"id": taskId})
    else:
        taskResult = await client.send_task(payload)
        print(f"\n{taskResult.model_dump_json(exclude_none=True)}")

    ## 如果结果需要更多输入，继续循环
    state = TaskState(taskResult.result.status.state)
    if state.name == TaskState.INPUT_REQUIRED.name:
        return await completeTask(
            client,
            streaming,
            use_push_notifications,
            notification_receiver_host,
            notification_receiver_port,
            taskId,
            sessionId
        )
    else:
        ## 任务完成
        return True


if __name__ == "__main__":
    asyncio.run(cli())
