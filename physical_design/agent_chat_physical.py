# add physical model designer
# this is for demo presentation, not for evaluation. So there is only one input sample.
import argparse
import asyncio
import json
import os
import sys
from collections import defaultdict
import io
from typing import List
from typing_extensions import Self
from pydantic import BaseModel

from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import LLMMessage
from typing_extensions import Annotated
# from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_core import Component

from autogen_agentchat.agents import AssistantAgent, SocietyOfMindAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat, RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from user_prompt_english import (get_conceptual_design_agent_prompt, get_logical_design_agent_prompt, get_QA_agent_prompt, get_report_prompt,\
    get_selector_prompt, get_manager_prompt, selector_func, get_reviewer_prompt, get_execution_agent_prompt, get_physical_design_agent_prompt)




def compute_closure(base_set, deps):
    closure = set(base_set)
    changed = True
    while changed:
        changed = False
        for lhs, rhs in deps:
            if lhs <= closure and not rhs <= closure:
                closure.update(rhs)
                changed = True
    return closure


def find_candidate_keys(attrs, deps):
    # Check if it is a candidate key
    def is_candidate_key(candidate, deps, all_attributes):
        return compute_closure(candidate, deps) == all_attributes

    from itertools import combinations
    all_attributes = set(attrs)
    candidates = []
    for i in range(1, len(attrs) + 1):
        for combo in combinations(attrs, i):
            candidate = set(combo)
            if is_candidate_key(candidate, deps, all_attributes):
                # Check if any subset is already a candidate key
                if any(all(sub in candidate for sub in c) for c in candidates):
                    continue
                candidates.append(list(candidate))
    return candidates


async def get_attribute_keys_by_arm_strong(dependencies_json: Annotated[
    str, "json in function dependencies {'entity set name or relationship set name': {'attribute 1': ['The attributes determined by the attribute 1']}}"]):
    '''Identify primary keys based on functional dependencies'''
    # Attribute sets
    attributes_all = {}
    dependencies_all = {}
    dependencies_json = json.loads(dependencies_json)
    for entity_name in dependencies_json:
        entity = dependencies_json[entity_name]
        attributes = []
        dependencies = []
        for depend_key in entity:
            if '&' in depend_key:
                depend_key_list = [it.strip() for it in depend_key.split('&')]  # Handle multiple left values
            elif ',' in depend_key:
                depend_key_list = [it.strip() for it in depend_key.split(',')]  # Handle multiple left values
            else:
                depend_key_list = [depend_key]
            attributes.extend(list(set(depend_key_list) | set(entity[depend_key])))
            dependencies.append((set(depend_key_list), set(entity[depend_key])))
        attributes = list(set(attributes))

        attributes_all[entity_name] = attributes
        dependencies_all[entity_name] = dependencies


    candidate_keys_dict = {}
    # Execute candidate key search
    for entity_name in attributes_all:
        candidate_keys = find_candidate_keys(attributes_all[entity_name], dependencies_all[entity_name])
        # print(f"The candidate keys of entity {entity_name} are:", candidate_keys)
        candidate_keys_dict[entity_name] = candidate_keys
    return {"attributes_all": attributes_all, "entity_primary_keys": candidate_keys_dict}


def get_attribute_keys_by_arm_strong_each(attributes, dependencies):
    dependencies_all = []
    for depend_key in dependencies:
        if '&' in depend_key:
            depend_key_list = [it.strip() for it in depend_key.split('&')]  # Handle multiple left values
        elif ',' in depend_key:
            depend_key_list = [it.strip() for it in depend_key.split(',')]  # Handle multiple left values
        else:
            depend_key_list = [depend_key]
        dependencies_all.append((set(depend_key_list), set(dependencies[depend_key])))
    # Execute candidate key search
    candidate_keys = find_candidate_keys(attributes, dependencies_all)
    # print(candidate_keys_dict)
    return candidate_keys


