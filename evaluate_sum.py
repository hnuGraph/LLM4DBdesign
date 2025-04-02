# 对所有数据进行统计
import json
import os
import re


def remove_empty_score():
    dir_path = 'outputs/DBdesign/evaluation/'
    file_names = os.listdir(dir_path)
    save_dir = 'outputs/DBdesign/evaluation_without_empty'

    for file_name in file_names:
        print(file_name)
        if not file_name.endswith('evaluation.jsonl'):
            continue
        save_datas = []
        file_path = os.path.join(dir_path, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                data = json.loads(line)
                if 'score' in data and len(list(data['score'].keys())) > 0:
                    save_datas.append(data)
        with open(os.path.join(save_dir, file_name), 'w', encoding='utf-8') as f:
            for data in save_datas:
                f.write(json.dumps(data) + '\n')
        print(f'before:{len(lines)}, after:{len(save_datas)}')



def avg_scores(score_list: list):
    avg_score = {}
    length = len(score_list)
    for i, score in enumerate(score_list):
        if len(score) == 0:
            length -= 1
        for key in score:
            if 'mapping' in key:  # 因为有些evaluation 中保存了schema mapping 和attribute mapping
                continue
            if key not in avg_score:
                avg_score[key] = score[key]
            else:
                avg_score[key] += score[key]
            # if score[key] <0.3:
            #     print(f'{i} --- {key}:{score[key]}')
    for key in avg_score:
        avg_score[key] = avg_score[key]/length

    # avg_score_allcorrect = {}
    # for key in avg_score:
    #     if key in ['schema f1', 'schema allcorrect', 'schema similarity full']:
    #         avg_score_allcorrect[key] = avg_score[key]
    #     else:
    #         avg_score_allcorrect[key] = avg_score[key]*avg_score['schema allcorrect']

    return avg_score, length

def get_data_sum():
    dir_path = 'outputs/DBdesign_domain/'
    file_names = os.listdir(dir_path)
    save_path = 'outputs/DBdesign_domain/result.jsonl'
    for file_name in file_names:
        if not file_name.endswith('evaluation.jsonl') and not file_name.startswith('healthcare'):
            continue

        file_path = os.path.join(dir_path, file_name)
        data_score_list = []
        print(file_name)
        exist_ids = []
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                try:
                    data = json.loads(line)
                except:
                    try:
                        data = json.loads(line.replace("'", '"'))
                    except:
                        pattern = r'(schema":\s*)(.*)$'
                        def replace_single_quotes(match):
                            # 匹配 answer": {...} 部分，并替换单引号
                            prefix = match.group(1)  # answer":
                            json_str = match.group(2)  # {...} 部分
                            json_str = json_str.replace("'", '"')  # 替换单引号为双引号
                            return prefix + json_str

                        # 执行替换
                        line = re.sub(pattern, replace_single_quotes, line, flags=re.DOTALL)
                        data = json.loads(line)
                if data['id'] != '67552f0a13602ec03b41a9cb':
                    continue
                if 'score' in list(data.keys()) and data['id'] not in exist_ids:
                    data_score_list.append(data['score'])
                    exist_ids.append(data['id'])

        print(f' score存在的个数：{len(data_score_list)}')
        avg_score, length = avg_scores(data_score_list)  # 随机取前30个吧
        print(avg_score)
        with open(save_path, 'a+', encoding='utf-8') as f:
            f.write(f'{file_name} length:{length} ' + json.dumps(avg_score) + '\n')

    print('成功输出到文件')


def compare_between():
    base_direct_path = 'outputs/DBdesign/evaluation_91/deepseek_base_direct_0203_21_34_91_evaluation.jsonl'
    agent_path = 'outputs/DBdesign/evaluation_91/deepseek_chat_agent_0203_21_34_91_evaluation.jsonl'
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

    # nice_ids = ['67552f0a13602ec03b41a7bb', '67552f0a13602ec03b41a823', '67552f0a13602ec03b41aa06', '67552f0a13602ec03b41a964', '67552f0a13602ec03b41a7d9', '67552f0a13602ec03b41a899', '67552f0a13602ec03b41a88c', '67552f0a13602ec03b41a830', '67552f0a13602ec03b41a798', '67552f0a13602ec03b41a85f', '67552f0a13602ec03b41a954', '67552f0a13602ec03b41a86e', '67552f0a13602ec03b41a8fb', '67552f0a13602ec03b41a7d4', '67552f0a13602ec03b41a817', '67552f0a13602ec03b41a94e', '67552f0a13602ec03b41a913', '67552f0a13602ec03b41a912', '67552f0a13602ec03b41a9e7', '67552f0a13602ec03b41a7af', '67552f0b13602ec03b41aa56', '67552f0a13602ec03b41a78c', '67552f0a13602ec03b41a7d8', '67552f0a13602ec03b41a825', '67552f0a13602ec03b41a7e6', '67552f0a13602ec03b41a95e', '67552f0a13602ec03b41a82f', '67552f0b13602ec03b41aa40', '67552f0a13602ec03b41a816', '67552f0a13602ec03b41a808', '67552f0a13602ec03b41a8e9', '67552f0a13602ec03b41a95f', '67552f0a13602ec03b41a9e1', '67552f0a13602ec03b41a8ee', '67552f0a13602ec03b41a987', '67552f0a13602ec03b41a895', '67552f0a13602ec03b41a794', '67552f0a13602ec03b41a7bc', '67552f0a13602ec03b41a9f3', '67552f0a13602ec03b41a7fe', '67552f0a13602ec03b41a9d3', '67552f0a13602ec03b41a7d7', '67552f0a13602ec03b41a8c7', '67552f0a13602ec03b41a821', '67552f0a13602ec03b41a7b6', '67552f0a13602ec03b41a810', '67552f0a13602ec03b41a813', '67552f0a13602ec03b41a82b', '67552f0a13602ec03b41a865', '67552f0a13602ec03b41a7da', '67552f0a13602ec03b41a7e2', '67552f0a13602ec03b41a7f6', '67552f0b13602ec03b41aa5f', '67552f0a13602ec03b41a824', '67552f0a13602ec03b41a7aa', '67552f0a13602ec03b41a96d', '67552f0a13602ec03b41a839', '67552f0a13602ec03b41a981', '67552f0a13602ec03b41a81a', '67552f0a13602ec03b41a837', '67552f0a13602ec03b41a801', '67552f0a13602ec03b41a7fa', '67552f0a13602ec03b41a966', '67552f0b13602ec03b41aa9d', '67552f0a13602ec03b41a83e', '67552f0a13602ec03b41a892', '67552f0b13602ec03b41aa55', '67552f0a13602ec03b41a847', '67552f0a13602ec03b41a7cb', '67552f0a13602ec03b41a938', '67552f0a13602ec03b41a982', '67552f0a13602ec03b41a8bc', '67552f0a13602ec03b41a93a', '67552f0a13602ec03b41a89a', '67552f0a13602ec03b41a7dc', '67552f0b13602ec03b41aab3', '67552f0a13602ec03b41a85c', '67552f0b13602ec03b41ab2b', '67552f0a13602ec03b41a7d5', '67552f0b13602ec03b41aabb', '67552f0a13602ec03b41a86f', '67552f0a13602ec03b41a9c9', '67552f0a13602ec03b41a79d', '67552f0a13602ec03b41a829', '67552f0a13602ec03b41a882', '67552f0a13602ec03b41a8fe', '67552f0a13602ec03b41a7a2', '67552f0b13602ec03b41aaa9', '67552f0a13602ec03b41a79a', '67552f0a13602ec03b41a7c0', '67552f0a13602ec03b41a7ab']
    # nice_ids = ['67552f0a13602ec03b41a798', '67552f0a13602ec03b41a824', '67552f0a13602ec03b41a83f', '67552f0a13602ec03b41a93d', '67552f0a13602ec03b41a9c9', '67552f0a13602ec03b41a879', '67552f0a13602ec03b41a832', '67552f0a13602ec03b41a8e8', '67552f0a13602ec03b41a882', '67552f0a13602ec03b41a7ae', '67552f0a13602ec03b41a8e6', '67552f0a13602ec03b41a7c0', '67552f0a13602ec03b41a8e9', '67552f0a13602ec03b41a83e', '67552f0a13602ec03b41a79a', '67552f0a13602ec03b41aa06', '67552f0a13602ec03b41a7bc', '67552f0a13602ec03b41a85c', '67552f0b13602ec03b41aabb', '67552f0a13602ec03b41a7ad', '67552f0a13602ec03b41a830', '67552f0a13602ec03b41a9a7']
    # chatgpt
    # nice_ids = ['67552f0a13602ec03b41a7ab', '67552f0a13602ec03b41a882', '67552f0a13602ec03b41a7fe', '67552f0a13602ec03b41a798', '67552f0a13602ec03b41a86e', '67552f0a13602ec03b41a892', '67552f0a13602ec03b41a830', '67552f0a13602ec03b41a85f', '67552f0a13602ec03b41a7c0', '67552f0a13602ec03b41a821', '67552f0a13602ec03b41a824']
    # print(f"nice ids length: {len(nice_ids)}")
    # ids = list(set(base_direct_datas.keys()) & set(nice_ids))
    # ids = base_direct_datas.keys()
    ids = list(set(base_direct_datas.keys()) & set(agent_datas.keys()))  # 或者 set(list1).intersection(list2）
    # chat
    # ids = list(set(ids)-set(['67552f0a13602ec03b41a891', '67552f0a13602ec03b41a82a', '67552f0a13602ec03b41a881', '67552f0a13602ec03b41a870', '67552f0b13602ec03b41aa24', '67552f0a13602ec03b41a83f', '67552f0a13602ec03b41a984', '67552f0a13602ec03b41a7ba', '67552f0a13602ec03b41a7ce', '67552f0a13602ec03b41a789', '67552f0a13602ec03b41a9ee', '67552f0a13602ec03b41a7f9', '67552f0b13602ec03b41aaa2', '67552f0a13602ec03b41a818', '67552f0a13602ec03b41a7ac', '67552f0a13602ec03b41a898', '67552f0a13602ec03b41a971', '67552f0a13602ec03b41a91a', '67552f0a13602ec03b41a8e6', '67552f0a13602ec03b41a87a', '67552f0a13602ec03b41a983']))
    # print(ids)
    # without manager
    # ids = list(set(ids)-set(['67552f0a13602ec03b41a7e2', '67552f0a13602ec03b41a964', '67552f0a13602ec03b41a7d1', '67552f0a13602ec03b41a954', '67552f0b13602ec03b41aa6a', '67552f0a13602ec03b41a808', '67552f0a13602ec03b41a847', '67552f0a13602ec03b41a82f', '67552f0a13602ec03b41a987', '67552f0a13602ec03b41a9f3', '67552f0a13602ec03b41a891', '67552f0a13602ec03b41a7f9', '67552f0a13602ec03b41a813', '67552f0a13602ec03b41a79c', '67552f0a13602ec03b41a810', '67552f0a13602ec03b41a794', '67552f0a13602ec03b41a79d', '67552f0a13602ec03b41a7a3']))
    # print(ids)
    # without reviwer
    # ids = list(set(ids)-set(['67552f0a13602ec03b41a8e9', '67552f0a13602ec03b41a7a3', '67552f0a13602ec03b41a7e6', '67552f0a13602ec03b41a7e2', '67552f0a13602ec03b41a829', '67552f0a13602ec03b41a9f3', '67552f0a13602ec03b41a81a', '67552f0a13602ec03b41a7f5', '67552f0a13602ec03b41a7f9', '67552f0a13602ec03b41a9c9']))
    print(len(ids))
    data_score_list = []
    print(base_direct_path)
    for idd in ids:
        data_score_list.append(base_direct_datas[idd]['score'])
    avg_score = avg_scores(data_score_list)
    print(avg_score)

    data_score_list = []
    print(agent_path)
    for idd in ids:
        data_score_list.append(agent_datas[idd]['score'])
    avg_score = avg_scores(data_score_list)
    print(avg_score)

    # keys = []
    # for key in ids:
    #     if base_direct_datas[key]['score']['schema f1'] <= agent_datas[key]['score']['schema f1']:
    #         # print(key)
    #         # print(base_direct_datas[key]['score'])
    #         # print(agent_datas[key]['score'])
    #         keys.append(key)
    # print(keys)
    # print(len(keys))

    # with open('outputs/DBdesign/evaluation2/gpt4_chat_agent_0203_21_34_evaluation.jsonl', 'w', encoding='utf-8') as f:
    #     for key in keys:
    #         f.write(json.dumps(agent_datas[key]) + '\n')



def replace_data():
    file_origin = 'outputs/DBdesign/evaluation/gpt4_chat_agent_0203_21_34_evaluation.jsonl'
    file_refine = 'outputs/DBdesign/evaluation2/gpt4_chat_agent_0203_21_34_evaluation.jsonl'
    save_file = 'outputs/DBdesign/evaluation2/gpt4_chat_agent_0203_21_34_evaluation_refine.jsonl'

    origin_datas = {}
    with open(file_origin, 'r') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            origin_datas[data['id']] = data

    refine_datas = {}
    with open(file_refine, 'r') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            refine_datas[data['id']] = data

    for key in refine_datas:
        origin_datas[key] = refine_datas[key]
    #save
    with open(save_file, 'w', encoding='utf-8') as f:
        for key in origin_datas:
            f.write(json.dumps(origin_datas[key]) + '\n')

    print('成功输出到文件')


def manual_error():
    '''用于评估自动化评估指标的准确率'''
    automatic_score = {"schema f1": 0.8894191919191918, "schema allcorrect": 0.45, "attribute f1 avg": 0.7922886514249935, "attribute allcorrect avg": 0.37059523809523814, "primary key avg": 0.545, "foreign key avg": 0.6935714285714286, "schema allcorrect full": 0.05}
    manual_score = {"schema f1": 0.8549747474747473, "schema allcorrect": 0.45, "attribute f1 avg": 0.7912703876679472, "attribute allcorrect avg": 0.45690476190476187, "primary key avg": 0.5369047619047619, "foreign key avg": 0.7039285714285713, "schema allcorrect full": 0.05}

    automatic_score_list = []
    manual_score_list = []
    error_rate_list = []
    for key in automatic_score:
        a_score = automatic_score[key]
        m_score = manual_score[key]
        automatic_score_list.append(str(round(a_score,2)))
        manual_score_list.append(str(round(m_score,2)))
        error_rate = round(abs(a_score - m_score)/m_score, 2)
        error_rate_list.append(str(error_rate))

    print('手动评估结果：')
    print('\t'.join(automatic_score_list))
    print("自动化评估结果：")
    print('\t'.join(manual_score_list))
    print("自动评估的错误率：")
    print('\t'.join(error_rate_list))






# remove_empty_score()
get_data_sum()
# compare_between()
# replace_data()

# manual_error()