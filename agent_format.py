# 由于格式不可控导致的，配套prompt_generator_format.py使用

from collections import defaultdict

from prompt_generator_format import *
from data_utils import *
import json
from utils import (extract_functional_dependency_from_text, get_attribute_keys_by_arm_strong,
                   get_attribute_keys_by_arm_strong_each,get_common_element_list,
                   decompose_to_3NF, trans_relation_to_schema, predict_entity_schema, predict_relation_schema,
                   clear_analyses, trans_relation_to_schema_for_domain)



# 用来实现multi agent，会生成所有的交互过程。
def fully_decode(question, handler, args):
    data_info = {}
    if args.method == "base_direct":   # 直接使用一步生成所有数据库模式，不分成多个子任务；zero-shot。
        if args.few_shot:
            direct_prompt = get_direct_few_shot_prompt(question)
        else:
            direct_prompt = get_direct_prompt(question)
        # handler.get_output_multiagent 就是根据相应的prompt得到response的函数，response就是str
        output, output_json = handler.get_output_multiagent(user_input=direct_prompt, temperature=0, max_tokens=1000, system_role="")  # 没有system role

        # output是string类型的，解析一下，存成json
        print(f'output:\n {output}')
        data_info = {
            'question': question,
            'answer': output_json,
        }

    elif args.method == "base_cot":
        if args.few_shot:
            cot_prompt = get_cot_few_shot_prompt(question)
        else:
            cot_prompt = get_cot_prompt(question)
        output, output_json = handler.get_output_multiagent(user_input=cot_prompt, temperature=0, max_tokens=1000, system_role="")
        # 处理一下输出
        data_info = {
            'question': question,
            'answer': output_json,
            # 'gold_schema': gold_answer
        }

    # TODO 这个方式下的prompt format都没有调
    elif args.method == "expert_analyse":
        # 以划分为多个子任务的形式的进行，每个任务划分一个agent，可能太细了，总体需要9个agent，调用9次大模型
        print('### -------------------- 第一阶段 现实需求转为概念模型---------------------- ###')

        do_requirement_analyse = False  # 用来控制是否做需求分析

        if do_requirement_analyse:
            # 1. 先设计一个agent进行需求分析
            question_analyzer, prompt_get_question_analysis = get_question_analysis_prompt(question)
            # 需求分析的结果
            question_analyses = handler.get_output_multiagent(user_input=prompt_get_question_analysis,
                                                                  temperature=0, max_tokens=3000,
                                                                  system_role=question_analyzer)
        else:
            question_analyses = question

        # 2. 先做实体集和识别, 这里返回的两个值前面是role, 后面是对应的prompt #TODO 这里还有格式问题没有限制，先看下它是怎么返回的
        entity_analyzer, prompt_get_entity_analyses = get_entity_analysis_prompt(question_analyses)
        # 实体识别的结果
        entity_analyses = handler.get_output_multiagent(user_input=prompt_get_entity_analyses,
                                                          temperature=0, max_tokens=800,
                                                          system_role=entity_analyzer)
        # 把实体提取出来，只保留结果，去除分析步骤。
        entity_analyses_result = clear_analyses(entity_analyses)
        # entity_analyses_result = "最终可以得出数据库实体为：学生、课程。"

        # 3. 根据实体集的识别结果，做实体属性的识别。这里没有加原始的需求了。
        entity_attribute_analyzer, prompt_get_entity_attribute_analyses = get_entity_attribute_analysis_prompt(question_analyses, entity_analyses_result)
        # 实体属性识别的结果
        entity_attribute_analyses = handler.get_output_multiagent(user_input=prompt_get_entity_attribute_analyses,
                                                          temperature=0, max_tokens=800,
                                                          system_role=entity_attribute_analyzer)
        entity_attribute_analyses_result = clear_analyses(entity_attribute_analyses)
        # entity_attribute_analyses_result = "最终可以得出数据库实体的属性为：\n- 学生：学号、姓名、年龄\n- 课程：课程编号、课程名称、学分、授课教师、上课时间、选课人数"

        # 4. 根据实体识别出实体之间的关系，一般是二元关系和三元关系，很少有一元关系和四元关系 TODO 这里它老是自己识别出关系类型，看看后面是不是要合并吧
        relation_analyzer, prompt_get_relation_analyses = get_relation_analysis_prompt(question_analyses, entity_analyses)
        relation_analyses = handler.get_output_multiagent(user_input=prompt_get_relation_analyses,
                                                          temperature=0, max_tokens=800,
                                                          system_role=relation_analyzer)
        relation_analyses_result = clear_analyses(relation_analyses)
        # relation_analyses_result = '数据库实体关系为：选课关系:学生、课程'

        # 5. 根据关系的识别结果，得到关系之间的比例关系 TODO 这里是不是还应该指明是一对一，一对多，还是多对多
        relation_type_analyzer, prompt_get_relation_type_analyses = get_relation_analysis_type_prompt(question_analyses, relation_analyses_result)
        relation_type_analyses = handler.get_output_multiagent(user_input=prompt_get_relation_type_analyses,
                                                          temperature=0, max_tokens=800,
                                                          system_role=relation_type_analyzer)
        relation_type_analyses_result = clear_analyses(relation_type_analyses)
        # relation_type_analyses_result = '数据库实体之间的比例关系为：选课关系:多对多]'


        # 6. 根据关系的识别结果，得到关系之间的属性  TODO 这个属性也包括的两端实体的主键, 不应该这么做，因为这个时候还不知道实体的主键，做的时候跟标的时候不相同
        relation_attribute_analyzer, prompt_get_relation_attribute_analyses = get_relation_analysis_attribute_prompt(question_analyses, entity_attribute_analyses_result, relation_analyses_result)
        relation_attribute_analyses = handler.get_output_multiagent(user_input=prompt_get_relation_attribute_analyses,
                                                               temperature=0, max_tokens=800,
                                                               system_role=relation_attribute_analyzer)
        relation_attribute_analyses_result = clear_analyses(relation_attribute_analyses)
        # relation_attribute_analyses_result = '数据库关系的属性为：选课关系:选课时间、退课状态、选课人数。'

        # 7. 识别实体中函数之间的依赖关系
        entity_functional_dependency_analyzer, prompt_get_entity_functional_dependency_analyses = get_entity_functional_dependency_analysis_prompt(
            question_analyses, entity_attribute_analyses_result)
        entity_functional_dependency_analyses = handler.get_output_multiagent(user_input=prompt_get_entity_functional_dependency_analyses,
                                                               temperature=0, max_tokens=800,
                                                               system_role=entity_functional_dependency_analyzer)
        entity_functional_dependency_analyses_result = clear_analyses(entity_functional_dependency_analyses)

        # entity_functional_dependency_analyses_result = "数据库实体属性之间的函数依赖关系为：\n学生: (学号) → (姓名)\n学生: (学号) → (年龄)\n课程: (课程编号) → (课程名称)\n课程: (课程编号) → (学分)\n课程: (课程编号) → (授课教师)\n课程: (课程编号) → (上课时间)"

        print('### -------------------- 第二阶段 概念模型转为关系模型 ---------------------- ###')

        # 一、实体的转变。每个实体都将转为一个schema， 这个是确定的，不需要进行操作。

        # 二、关系的转变。每个关系需要完成参照完整性。只有n:n的关系才会形成新的schema，1：n 和1：1的关系都只需要将n端的对象的主键加入到原来的实体中。
        # 8. 得到实体的主键。从实体的函数依赖识别中对每个实体提取出json格式的依赖关系，看是用大模型抽取，还是用算法实现
        entity_functional_dependency_json = extract_functional_dependency_from_text(entity_functional_dependency_analyses_result)
        print(f'entity_functional_dependency_json:\n {entity_functional_dependency_json}')

        # 然后通过算法实现Arm Strong公理系统，得到实体的主键（主属性）和非主属性 TODO 如果后面返回的东西不对劲，是不是可以修改之前的答案？
        entity_attributes_all, entity_keys_and_attribute_map = get_attribute_keys_by_arm_strong(entity_functional_dependency_json)
        print(f'entity_attributes_all:\n {entity_attributes_all}')
        print(f'entity_keys_and_attribute_map:\n {entity_keys_and_attribute_map}')

        # 9. 根据关系类型，得到新的实体属性和新的schema。这里把entity_attributes_all也进行了更新。multi_relation返回的内容是跟entity_attributes_all格式一样的。
        multi_relation = trans_relation_to_schema(relation_analyses_result, relation_attribute_analyses_result,
                                                                 relation_type_analyses_result, entity_attributes_all, entity_keys_and_attribute_map)
        print(f'multi_relation:\n {multi_relation}')

        # 三、规范化设计

        # 10. 识别添加关系属性之后的实体的函数依赖，这里是为了拆表，不是识别主键。
        entity_functional_dependency_analyzer, prompt_get_entity_functional_dependency_analyses = get_entity_functional_dependency_analysis_prompt(
            question_analyses, json.dumps(entity_attributes_all, ensure_ascii=False))
        entity_add_relation_functional_dependency_analyses = handler.get_output_multiagent(
                                                    user_input=prompt_get_entity_functional_dependency_analyses,
                                                    temperature=0, max_tokens=800,
                                                    system_role=entity_functional_dependency_analyzer)
        entity_add_relation_functional_dependency_analyses_result = clear_analyses(entity_add_relation_functional_dependency_analyses)
        # entity_add_relation_functional_dependency_analyses_result = "数据库实体属性之间的函数依赖关系为：\n学生: (学号) → (姓名)\n学生: (学号) → (年龄)\n课程: (课程编号) → (课程名称)\n课程: (课程编号) → (学分)\n课程: (课程编号) → (授课教师)\n课程: (课程编号) → (上课时间)"

        print(f'entity_add_relation_functional_dependency_analyses_result:\n {entity_add_relation_functional_dependency_analyses_result}')

        entity_add_relation_functional_dependency_json = extract_functional_dependency_from_text(
            entity_add_relation_functional_dependency_analyses_result)
        print(f'entity_add_relation_functional_dependency_json:\n {entity_add_relation_functional_dependency_json}')

        # 然后通过算法实现Arm Strong公理系统，得到实体的主键（主属性）和非主属性 TODO 如果后面返回的东西不对劲，是不是可以修改之前的答案？
        entity_add_relation_attributes_all, entity_add_relation_keys_and_attribute_map = get_attribute_keys_by_arm_strong(
                                                                            entity_add_relation_functional_dependency_json)

        print(f'entity_add_relation_attributes_all:\n {entity_add_relation_attributes_all}')
        print(f'entity_add_relation_keys_and_attribute_map:\n {entity_add_relation_keys_and_attribute_map}')

        # 11. 通过arm strong公理判断是否具有部分函数依赖和传递函数依赖，即是否满足第二范式和第三范式
        transitive_partial_dependencies = decompose_to_3NF(
                                                            entity_add_relation_functional_dependency_json,
                                                            entity_add_relation_attributes_all,
                                                            entity_add_relation_keys_and_attribute_map
                                                            )
        transitive_partial_dependencies = {key: value for key, value in transitive_partial_dependencies.items()}  #转为普通dict
        # 选课关系中，没有这两种依赖关系
        print(f'transitive_partial_dependencies:\n {transitive_partial_dependencies}')

        # 12. 开始拆实体表，算法实现
        new_entity_add_relation_attributes_all = {}
        new_entity_add_relation_keys_and_attribute_map = {}
        for entity_name in transitive_partial_dependencies:
            if len(transitive_partial_dependencies[entity_name]['分解关系']) == 1:  # 表示不用拆表
                new_entity_add_relation_attributes_all[entity_name] = entity_add_relation_attributes_all[entity_name]
                new_entity_add_relation_keys_and_attribute_map[entity_name] = entity_add_relation_keys_and_attribute_map[entity_name]
            else:  # 需要拆表
                for sub_table_attributes in transitive_partial_dependencies[entity_name]['分解关系']:
                    candidate_keys = get_attribute_keys_by_arm_strong_each(sub_table_attributes,
                                                                           entity_add_relation_functional_dependency_json['dependencies'][entity_name])
                    new_entity_name = ''
                    for candidate_key in candidate_keys:
                        new_entity_name = ''.join(candidate_key)   # TODO 如果已经存在了这个new_entity_name 还需要额外的操作
                    # if new_entity_name in new_entity_add_relation_attributes_all:
                    #     new_entity_name +=
                    new_entity_add_relation_attributes_all[new_entity_name] = sub_table_attributes
                    new_entity_add_relation_keys_and_attribute_map[new_entity_name] = candidate_keys

        print(f'new_entity_add_relation_attributes_all:\n {new_entity_add_relation_attributes_all}')
        print(f'new_entity_add_relation_keys_and_attribute_map:\n {new_entity_add_relation_keys_and_attribute_map}')

        entity_schemas = predict_entity_schema(new_entity_add_relation_attributes_all,
                                               new_entity_add_relation_keys_and_attribute_map)


        # 13. 识别关系中关系属性之间的函数依赖，这里是为了拆表。
        relation_all_attribute = {}
        for relation_item in multi_relation:
            for relation_name in relation_item:
                relation_all_attribute[relation_name] = relation_item[relation_name]['属性']
        print(f'relation_all_attribute:\n {relation_all_attribute}')

        relation_functional_dependency_analyzer, prompt_get_relation_functional_dependency_analyses = get_relation_functional_dependency_analysis_prompt(
            question_analyses, relation_all_attribute)

        relation_functional_dependency_analyses = handler.get_output_multiagent(
                                                            user_input=prompt_get_relation_functional_dependency_analyses,
                                                            temperature=0, max_tokens=800,
                                                            system_role=relation_functional_dependency_analyzer)
        relation_functional_dependency_analyses_result = clear_analyses(relation_functional_dependency_analyses)
        # relation_functional_dependency_analyses_result = '''
        #                                                     数据库关系属性之间的函数依赖关系为：
        #                                                     选课关系: (学号, 课程编号) → (选课时间),
        #                                                     选课关系: (学号, 课程编号) → (退课状态)
        #                                                     选课关系: (学号, 课程编号) → (选课人数),
        #                                                     选课关系: (课程编号) → (选课人数)
        #                                                  '''

        print(f'relation_functional_dependency_analyses:\n {relation_functional_dependency_analyses} \n')
        print(f'relation_functional_dependency_analyses_result:\n {relation_functional_dependency_analyses_result}')

        # 14. 得到关系的主键。从实体的函数依赖识别中对每个实体提取出json格式的依赖关系
        relation_functional_dependency_json = extract_functional_dependency_from_text(
                                                         relation_functional_dependency_analyses_result)
        print(f'relation_functional_dependency_json:\n {relation_functional_dependency_json}')

        # 然后通过算法实现Arm Strong公理系统，得到关系的主键（主属性）和非主属性
        relation_attributes_all, relation_keys_and_attribute_map = get_attribute_keys_by_arm_strong(relation_functional_dependency_json)
        print(f'relation_attributes_all:\n {relation_attributes_all}')
        print(f'relation_keys_and_attribute_map:\n {relation_keys_and_attribute_map}')


        # 15. 通过arm strong公理判断是否具有部分函数依赖和传递函数依赖，即是否满足第二范式和第三范式 TODO 关系表可能不需要拆
        # relation_transitive_partial_dependencies = detect_transitive_and_partial_dependencies(
        #     relation_functional_dependency_json,
        #     relation_keys_and_attribute_map,
        #     relation_attributes_all)
        # # 选课关系中，没有这两种依赖关系
        # print(f'relation_transitive_partial_dependencies:\n {relation_transitive_partial_dependencies}')

        # 15.1. 开始拆关系表，算法实现



        # 16. 将关系转为schema 格式的输出。现在已经有所有的属性，和主键了。
        multi_relation_schemas = predict_relation_schema(multi_relation, relation_keys_and_attribute_map)
        print(f'multi_relation_schemas:\n {multi_relation_schemas}')

        # 合并两个JSON对象
        schema_predicted = {**entity_schemas, **multi_relation_schemas}
        print(f'schema_predicted:\n {schema_predicted}')



        data_info = {
            'question': question,
            'question_analyses': question_analyses,
            'entity_analyses': entity_analyses_result,
            'entity_attribute_analyses': entity_attribute_analyses_result,
            'relation_analyses': relation_analyses_result,
            'relation_attribute_analyses': relation_attribute_analyses_result,
            'relation_type_analyses': relation_type_analyses_result,
            'entity_functional_dependency_analyses': entity_functional_dependency_analyses_result,
            'relation_functional_dependency_analyses': relation_functional_dependency_analyses_result,
            'entity_functional_dependency_json':entity_functional_dependency_json,
            'entity_attributes_all':entity_attributes_all,
            'relation_functional_dependency_analyses_result': relation_functional_dependency_analyses_result,
            'relation_functional_dependency_json':relation_functional_dependency_json,
            'relation_attributes_all':relation_attributes_all,
            'multi_relation_schemas':multi_relation_schemas,
            'pred_schema': schema_predicted,
        }

        # 打印history
        if args.log_history:
            print('*********************** History *********************')
            print(data_info)



    elif args.method == "domain_analyse":
        # 这里可以少分几个agent， 分为实体agent和关系agent，还有一个函数依赖识别agent
        print('### -------------------- 第一阶段 现实需求转为概念模型---------------------- ###')
        do_requirement_analyse = False  # 用来控制是否做需求分析

        if do_requirement_analyse:
            # 1. 先设计一个agent进行需求分析
            question_analyzer, prompt_get_question_analysis = get_question_analysis_prompt(question)
            # 需求分析的结果
            question_analyses = handler.get_output_multiagent(user_input=prompt_get_question_analysis,
                                                              temperature=0, max_tokens=3000,
                                                              system_role=question_analyzer)
        else:
            question_analyses = question

        # 1. 实体识别+实体属性识别 实体agent
        entity_analyzer, prompt_get_entity_analyses = get_entity_all_analysis_prompt(question_analyses)  # english
        # 实体识别的结果
        entity_analyses, entity_analyses_result = handler.get_output_multiagent(user_input=prompt_get_entity_analyses,
                                                        temperature=0, max_tokens=800,
                                                        system_role=entity_analyzer)
        print(f'entity_analyses_result:\n {entity_analyses_result}')

        revision_history = {}
        # 先验证实体是不是正确的，这个非常关键。
        if 'entity_verification' in args.verification:   # 换成每个实体都来验证一下
            # 把每个实体都拿出来问
            new_entity_json_result = {}
            for entity_name in entity_analyses_result:
                quality_controller, quality_control_prompt = get_verification_entity_prompt(question_analyses, entity_analyses,
                                                                                  entity_name)
                quality_controller_opi, _ = handler.get_output_multiagent(user_input=quality_control_prompt,
                                                                       temperature=0, max_tokens=800,
                                                                       system_role=quality_controller)
                quality_controller_opinion = cleansing_voting(quality_controller_opi)  # "yes" / "no"

                print(f'quality_controller_opinion: {quality_controller_opinion}')
                revision_history[entity_name] = quality_controller_opinion

                if quality_controller_opinion == 'yes':
                    new_entity_json_result[entity_name] = entity_analyses_result[entity_name]

            entity_analyses_result = new_entity_json_result

        # entity_analyses_result = {'部门': ['部门ID', '部门名称', '部门类型'], '职工': ['职工号', '姓名', '出生日期', '性别', '电话', '岗位'], '产品': ['产品ID', '名称', '型号', '条码', '价格'], '零部件': ['零部件ID', '名称', '型号', '条码', '价格']}

        print(f'revision_history: \n {revision_history}')
        print(f'entity_analyses_result:\n {entity_analyses_result}')


        # 2. 根据实体与实体之间的关系，关系比例类型和关系属性
        relation_analyzer, prompt_get_relation_analyses = get_relation_all_analysis_prompt(question_analyses,
                                                                                       entity_analyses_result)
        relation_analyses, relation_analyses_result = handler.get_output_multiagent(user_input=prompt_get_relation_analyses,
                                                          temperature=0, max_tokens=800,
                                                          system_role=relation_analyzer)
        # relation_analyses_result = [{'部门与职工关系': ['部门', '职工'], '比例关系': '一对多', '关系属性': ['部门ID']}, {'部门与零部件关系': ['部门', '零部件'], '比例关系': '多对多', '关系属性': ['数量', '发货人', '领取人', '领取时间']}, {'部门与产品关系': ['部门', '产品'], '比例关系': '多对多', '关系属性': ['数量', '交货人', '收货人', '入库时间']}]

        # print(f'relation_analyses:\n {relation_analyses}')
        print(f'relation_analyses_result:\n {relation_analyses_result}')


        # 3. 识别实体中函数之间的依赖关系
        entity_functional_dependency_analyzer, prompt_get_entity_functional_dependency_analyses = get_entity_functional_dependency_analysis_prompt(
            question_analyses, entity_analyses_result)
        entity_functional_dependency_analyses, entity_functional_dependency_analyses_result = handler.get_output_multiagent(
            user_input=prompt_get_entity_functional_dependency_analyses,
            temperature=0, max_tokens=800,
            system_role=entity_functional_dependency_analyzer)
        # entity_functional_dependency_analyses_result = {'部门': {'部门ID': ['部门名称', '部门类型']}, '职工': {'职工号': ['姓名', '出生日期', '性别', '电话', '岗位']}, '产品': {'产品ID': ['名称', '型号', '条码', '价格']}, '零部件': {'零部件ID': ['名称', '型号', '条码', '价格']}}
        print(f'entity_functional_dependency_analyses_result:\n {entity_functional_dependency_analyses_result}')

        # 函数依赖很重要，也写一个agent进行质量控制
        revision_entity_denpendency_history = defaultdict(list)
        if 'entity_denpendency_verification' in args.verification:   # 换成每个依赖关系都验证一下
            # 把每个实体都拿出来问
            new_entity_functional_dependency_analyses_result = {}
            for entity_name, entity_value in entity_functional_dependency_analyses_result.items():
                entity_dependency = {entity_name:entity_value}
                ENTITY_REVISE_FLAG = True
                ENTITY_REVISE_NUM = 3
                tried_num = 0
                while tried_num<ENTITY_REVISE_NUM and ENTITY_REVISE_FLAG:
                    tried_num += 1

                    quality_controller, quality_control_prompt = get_dependency_consensus_prompt(question_analyses,
                                                                {entity_name:entity_analyses_result[entity_name]},
                                                    entity_dependency)
                    quality_controller_opi, _ = handler.get_output_multiagent(user_input=quality_control_prompt,
                                                                           temperature=0, max_tokens=800,
                                                                           system_role=quality_controller)
                    quality_controller_opinion = cleansing_voting(quality_controller_opi)  # "yes" / "no"

                    print(f'quality_controller_opinion: {quality_controller_opinion}')
                    revision_entity_denpendency_history[entity_name].append(quality_controller_opinion)

                    if quality_controller_opinion == 'yes':
                        new_entity_functional_dependency_analyses_result[entity_name] = entity_value
                        ENTITY_REVISE_FLAG = False
                    else:  # 修改
                        revise_control_prompt = get_dependency_consensus_opinion_prompt(question_analyses,
                                                            {entity_name: entity_analyses_result[entity_name]},
                                                                            entity_dependency,
                                                                             quality_controller_opi )
                        (revise_entity_functional_dependency_analyses,
                         revise_entity_functional_dependency_analyses_result) = handler.get_output_multiagent(user_input=revise_control_prompt,
                                                                              temperature=0, max_tokens=800,
                                                                              system_role=quality_controller)
                        entity_dependency = revise_entity_functional_dependency_analyses_result

                if tried_num==ENTITY_REVISE_NUM:
                    new_entity_functional_dependency_analyses_result[entity_name] = entity_dependency[entity_name]
            entity_functional_dependency_analyses_result = new_entity_functional_dependency_analyses_result
            print(f'revision_entity_denpendency_history:\n {revision_entity_denpendency_history}')

        print(f'new_entity_functional_dependency_analyses_result:\n {entity_functional_dependency_analyses_result}')


        print('### -------------------- 第二阶段 概念模型转为关系模型 ---------------------- ###')

        # 4. 得到实体的主键。从实体的函数依赖识别中对每个实体提取出json格式的依赖关系，看是用大模型抽取，还是用算法实现

        # 然后通过算法实现Arm Strong公理系统，得到实体的主键（主属性）和非主属性 TODO 如果后面返回的东西不对劲，是不是可以修改之前的答案？
        # TODO 这里的entity_attributes_all是不是跟之前的entity_analyses_result的结果是一样的，都只包含实体和实体属性。
        entity_attributes_all, entity_keys_and_attribute_map = get_attribute_keys_by_arm_strong(
            entity_functional_dependency_analyses_result)
        print(f'entity_attributes_all:\n {entity_attributes_all}')
        print(f'entity_keys_and_attribute_map:\n {entity_keys_and_attribute_map}')


        # 5. 根据关系类型，得到新的实体属性和新的schema。这里把entity_attributes_all也进行了更新。multi_relation返回的内容是跟entity_attributes_all格式一样的。
        multi_relation, entity_attributes_all_with_foreign_key = trans_relation_to_schema_for_domain(relation_analyses_result, entity_attributes_all,
                                                  entity_keys_and_attribute_map)
        print(f'entity_add_relation_attributes_all:\n {entity_attributes_all}')
        print(f'entity_attributes_all_with_foreign_key:\n {entity_attributes_all_with_foreign_key}')
        print(f'multi_relation:\n {multi_relation}')

        # 三、规范化设计
        # 6. 识别添加关系属性之后的实体的函数依赖，这里是为了拆表，不是识别主键。
        entity_functional_dependency_analyzer, prompt_get_entity_functional_dependency_analyses = get_entity_functional_dependency_analysis_prompt(
            question_analyses, json.dumps(entity_attributes_all, ensure_ascii=False))
        entity_add_relation_functional_dependency_analyses, entity_add_relation_functional_dependency_json = handler.get_output_multiagent(
            user_input=prompt_get_entity_functional_dependency_analyses,
            temperature=0, max_tokens=800,
            system_role=entity_functional_dependency_analyzer)
        # entity_add_relation_functional_dependency_json = {'职工': {'职工号': ['性别', '姓名', '岗位', '电话', '出生日期', '部门ID']}, '产品': {'产品ID': ['价格', '型号', '条码', '名称', '部门ID']}, '零部件': {'零部件ID': ['价格', '型号', '条码', '名称', '部门ID']}, '部门': {'部门ID': ['部门名称', '部门类型']}}
        print(f'entity_add_relation_functional_dependency_json:\n {entity_add_relation_functional_dependency_json}')

        # 然后通过算法实现Arm Strong公理系统，得到实体的主键（主属性）和非主属性 TODO 如果后面返回的东西不对劲，是不是可以修改之前的答案？
        entity_add_relation_attributes_all, entity_add_relation_keys_and_attribute_map = get_attribute_keys_by_arm_strong(
            entity_add_relation_functional_dependency_json)

        print(f'entity_add_relation_attributes_all:\n {entity_add_relation_attributes_all}')
        print(f'entity_add_relation_keys_and_attribute_map:\n {entity_add_relation_keys_and_attribute_map}')

        # 7. 通过arm strong公理判断是否具有部分函数依赖和传递函数依赖，即是否满足第二范式和第三范式
        transitive_partial_dependencies = decompose_to_3NF(
            entity_add_relation_functional_dependency_json,
            entity_add_relation_keys_and_attribute_map
        )
        transitive_partial_dependencies = {key: value for key, value in
                                           transitive_partial_dependencies.items()}  # 转为普通dict
        # 选课关系中，没有这两种依赖关系
        print(f'transitive_partial_dependencies:\n {transitive_partial_dependencies}')

        # 8. 开始拆实体表，算法实现
        new_entity_add_relation_attributes_all = defaultdict(dict)
        new_entity_add_relation_keys_and_attribute_map = {}
        for entity_name in transitive_partial_dependencies:
            if len(transitive_partial_dependencies[entity_name]['分解关系']) == 1:  # 表示不用拆表
                new_entity_add_relation_attributes_all[entity_name]['属性'] = entity_add_relation_attributes_all[entity_name]
                new_entity_add_relation_keys_and_attribute_map[entity_name] = entity_add_relation_keys_and_attribute_map[entity_name]
            else:  # 需要拆表
                for sub_table_attributes in transitive_partial_dependencies[entity_name]['分解关系']:
                    candidate_keys = get_attribute_keys_by_arm_strong_each(sub_table_attributes,
                                                                           entity_add_relation_functional_dependency_json[entity_name])
                    new_entity_name = ''
                    for candidate_key in candidate_keys:
                        new_entity_name = ''.join(candidate_key)  # TODO 如果已经存在了这个new_entity_name 还需要额外的操作
                    new_entity_add_relation_attributes_all[new_entity_name]['属性'] = sub_table_attributes
                    new_entity_add_relation_attributes_all[new_entity_name]['外键'] = {}
                    # 处理下外键关系

                    foreign_keys = list(entity_attributes_all_with_foreign_key[entity_name]['外键'].keys())
                    common_keys = get_common_element_list(foreign_keys, sub_table_attributes)

                    for key in common_keys:
                        new_entity_add_relation_attributes_all[new_entity_name]['外键'][key] = entity_attributes_all_with_foreign_key[entity_name]['外键'][key]
                    new_entity_add_relation_keys_and_attribute_map[new_entity_name] = candidate_keys

        print(f'new_entity_add_relation_attributes_all:\n {new_entity_add_relation_attributes_all}')
        print(f'new_entity_add_relation_keys_and_attribute_map:\n {new_entity_add_relation_keys_and_attribute_map}')

        entity_schemas = predict_entity_schema(new_entity_add_relation_attributes_all,
                                               new_entity_add_relation_keys_and_attribute_map)
        print(f'entity_schemas:\n {entity_schemas}')

        # 9. 识别关系中关系属性之间的函数依赖，这里是为了拆表。
        relation_all_attribute = {}
        for relation_name in multi_relation:
            relation_all_attribute[relation_name] = multi_relation[relation_name]['属性']
        print(f'relation_all_attribute:\n {relation_all_attribute}')

        if relation_all_attribute:
            # 10. 得到关系的主键。从实体的函数依赖识别中对每个实体提取出json格式的依赖关系
            relation_functional_dependency_analyzer, prompt_get_relation_functional_dependency_analyses = get_relation_functional_dependency_analysis_prompt(
                question_analyses, relation_all_attribute)
            relation_functional_dependency_analyses, relation_functional_dependency_analyses_result = handler.get_output_multiagent(
                user_input=prompt_get_relation_functional_dependency_analyses,
                temperature=0, max_tokens=800,
                system_role=relation_functional_dependency_analyzer)
            # print(f'relation_functional_dependency_analyses:\n {relation_functional_dependency_analyses} \n')
            print(f'relation_functional_dependency_analyses_result:\n {relation_functional_dependency_analyses_result}')

            # 函数依赖很重要，也写一个agent进行质量控制
            revision_relation_denpendency_history = defaultdict(list)
            if 'relation_denpendency_verification' in args.verification:  # 换成每个依赖关系都验证一下
                # 把每个实体都拿出来问
                new_relation_functional_dependency_analyses_result = {}
                for relation_name, relation_value in relation_functional_dependency_analyses_result.items():
                    relation_dependency = {relation_name: relation_value}
                    RELATION_REVISE_FLAG = True
                    RELATION_REVISE_NUM = 3
                    tried_num = 0
                    while tried_num < RELATION_REVISE_NUM and RELATION_REVISE_FLAG:
                        tried_num += 1

                        quality_controller, quality_control_prompt = get_relation_dependency_consensus_prompt(question_analyses,
                                                                {relation_name:relation_all_attribute[relation_name]},
                                                                               relation_dependency)
                        quality_controller_opi, _ = handler.get_output_multiagent(user_input=quality_control_prompt,
                                                                                  temperature=0, max_tokens=800,
                                                                                  system_role=quality_controller)
                        quality_controller_opinion = cleansing_voting(quality_controller_opi)  # "yes" / "no"

                        print(f'quality_controller_opi: \n {quality_controller_opi}' )
                        print(f'quality_controller_opinion: {quality_controller_opinion}')
                        revision_relation_denpendency_history[relation_name].append(quality_controller_opinion)

                        if quality_controller_opinion == 'yes':
                            new_relation_functional_dependency_analyses_result[relation_name] = relation_value
                            RELATION_REVISE_FLAG = False
                        else:  # 修改
                            revise_control_prompt = get_relation_dependency_consensus_opinion_prompt(question_analyses,
                                                        {relation_name:relation_all_attribute[relation_name]},
                                                                                            relation_dependency,
                                                                                            quality_controller_opi)
                            (revise_relation_functional_dependency_analyses,
                             revise_relation_functional_dependency_analyses_result) = handler.get_output_multiagent(
                                user_input=revise_control_prompt,
                                temperature=0, max_tokens=800,
                                system_role=quality_controller)
                            print(f'revise_relation_functional_dependency_analyses: \n revise_relation_functional_dependency_analyses')
                            print(f'revise_relation_functional_dependency_analyses_result: \n revise_relation_functional_dependency_analyses_result')
                            relation_dependency = revise_relation_functional_dependency_analyses_result

                    if tried_num == RELATION_REVISE_NUM:
                        new_relation_functional_dependency_analyses_result[relation_name] = relation_dependency[relation_name]
                relation_functional_dependency_analyses_result = new_relation_functional_dependency_analyses_result
                print(f'revision_relation_denpendency_history:\n {revision_relation_denpendency_history}')

            # relation_functional_dependency_analyses_result = {'部门与零部件关系': {'部门ID, 零部件ID, 领取时间': ['数量', '发货人', '领取人']}, '部门与产品关系': {'部门ID, 产品ID, 入库时间': ['数量', '交货人', '收货人']}}
            # relation_functional_dependency_analyses_result = {'部门与零部件关系': {}, '部门与产品关系': {}}

            print(f'new_relation_functional_dependency_analyses_result:\n {relation_functional_dependency_analyses_result}')


            # 然后通过算法实现Arm Strong公理系统，得到关系的主键（主属性）和非主属性
            relation_attributes_all, relation_keys_and_attribute_map = get_attribute_keys_by_arm_strong(
                relation_functional_dependency_analyses_result)
            print(f'relation_attributes_all:\n {relation_attributes_all}')
            print(f'relation_keys_and_attribute_map:\n {relation_keys_and_attribute_map}')

            # **10.1 如果关系中没有主键，重新设计关系，可能会产生新的关系表。也就是说两个实体之间不能通过一个关系简单连接。
            new_multi_relation = {}
            new_relation_keys_and_attribute_map = {}
            for relation_name in relation_keys_and_attribute_map:
                if len(relation_keys_and_attribute_map[relation_name]) == 0:  # 没有主键，重新划分。
                    relation_item = {}
                    for item in relation_analyses_result:
                        if list(item.keys())[0] == relation_name:
                            relation_item = item
                    revised_relation_analyzer, prompt_get_relation_revised_analyses = get_relation_revised_analysis_prompt(
                        question_analyses, relation_item, entity_schemas)
                    revised_relation_analyses, revised_relation_analyses_result = handler.get_output_multiagent(
                        user_input=prompt_get_relation_revised_analyses,
                        temperature=0, max_tokens=800,
                        system_role=revised_relation_analyzer)
                    print(f'revised_relation_analyses_result:\n {revised_relation_analyses_result}')

                    for key in revised_relation_analyses_result:
                        new_multi_relation[key] = revised_relation_analyses_result[key]
                        new_relation_keys_and_attribute_map[key] = [set(revised_relation_analyses_result[key]['主键'])]
                else:
                    new_multi_relation[relation_name] = multi_relation[relation_name]
                    new_relation_keys_and_attribute_map[relation_name] = relation_keys_and_attribute_map[relation_name]

            print(f'new_multi_relation:\n {new_multi_relation}')
            print(f'new_relation_keys_and_attribute_map:\n {new_relation_keys_and_attribute_map}')

            # 11. 将关系转为schema 格式的输出。现在已经有所有的属性，和主键了。
            multi_relation_schemas = predict_relation_schema(new_multi_relation, new_relation_keys_and_attribute_map)
            print(f'multi_relation_schemas:\n {multi_relation_schemas}')

            # 合并两个JSON对象
            schema_predicted = {**entity_schemas, **multi_relation_schemas}
        else:
            schema_predicted = entity_schemas

        print(f'schema_predicted:\n {schema_predicted}')

        data_info = {
            'question': question,
            'question_analyses': question_analyses,
            'entity_analyses': entity_analyses_result,
            'revision_history':revision_history,
            'relation_analyses': relation_analyses_result,
            'entity_functional_dependency_analyses': entity_functional_dependency_analyses_result,
            'entity_attributes_all': entity_attributes_all,
            # 'relation_functional_dependency_analyses_result': relation_functional_dependency_analyses_result,
            # 'multi_relation_schemas': multi_relation_schemas,
            'pred_schema': schema_predicted,
        }

        # 打印history
        if args.log_history:
            print('*********************** History *********************')
            print(data_info)


    elif args.method == "pseudo_code_analyse":
        schema_analyzer, prompt_get_schema_analyses = get_pseudo_code_prompt(question, './pseudo_code.md')

        print(f'prompt_get_schema_analyses: \n{prompt_get_schema_analyses}')
        relation_functional_dependency_analyses, output_json = handler.get_output_multiagent(
            user_input=schema_analyzer,
            temperature=0, max_tokens=800,
            system_role=prompt_get_schema_analyses)

        # print('**********************************')
        # print(relation_functional_dependency_analyses)

        data_info = {
            'question': question,
            'pred_schema': output_json,
        }

    return data_info






