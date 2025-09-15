# 写在前面，不知道为什么会经常性的client timeout，但是在终端先运行
# MYSQL_HOST=localhost MYSQL_PORT=3306 MYSQL_USER=root MYSQL_PASSWORD=123456 MYSQL_DATABASE=mcp uvx --from mysql-mcp-server mysql_mcp_server
# 就不会有连接问题
# 每一次更新文件，就需要重连
# 预先启动服务：考虑在主程序执行前预先启动MCP服务器，确保它已完全初始化后再连接。

import asyncio
import os
from pathlib import Path
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken
from autogen_agentchat.ui import Console

async def main() -> None:
    # Setup server params for MySQL access
    model_client = OpenAIChatCompletionClient(
        model="gpt-3.5-turbo",
        base_url="https://www.dmxapi.com/v1/",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True,
        }
    )

    # MySQL connection parameters  数据库连接是没有问题的
    mysql_params = {
        "host": "localhost",
        "port": "3306",
        "user": "root",
        "password": "123456",  # 请替换为你的实际密码
        "database": "mcp"     # 请替换为你要访问的数据库名
    }

    # 创建 MySQL 服务器参数
    # 这个是基于python的，要求python3，11，现在的版本是3.10导致了很多报错，
    # 基于node.js的，要求node.js 18，现在的版本是16，导致了很多报错，升级到18要求Linux内核相应地升级，风险很大。

    server_params = StdioServerParams(
      command = "uvx",
      args = [
                "--from",
                "mysql-mcp-server",
                "mysql_mcp_server"
            ],
      env = {
        "MYSQL_HOST": mysql_params["host"],
        "MYSQL_PORT": mysql_params["port"],
        "MYSQL_USER": mysql_params["user"],
        "MYSQL_PASSWORD": mysql_params["password"],
        "MYSQL_DATABASE": mysql_params["database"],
      },
    )
    
    # 获取所有可用的 MySQL 工具
    tools = await mcp_server_tools(server_params)
    for tool in tools:
        print("Available MySQL tools:", tool._tool)  # 无语了，，就一个'execute_sql'这一个tool？ 好像也是


    # 创建可以使用这些工具的 agent
    agent = AssistantAgent(
        name="mysql_manager",
        model_client=model_client,
        tools=tools,  # type: ignore
    )

    # 使用 agent 执行 MySQL 操作
    # result = await agent.run(
    #     task="fWhat are the tables in the database? find user name who's age is older than 25."
    # )
    # print(result.messages[-1])
    context = """
              - 表名：user
                - 字段：
                • id (整数, 主键)
                • name (字符串)
                • age (整数)
                - 数据示例：10条人员记录，年龄范围22-35岁

              """
    await Console(
        agent.run_stream(task= "帮我新建立一个课程表，它的物理层schema如下：Course(Cno, Cname, Cpno, Ccredit) \n 分别表示课程的编号（主键）、名称、授课老师编号和学分。你需要为它们定义字段类型，以及约束。", cancellation_token=CancellationToken())
    )

    print('finished')

if __name__ == "__main__":
    asyncio.run(main()) 