# 自动评估关系模式的效果。
'''
可以参考之前的entailment tree的做法

1. 对每个sample中的每个schema都分开进行计算
2. 首先确定schema的数量。数量少了是没有满足需求或者是没有对数据库表进行规范化拆分，数量多了是冗余，不太可能是更细粒度的拆表。
   用什么指标：根据schema name 进行召回和准确率计算。F1 和 Allcorrect。 schema name可能还需要语义识别类的工具。
3. 确定schema中每个属性的完整性。这里的属性多了，也可以反应出来不是第三范式。
   用什么指标：同样使用 F1 和 Allcorrect 指标。
4. 主键识别。
   用什么指标：Allcorrect 指标。
5. 外键识别。
   用什么指标：Allcorrect 指标。
6. 总体的文本相似度测评。
   用什么指标：BLEURT，为了符合“文本"这个限制，我们还是将关系模式转成文本格式的描述，用固定的格式填充进去。

7. 这样算一个加权，就可以得到一个sample中所有schema的评估值，取平均值可以得到sample在对应项上的得分。
然后再为每个sample计算一个总的得分，就是把这些指标都合起来算一个总指标。

'''
import json

import numpy as np
from nltk.corpus import wordnet
# from bleurt import score
import os
import re
import spacy
# import sacrebleu
from sentence_transformers import SentenceTransformer


# 这个太慢了，用sentence-bert好了
# checkpoint = "../bleurt/BLEURT-20"
# scorer = score.BleurtScorer(checkpoint)



model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# sentences = ["This is an example sentence", "Each sentence is converted"]
# embeddings = model.encode(sentences)
# print(embeddings)


spacy_nlp = spacy.load("en_core_web_sm")

def get_jsonl(path):
    datas = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # datas = [json.loads(line) for line in lines]  # 转成list格式
        for line in lines:
            line = json.loads(line)
            datas[line['id']] = line

    return datas

def are_synonyms(word1, word2):
    synsets1 = wordnet.synsets(word1)   # 当word1和word2不是当个名词的时候，识别不出来。
    synsets2 = wordnet.synsets(word2)
    for syn1 in synsets1:
        for syn2 in synsets2:
            if syn1 == syn2:  # 检查是否属于同一个 Synset
                return True
    return False

def match_synonyms(golden_list, predict_list, mapping:dict):
    for golden_name in golden_list:
        for predict_name in predict_list:
            golden_name_split = golden_name.replace('Record', '').split(' ') # 用空格分开
            predict_name_split = predict_name.replace('Record', '').split(' ')
            if len(golden_name_split) != len(predict_name_split):
                continue
            golden_name_split = ['ID' if n.lower()=='number' else n for n in golden_name_split]
            predict_name_split = ['ID' if n.lower()=='number' else n for n in predict_name_split]
            if golden_name.lower() == predict_name.lower(): # 完全相等
                mapping[golden_name] = predict_name
                break
            flag = True
            for g_name, p_name in zip(golden_name_split, predict_name_split):
                if not are_synonyms(g_name, p_name):
                    flag = False
                    break
            if flag:
                # print(golden_name, predict_name, 'yes')
                mapping[golden_name] = predict_name
                break




def schema_name_similarity(references:list, candidates:list, mapping:dict, threshold=0.6):
    # 先把所有的list都转为embedding
    references_embeddings = model.encode(references)
    candidates_embeddings = model.encode(candidates)
    # print(embeddings)

    for i, golden_name in enumerate(references):
        if golden_name not in mapping:
            for j, predict_name in enumerate(candidates):
                if predict_name not in list(mapping.values()):
                    # scores = scorer.score(references=[golden_name], candidates=[predict_name])
                    scores = references_embeddings[i] @ candidates_embeddings[j]
                    print(golden_name, predict_name, scores)
                    # if scores[0] > threshold:
                    if scores.item() > threshold:
                        # threshold = max(scores[0], threshold)
                        threshold = max(scores.item(), threshold)
                        # print(f"golen name: {golden_name}, predict_name: {predict_name}, similarity scores: {scores[0]} ")
                        mapping[golden_name] = predict_name



