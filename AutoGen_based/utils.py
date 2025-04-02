import json
import re
from collections import defaultdict

# Define tools

def extract_functional_dependency_from_text(dependency_text):
    '''从string类型的数据中抽取出json格式的函数依赖，好给后面的arm strong系统做分析。'''
    # 解析文本并构建字典
    description = ""
    dependencies = {}
    lines = dependency_text.strip().split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if '→' not in line:  # 第一行是描述，过滤掉
            description = line
        else:
            # 移除开头的"- "和尾部的逗号（如果有）
            line = line.replace('- ', '').rstrip(',')
            # 分割实体和其依赖关系
            entity, attrs = line.split(':')
            entity = entity.strip()
            # attrs = attrs.strip().split(',')  # 这个是glm4识别的
            attrs = attrs.strip().split('，')   # gpt4每个都分行了，就不需要显示了
            # 解析每个属性依赖关系
            entity_dependencies = {}
            for attr in attrs:
                # 分割左侧和右侧
                left, right = attr.split(' → ')
                left = left.strip().replace('(','').replace(')', '')
                right = right.strip().replace('(','').replace(')', '')
                right = right.split(',')
                # 将右侧属性添加到字典中
                if left not in entity_dependencies:
                    entity_dependencies[left] = []
                entity_dependencies[left].extend(right)
            # 将实体及其依赖关系添加到总字典中
            if entity not in dependencies:
                dependencies[entity] = entity_dependencies
            else:
                for key, value in entity_dependencies.items():  # 处理异常情况，例如两个同一个属性决定的内容，分成两行显示了。
                    if key in dependencies[entity]:
                        dependencies[entity][key].extend(entity_dependencies[key])
                    else:
                        dependencies[entity][key] = entity_dependencies[key]

    # 将字典转换为JSON格式，并包含描述性文本
    json_output = {"description": description, "dependencies": dependencies}

    return json_output


