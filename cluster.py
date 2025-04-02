# 对标注好的数据进行聚类，看看他们是属于什么领域的
import json
import os
import pickle
import random
from collections import Counter

import numpy as np
import openai
import torch
from matplotlib import pyplot as plt
# from sentence_transformers import SentenceTransformer
# from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist
from collections import defaultdict

openai.base_url = ""
# openai.api_version = ""
openai.api_key = ""
openai.default_headers = {"x-foo": "true"}


def cluster_question():
    def get_embedding(text):
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding

    path = 'datasets/RSchema/annotation_0203_21_34.jsonl'
    output_path = 'datasets/Cluster_data/annotation_0203_21_34.jsonl'
    datas = []
    questions = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = json.loads(line)
            datas.append(line)
            questions.append(line['question'])

    # 先得到所有rule的embedding
    model = SentenceTransformer('/media/hnu/LLM/MiniCPM-Embedding', trust_remote_code=True,
                                model_kwargs={"attn_implementation": "flash_attention_2", "torch_dtype": torch.float16})
    if os.path.exists('data_embedding.pkl'):
        with open('data_embedding.pkl', 'rb') as fin:
            embeddings = pickle.load(fin)
        print('load saved pkl.')
    else:
        embeddings = np.vstack([get_embedding(data['question'][:20]) for data in datas])
        embeddings = embeddings.astype('float32')
        with open('data_embedding.pkl', mode='wb') as f:
            pickle.dump(embeddings, f)
        print('finish saving pkl.')

    K = range(20, 80, 1)

    # 用肘部法则SSE（误差平方和）判断最好的K值
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

    sse_result = []
    for n in K:
        k_model = KMeans(n_clusters=n, random_state=42).fit(embeddings)  # 定义6种大标签
        y_pred = k_model.predict(embeddings)
        print(y_pred)
        print(Counter(y_pred))
        sse_result.append(
            sum(np.min(cdist(embeddings, k_model.cluster_centers_, 'euclidean'), axis=1)) / len(embeddings))

        # 输出看看
        n_dict = {i: [] for i in range(n)}
        for i in range(len(y_pred)):
            n_dict[y_pred[i]].append(i)

        # 新加列保存
        for i, (data, pred)in enumerate(zip(datas, y_pred)):
            datas[i]['topic'] = pred.item()
        # 保存
        with open(output_path+str(n),'w', encoding='utf-8') as f:
            for data in datas:
                f.write(json.dumps(data) + '\n')
        print('成功保存文件!!')

    plt.plot(K, sse_result, 'gx-')
    plt.xlabel('k')
    plt.ylabel(u'average')
    plt.title(u'best K-means cluster')
    plt.savefig('最佳聚类数量.png')
    plt.show()


def cluster_type():
    path = 'datasets/Cluster_data/annotation_0203_21_34.jsonl26'
    question_dict = defaultdict(list)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = json.loads(line)
            question_dict[str(line['topic'])].append(line['question'])

    outputs = {}
    print(question_dict.keys())
    print([len(question_dict[key]) for key in question_dict])
    for key in question_dict:
        print(question_dict[key][:10])
        assert 1==0
        input_text = '\n'.join(question_dict[key][:10])+'The above are 10 examples, please summarize their respective fields.'
        response = openai.chat.completions.create(
            model='gpt-4o',
            top_p=1,  # top_p的意思是选择概率质量值之和达到top_p的概率分布采样结果
            messages=[{"role": "user", "content": input_text}],
        )
        print(response.choices[0].message.content)
        assert 1==0
        outputs[key] = response.choices[0].message.content
    print(outputs)

