import argparse
import asyncio
import json
import os
import sys
import io
import logging
from typing import List
from typing_extensions import Self
from pydantic import BaseModel

from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import LLMMessage
from autogen_core import Component

from autogen_agentchat.agents import AssistantAgent, SocietyOfMindAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat, RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from user_prompt_english import (get_conceptual_design_agent_prompt, get_logical_design_agent_prompt, get_QA_agent_prompt,\
    get_selector_prompt, get_manager_prompt, selector_func, get_reviewer_prompt, get_execution_agent_prompt, get_society_of_mind_prompt)
from util import *
from context import RoleChatCompletionContext, RecipientChatCompletionContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



async def main(args):

    logger.info(args)

    mapping = {'gpt4': 'gpt-4o-2024-08-06',
               'chatgpt': 'gpt-3.5-turbo',
               'deepseek': 'deepseek-v3-241226'}
    model_client = OpenAIChatCompletionClient(
        # model="gpt-3.5-turbo",  # gpt-3.5-turbo deepseek-v3-241226 deepseek-v3  #gpt-4o-mini-2024-07-18 #"gpt-4o-2024-08-06"
        model = mapping[args.model_name],
        base_url="https://www.dmxapi.com/v1/",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True, 
        }
    )
    logger.info('finish loading model')

    conceptual_designer_agent = AssistantAgent(
        "ConceptualDesignerAgent",
        description="Concept designers design conceptual models based on requirements analysis.",
        model_client=model_client,
        system_message=get_conceptual_design_agent_prompt(),
        model_context=RecipientChatCompletionContext(name=["society_of_mind", "ConceptualDesignerAgent"])
    )

    logical_designer_agent = AssistantAgent(
        "LogicalDesignerAgent",
        description="The logic designer designs the logical model based on the conceptual model.",
        model_client=model_client,
        tools=[get_attribute_keys_by_arm_strong, confirm_to_third_normal_form],
        system_message=get_logical_design_agent_prompt(),
        reflect_on_tool_use=True
        # model_context=RecipientChatCompletionContext(name=["ManagerAgent", "LogicalDesignerAgent"])
    )

    qa_agent = AssistantAgent(
        "QAAgent",
        description="QA engineers generate test cases based on requirement analysis.",
        model_client=model_client,
        system_message=get_QA_agent_prompt(),
        model_context=RecipientChatCompletionContext(name=['QAAgent']) #limited, can only see the requirement analysis
    )

    execution_agent = AssistantAgent(
        "ExecutionAgent",
        description="The execution agent evaluates whether the current database logic design schemas satisfies the test cases.",
        model_client=model_client,
        system_message=get_execution_agent_prompt(),
        model_context=RecipientChatCompletionContext(name=["ExecutionAgent"])
    )

    manager = AssistantAgent(
        "ManagerAgent",
        description="Managers have two jobs. One is to analyze user requirement, and the other is to decide the final acceptance.",
        model_client=model_client,
        system_message=get_manager_prompt(),
        model_context=RecipientChatCompletionContext(name=["ManagerAgent"])
    )

    conceptual_reviewer_agent = AssistantAgent(
        "ConceptualReviewerAgent",
        description="Determine whether the current conceptual model satisfies all constraints.",
        model_client=model_client,
        system_message=get_reviewer_prompt(),
    )


    text_mention_termination = TextMentionTermination("TERMINATE")
    max_messages_termination = MaxMessageTermination(max_messages=15)
    termination = text_mention_termination | max_messages_termination


    # for conceptual model design, nested group chat
    inner_termination = TextMentionTermination("Approve") | max_messages_termination
    inner_team = RoundRobinGroupChat([conceptual_designer_agent, conceptual_reviewer_agent], termination_condition=inner_termination)
    society_of_mind_agent = SocietyOfMindAgent("society_of_mind",
                                               description='A team that designs conceptual models based on requirements analysis.',
                                               team=inner_team,
                                               model_client=model_client,
                                               instruction='Earlier you were asked to designs conceptual models. You and your team worked diligently to address that request. Here is a transcript of that conversation:',
                                               response_prompt=get_society_of_mind_prompt()
                                            #    model_context=RecipientChatCompletionContext(["society_of_mind"])
                                              )

    team = SelectorGroupChat([manager, society_of_mind_agent, logical_designer_agent, qa_agent, execution_agent],
                                 model_client=model_client,
                                 termination_condition=termination,
                                 allow_repeated_speaker=True,
                                 selector_prompt=get_selector_prompt(),
                                 selector_func=selector_func
                             )
        
    save_file_path = f'{args.save_file_dir}/agent_chat_{args.model_name}_for_test.txt'
    save_file_error_path = f'{args.save_file_dir}/agent_chat_error_{args.model_name}.txt'
    save_file_json_path = save_file_path.replace('.txt', '.jsonl')
    with open(args.test_file_path, 'r', encoding='utf-8') as f:
        test_datas = [json.loads(line) for line in f][args.start_pos : args.end_pos]
    
    
    # retry_ids = ['67552f0a13602ec03b41a85c', '67552f0a13602ec03b41a8ac', '67552f0a13602ec03b41a845', '67552f0a13602ec03b41a8dc', '67552f0a13602ec03b41a982', '67552f0a13602ec03b41a9b6', '67552f0a13602ec03b41a8c0', '67552f0b13602ec03b41aa2e', '67552f0a13602ec03b41a7a3', '67552f0a13602ec03b41a7f7', '67552f0a13602ec03b41a7bd', '67552f0a13602ec03b41a99f', '67552f0a13602ec03b41a83e', '67552f0a13602ec03b41a91c', '67552f0a13602ec03b41a9af', '67552f0b13602ec03b41aa39']
    retry_ids = ['67552f0a13602ec03b41a87a']
    # logger.info('++++++++++ Begin to generate logical schemas +++++++++++')
    with open(save_file_path, 'a+') as f:
        # original_stdout = sys.stdout
        # sys.stdout = f
        for data in test_datas:
            if data['id'] not in retry_ids:
                continue
            # we need to retry when failed, 3 times
            i = 0
            for i in range(args.retry_times):
                try:
                    captured_output = io.StringIO()
                    original_stdout = sys.stdout
                    sys.stdout = captured_output

                    logger.info(f'---- id:{data["id"]} ----')
                    print(f'---- id:{data["id"]} ----')

                    text = data['question']
                    await Console(team.run_stream(task=text))
                    await team.reset()  # Reset the team for the next run. the next task is not related to the previous task
                    output_string = captured_output.getvalue()

                    # save the output to text file
                    f.write(output_string)
                    logger.info(f"Successfully saved to txt format.")
                    # convert the text format to json format
                    data_list = extract_answer_from_sample(output_string)
                    logger.info(f"Successfully converted to json format.")
                    logger.info(data_list)
                    with open(save_file_json_path, 'a+') as json_f:
                        for item in data_list:
                            json_f.write(json.dumps(item, ensure_ascii=False) + '\n')
                    break
                except Exception as e:
                    logger.error("Conversion failed")
                    logger.error(e)
                    continue
                finally:
                    sys.stdout = original_stdout

            if i == args.retry_times - 1:
                logger.error(f"Failed to convert to json format after {args.retry_times} times.")
                with open(save_file_error_path, 'a+') as error_f:
                    error_f.write(f'{data["id"]}\n')
    
    return save_file_path
    
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', default='deepseek')  
    parser.add_argument('--test_file_path', default='../dataset/RSchema/annotation.jsonl')
    parser.add_argument('--save_file_dir', default='../output/agent_txt')
    parser.add_argument('--start_pos', type=int, default=0, help='Start position in dataset')
    parser.add_argument('--end_pos', type=int, default=550, help='End position in dataset (-1 for all)')
    parser.add_argument('--retry_times', type=int, default=3, help='Retry times when failed')
    args = parser.parse_args()
    save_file_chat_path = asyncio.run(main(args))

    logger.info(f"Output has been saved to file: {save_file_chat_path}")

    # # Parse txt file for structured saving
    # save_file_json_path = save_file_chat_path.replace('.txt', '.jsonl')
    # try:
    #     extract_answer_from_text(save_file_chat_path, save_file_json_path)
    #     logger.info(f"Successfully converted and saved to file: {save_file_json_path}")
    # except Exception as e:
    #     logger.error("Conversion failed")
    #     logger.error(e)