def get_common_element_list(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    intersection = list(set1.intersection(set2))
    return intersection



# 计算闭包
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

# 寻找所有候选键
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
                candidates.append(candidate)
    return candidates

async def get_attribute_keys_by_arm_strong(dependencies_json):
    '''依据函数依赖关系识别出主键'''
    # 属性集
    attributes_all = {}
    dependencies_all = {}
    # for entity_name in dependencies_json['dependencies']:
    #     entity = dependencies_json['dependencies'][entity_name]
    for entity_name in dependencies_json:
        entity = dependencies_json[entity_name]
        attributes = []
        dependencies = []
        for depend_key in entity:
            if '&' in depend_key:
                depend_key_list = [it.strip() for it in depend_key.split('&')]     # 处理多个左值的情况
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
    # print(candidate_keys_dict)
    return attributes_all, candidate_keys_dict



async def get_attribute_keys_by_arm_strong_each(attributes, dependencies):
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



async def decompose_to_3NF(entity_fd_json, entity_primary_keys):
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

    # 解析函数依赖
    functional_dependencies = parse_dependencies(entity_fd_json)

    # 保存结果
    results_by_entity = defaultdict(lambda: {"分解关系": []})

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
            if rel not in unique_relations:
                unique_relations.append(rel)

        # 输出分解后的关系
        results_by_entity[entity]["分解关系"] = unique_relations

    return results_by_entity


# 这个函数暂时没用
def detect_transitive_and_partial_dependencies(entity_fd_json, keys_and_attribute_map, entity_attributes_all):
    '''判断是否有对主键的传递函数依赖和部分函数依赖。'''
    def parse_dependencies(entity_fd_json):
        """
        解析函数依赖关系，支持处理以逗号分隔的属性。
        """
        functional_dependencies = []
        for entity, dependencies in entity_fd_json['dependencies'].items():
            for determinant, dependents in dependencies.items():
                determinant_list = [attr.strip() for attr in determinant.split(",")]
                for dependent in dependents:
                    dependent_list = [attr.strip() for attr in dependent.split(",")]
                    functional_dependencies.append((determinant_list, dependent_list, entity))
        return functional_dependencies

    """
    自动分解当前关系到 3NF。
    """
    # 解析函数依赖
    functional_dependencies = parse_dependencies(entity_fd_json)

    # 保存结果
    results_by_entity = defaultdict(lambda: {"分解关系": []})

    # 按实体分类依赖
    dependencies_by_entity = defaultdict(list)
    for determinant, dependent, entity in functional_dependencies:
        dependencies_by_entity[entity].append((determinant, dependent))

    # 函数依赖分析
    for entity, deps in dependencies_by_entity.items():
        attributes = entity_attributes_all[entity]
        primary_keys = keys_and_attribute_map[entity]  # 获取当前实体的主键

        # 分解后的关系
        relations = []

        # 1. 分解部分依赖：处理所有的依赖关系
        for X, Y in deps:
            closure = compute_closure(X, dependencies_by_entity[entity])

            # 如果 X 是主键的超集
            if any(set(X).issubset(pk) for pk in primary_keys):
                # 只有当 Y 不在 X 的闭包中时才需要分解
                if not set(Y).issubset(closure):
                    partial_relation = set(X) | set(Y)
                    if partial_relation not in relations:
                        relations.append(partial_relation)

        # 2. 处理其他依赖
        for X, Y in deps:
            if set(Y).issubset(compute_closure(X, dependencies_by_entity[entity])):
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
            if rel not in unique_relations:
                unique_relations.append(rel)

        # 输出分解后的关系
        results_by_entity[entity]["分解关系"] = unique_relations

    return results_by_entity


async def trans_relation_to_schema(relation_analyses_result, relation_attribute_analyses_result,
                            relation_type_analyses_result, attributes_all, entity_keys_and_attribute_map):
    '''规范化设计的部分。根据关系类型，和实体的主键，得到新的实体属性和新的schema。这个也是纯算法实现的。'''
    # 先处理一下实体的关系，也就是1：n的关系
    def extract_relation(text):
        # 使用正则表达式匹配关系和实体
        pattern = r"(\w+):([\w、]+)"
        matches = re.findall(pattern, text)

        # 构建字典
        relationships = {}
        for match in matches:
            relationship, entities_str = match
            # 分割实体字符串为列表
            entities = [entity.strip() for entity in entities_str.split('、')]
            # 将关系和对应的实体列表添加到字典中
            relationships[relationship] = entities
        return relationships

    relationship_dict = extract_relation(relation_analyses_result) #{"选课关系": ["学生", "课程"], "授课关系": ["教师", "课程"]}
    relation_type_analyses_result = relation_type_analyses_result.replace(']','') # 不知道为什么老是自己生成这个
    relation_type_dict = extract_relation(relation_type_analyses_result) #{"选课关系": ["多对多"], "授课关系": ["一对多"]}
    relation_attribute_dict = extract_relation(relation_attribute_analyses_result)   #{"选课关系": ["选课时间", "退课时间", "选课状态", "选课人数"], "授课关系": ["授课开始时间", "授课结束时间", "授课地点"]}

    print('********************************')
    print(relationship_dict)
    print(relation_type_analyses_result)
    print(relation_type_dict)
    print(relation_attribute_dict)

    multi_relation = {}
    for relation_name in relationship_dict:
        if relation_type_dict[relation_name][0] == '多对多':
            entity_name_n1 = relationship_dict[relation_name][0]
            entity_n1_key = list(entity_keys_and_attribute_map[entity_name_n1][0])
            entity_name_n2 = relationship_dict[relation_name][1]
            entity_n2_key = list(entity_keys_and_attribute_map[entity_name_n2][0])

            relation_attribute_list = relation_attribute_dict[relation_name]
            relation_attribute_list.extend(entity_n1_key)
            relation_attribute_list.extend(entity_n2_key)
            multi_relation[relation_name] = {'属性':relation_attribute_list, '外键':{entity_n1_key:{entity_name_n1:entity_n1_key}, entity_n2_key:{entity_name_n2: entity_n2_key}}}  # 这个格式就跟实体的属性格式很像了

        elif relation_type_dict[relation_name][0] == '多对一':
            entity_name_1 = relationship_dict[relation_name][1]
            entity_1_key = list(entity_keys_and_attribute_map[entity_name_1][1])
            entity_name_n = relationship_dict[relation_name][0]
            attributes_all[entity_name_n].extend(entity_1_key)

        else:  # 无论是一对多还是一对一，把1端的主键加入到n端中
            entity_name_1 = relationship_dict[relation_name][0]
            entity_1_key = list(entity_keys_and_attribute_map[entity_name_1][0])
            entity_name_n = relationship_dict[relation_name][1]
            attributes_all[entity_name_n].extend(entity_1_key)

    return multi_relation





async def trans_relation_to_schema_for_domain(relation_analyses_result, attributes_all,
                                      entity_keys_and_attribute_map):
    '''规范化设计的部分。根据关系类型，和实体的主键，得到新的实体属性和新的schema。这个也是纯算法实现的。'''

    multi_relation = {}
    attributes_all_with_foreign_key = {}  # 还要存外键  可以是attribute_all本身也改， 外键也存
    for relationship in relation_analyses_result:
        relation_name = list(relationship.keys())[0]

        if relationship['比例关系'] == '多对多':
            entity_name_n1 = relationship[relation_name][0]
            entity_n1_key = list(entity_keys_and_attribute_map[entity_name_n1][0])
            entity_name_n2 = relationship[relation_name][1]
            entity_n2_key = list(entity_keys_and_attribute_map[entity_name_n2][0])

            relation_attribute_list = relationship['关系属性']
            relation_attribute_list.extend(entity_n1_key)
            relation_attribute_list.extend(entity_n2_key)
            multi_relation[relation_name] = {'属性':relation_attribute_list, '外键':{entity_n1_key[0]:{entity_name_n1:entity_n1_key[0]}, entity_n2_key[0]:{entity_name_n2: entity_n2_key[0]}}}  # 这个格式就跟实体的属性格式很像了

        elif relationship['比例关系'] == '多对一':  # TODO 还需要给entity中加外键
            entity_name_1 = relationship[relation_name][1]
            entity_1_key = list(entity_keys_and_attribute_map[entity_name_1][1])
            entity_name_n = relationship[relation_name][0]
            attributes_all[entity_name_n].extend(entity_1_key)
            attributes_all_with_foreign_key[entity_name_n] = {'属性':attributes_all[entity_name_n], '外键':{entity_1_key[0]:{entity_name_1:entity_1_key[0]}}}


        else:  # 无论是一对多还是一对一，把1端的主键加入到n端中
            entity_name_1 = relationship[relation_name][0]
            entity_1_key = list(entity_keys_and_attribute_map[entity_name_1][0])  # TODO 默认这个时候的主键只有一个，因为在连接的实体主键一般只有一个
            entity_name_n = relationship[relation_name][1]
            attributes_all[entity_name_n].extend(entity_1_key)
            attributes_all_with_foreign_key[entity_name_n] = {'属性':attributes_all[entity_name_n], '外键':{entity_1_key[0]:{entity_name_1:entity_1_key[0]}}}


    return multi_relation, attributes_all_with_foreign_key





async def predict_entity_schema(entity_add_relation_attributes_all, entity_add_relation_keys_and_attribute_map):
    '''将主键加入到属性集合中'''
    entity_attributes_all_and_key = {}
    for entity_name in entity_add_relation_attributes_all:
        attributes = list(entity_add_relation_attributes_all[entity_name]['属性'])
        if '外键' in entity_add_relation_attributes_all[entity_name]:
            foreign_key = entity_add_relation_attributes_all[entity_name]['外键']
        else:
            foreign_key = {}
        keys = list(entity_add_relation_keys_and_attribute_map[entity_name][0])
        entity_attributes_all_and_key[entity_name] = {'属性':attributes, '主键':keys, '外键':foreign_key}

    return entity_attributes_all_and_key


async def predict_relation_schema(multi_relation, relation_keys_and_attribute_map):
    relation_attributes_all_and_key = {}
    for relation_name in multi_relation:  # multi_relation是一个list，其中每个元素对应一个关系。
        attributes = list(multi_relation[relation_name]['属性'])
        keys = list(relation_keys_and_attribute_map[relation_name][0])
        relation_attributes_all_and_key[relation_name] = {'属性':attributes, '主键':keys, '外键':multi_relation[relation_name]['外键']}  # 这里还差一个外键

    return relation_attributes_all_and_key



def clear_analyses(analyses):
    match = re.search("最终可以得出(.*)", analyses, re.DOTALL)
    # 如果匹配成功，则输出匹配的内容
    if match:
        content_after = match.group(1)
        return content_after.strip()  # 使用strip()去除前后的空白字符
    else:
        return "没有找到匹配的内容"



def extract_json_from_text(text):
    data = {}
    if 'yes' in text or 'no' in text:
        data = {}
    else:
        # 使用正则表达式查找第一个{或[的位置
        match_s = re.search(r'[{\[]', text)
        matches_e = re.findall(r'[}\]]', text)
        if match_s and matches_e:
            first_bracket_pos = match_s.start()
            end_bracket_pos = text.rfind(matches_e[-1])
            json_str = text[first_bracket_pos: end_bracket_pos+1].replace('`', '').replace("'", '"')
            # print(json_str)
            data = json.loads(json_str)
        else:
            print('没有匹配到json')

    return data



async def get_time(city: str) -> str:
    return f"The weather in {city} is 173 degrees and Sunny."


async def get_computer(city: str) -> str:
    return f"The weather in {city} is 723 degrees and Sunny."