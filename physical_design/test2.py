# test report agent
# successful
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from user_prompt_english import get_report_prompt
from autogen_agentchat.ui import Console
import asyncio
import os


async def main():
    model_client = OpenAIChatCompletionClient(
        # model="gpt-3.5-turbo",  # gpt-3.5-turbo deepseek-v3-241226 deepseek-v3  #gpt-4o-mini-2024-07-18 #"gpt-4o-2024-08-06"
        model = "gpt-4o-2024-08-06",
        base_url="https://www.dmxapi.com/v1/",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True, 
        }
    )
    print('finish loading model')

    report_agent = AssistantAgent(
        'ReportAgent',
        description='The report agent compiles the current information into a standardized report format.',
        model_client=model_client,
        system_message=get_report_prompt(),
    )
    
    with open('saved_files/A_university_ne.md', 'r') as f:
        text = f.read()
    
    result = await Console(report_agent.run_stream(task=text))
    print('===================')
    print(result.messages[1].content)

asyncio.run(main())


# test html to pdf
# successful.

# from xhtml2pdf import pisa

# def convert_html_to_pdf(html_string, output_filename):
#     with open(output_filename, "wb") as output_file:
#         pisa.CreatePDF(html_string, dest=output_file)
#         return True
#     return False

# # 使用示例
# html = "<html><body><h1>Hello World</h1></body></html>"
# convert_html_to_pdf(html, "output.pdf")
# print('finish')


