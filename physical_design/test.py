import asyncio
import os
from pathlib import Path
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_agentchat.agents import AssistantAgent
from autogen_core import CancellationToken


async def main() -> None:
    # Setup server params for local filesystem access
    
    model_client = OpenAIChatCompletionClient(
        model="gpt-3.5-turbo",  # gpt-3.5-turbo deepseek-v3-241226 deepseek-v3  #gpt-4o-mini-2024-07-18 #"gpt-4o-2024-08-06"
        base_url="https://www.dmxapi.com/v1/",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True,  # 这里就指定输出是json了
        }
    )
    desktop = str(Path.home() / "Desktop")
    print(desktop)
    server_params = StdioServerParams(
        command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", desktop]
    )

    # Get all available tools from the server
    tools = await mcp_server_tools(server_params)

    print("Available tools:", tools)
    print("Tools type:", type(tools))
    print("Tools length:", len(tools) if hasattr(tools, '__len__') else "Not iterable")

    # Create an agent that can use all the tools
    agent = AssistantAgent(
        name="file_manager",
        model_client=model_client,
        tools=tools,  # type: ignore
    )

    # The agent can now use any of the filesystem tools
    await agent.run(task="Create a file called test.txt with some content in the desktop folder.", cancellation_token=CancellationToken())
    print ('finished')

if __name__ == "__main__":
    asyncio.run(main())