def sent_overlap(sent1, sent2, spacy_nlp, thre=-1):
    def LCstring(string1, string2):
        len1 = len(string1)
        len2 = len(string2)
        res = [[0 for i in range(len1 + 1)] for j in range(len2 + 1)]
        result = 0
        for i in range(1, len2 + 1):
            for j in range(1, len1 + 1):
                if string2[i - 1] == string1[j - 1]:
                    res[i][j] = res[i - 1][j - 1] + 1
                    result = max(result, res[i][j])
        return result

    spacy_nlp.Defaults.stop_words.add("record")

    doc1 = spacy_nlp(sent1)
    doc2 = spacy_nlp(sent2)

    word_set1 = set([token.lemma_ for token in doc1 if not (token.is_stop or token.is_punct)])
    word_set2 = set([token.lemma_ for token in doc2 if not (token.is_stop or token.is_punct)])

    if thre == -1:
        # do not use LCstring
        if len(word_set1.intersection(word_set2)) > 0:
            return True
        else:
            return False

    # use LCstring
    max_socre = -1
    for word1 in word_set1:
        for word2 in word_set2:
            if word1==word2:
                continue
            lcs = LCstring(word1, word2)
            score = lcs / min(len(word1), len(word2))
            max_socre = score if score > max_socre else max_socre
    if max_socre > thre:
        return True
    else:
        return False


def schema_sent_overlap(references:list, candidates:list, mapping:dict):
    for golden_name in references:
        if golden_name not in mapping:
            for predict_name in candidates:
                if predict_name not in list(mapping.values()):
                    if sent_overlap(golden_name.lower(), predict_name.lower(), spacy_nlp, thre=0.75):
                        mapping[golden_name] = predict_name


def schema_attributes_match(golden_schema:dict, candidates_schema:dict, mapping:dict):
    for golden_name in golden_schema.keys():
        if golden_name not in mapping:
            for predict_name in candidates_schema.keys():
                if predict_name not in list(mapping.values()):
                    golden_attributes = golden_schema[golden_name]['Attributes']
                    predict_attributes = candidates_schema[predict_name]['Attributes']
                    attribute_mapping = {}
                    match_synonyms(golden_attributes, predict_attributes, attribute_mapping)
                    # 再加一层相似度
                    schema_name_similarity(golden_attributes, predict_attributes, attribute_mapping)
                    # 加字符串匹配
                    schema_sent_overlap(golden_attributes, predict_attributes, attribute_mapping)
                    if (len(list(attribute_mapping.keys()))/len(golden_schema[golden_name]['Attributes'])) > 0.8:
                            mapping[golden_name] = predict_name


def align_predict_and_golden(predict:json, golden:json, schema_mapping:json, sample_attribute_mapping:json):
    aligned_predict = {}
    aligned_golden = {}
    for key in schema_mapping: # dict 是按插入顺序的，没有在内部自动对key进行排序
        aligned_golden[key] = golden[key]
        aligned_predict[schema_mapping[key]] = predict[schema_mapping[key]]
    # 填入剩下的schema
    for key in golden:
        if key not in aligned_golden:
            aligned_golden[key] = golden[key]
    for key in predict:
        if key not in aligned_predict:
            aligned_golden[key] = predict[key]

    # 接下来对齐属性, 也都要同时改golden 和predict 中属性的顺序
    for key in schema_mapping:
        aligned_golden[key]['Attributes'] = []  #先置空
        aligned_predict[schema_mapping[key]]['Attributes'] = []
        for attribute in sample_attribute_mapping[key]:
            aligned_golden[key]['Attributes'].append(attribute)
            aligned_predict[schema_mapping[key]]['Attributes'].append(sample_attribute_mapping[key][attribute])
        # 填入剩下的
        for attribute in golden[key]['Attributes']:
            if attribute not in aligned_golden[key]['Attributes']:
                aligned_golden[key]['Attributes'].append(attribute)
        for attribute in predict[schema_mapping[key]]['Attributes']:
            if attribute not in aligned_predict[schema_mapping[key]]['Attributes']:
                aligned_predict[key]['Attributes'].append(attribute)

    return aligned_predict, aligned_golden