def cluster_primary_api():
    # 先对系统进行总结
    # path = 'datasets/RSchema/annotation_0203_21_34.jsonl'
    output_path = 'datasets/Cluster_data/annotation_0203_21_34_api.jsonl'
    datas = []
    questions = []
    remind_ids = ['2', '6', '14', '20', '36', '57', '74', '80', '81', '90', '91', '98', '101', '103', '113', '123',
                  '126', '131', '144', '156', '167', '168', '170', '171', '172', '175', '178', '180', '181', '184',
                  '195', '204', '206', '207', '208', '220', '224', '226', '227', '234', '235', '241', '242', '244',
                  '245', '247', '248', '251', '252', '254', '255', '256', '262', '263', '272', '274', '275', '276',
                  '278', '280', '284', '285', '291', '300', '301', '303', '304', '306', '307', '310', '311', '312',
                  '313', '316', '318', '321', '332', '345', '352']
    # remind_ids = []
    with open(output_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = json.loads(line)
            datas.append(line)
            questions.append(line['question'])
            if 'topic' not in line:
                remind_ids.append(str(i))
    print(remind_ids)
    print(len(remind_ids))
    input_text = ''
    # for i, question in enumerate(questions):
    for id in remind_ids:
        input_text += f'example {id} : '+ questions[int(id)] + '\n'
    input_text += 'The above is some data. Please classify them and return them in JSON format. The JSON format is {{"System Domain Category Name": ["1","3"]}}. The values in the value list are the numbers of examples. Please do not generate unnecessary explanations.'
    print(input_text)
    print(len(input_text))
    response = openai.chat.completions.create(
            model='gpt-4o',
            top_p=1,  # top_p的意思是选择概率质量值之和达到top_p的概率分布采样结果
            messages=[{"role": "user", "content": input_text}],
        )
    answer = response.choices[0].message.content
    print(answer)
    answer = json.loads(answer.replace('```json','').replace('```',''))
    ids = []
    for key in answer:
        for value in answer[key]:
            datas[int(value)]['topic'] = key
        ids.extend(answer[key])
    with open(output_path, 'w', encoding='utf-8') as f:
        for data in datas:
            f.write(json.dumps(data) + '\n')
    print('成功保存文件!!')
    print(ids)


def cluster_outline_api():
    # 先对系统进行总结
    # path = 'datasets/RSchema/annotation_0203_21_34.jsonl'
    output_path = 'datasets/Cluster_data/annotation_0203_21_34_api.jsonl'
    datas = []
    topics = []
    remind_ids = []
    with open(output_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = json.loads(line)
            datas.append(line)
            if 'topic' not in line:
                remind_ids.append(str(i))
            else:
                topics.append(line['topic'])
    print(remind_ids)
    print(len(remind_ids))
    input_text = ''


    # for i, question in enumerate(questions):
    for id in remind_ids:
        input_text += f'example {id} : '+ questions[int(id)] + '\n'
    input_text += 'The above is some data. Please classify them and return them in JSON format. The JSON format is {{"System Domain Category Name": ["1","3"]}}. The values in the value list are the numbers of examples. Please do not generate unnecessary explanations.'
    print(input_text)
    print(len(input_text))
    response = openai.chat.completions.create(
            model='gpt-4o',
            top_p=1,  # top_p的意思是选择概率质量值之和达到top_p的概率分布采样结果
            messages=[{"role": "user", "content": input_text}],
        )
    answer = response.choices[0].message.content
    print(answer)
    answer = json.loads(answer.replace('```json','').replace('```',''))
    ids = []
    for key in answer:
        for value in answer[key]:
            datas[int(value)]['topic'] = key
        ids.extend(answer[key])
    with open(output_path, 'w', encoding='utf-8') as f:
        for data in datas:
            f.write(json.dumps(data) + '\n')
    print('成功保存文件!!')
    print(ids)


def counter_cluster():
    path = 'datasets/Cluster_data/annotation_0203_21_34_api.jsonl'
    datas = []
    topic_dict = defaultdict(list)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = json.loads(line)
            datas.append(line)
            topic_dict[str(line['topic'])].append(str(i))

    print(topic_dict)
    topic_list = list(topic_dict.keys())
    # input_text = ''
    # for i, topic in enumerate(topic_list):
    #     input_text += f'domain {i} : '+ topic + '\n'
    # input_text += ('The above are some classifications that management systems belong to. You need to cluster them into industry categories, and the number of categories should not exceed 50.'
    #                ' Return them in JSON format. The JSON format is {{"Domain Category Name": ["1","3"]}}. The values in the value list are the numbers of examples. Please do not generate unnecessary explanations.')
    # print(input_text)
    # response = openai.chat.completions.create(
    #     model='gpt-4o',
    #     top_p=1,  # top_p的意思是选择概率质量值之和达到top_p的概率分布采样结果
    #     messages=[{"role": "user", "content": input_text}],
    # )
    # answer = response.choices[0].message.content
    # print(answer)
    # answer = json.loads(answer.replace('```json', '').replace('```', ''))

    answer = {
    "Aerospace and Travel": ["0", "71", "215"],
    "Transportation and Vehicle Management": ["1", "18", "64", "109", "142"],
    "Supply Chain and Logistics": ["2", "96", "123"],
    "Telecommunications and Networking": ["3", "207"],
    "Software and IT Services": ["4", "59", "52", "53", "78", "81", "86", "97", "99", "212", "72", "222", "174", "200", "193", "138", "221", "178", "145", "171", "194", "173", "227", "179"],
    "Media and Broadcasting": ["5", "27", "158"],
    "Equipment and Machinery Management": ["6", "35", "34", "229"],
    "Government and Public Administration": ["7", "11", "125"],
    "Agriculture and Food Production": ["8", "13", "100", "176"],
    "Food and Beverage": ["9", "217"],
    "Human Resources and Employee Management": ["10", "58", "10", "218"],
    "Commercial and Retail": ["22", "23", "24", "49", "26", "25", "101", "91", "87", "133", "122", "124"],
    "Education Management": ["83", "131", "132", "189", "95", "212", "224", "131", "238"],
    "Technology and Science": ["40", "194"],
    "Insurance and Financial Services": ["46", "245", "209", "165", "245"],
    "E-commerce Platforms": ["49", "91", "87"],
    "Healthcare and Medical Services": ["110", "235"],
    "Hospitality and Events": ["115", "151", "57"],
    "Real Estate and Construction": ["21", "22", "24"],
    "Retail and Wholesale": ["26", "25", "133"],
    "Banking and Financial Management": ["163", "164", "213"],
    "Information and Data Management": ["42", "43", "112", "195", "240"],
    "Business and Enterprises": ["41", "54", "76", "82", "231", "191", "241", "245"],
    "Writing and Manuscripts": ["28", "50", "105"],
    "Environment and Natural Resources": ["161", "30"],
    "Mining and Safety": ["44", "45", "45"],
    "Music and Entertainment": ["29", "185", "159"],
    "Commerce and Retail": ["87", "26", "101"],
    "Sports and Recreation": ["90", "124"],
    "Consulting and Business Services": ["128", "129"],
    "Subscription and Membership": ["136", "68", "211"],
    "Internet and Digital Solutions": ["87", "166"],
    "Security and Access Control": ["75", "171", "145"],
    "Legal and Patent Management": ["37", "166"],
    "Utilities and Services": ["33", "125"],
    "Hospitality Management": ["151", "115"],
    "Content Management": ["169", "205"],
    "Communication and Social Media": ["81", "67", "77", "186"],
    "Electronics and Technical Services": ["19", "148"],
    "Publishing and Media": ["5", "150"],
    "Corporate and Business Management": ["54", "241"],
    "Legal and Compliance": ["164", "166"],
    "Network and Internet Services": ["226", "193"],
    "Food and Hospitality": ["151", "239", "151"],
    "Property and Estate Management": ["22", "122", "23"]
}

    categorys = ['' for i in range(len(datas))]
    for category in answer:
        topic_ids = answer[category]
        each_category = []  #每个分类中的所有topic所在的data
        for topic_id in topic_ids:
            if int(topic_id)>=len(topic_list):
                print(topic_id)
            each_category.extend(topic_dict[topic_list[int(topic_id)]])
        for cate in each_category:
            categorys[int(cate)]= category
    print(categorys)
    print(len(categorys))

    assert len(categorys) == len(datas)
    # save
    for i, item in enumerate(datas):
        datas[i]['category'] = categorys[i]

    with open(path, 'w', encoding='utf-8') as f:
        for data in datas:
            f.write(json.dumps(data) + '\n')
    print('成功分类领域类别。')


# 采样
def sample_per_category():
    path = 'datasets/Cluster_data/annotation_0203_21_34_api.jsonl'
    output_path = 'datasets/RSchema/annotation_0203_21_34_sample.jsonl'
    datas = []
    category_dict = defaultdict(list)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            line = json.loads(line)
            datas.append(line)
            category_dict[line['category']].append(i)
    print(category_dict)
    sample_datas = []
    for category in category_dict:
        sample_ids = random.sample(category_dict[category], min(2, len(category_dict[category])))
        for sample_id in sample_ids:
            sample_datas.append(datas[sample_id])
    print(len(sample_datas))

    # save
    with open(output_path,'w',encoding='utf-8') as f:
        for data in sample_datas:
            f.write(json.dumps(data) + '\n')
    print('成功保存文件！')

# 将还没有大类的小类进行分类
def category_rest_data():
    path = 'datasets/Cluster_data/annotation_0203_21_34_api.jsonl'
    category_topic = []
    categorys = []
    ids = []
    datas = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            datas[data['id']] = data
            if data['category']=='':
                category_topic.append(data['topic'])
                ids.append(data['id'])
            elif data['category'] not in categorys:
                categorys.append(data['category'])
    print(f"待处理：{len(ids)}")
    input_text = ''
    for i, topic in enumerate(category_topic):
        input_text += f'domain {i} : '+ topic + '\n'
    categorys_text = ', '.join(categorys)
    input_text += (f'The above are some classifications that management systems belong to. You need to classify them into industry categories. Industry category includes {categorys_text}. \n'
                   ' Return them in JSON format. The JSON format is {{"Domain Category Name": ["1","3"]}}. The values in the value list are the numbers of examples. Please do not generate unnecessary explanations.')
    print(input_text)
    response = openai.chat.completions.create(
        model='gpt-4o',
        top_p=1,  # top_p的意思是选择概率质量值之和达到top_p的概率分布采样结果
        messages=[{"role": "user", "content": input_text}],
    )
    answer = response.choices[0].message.content
    print(answer)
    answer = json.loads(answer.replace('```json', '').replace('```', ''))
    count = 0
    for category in answer:
        topic_ids = answer[category]
        for topic_id in topic_ids:
            datas[ids[int(topic_id)]]['category'] = category
            count += 1
    print(f"已处理:{count}")
    # save
    with open(path, 'a+', encoding='utf-8') as f:
        for key in datas:
            f.write(json.dumps(datas[key]) + '\n')


# cluster_question()
# cluster_type(
# cluster_api()
# counter_cluster()
# sample_per_category()
category_rest_data()