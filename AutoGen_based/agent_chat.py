import argparse
import asyncio
import json
import sys
from collections import defaultdict

from autogen_core.model_context import BufferedChatCompletionContext, HeadAndTailChatCompletionContext
from typing_extensions import Annotated

from autogen_agentchat.agents import AssistantAgent, SocietyOfMindAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat, RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from user_prompt_english import (get_conceptual_design_agent_prompt, get_logical_design_agent_prompt, get_QA_agent_prompt, \
    get_selector_prompt, get_manager_prompt,get_dependency_agent_prompt, get_primary_key_agent_prompt, selector_func,
                         get_reviewer_prompt, get_execution_agent_prompt)


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
    # 检查是否是候选键
    def is_candidate_key(candidate, deps, all_attributes):
        return compute_closure(candidate, deps) == all_attributes

    from itertools import combinations
    all_attributes = set(attrs)
    candidates = []
    for i in range(1, len(attrs) + 1):
        for combo in combinations(attrs, i):
            candidate = set(combo)
            if is_candidate_key(candidate, deps, all_attributes):
                # 检查是否有子集已是候选键
                if any(all(sub in candidate for sub in c) for c in candidates):
                    continue
                candidates.append(list(candidate))
    return candidates


async def get_attribute_keys_by_arm_strong(dependencies_json: Annotated[
    str, "json in function dependencies {'entity set name or relationship set name': {'attribute 1': ['The attributes determined by the attribute 1']}}"]):
    '''依据函数依赖关系识别出主键'''
    # 属性集
    attributes_all = {}
    dependencies_all = {}
    dependencies_json = json.loads(dependencies_json)
    # for entity_name in dependencies_json['dependencies']:
    #     entity = dependencies_json['dependencies'][entity_name]
    for entity_name in dependencies_json:
        entity = dependencies_json[entity_name]
        attributes = []
        dependencies = []
        for depend_key in entity:
            if '&' in depend_key:
                depend_key_list = [it.strip() for it in depend_key.split('&')]  # 处理多个左值的情况
            elif ',' in depend_key:
                depend_key_list = [it.strip() for it in depend_key.split(',')]  # 处理多个左值的情况
            else:
                depend_key_list = [depend_key]
            attributes.extend(list(set(depend_key_list) | set(entity[depend_key])))
            dependencies.append((set(depend_key_list), set(entity[depend_key])))
        attributes = list(set(attributes))

        attributes_all[entity_name] = attributes
        dependencies_all[entity_name] = dependencies

    # print(attributes_all)
    # print(dependencies_all)

    candidate_keys_dict = {}
    # 执行候选键搜索
    for entity_name in attributes_all:
        candidate_keys = find_candidate_keys(attributes_all[entity_name], dependencies_all[entity_name])
        # print(f"实体{entity_name}的候选键是:", candidate_keys)
        candidate_keys_dict[entity_name] = candidate_keys
    return {"attributes_all": attributes_all, "entity_primary_keys": candidate_keys_dict}


def get_attribute_keys_by_arm_strong_each(attributes, dependencies):
    dependencies_all = []
    for depend_key in dependencies:
        if '&' in depend_key:
            depend_key_list = [it.strip() for it in depend_key.split('&')]  # 处理多个左值的情况
        elif ',' in depend_key:
            depend_key_list = [it.strip() for it in depend_key.split(',')]  # 处理多个左值的情况
        else:
            depend_key_list = [depend_key]
        dependencies_all.append((set(depend_key_list), set(dependencies[depend_key])))

    # print(attributes_all)
    # print(dependencies_all)

    # 执行候选键搜索
    candidate_keys = find_candidate_keys(attributes, dependencies_all)
    # print(candidate_keys_dict)
    return candidate_keys