async def confirm_to_third_normal_form(dependencies_json: Annotated[
    str, "json in function dependencies {'entity set name or relationship set name':{'attribute 1':['The attributes determined by the attribute 1']}}"],
                           entity_primary_keys: Annotated[
                               str, "json in {entity set name or relationship set name:[[primary key 1],[primary key 2]]}"],
                           attributes_all: Annotated[str, "json in {'entity set name or relationship set name':['attribute 1','attribute 2']}"]):
    """
    Automatically decompose current relations to 3NF.
    """

    def parse_dependencies(entity_fd_json):
        """
        Parse functional dependencies, supporting attributes separated by commas.
        """
        functional_dependencies = []
        for entity, dependencies in entity_fd_json.items():
            for determinant, dependents in dependencies.items():
                determinant_list = [attr.strip() for attr in determinant.split(",")]
                functional_dependencies.append((determinant_list, dependents, entity))
        return functional_dependencies

    def find_closure(dependencies, target_set):
        """
        Calculate the closure of attribute set target_set.
        """
        closure = set(target_set)
        changed = True
        while changed:
            changed = False
            for X, Y in dependencies:
                if set(X).issubset(closure) and not set(Y).issubset(closure):
                    closure.update(Y)
                    changed = True
        return closure

    dependencies_json = json.loads(dependencies_json)
    entity_primary_keys = json.loads(entity_primary_keys)
    attributes_all = json.loads(attributes_all)

    # Parse functional dependencies
    functional_dependencies = parse_dependencies(dependencies_json)

    # Save results
    transitive_partial_dependencies = defaultdict(lambda: {"decompose_relationships": []})

    # Classify dependencies by entity
    dependencies_by_entity = defaultdict(list)
    for determinant, dependent, entity in functional_dependencies:
        dependencies_by_entity[entity].append((determinant, dependent))

    # Functional dependency analysis
    for entity, deps in dependencies_by_entity.items():
        primary_keys = entity_primary_keys[entity]  # Get current entity's primary key

        # Decomposed relations
        relations = []

        for X, Y in deps:
            closure = find_closure(dependencies_by_entity[entity], X)

            if any(set(X).issubset(pk) for pk in primary_keys):
                if not set(Y).issubset(closure):
                    partial_relation = set(X) | set(Y)
                    if partial_relation not in relations:
                        relations.append(partial_relation)

        for X, Y in deps:
            if set(Y).issubset(find_closure(dependencies_by_entity[entity], X)):
                relation = set(X) | set(Y)
                if relation not in relations:
                    relations.append(relation)

        for pk in primary_keys:
            if not any(set(pk).issubset(relation) for relation in relations):
                relations.append(set(pk))

        # Remove duplicate relations
        unique_relations = []
        for rel in relations:
            if len(rel) == 1:
                continue
            if rel not in unique_relations:
                unique_relations.append(rel)

        transitive_partial_dependencies[entity]["decompose_relationships"] = unique_relations

    transitive_partial_dependencies = {key: value for key, value in
                                       transitive_partial_dependencies.items()}  # Convert to regular dict

    new_entity_add_relation_attributes_all = defaultdict(dict)
    new_entity_add_relation_keys_and_attribute_map = {}
    for entity_name in transitive_partial_dependencies:
        if len(transitive_partial_dependencies[entity_name]['decompose_relationships']) == 1:  # No need to split table
            new_entity_add_relation_attributes_all[entity_name]['Attribute'] = attributes_all[
                entity_name]
            new_entity_add_relation_keys_and_attribute_map[entity_name] = entity_primary_keys[
                entity_name]
        else:  # Need to split table
            for sub_table_attributes in transitive_partial_dependencies[entity_name]['decompose_relationships']:
                candidate_keys = get_attribute_keys_by_arm_strong_each(sub_table_attributes,
                                                                            dependencies_json[entity_name])
                new_entity_name = ''
                for candidate_key in candidate_keys:
                    new_entity_name = ''.join(candidate_key)  
                new_entity_add_relation_attributes_all[new_entity_name]['Attribute'] = sub_table_attributes
                new_entity_add_relation_attributes_all[new_entity_name]['Foreign key'] = {}
                # Handle foreign key relationships

                # foreign_keys = list(entity_attributes_all_with_foreign_key[entity_name]['Foreign key'].keys())
                # common_keys = get_common_element_list(foreign_keys, sub_table_attributes)

                # for key in common_keys:
                #     new_entity_add_relation_attributes_all[new_entity_name]['Foreign key'][key] = \
                #     entity_attributes_all_with_foreign_key[entity_name]['Foreign key'][key]
                new_entity_add_relation_keys_and_attribute_map[new_entity_name] = candidate_keys

    return {"entity_attributes_all": new_entity_add_relation_attributes_all,
            "entity_keys_and_attribute_map": new_entity_add_relation_keys_and_attribute_map}





class RoleChatCompletionContextConfig(BaseModel):
    name: str
    initial_messages: List[LLMMessage] | None = None


