from data_utils import MyDataset
from api_utils import api_handler
from string import punctuation
import argparse
import tqdm
import json
from agent_format import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', default='gpt4')  # gpt4 chatgpt 
    parser.add_argument('--dataset_name', default='DBexample')
    parser.add_argument('--dataset_dir', default='./datasets/RSchema/')
    parser.add_argument('--start_pos', type=int, default=0)
    parser.add_argument('--end_pos', type=int, default=790)
    parser.add_argument('--output_files_folder', default='./outputs/DBdesign_domain')
    # parser.add_argument('--method', type=str, default='anal_only', choices=['syn_verif', 'syn_only', 'anal_only', 'base_direct', 'base_cot'])
    parser.add_argument('--method', type=str, default='base_direct',
                        choices=['expert_analyse', 'domain_analyse', 'pseudo_code_analyse', 'base_direct', 'base_cot'])
    parser.add_argument('--verification', type=str,
                        default='entity_verification, entity_denpendency_verification, relation_denpendency_verification',
                        choices=['entity_verification'])
    parser.add_argument('--max_attempt_vote', type=int, default=1) 
    parser.add_argument('--log_history', default=True)
    parser.add_argument('--few_shot', default=False)

    args = parser.parse_args()

    print(args)

    ### get handler
    if args.model_name in ['instructgpt', 'newinstructgpt', 'chatgpt', 'gpt4', 'glm4', 'deepseek']:  # select the model
        handler = api_handler(args.model_name)
    else:
        raise ValueError

    ### get dataobj
    dataobj = MyDataset('annotation_0203_21_34', args, traindata_obj=None)  # test_english
    version = '0203_21_34'
    ### set test range
    end_pos = len(dataobj) if args.end_pos == -1 else args.end_pos
    test_range = range(args.start_pos, end_pos)  # closed interval

    ### set output_file_name
    if args.verification != '' and args.method == 'domain_analyse':
        exact_output_file = f"{args.output_files_folder}/{args.model_name}-{args.method}-{args.verification}_{version}.jsonl"
    else:
        if args.few_shot:
            exact_output_file = f"healthcare_domain_{args.output_files_folder}/{args.model_name}-{args.method}_{version}_fewshot.jsonl"
        else:
            exact_output_file = f"healthcare_domain_{args.output_files_folder}/{args.model_name}-{args.method}_{version}.jsonl"
    # print(exact_output_file)
    dir_path = os.path.dirname(exact_output_file)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"dir {dir_path} create。")
    else:
        print(f"dir {dir_path} exist。")

    input_prompt = {}
    # finance_ids = ['67552f0b13602ec03b41ab51', '67552f0a13602ec03b41a84b', '67552f0a13602ec03b41a9ff',
    #                '67552f0a13602ec03b41a973', '67552f0a13602ec03b41a84e', '67552f0a13602ec03b41a952',
    #                '67552f0a13602ec03b41a9cb', '67552f0a13602ec03b41a8fe', '67552f0a13602ec03b41a82c',
    #                '67552f0a13602ec03b41a847', '67552f0a13602ec03b41a78c', '67552f0a13602ec03b41a84c',
    #                '67552f0a13602ec03b41a91b', '67552f0b13602ec03b41ab17', '67552f0a13602ec03b41a962',
    #                '67552f0a13602ec03b41a84a', '67552f0a13602ec03b41a83b', '67552f0a13602ec03b41a888',
    #                '67552f0b13602ec03b41aa5a']
    healthcare_ids = ['67552f0a13602ec03b41a9f6', '67552f0a13602ec03b41a87e', '67552f0a13602ec03b41a91d',
                      '67552f0b13602ec03b41aa5c', '67552f0a13602ec03b41a9fb', '67552f0a13602ec03b41a957',
                      '67552f0b13602ec03b41aa67', '67552f0b13602ec03b41ab0f', '67552f0a13602ec03b41a886',
                      '67552f0a13602ec03b41a8ae']

    if args.few_shot:
        exist_path = f'outputs/DBdesign_domain/healthcare_domain_{args.model_name}_{args.method}_fewshot_evaluation.jsonl'
    else:
        exist_path = f'outputs/DBdesign_domain/healthcare_domain_{args.model_name}_{args.method}_evaluation.jsonl'
    exist_data = {}
    with open(exist_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # datas = [json.loads(line) for line in lines]  # 转成list格式
        for line in lines:
            line = json.loads(line)
            exist_data[line['id']] = line

    for idx in tqdm.tqdm(test_range, desc=f"{args.start_pos} ~ {end_pos}"):
        raw_sample = dataobj.get_by_idx(idx)
        if raw_sample['id'] not in healthcare_ids or raw_sample['id'] in exist_data:
            continue
        question = raw_sample['question']  

        realqid = idx
        data_info = fully_decode(question, handler, args)
        data_info['id'] = raw_sample['id']
        data_info['remarks'] = raw_sample['remarks']
        print(f'---- id : {data_info["id"]}')
        print(data_info)
        with open(exact_output_file, 'a+') as f:
            f.write(json.dumps(data_info, ensure_ascii=False) + '\n')
    print(f'save to {exact_output_file}')
