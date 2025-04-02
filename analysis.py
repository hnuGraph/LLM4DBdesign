# 用于分析结果
import json
import re
import sys
from collections import defaultdict, Counter


def base_direct_and_agent():
    base_direct_path = 'outputs/DBdesign/evaluation/gpt4-base_direct_0203_21_34_evaluation.jsonl'
    agent_path = 'outputs/DBdesign/evaluation/gpt4_chat_agent_0203_21_34_evaluation.jsonl'
    base_direct_datas = {}
    with open(base_direct_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            base_direct_datas[data['id']] = data
    print(len(base_direct_datas))
    agent_datas = {}
    with open(agent_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            agent_datas[data['id']] = data
    print(len(agent_datas))

    for key in base_direct_datas:
        if key in agent_datas:
            if base_direct_datas[key]['score']['schema f1']<agent_datas[key]['score']['schema f1']:
                print(key)
                print(base_direct_datas[key]['score'])
                print(agent_datas[key]['score'])
                assert 1==0

# 分析转移轨迹
def trajectory_matrix():
    path = 'outputs/DBdesign/evaluation_without_empty/gpt4_chat_agent_0203_21_34_evaluation.jsonl'
    nice_ids = ['67552f0a13602ec03b41a7bb', '67552f0a13602ec03b41a823', '67552f0a13602ec03b41aa06', '67552f0a13602ec03b41a964', '67552f0a13602ec03b41a7d9', '67552f0a13602ec03b41a899', '67552f0a13602ec03b41a88c', '67552f0a13602ec03b41a830', '67552f0a13602ec03b41a798', '67552f0a13602ec03b41a85f', '67552f0a13602ec03b41a954', '67552f0a13602ec03b41a86e', '67552f0a13602ec03b41a8fb', '67552f0a13602ec03b41a7d4', '67552f0a13602ec03b41a817', '67552f0a13602ec03b41a94e', '67552f0a13602ec03b41a913', '67552f0a13602ec03b41a912', '67552f0a13602ec03b41a9e7', '67552f0a13602ec03b41a7af', '67552f0b13602ec03b41aa56', '67552f0a13602ec03b41a78c', '67552f0a13602ec03b41a7d8', '67552f0a13602ec03b41a825', '67552f0a13602ec03b41a7e6', '67552f0a13602ec03b41a95e', '67552f0a13602ec03b41a82f', '67552f0b13602ec03b41aa40', '67552f0a13602ec03b41a816', '67552f0a13602ec03b41a808', '67552f0a13602ec03b41a8e9', '67552f0a13602ec03b41a95f', '67552f0a13602ec03b41a9e1', '67552f0a13602ec03b41a8ee', '67552f0a13602ec03b41a987', '67552f0a13602ec03b41a895', '67552f0a13602ec03b41a794', '67552f0a13602ec03b41a7bc', '67552f0a13602ec03b41a9f3', '67552f0a13602ec03b41a7fe', '67552f0a13602ec03b41a9d3', '67552f0a13602ec03b41a7d7', '67552f0a13602ec03b41a8c7', '67552f0a13602ec03b41a821', '67552f0a13602ec03b41a7b6', '67552f0a13602ec03b41a810', '67552f0a13602ec03b41a813', '67552f0a13602ec03b41a82b', '67552f0a13602ec03b41a865', '67552f0a13602ec03b41a7da', '67552f0a13602ec03b41a7e2', '67552f0a13602ec03b41a7f6', '67552f0b13602ec03b41aa5f', '67552f0a13602ec03b41a824', '67552f0a13602ec03b41a7aa', '67552f0a13602ec03b41a96d', '67552f0a13602ec03b41a839', '67552f0a13602ec03b41a981', '67552f0a13602ec03b41a81a', '67552f0a13602ec03b41a837', '67552f0a13602ec03b41a801', '67552f0a13602ec03b41a7fa', '67552f0a13602ec03b41a966', '67552f0b13602ec03b41aa9d', '67552f0a13602ec03b41a83e', '67552f0a13602ec03b41a892', '67552f0b13602ec03b41aa55', '67552f0a13602ec03b41a847', '67552f0a13602ec03b41a7cb', '67552f0a13602ec03b41a938', '67552f0a13602ec03b41a982', '67552f0a13602ec03b41a8bc', '67552f0a13602ec03b41a93a', '67552f0a13602ec03b41a89a', '67552f0a13602ec03b41a7dc', '67552f0b13602ec03b41aab3', '67552f0a13602ec03b41a85c', '67552f0b13602ec03b41ab2b', '67552f0a13602ec03b41a7d5', '67552f0b13602ec03b41aabb', '67552f0a13602ec03b41a86f', '67552f0a13602ec03b41a9c9', '67552f0a13602ec03b41a79d', '67552f0a13602ec03b41a829', '67552f0a13602ec03b41a882', '67552f0a13602ec03b41a8fe', '67552f0a13602ec03b41a7a2', '67552f0b13602ec03b41aaa9', '67552f0a13602ec03b41a79a', '67552f0a13602ec03b41a7c0', '67552f0a13602ec03b41a7ab']

    datas = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            if data['id'] in nice_ids:
                datas.append(data['trajectory'])

    transition_counts = defaultdict(int)
    for trajectory in datas:
        for i in range(len(trajectory) - 1):
            from_agent = trajectory[i]
            to_agent = trajectory[i + 1]
            transition_counts[(from_agent, to_agent)] += 1

        # 计算频率
        total_transitions = sum(transition_counts.values())  # 是计算每个案例的反馈频率，不是计算所有反馈中的
        transition_frequencies = {k: v / len(nice_ids) for k, v in transition_counts.items()}

    roles = ['ManagerAgent', 'ConceptualDesignerAgent', 'ConceptualReviewerAgent', 'LogicalDesignerAgent', 'QAAgent', 'ExecutionAgent']
    matrix = [[0 for _ in range(len(roles))] for _ in range(len(roles))]

    for (role1, role2) in transition_counts.keys():
        index1 = roles.index(role1)
        index2 = roles.index(role2)
        matrix[index1][index2] = transition_counts[(role1, role2)]


    # 输出结果
    print("Transition Counts:", dict(transition_counts))
    print("Transition Frequencies:", dict(transition_frequencies))
    print(matrix)

    for i in range(len(matrix)):
        matrix_str = [str(item) for item in matrix[i]]
        print('\t'.join(matrix_str))

# 生成每个类别，大类和小类
def topic_visual():
    path = 'datasets/Cluster_data/annotation_0203_21_34_api.jsonl'
    save_file_path = 'datasets/Cluster_data/cluser_result.txt'
    topic = []
    category_topic = defaultdict(list)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            topic.append(data['topic'])
            if data['category'] not in category_topic:
                category_topic[data['category']].append(data['topic'])
            elif data['topic'] not in category_topic[data['category']]:
                category_topic[data['category']].append(data['topic'])
    topic_dict = dict(Counter(topic))
    category_dict = {}
    with open(save_file_path, 'a+') as f:
        # 保存当前的标准输出
        original_stdout = sys.stdout
        # 将标准输出重定向到文件
        sys.stdout = f
        print(len(topic_dict.keys()))
        print(len(category_topic.keys()))
        for category in category_topic.keys():
            print(f'大类：{category}')
            print('小类:')
            lenth_all = 0
            for topic in category_topic[category]:
                lenth = topic_dict[topic]
                lenth_all += lenth
                print(f"{topic} ({lenth})")
            print(f'大类：{category} 总计条数：{lenth_all}')
            category_dict[category] = lenth_all
            print('\n')
        # 恢复标准输出
        sys.stdout = original_stdout
        for key in category_dict.keys():
            print(key,'\t', category_dict[key])
        print("输出已保存到文件")

def cast_analysis():
    file_path = 'outputs/DBdesignText/DBdesignAgent_annotation_0203_21_34.txt'
    with open(file_path, 'r', encoding='utf-8') as f:
        # 打开文件并读取内容
        content = f.read()

    # chatgpt
    # nice_ids = ['67552f0a13602ec03b41a7ab', '67552f0a13602ec03b41a882', '67552f0a13602ec03b41a7fe', '67552f0a13602ec03b41a798', '67552f0a13602ec03b41a86e', '67552f0a13602ec03b41a892', '67552f0a13602ec03b41a830', '67552f0a13602ec03b41a85f', '67552f0a13602ec03b41a7c0', '67552f0a13602ec03b41a821', '67552f0a13602ec03b41a824']
    #gpt4
    # nice_ids = ['67552f0a13602ec03b41a7bb', '67552f0a13602ec03b41a823', '67552f0a13602ec03b41aa06', '67552f0a13602ec03b41a964', '67552f0a13602ec03b41a7d9', '67552f0a13602ec03b41a899', '67552f0a13602ec03b41a88c', '67552f0a13602ec03b41a830', '67552f0a13602ec03b41a798', '67552f0a13602ec03b41a85f', '67552f0a13602ec03b41a954', '67552f0a13602ec03b41a86e', '67552f0a13602ec03b41a8fb', '67552f0a13602ec03b41a7d4', '67552f0a13602ec03b41a817', '67552f0a13602ec03b41a94e', '67552f0a13602ec03b41a913', '67552f0a13602ec03b41a912', '67552f0a13602ec03b41a9e7', '67552f0a13602ec03b41a7af', '67552f0b13602ec03b41aa56', '67552f0a13602ec03b41a78c', '67552f0a13602ec03b41a7d8', '67552f0a13602ec03b41a825', '67552f0a13602ec03b41a7e6', '67552f0a13602ec03b41a95e', '67552f0a13602ec03b41a82f', '67552f0b13602ec03b41aa40', '67552f0a13602ec03b41a816', '67552f0a13602ec03b41a808', '67552f0a13602ec03b41a8e9', '67552f0a13602ec03b41a95f', '67552f0a13602ec03b41a9e1', '67552f0a13602ec03b41a8ee', '67552f0a13602ec03b41a987', '67552f0a13602ec03b41a895', '67552f0a13602ec03b41a794', '67552f0a13602ec03b41a7bc', '67552f0a13602ec03b41a9f3', '67552f0a13602ec03b41a7fe', '67552f0a13602ec03b41a9d3', '67552f0a13602ec03b41a7d7', '67552f0a13602ec03b41a8c7', '67552f0a13602ec03b41a821', '67552f0a13602ec03b41a7b6', '67552f0a13602ec03b41a810', '67552f0a13602ec03b41a813', '67552f0a13602ec03b41a82b', '67552f0a13602ec03b41a865', '67552f0a13602ec03b41a7da', '67552f0a13602ec03b41a7e2', '67552f0a13602ec03b41a7f6', '67552f0b13602ec03b41aa5f', '67552f0a13602ec03b41a824', '67552f0a13602ec03b41a7aa', '67552f0a13602ec03b41a96d', '67552f0a13602ec03b41a839', '67552f0a13602ec03b41a981', '67552f0a13602ec03b41a81a', '67552f0a13602ec03b41a837', '67552f0a13602ec03b41a801', '67552f0a13602ec03b41a7fa', '67552f0a13602ec03b41a966', '67552f0b13602ec03b41aa9d', '67552f0a13602ec03b41a83e', '67552f0a13602ec03b41a892', '67552f0b13602ec03b41aa55', '67552f0a13602ec03b41a847', '67552f0a13602ec03b41a7cb', '67552f0a13602ec03b41a938', '67552f0a13602ec03b41a982', '67552f0a13602ec03b41a8bc', '67552f0a13602ec03b41a93a', '67552f0a13602ec03b41a89a', '67552f0a13602ec03b41a7dc', '67552f0b13602ec03b41aab3', '67552f0a13602ec03b41a85c', '67552f0b13602ec03b41ab2b', '67552f0a13602ec03b41a7d5', '67552f0b13602ec03b41aabb', '67552f0a13602ec03b41a86f', '67552f0a13602ec03b41a9c9', '67552f0a13602ec03b41a79d', '67552f0a13602ec03b41a829', '67552f0a13602ec03b41a882', '67552f0a13602ec03b41a8fe', '67552f0a13602ec03b41a7a2', '67552f0b13602ec03b41aaa9', '67552f0a13602ec03b41a79a', '67552f0a13602ec03b41a7c0', '67552f0a13602ec03b41a7ab']
    nice_ids = ['67552f0a13602ec03b41a798', '67552f0a13602ec03b41a824', '67552f0a13602ec03b41a83f', '67552f0a13602ec03b41a93d', '67552f0a13602ec03b41a9c9', '67552f0a13602ec03b41a879', '67552f0a13602ec03b41a832', '67552f0a13602ec03b41a8e8', '67552f0a13602ec03b41a882', '67552f0a13602ec03b41a7ae', '67552f0a13602ec03b41a8e6', '67552f0a13602ec03b41a7c0', '67552f0a13602ec03b41a8e9', '67552f0a13602ec03b41a83e', '67552f0a13602ec03b41a79a', '67552f0a13602ec03b41aa06', '67552f0a13602ec03b41a7bc', '67552f0a13602ec03b41a85c', '67552f0b13602ec03b41aabb', '67552f0a13602ec03b41a7ad', '67552f0a13602ec03b41a830', '67552f0a13602ec03b41a9a7']

    entries = re.split(r'---- id:', content)[1:]  # 先去掉开头的空字符串
    prompt_tokens_value_list = []
    completion_tokens_value_list = []
    duration_value_list = []

    for entry in entries:
        # 提取id
        id_match = re.match(r'([a-f0-9]{24})', entry)
        if id_match:
            id_value = id_match.group(1)
            print(id_value)
            if id_value not in nice_ids:
                continue
            # 正则表达式匹配数值
            prompt_tokens = re.search(r"Total prompt tokens:\s*(\d+)", entry)
            completion_tokens = re.search(r"Total completion tokens:\s*(\d+)", entry)
            duration = re.search(r"Duration:\s*([\d.]+)", entry)

            # 提取匹配的数值
            prompt_tokens_value = int(prompt_tokens.group(1)) if prompt_tokens else None
            completion_tokens_value = int(completion_tokens.group(1)) if completion_tokens else None
            duration_value = float(duration.group(1)) if duration else None

            prompt_tokens_value_list.append(prompt_tokens_value)
            completion_tokens_value_list.append(completion_tokens_value)
            duration_value_list.append(duration_value)
            # print(prompt_tokens_value_list)
            # print(completion_tokens_value_list)
            # assert 1==0

    print("Total prompt tokens:", sum(prompt_tokens_value_list)/len(prompt_tokens_value_list)/25*15)
    print("Total completion tokens:", sum(completion_tokens_value_list)/len(completion_tokens_value_list)/25*15)
    print("Duration:", sum(duration_value_list)/len(duration_value_list)/25*15)

# 计算chatgpt cot 和gpt4 cot所需要的token
def count_prompt_tokens():
    from prompt_generator_format import get_cot_prompt
    path = 'outputs/DBdesign/gpt4-base_cot_0203_21_34.jsonl'
    count_len = 0
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            count_len += len(str(data['answer']).split(' '))
            count_len += len(get_cot_prompt(data['question']).split(' ')) * 1.3
        count_len /= len(lines)
    print(count_len*1.3)


def all_ids():
    path = './datasets/RSchema/annotation_0215_13_41.jsonl'
    data_ids = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            data_ids.append(data['id'])

    print(data_ids)

def schema_text_length():
    path = './datasets/RSchema/annotation_0215_13_41.jsonl'
    data_text_total_len = 0
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            question_len = len(data['question'].split(' '))
            data_text_total_len += question_len

    print(data_text_total_len/len(lines))


# base_direct_and_agent()
# trajectory_matrix()
# topic_visual()
# cast_analysis()
# count_prompt_tokens()
# all_ids()
schema_text_length()