class RoleChatCompletionContext(ChatCompletionContext, Component[RoleChatCompletionContextConfig]):
    """A chat completion context that keeps a view of the specific assistant,
    Args:
        name (int): The name of the assistant.
        initial_messages (List[LLMMessage] | None): The initial messages.
    """

    component_config_schema = RoleChatCompletionContextConfig
    # component_provider_override = "autogen_core.model_context.HeadAndTailChatCompletionContext"

    def __init__(self, name: str, initial_messages: List[LLMMessage] | None = None) -> None:
        super().__init__(initial_messages)
        self._name = name

    async def get_messages(self) -> List[LLMMessage]:
        """Get messages from the specific assistant"""
        # Filter out thought field from AssistantMessage.
        messages_out: List[LLMMessage] = []
        for message in self._messages:
            if message.source == self._name:
                messages_out.append(message)
        return messages_out

    def _to_config(self) -> RoleChatCompletionContextConfig:
        return RoleChatCompletionContextConfig(
            name=self._name, initial_messages=self._initial_messages
        )

    @classmethod
    def _from_config(cls, config: RoleChatCompletionContextConfig) -> Self:
        return cls(name=config.name, initial_messages=config.initial_messages)



async def main(args):

    print('===================')
    print(args)
    # MySQL connection parameters  
    # mysql_params = {
    #     "host": "localhost",
    #     "port": args.database_port,
    #     "user": args.database_user,
    #     "password": args.database_password, 
    #     "database": args.database_name,
    # }

    # # mcp server
    # server_params = StdioServerParams(
    #     command = "uvx",
    #     args = [
    #             "--from",
    #             "mysql-mcp-server",
    #             "mysql_mcp_server"
    #         ],
    #     env = {
    #     "MYSQL_HOST": mysql_params["host"],
    #     "MYSQL_PORT": mysql_params["port"],
    #     "MYSQL_USER": mysql_params["user"],
    #     "MYSQL_PASSWORD": mysql_params["password"],
    #     "MYSQL_DATABASE": mysql_params["database"],
    #     },
    # )

    # # get mcp mysql tools
    # tools = await mcp_server_tools(server_params)

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
    print('finish loading model')

    conceptual_designer_agent = AssistantAgent(
        "ConceptualDesignerAgent",
        description="Concept designers design conceptual models based on requirements analysis.",
        model_client=model_client,
        system_message=get_conceptual_design_agent_prompt(),
    )

    logical_designer_agent = AssistantAgent(
        "LogicalDesignerAgent",
        description="The logic designer designs the logical model based on the conceptual model.",
        model_client=model_client,
        tools=[get_attribute_keys_by_arm_strong, confirm_to_third_normal_form],
        system_message=get_logical_design_agent_prompt(),
        reflect_on_tool_use=True
    )

    qa_agent = AssistantAgent(
        "QAAgent",
        description="QA engineers generate test cases based on requirement analysis.",
        model_client=model_client,
        system_message=get_QA_agent_prompt(),
        model_context=RoleChatCompletionContext(name='ManagerAgent'), #limited, can only see the requirement analysis
    )

    execution_agent = AssistantAgent(
        "ExecutionAgent",
        description="The execution agent evaluates whether the current database logic design schemas satisfies the test cases.",
        model_client=model_client,
        system_message=get_execution_agent_prompt(),
    )

    manager = AssistantAgent(
        "ManagerAgent",
        description="Managers have two jobs. One is to analyze user requirement, and the other is to decide the final acceptance.",
        model_client=model_client,
        system_message=get_manager_prompt(),
    )

    conceptual_reviewer_agent = AssistantAgent(
        "ConceptualReviewerAgent",
        description="Determine whether the current conceptual model satisfies all constraints.",
        model_client=model_client,
        system_message=get_reviewer_prompt(),
    )


    #Physical designers do not belong to this group because they cannot provide feedback on the design process and only follow the results of logical designers.  
    physical_designer_agent = AssistantAgent(
        "PhysicalDesignerAgent",
        description='The physical designer designs and executes the SQL statements based on the logical model.',
        model_client=model_client,
        # tools=tools,
        system_message=get_physical_design_agent_prompt(),
        # reflect_on_tool_use=True,
    )

    # agent to produce a report
    report_agent = AssistantAgent(
        'ReportAgent',
        description='The report agent compiles the current information into a standardized report format.',
        model_client=model_client,
        system_message=get_report_prompt(),
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
                                               instruction='Output the Final Answer formatted in json by ConceptualDesignerAgent. Do NOT change anything.')

    team = SelectorGroupChat([manager, society_of_mind_agent, logical_designer_agent, qa_agent, execution_agent],
                                 model_client=model_client,
                                 termination_condition=termination,
                                 allow_repeated_speaker=True,
                                 selector_prompt=get_selector_prompt(),
                                 selector_func=selector_func
                             )
    
    # -------------------- Test Examples -------------------
    # for chinese
    # text = '某大学需要一个学生选课管理系统来维护和跟踪学生的选课信息。学生有学号、姓名、年龄等信息，每个学生可以选修多门课程，在规定时间内可以退课或换课。每门课程有课程编号、课程名称、学分、授课教师和上课时间等信息。课程的受欢迎程度取决于选课人数，系统可以预测课程的受欢迎程度，为教务决策提供支持。'
    # text = '某工厂的业务需求情况为：工厂有多个部门，其中有些是生产部门，叫作车间。一个部门有多个职工，一个职工只属于一个部门。每个职工有职工号、姓名、出生日期、性别，电话和岗位；工厂生产多种产品。产品有名称、型号，条码，价格。部门要从库房领取零部件，也要把自己的产品入库。零部件有名称、型号、条码，价格。部门每次领取的时候可以领取多个零件，并记录领了哪些零部件和数量，以及处理该次领取的发货人，领取人，领取时间。部门也可以每次入库多个产品，并记录入库了哪些产品和数量，以及处理该次入库的交货人，收货人，入库时间。该生产管理信息系统要能对部门进行绩效考核。'
    # for english
    # text = "A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, the name of the course chosen by the student, etc. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
    # text = 'The business needs of a factory are as follows: the factory has multiple departments, some of which are production departments, called workshops. A department has multiple employees, and an employee belongs to only one department. Each employee has an employee number, name, date of birth, gender, telephone number and position; the factory produces a variety of products. Products have names, models, barcodes and prices. Departments need to collect parts from the warehouse and also put their products into the warehouse. Parts have names, models, barcodes and prices; each time they are collected, they need to record which parts have been collected, their quantity, the consignor, the recipient, and the collection time. When products are put into the warehouse, they also need to record which products have been put into the warehouse, their quantity, the consignor, the consignee, and the storage time. The production management information system should be able to evaluate the performance of the department.'
    # text = "The required functions of a certain tourism management system are described as follows: In the user management module, users can register by filling in their username, password, email address and phone number. The system will set the default user role to \"ordinary user\" and save the creation time and update time. In the team management module, administrators can create new team activities and fill in the event title, description, start and end date, event location and other information. After the event is created, the system will record the release time and update time. Users can sign up for team activities, and the system will record the user's registration time and status (such as registered, canceled). Users can cancel their registration before the event starts. In the attraction management module, administrators can manage the attraction list, including adding new attractions, deleting old attractions, or modifying the name, description, picture and location of the attraction. The system will record the creation time and update time. Users can comment on the attractions, including the content of the comment and the rating."
    # text = "The business requirements of a warehouse management system are described as follows: a warehousing company manages multiple warehouses, each of which has a warehouse number, address, and capacity. The company has multiple loaders, each of which has a number, name, and phone number. Each inbound and outbound task needs to record the warehouse number, loader information, cargo information, quantity, and time. The system needs to support real-time monitoring and performance evaluation of warehouses and loading and unloading tasks."

    text = args.requirement_text

    # backup markdown file 
    save_file_path = 'saved_files/' + '_'.join(text[:15].split()) + '.md' 
    
    # Create a StringIO object to capture the output
    captured_output = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured_output
    print('++++++++++ Begin to generate logical schemas +++++++++++')
    await Console(team.run_stream(task=text))
    # Reset the team for the next run. the next task is not related to the previous task
    await team.reset()  
    output_string = captured_output.getvalue()

    print('++++++++++ Begin to generate physical DDL +++++++++++')
    # the team meassage will give to the physical model agent. workflow
    await Console(physical_designer_agent.run_stream(task=output_string))
    output_string = captured_output.getvalue()

    print('++++++++++ Begin to generate report +++++++++++')
    # produce a report, change format, download. challenge.
    result = await Console(report_agent.run_stream(task=output_string))
    print('Success.')
    output_string = captured_output.getvalue()

    sys.stdout = original_stdout
    captured_output.close()

    with open(save_file_path, 'w') as f:
        f.write(output_string)
    
    print(f"finish saving file to {save_file_path}")

    note_message = f" \n\n### NOTE \n(1) Use the following statement to create a new database in MySQL: \n```sql \nCREATE DATABASE {args.database_name}; \n``` \n(2) Copy the above statement to MySQL for execution. "

    return result.messages[1].content + note_message
    
    
# ----------- for test -----------
requirement_text = "A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, the name of the course chosen by the student, etc. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."

parser = argparse.ArgumentParser()
parser.add_argument('--model_name', default='gpt4')  
parser.add_argument('--database_name', default='relation_mcp_test')
parser.add_argument('--database_user', default='root')
parser.add_argument('--database_password', default='123456')
parser.add_argument('--database_port', default='3306')
parser.add_argument('--requirement_text', default=requirement_text)

args = parser.parse_args()
# asyncio.run(main(args))
