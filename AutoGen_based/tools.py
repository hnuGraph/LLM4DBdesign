from collections import defaultdict

from typing_extensions import Annotated


# 计算闭包
async def compute_closure(base_set, deps):
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
async def find_candidate_keys(attrs, deps):
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

async def get_attribute_keys_by_arm_strong(dependencies_json:Annotated[str, "json in function dependencies {实体名或关系名:{属性名1:[被函数决定的属性名]}}"]):
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


async def decompose_to_3NF(entity_fd_json:Annotated[str, "json in function dependencies {实体名或关系名:{属性名x:[被属性名x函数决定的属性名]}}"],
                           entity_primary_keys:Annotated[dict, "json in {实体名或关系名:[{属性名}]}"],
                           attributes_all:Annotated[dict, "json in {实体名或关系名:[属性名]}"]):
    """
    自动分解当前关系到 3NF。
    """

    def get_common_element_list(list1, list2):
        set1 = set(list1)
        set2 = set(list2)
        intersection = list(set1.intersection(set2))
        return intersection

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
    transitive_partial_dependencies = defaultdict(lambda: {"分解关系": []})

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
        transitive_partial_dependencies[entity]["分解关系"] = unique_relations


    transitive_partial_dependencies = {key: value for key, value in
                                       transitive_partial_dependencies.items()}  # 转为普通dict
    # 选课关系中，没有这两种依赖关系
    print(f'transitive_partial_dependencies:\n {transitive_partial_dependencies}')

    # 8. 开始拆实体表，算法实现
    new_entity_add_relation_attributes_all = defaultdict(dict)
    new_entity_add_relation_keys_and_attribute_map = {}
    for entity_name in transitive_partial_dependencies:
        if len(transitive_partial_dependencies[entity_name]['分解关系']) == 1:  # 表示不用拆表
            new_entity_add_relation_attributes_all[entity_name]['属性'] = attributes_all[
                entity_name]
            new_entity_add_relation_keys_and_attribute_map[entity_name] = entity_primary_keys[
                entity_name]
        else:  # 需要拆表
            for sub_table_attributes in transitive_partial_dependencies[entity_name]['分解关系']:
                candidate_keys = get_attribute_keys_by_arm_strong_each(sub_table_attributes,
                                                                       entity_fd_json[
                                                                           entity_name])
                new_entity_name = ''
                for candidate_key in candidate_keys:
                    new_entity_name = ''.join(candidate_key)  # TODO 如果已经存在了这个new_entity_name 还需要额外的操作
                new_entity_add_relation_attributes_all[new_entity_name]['属性'] = sub_table_attributes
                new_entity_add_relation_attributes_all[new_entity_name]['外键'] = {}
                # 处理下外键关系

                # foreign_keys = list(entity_attributes_all_with_foreign_key[entity_name]['外键'].keys())
                # common_keys = get_common_element_list(foreign_keys, sub_table_attributes)

                # for key in common_keys:
                #     new_entity_add_relation_attributes_all[new_entity_name]['外键'][key] = \
                #     entity_attributes_all_with_foreign_key[entity_name]['外键'][key]
                new_entity_add_relation_keys_and_attribute_map[new_entity_name] = candidate_keys

    print(f'new_entity_add_relation_attributes_all:\n {new_entity_add_relation_attributes_all}')
    print(f'new_entity_add_relation_keys_and_attribute_map:\n {new_entity_add_relation_keys_and_attribute_map}')

    return new_entity_add_relation_attributes_all, new_entity_add_relation_keys_and_attribute_map