def evaluate(golden:json, predict:json):
    golden_schemas_names = list(golden.keys())
    predict_schemas_names = list(predict.keys())

    # 2. schema个数的f1
    schema_mapping = {}  # 改变了schema_mapping的值
    print(f"golden schemas: {golden_schemas_names}")
    print(f"predict schemas: {predict_schemas_names}")
    match_synonyms(golden_schemas_names, predict_schemas_names, schema_mapping)  # TODO 这里只用同义词太不全面了
    print(schema_mapping)
    # 再加一个n-gram的匹配
    schema_sent_overlap(golden_schemas_names, predict_schemas_names, schema_mapping)
    print(schema_mapping)
    # 再加一层相似度
    schema_name_similarity(golden_schemas_names, predict_schemas_names, schema_mapping)
    print(schema_mapping)
    # # 再加一个属性识别 属性相同
    # schema_attributes_match(golden, predict, schema_mapping)
    # print(schema_mapping)

    schema_precision = len(schema_mapping)/len(predict_schemas_names)
    schema_recall = len(schema_mapping)/len(golden_schemas_names)
    schema_f1 = 2*schema_precision*schema_recall/(schema_precision+schema_recall) #if schema_precision+schema_recall!=0 else 0
    # 表示这个sample的schema是不是全部
    schema_all_correct = 1 if schema_f1==1 else 0

    sample_attribute_f1 = 0
    sample_attribute_all_correct = 0
    sample_primary_key = 0
    sample_foreign_key = 0
    sample_attribute_mapping = {}
    sample_golden_schema_description = []
    sample_predict_schema_description = []
    for schema_name in schema_mapping:
        # 3. 确定schema中每个属性的完整性
        golden_attributes = golden[schema_name]['Attributes']
        predict_attributes = predict[schema_mapping[schema_name]]['Attributes']
        attribute_mapping = {}
        print(f"golden attributtes: {golden_attributes}")
        print(f"predict attributtes: {predict_attributes}")
        print('^^^^^^^^^ attributes ^^^^^^^^^^^')
        match_synonyms(golden_attributes, predict_attributes, attribute_mapping)
        print(attribute_mapping)
        # 再加一层相似度
        schema_name_similarity(golden_attributes, predict_attributes, attribute_mapping)
        print(attribute_mapping)
        # 字符串匹配
        schema_sent_overlap(golden_attributes, predict_attributes, attribute_mapping)
        print(attribute_mapping)

        sample_attribute_mapping[schema_name] = attribute_mapping
        attribute_precision = len(attribute_mapping)/len(predict_attributes)
        attribute_recall = len(attribute_mapping)/len(golden_attributes)
        attribute_f1 = 2*attribute_precision*attribute_recall/(attribute_precision+attribute_recall+1e-5)
        print(f"attribute f1:{attribute_f1}")
        sample_attribute_f1 += attribute_f1
        sample_attribute_all_correct += 1 if abs(attribute_f1-1)<1e-3 else 0
        # 4. 确定schema中的主键情况，必须完全一致
        golden_primary_keys = golden[schema_name]['Primary key']
        predict_primary_keys = predict[schema_mapping[schema_name]]['Primary key']
        if len(golden_primary_keys)!=len(predict_primary_keys):
            flag = False
        else:
            flag = True
            for primary_key in golden_primary_keys:
                if primary_key not in attribute_mapping or attribute_mapping[primary_key] not in predict_primary_keys:
                    flag = False
                    break
        sample_primary_key += 1 if flag else 0
        # 5. 确定schema中的外键情况，必须完全一致
        if 'Foreign key' in golden[schema_name]:
            golden_foreign_keys = golden[schema_name]['Foreign key']
        else:
            golden_foreign_keys = {}
        if 'Foreign key' in predict[schema_mapping[schema_name]]:
            predict_foreign_keys = predict[schema_mapping[schema_name]]['Foreign key']
        else:
            predict_foreign_keys = {}
        # 把predict_foreign_keys 改成跟golden一样，再比较是不是一样的 TODO 这里还需要改
        if len(golden_foreign_keys)!=len(predict_foreign_keys):
            flag = False
        else:
            flag = True
            # for foreign_key, foreign_item in predict_foreign_keys.items():
            #     if foreign_key not in attribute_mapping or attribute_mapping[foreign_key] not in list(predict_foreign_keys.keys()):
            #         flag = False
            #         break
            #     for item_key, item_value in foreign_item.items():
            #         if item_key not in schema_mapping or item_value not in sample_attribute_mapping[item_key]:
            #             flag = False
            #             break
            #     if not flag:
            #         break
        sample_foreign_key += 1 if flag else 0

    sample_attribute_f1_avg = sample_attribute_f1/len(golden_schemas_names)
    sample_attribute_all_correct_avg = sample_attribute_all_correct/len(golden_schemas_names)
    sample_primary_key_avg = sample_primary_key/len(golden_schemas_names)
    sample_foreign_key_avg = sample_foreign_key/len(golden_schemas_names)

    if (sample_primary_key_avg+sample_foreign_key_avg+sample_attribute_all_correct_avg+schema_all_correct)>3.9:
        schema_all_correct_full = 1
    else:
        schema_all_correct_full = 0

    score_json = {
                  "schema mapping": schema_mapping,
                  "attribute mapping":sample_attribute_mapping,
                  "schema f1": schema_f1,
                  "schema allcorrect": schema_all_correct,
                  "attribute f1 avg": sample_attribute_f1_avg,
                  "attribute allcorrect avg": sample_attribute_all_correct_avg,
                  "primary key avg": sample_primary_key_avg,
                  "foreign key avg": sample_foreign_key_avg,
                  "schema allcorrect full": schema_all_correct_full
                  }

    return score_json