async def confirm_to_third_normal_form(dependencies_json: Annotated[
    str, "json in function dependencies {'entity set name or relationship set name':{'attribute 1':['The attributes determined by the attribute 1']}}"],
                           entity_primary_keys: Annotated[
                               str, "json in {entity set name or relationship set name:[[primary key 1],[primary key 2]]}"],
                           attributes_all: Annotated[str, "json in {'entity set name or relationship set name':['attribute 1','attribute 2']}"]):
    """
    自动分解当前关系到 3NF。
    """

    def parse_dependencies(entity_fd_json):
        """
        解析函数依赖关系，支持处理以逗号分隔的属性。
        """
        functional_dependencies = []
        for entity, dependencies in entity_fd_json.items():
            for determinant, dependents in dependencies.items():
                determinant_list = [attr.strip() for attr in determinant.split(",")]
                functional_dependencies.append((determinant_list, dependents, entity))
        return functional_dependencies

    def find_closure(dependencies, target_set):
        """
        计算属性集 target_set 的闭包。
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

    # 解析函数依赖
    functional_dependencies = parse_dependencies(dependencies_json)

    # 保存结果
    transitive_partial_dependencies = defaultdict(lambda: {"decompose_relationships": []})

    # 按实体分类依赖
    dependencies_by_entity = defaultdict(list)
    for determinant, dependent, entity in functional_dependencies:
        dependencies_by_entity[entity].append((determinant, dependent))

    # 函数依赖分析
    for entity, deps in dependencies_by_entity.items():
        primary_keys = entity_primary_keys[entity]  # 获取当前实体的主键

        # 分解后的关系
        relations = []

        # 1. 分解部分依赖：处理所有的依赖关系
        for X, Y in deps:
            closure = find_closure(dependencies_by_entity[entity], X)

            # 如果 X 是主键的超集
            if any(set(X).issubset(pk) for pk in primary_keys):
                # 只有当 Y 不在 X 的闭包中时才需要分解
                if not set(Y).issubset(closure):
                    partial_relation = set(X) | set(Y)
                    if partial_relation not in relations:
                        relations.append(partial_relation)

        # 2. 处理其他依赖
        for X, Y in deps:
            if set(Y).issubset(find_closure(dependencies_by_entity[entity], X)):
                relation = set(X) | set(Y)
                if relation not in relations:
                    relations.append(relation)

        # 确保每个主键都在某个关系中
        for pk in primary_keys:
            if not any(set(pk).issubset(relation) for relation in relations):
                relations.append(set(pk))

        # 移除重复关系
        unique_relations = []
        for rel in relations:
            if len(rel) == 1:
                continue
            if rel not in unique_relations:
                unique_relations.append(rel)

        # 输出分解后的关系
        transitive_partial_dependencies[entity]["decompose_relationships"] = unique_relations

    transitive_partial_dependencies = {key: value for key, value in
                                       transitive_partial_dependencies.items()}  # 转为普通dict
    # 选课关系中，没有这两种依赖关系
    # print(f'transitive_partial_dependencies:\n {transitive_partial_dependencies}')

    # 8. 开始拆实体表，算法实现
    new_entity_add_relation_attributes_all = defaultdict(dict)
    new_entity_add_relation_keys_and_attribute_map = {}
    for entity_name in transitive_partial_dependencies:
        if len(transitive_partial_dependencies[entity_name]['decompose_relationships']) == 1:  # 表示不用拆表
            new_entity_add_relation_attributes_all[entity_name]['Attribute'] = attributes_all[
                entity_name]
            new_entity_add_relation_keys_and_attribute_map[entity_name] = entity_primary_keys[
                entity_name]
        else:  # 需要拆表
            for sub_table_attributes in transitive_partial_dependencies[entity_name]['decompose_relationships']:
                candidate_keys = get_attribute_keys_by_arm_strong_each(sub_table_attributes,
                                                                            dependencies_json[entity_name])
                new_entity_name = ''
                for candidate_key in candidate_keys:
                    new_entity_name = ''.join(candidate_key)  # TODO 如果已经存在了这个new_entity_name 还需要额外的操作
                new_entity_add_relation_attributes_all[new_entity_name]['Attribute'] = sub_table_attributes
                new_entity_add_relation_attributes_all[new_entity_name]['Foreign key'] = {}
                # 处理下外键关系

                # foreign_keys = list(entity_attributes_all_with_foreign_key[entity_name]['外键'].keys())
                # common_keys = get_common_element_list(foreign_keys, sub_table_attributes)

                # for key in common_keys:
                #     new_entity_add_relation_attributes_all[new_entity_name]['外键'][key] = \
                #     entity_attributes_all_with_foreign_key[entity_name]['外键'][key]
                new_entity_add_relation_keys_and_attribute_map[new_entity_name] = candidate_keys

    return {"entity_attributes_all": new_entity_add_relation_attributes_all,
            "entity_keys_and_attribute_map": new_entity_add_relation_keys_and_attribute_map}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', default='gpt4')  # gpt4 chatgpt glm4 这个是免费的，可以后续开放chatgpt的接口
    parser.add_argument('--dataset_dir', default='../outputs/DBdesign_domain/text')
    args = parser.parse_args()

    print(args)
    mapping = {'gpt4': 'gpt-4o-2024-08-06',
               'chatgpt': 'gpt-3.5-turbo',
               'deepseek': 'deepseek-v3-241226'}
    model_client = OpenAIChatCompletionClient(
        # model="gpt-3.5-turbo",  # gpt-3.5-turbo deepseek-v3-241226 deepseek-v3  #gpt-4o-mini-2024-07-18 #"gpt-4o-2024-08-06"
        model = mapping[args.model_name],
        base_url="",
        api_key="",
        model_capabilities={
            "vision": True,
            "function_calling": True,
            "json_output": True,  # 这里就指定输出是json了
        }
    )
    print('finish loading model')

    conceptual_designer_agent = AssistantAgent(
        "ConceptualDesignerAgent",
        description="Concept designers design conceptual models based on requirements analysis.",
        model_client=model_client,
        system_message=get_conceptual_design_agent_prompt(),
        # model_context=HeadAndTailChatCompletionContext(head_size=1, tail_size=4),  # a view of the first n and last m messages
    )

    logical_designer_agent = AssistantAgent(
        "LogicalDesignerAgent",
        description="The logic designer designs the logical model based on the conceptual model.",
        model_client=model_client,
        tools=[get_attribute_keys_by_arm_strong, confirm_to_third_normal_form],
        system_message=get_logical_design_agent_prompt(),
        # model_context=HeadAndTailChatCompletionContext(head_size=1, tail_size=2), # a view of the first n and last m messages
        reflect_on_tool_use=True
    )

    qa_agent = AssistantAgent(
        "QAAgent",
        description="QA engineers generate test cases based on requirement analysis.",
        model_client=model_client,
        system_message=get_QA_agent_prompt(),
        # model_context=HeadAndTailChatCompletionContext(head_size=1, tail_size=2), # 只能看到需求分析
    )
    #
    # dependencies_identifier_agent = AssistantAgent(
    #     "DependenciesIdentifierAgent",
    #     description="识别出概念模型中的函数依赖关系",
    #     model_client=model_client,
    #     system_message=get_dependency_agent_prompt(),
    # )
    #
    # primary_key_agent = AssistantAgent(
    #     "PrimaryKeyAgent",
    #     description="识别主键",
    #     model_client=model_client,
    #     tools = [get_attribute_keys_by_arm_strong],
    #     system_message=get_primary_key_agent_prompt(),
    # )
    #
    # normalization_agent = AssistantAgent(
    #     "NormalizationAgent",
    #     description="判断是否具有部分函数依赖和传递函数依赖，如果存在则进行拆分",
    #     model_client=model_client,
    #     tools = [confirm_to_third_paradigm],
    #     system_message=get_primary_key_agent_prompt(),
    # )

    execution_agent = AssistantAgent(
        "ExecutionAgent",
        description="The execution agent evaluates whether the current database logic design schemas satisfies the test cases.",
        model_client=model_client,
        system_message=get_execution_agent_prompt(),
        # model_context=HeadAndTailChatCompletionContext(head_size=1, tail_size=4),
        # a view of the first n and last m messages
    )

    manager = AssistantAgent(
        "ManagerAgent",
        description="Managers have two jobs. One is to analyze user requirement, and the other is to decide the final acceptance.",
        model_client=model_client,
        system_message=get_manager_prompt(),
        # model_context=HeadAndTailChatCompletionContext(head_size=1, tail_size=4), # a view of the first n and last m messages
    )

    conceptual_reviewer_agent = AssistantAgent(
        "ConceptualReviewerAgent",
        description="Determine whether the current conceptual model satisfies all constraints.",
        model_client=model_client,
        system_message=get_reviewer_prompt(),
        # model_context=HeadAndTailChatCompletionContext(head_size=1, tail_size=4), # a view of the first n and last m messages
    )

    text_mention_termination = TextMentionTermination("TERMINATE")
    max_messages_termination = MaxMessageTermination(max_messages=15)
    termination = text_mention_termination | max_messages_termination

    # team = SelectorGroupChat(
    #     # [manager, conceptual_designer_agent, logical_designer_agent,
    #     #  primary_key_agent, dependencies_identifier_agent, normalization_agent, qa_agent],
    #     [manager, conceptual_designer_agent, conceptual_reviewer_agent, logical_designer_agent, qa_agent],
    #     model_client=model_client,
    #     termination_condition=termination,
    #     allow_repeated_speaker=True,
    #     selector_prompt=get_selector_prompt(),
    #     selector_func=selector_func
    # )

    # 换成嵌套式的聊天试试，这样反思就的过程就不对外开放了
    inner_termination = TextMentionTermination("Approve") | max_messages_termination
    inner_team = RoundRobinGroupChat([conceptual_designer_agent, conceptual_reviewer_agent], termination_condition=inner_termination)
    society_of_mind_agent = SocietyOfMindAgent("society_of_mind",
                                               description='A team that designs conceptual models based on requirements analysis.',
                                               team=inner_team,
                                               model_client=model_client)

    # team = SelectorGroupChat([manager, conceptual_designer_agent, conceptual_reviewer_agent, logical_designer_agent, qa_agent, execution_agent],
    team = SelectorGroupChat([manager, society_of_mind_agent, logical_designer_agent, qa_agent, execution_agent],
                                 model_client=model_client,
                                 termination_condition=termination,
                                 allow_repeated_speaker=True,
                                 selector_prompt=get_selector_prompt(),
                                 selector_func=selector_func
                             )


    # text = "A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, the name of the course chosen by the student, etc. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
    # text = 'The business needs of a factory are as follows: the factory has multiple departments, some of which are production departments, called workshops. A department has multiple employees, and an employee belongs to only one department. Each employee has an employee number, name, date of birth, gender, telephone number and position; the factory produces a variety of products. Products have names, models, barcodes and prices. Departments need to collect parts from the warehouse and also put their products into the warehouse. Parts have names, models, barcodes and prices; each time they are collected, they need to record which parts have been collected, their quantity, the consignor, the recipient, and the collection time. When products are put into the warehouse, they also need to record which products have been put into the warehouse, their quantity, the consignor, the consignee, and the storage time. The production management information system should be able to evaluate the performance of the department.'
    # text = "The required functions of a certain tourism management system are described as follows: In the user management module, users can register by filling in their username, password, email address and phone number. The system will set the default user role to \"ordinary user\" and save the creation time and update time. In the team management module, administrators can create new team activities and fill in the event title, description, start and end date, event location and other information. After the event is created, the system will record the release time and update time. Users can sign up for team activities, and the system will record the user's registration time and status (such as registered, canceled). Users can cancel their registration before the event starts. In the attraction management module, administrators can manage the attraction list, including adding new attractions, deleting old attractions, or modifying the name, description, picture and location of the attraction. The system will record the creation time and update time. Users can comment on the attractions, including the content of the comment and the rating."
    # text = "The business requirements of a warehouse management system are described as follows: a warehousing company manages multiple warehouses, each of which has a warehouse number, address, and capacity. The company has multiple loaders, each of which has a number, name, and phone number. Each inbound and outbound task needs to record the warehouse number, loader information, cargo information, quantity, and time. The system needs to support real-time monitoring and performance evaluation of warehouses and loading and unloading tasks."
    # await Console(team.run_stream(task=text))

    # read the test file
    test_file_path = '../datasets/RSchema/annotation_0203_21_34.jsonl'
    save_file_path = f'{args.dataset_dir}/agent_chat_healthcare_domain_{args.model_name}.txt'
    exiting_datas_path = f'../outputs/DBdesign_domain/healthcare_domain_{args.model_name}_chat_agent_evaluation.jsonl'
    exiting_datas = {}
    with open(exiting_datas_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            exiting_datas[data['id']] = data

    # finance_ids = ['67552f0a13602ec03b41a84b', '67552f0a13602ec03b41a84e', '67552f0a13602ec03b41a8fe', '67552f0a13602ec03b41a82c', '67552f0a13602ec03b41a847', '67552f0a13602ec03b41a78c', '67552f0a13602ec03b41a84c', '67552f0a13602ec03b41a91b', '67552f0a13602ec03b41a84a', '67552f0a13602ec03b41a83b', '67552f0a13602ec03b41a888']
    healthcare_ids = ['67552f0a13602ec03b41a9f6', '67552f0a13602ec03b41a87e', '67552f0a13602ec03b41a91d',
                      '67552f0b13602ec03b41aa5c', '67552f0a13602ec03b41a9fb', '67552f0a13602ec03b41a957',
                      '67552f0b13602ec03b41aa67', '67552f0b13602ec03b41ab0f', '67552f0a13602ec03b41a886',
                      '67552f0a13602ec03b41a8ae']

    with open(test_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # for i, line in enumerate(lines):
        #     print(i)
        #     json.loads(line)
        test_datas = [json.loads(line) for line in lines]

    with open(save_file_path, 'a+') as f:
        # 保存当前的标准输出
        original_stdout = sys.stdout
        # 将标准输出重定向到文件
        sys.stdout = f
        for i, data in enumerate(test_datas):
            if data['id'] in healthcare_ids and data['id'] not in exiting_datas.keys():
                print(f'---- id:{data["id"]} ----')
                text = data['question']
                # Use asyncio.run(...) if you are running this in a script.
                await Console(team.run_stream(task=text))
                await team.reset()  # Reset the team for the next run. the next task is not related to the previous task
        # 恢复标准输出
        sys.stdout = original_stdout
        print("输出已保存到文件")


asyncio.run(main())