def avg_scores(score_list: list):
    avg_score = {}
    length = len(score_list)
    for score in score_list:
        for key in score:
            if key not in avg_score:
                avg_score[key] = score[key]
            else:
                avg_score[key] += score[key]
    for key in avg_score:
        avg_score[key] = avg_score[key]/length

    avg_score_allcorrect = {}
    for key in avg_score:
        if key in ['schema f1', 'schema allcorrect', 'schema similarity full']:
            avg_score_allcorrect[key] = avg_score[key]
        else:
            avg_score_allcorrect[key] = avg_score[key]*avg_score['schema allcorrect']

    return avg_score, avg_score_allcorrect


def transform_json(data:json):
    def split_camel_case(s):
        # 使用正则表达式将驼峰式命名的字符串分割为单词
        return re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', s)
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            new_key = split_camel_case(key)
            new_value = transform_json(value)
            new_dict[new_key] = new_value
        return new_dict
    elif isinstance(data, list):
        return [transform_json(item) for item in data]
    elif isinstance(data, str):
        return split_camel_case(data)
    else:
        return data


def main():
    # 对所有的sample进行测试。
    golden_answer_path = ['./datasets/RSchema/annotation_0203_21_34.jsonl']   # 这个是通过prepared_data.py处理后的，跟predict的格式一样。
    predict_answer_path = ['./outputs/DBdesign/gpt4_chat_pipeline_0203_21_34.jsonl']
    save_path = 'outputs/DBdesign/evaluation_91/gpt4_chat_pipeline_0203_21_34_91_evaluation.jsonl'

    golden_answer = {}
    for path in golden_answer_path:
        each_golden_answer = get_jsonl(path)
        golden_answer |= {k: v for k, v in each_golden_answer.items() if k not in golden_answer}

    predict_answer = {}
    for path in predict_answer_path:
        each_predict_answer = get_jsonl(path)
        predict_answer |= {k: v for k, v in each_predict_answer.items() if k not in predict_answer}

    # assert len(golden_answer)==len(predict_answer)
    # score_list = []
    # 先判断predict id 全部在golden id 里面
    count = 0
    for key in predict_answer:
        if key not in golden_answer:
            print(key)
            count += 1
    if count > 0:
        assert 1 == 0

    nice_ids = ['67552f0a13602ec03b41a7bb', '67552f0a13602ec03b41a823', '67552f0a13602ec03b41aa06', '67552f0a13602ec03b41a964', '67552f0a13602ec03b41a7d9', '67552f0a13602ec03b41a899', '67552f0a13602ec03b41a88c', '67552f0a13602ec03b41a830', '67552f0a13602ec03b41a798', '67552f0a13602ec03b41a85f', '67552f0a13602ec03b41a954', '67552f0a13602ec03b41a86e', '67552f0a13602ec03b41a8fb', '67552f0a13602ec03b41a7d4', '67552f0a13602ec03b41a817', '67552f0a13602ec03b41a94e', '67552f0a13602ec03b41a913', '67552f0a13602ec03b41a912', '67552f0a13602ec03b41a9e7', '67552f0a13602ec03b41a7af', '67552f0b13602ec03b41aa56', '67552f0a13602ec03b41a78c', '67552f0a13602ec03b41a7d8', '67552f0a13602ec03b41a825', '67552f0a13602ec03b41a7e6', '67552f0a13602ec03b41a95e', '67552f0a13602ec03b41a82f', '67552f0b13602ec03b41aa40', '67552f0a13602ec03b41a816', '67552f0a13602ec03b41a808', '67552f0a13602ec03b41a8e9', '67552f0a13602ec03b41a95f', '67552f0a13602ec03b41a9e1', '67552f0a13602ec03b41a8ee', '67552f0a13602ec03b41a987', '67552f0a13602ec03b41a895', '67552f0a13602ec03b41a794', '67552f0a13602ec03b41a7bc', '67552f0a13602ec03b41a9f3', '67552f0a13602ec03b41a7fe', '67552f0a13602ec03b41a9d3', '67552f0a13602ec03b41a7d7', '67552f0a13602ec03b41a8c7', '67552f0a13602ec03b41a821', '67552f0a13602ec03b41a7b6', '67552f0a13602ec03b41a810', '67552f0a13602ec03b41a813', '67552f0a13602ec03b41a82b', '67552f0a13602ec03b41a865', '67552f0a13602ec03b41a7da', '67552f0a13602ec03b41a7e2', '67552f0a13602ec03b41a7f6', '67552f0b13602ec03b41aa5f', '67552f0a13602ec03b41a824', '67552f0a13602ec03b41a7aa', '67552f0a13602ec03b41a96d', '67552f0a13602ec03b41a839', '67552f0a13602ec03b41a981', '67552f0a13602ec03b41a81a', '67552f0a13602ec03b41a837', '67552f0a13602ec03b41a801', '67552f0a13602ec03b41a7fa', '67552f0a13602ec03b41a966', '67552f0b13602ec03b41aa9d', '67552f0a13602ec03b41a83e', '67552f0a13602ec03b41a892', '67552f0b13602ec03b41aa55', '67552f0a13602ec03b41a847', '67552f0a13602ec03b41a7cb', '67552f0a13602ec03b41a938', '67552f0a13602ec03b41a982', '67552f0a13602ec03b41a8bc', '67552f0a13602ec03b41a93a', '67552f0a13602ec03b41a89a', '67552f0a13602ec03b41a7dc', '67552f0b13602ec03b41aab3', '67552f0a13602ec03b41a85c', '67552f0b13602ec03b41ab2b', '67552f0a13602ec03b41a7d5', '67552f0b13602ec03b41aabb', '67552f0a13602ec03b41a86f', '67552f0a13602ec03b41a9c9', '67552f0a13602ec03b41a79d', '67552f0a13602ec03b41a829', '67552f0a13602ec03b41a882', '67552f0a13602ec03b41a8fe', '67552f0a13602ec03b41a7a2', '67552f0b13602ec03b41aaa9', '67552f0a13602ec03b41a79a', '67552f0a13602ec03b41a7c0', '67552f0a13602ec03b41a7ab']
    fail_to_evalute = {}
    for i, predict_id in enumerate(predict_answer):
        print(f'compute sample: {i} id: {predict_id}----')
        if predict_id not in nice_ids:
            continue
        golden = golden_answer[predict_id]['answer']
        if 'predict' not in predict_answer[predict_id]:  # answer predict # agent 框架的
        # if 'schema' not in predict_answer[predict_id]['answer']:  # direct 和cot方法的
            print('empty answer ......')
            continue
        else:
            try:
                predict = predict_answer[predict_id]['predict']  # agent 框架的
                # predict = predict_answer[predict_id]['answer']['schema'] # direct 和cot方法的
                scores = evaluate(golden, predict)  # 只有schema部分
            except Exception as e:
                print(e)
                print(f"---- id: {predict_id} ----")
                fail_to_evalute[predict_id] = e
                scores = {}
            predict_answer[predict_id]['score'] = scores
            print(scores)

            # 单个保存
            with open(save_path, 'a+', encoding='utf-8') as f:
                f.write(json.dumps(predict_answer[predict_id]) + '\n')

    print(fail_to_evalute)
    print(f'finish saving to file: {save_path}')



    # for i, (golden, predict) in enumerate(zip(golden_answer, predict_answer)):
    #     # assert golden['id'] == predict['id']
    #     print(f'compute sample {i} ----')
    #     # if i in [2,4,5,6]:
    #     #     print('continue')
    #     #     continue
    #     # if i==4:
    #     golden = golden['answer']
    #     predict = predict['answer']['schema']
    #     # 将ProductID 这类型的单词换成product ID
    #     golden = transform_json(golden)
    #     predict = transform_json(predict)
    #     scores = evaluate(golden, predict)  # 只有schema部分
    #     score_list.append(scores)
    #
    # avg_score, avg_score_allcorrect = avg_scores(score_list)
    # print(avg_score)
    # print(avg_score_allcorrect)


main()
# dd = {}
# match_synonyms(['User', 'Mail', 'Attachment', 'Mail Recipient', 'Mail Attachment'],
#                ['User', 'Email', 'Recipient', 'Attachment', 'Send', 'Send-To', 'Have-Attachment'],
#                dd)
# print(dd)
