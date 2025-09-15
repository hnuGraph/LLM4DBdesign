import json
import re
import logging
from collections import defaultdict
from typing_extensions import Annotated

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


def extract_answer_from_text(file_path, save_path):
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = re.split(r'---- id:', content)[1:]  
    print(f'len of ids : {len(entries)}')
    data_list = []
    suss_ids = []
    id_counts = []
    for entry in entries:
        # Extract id
        id_match = re.match(r'([a-f0-9]{24})', entry)
        if id_match:
            id_value = id_match.group(1)
            logger.info(id_value)
            id_counts.append(id_value)
            # Get trajectory (execution order) information
            trajectory = []
            agents = re.findall(r'---------- (\w+Agent) ----------', entry)
            trajectory.extend(agents)  # Collect all Agent names as execution order

            pattern = r'```json(.*?)```'
            matches = re.findall(pattern, entry, re.DOTALL)
            flag = 0
            
            # Print matched content
            for match in matches[::-1]:  
                try:
                    match_format = json.loads(match.strip())
                except:
                    try:
                        match_format = json.loads(match.strip().replace("'", '"'))
                    except Exception as e:
                        logger.error(e)
                        match_format = match
                        if '"schema"' in match_format or "'schema'" in match_format:  #schema  #output
                            flag = 1
                if isinstance(match_format, dict) and 'schema' in match_format:
                    answer = match_format['schema']
                elif flag == 1:
                    answer = match_format
                else:
                    continue
                # Create dictionary and add to list
                data = {
                    'id': id_value,
                    'trajectory': trajectory,
                    'schema': answer
                }
                data_list.append(data)
                suss_ids.append(id_value)
                break
    
    error_ids = list(set(id_counts) - set(suss_ids))
        
    print(f'total ids : {len(id_counts)}, sucess ids : {len(suss_ids)}, error ids: {len(error_ids)}')
    print(error_ids)

    # # Save to file
    # with open(save_path, 'w', encoding='utf-8') as f:
    #     for data in data_list:
    #         f.write(json.dumps(data, ensure_ascii=False) + '\n')


 
def extract_answer_from_sample(content):

    entries = re.split(r'---- id:', content)[1:]  
    data_list = []
    for entry in entries:
        # Extract id
        id_match = re.match(r'([a-f0-9]{24})', entry)
        if id_match:
            id_value = id_match.group(1)
            logger.info(id_value)
            # Get trajectory (execution order) information
            trajectory = []
            agents = re.findall(r'---------- (\w+Agent) ----------', entry)
            trajectory.extend(agents)  # Collect all Agent names as execution order

            pattern = r'```json(.*?)```'
            matches = re.findall(pattern, entry, re.DOTALL)
            flag = 0
            # Print matched content
            for match in matches[::-1]:  
                try:
                    match_format = json.loads(match.strip())
                except:
                    try:
                        match_format = json.loads(match.strip().replace("'", '"'))
                    except Exception as e:
                        logger.error(e)
                        match_format = match
                        if '"schema"' in match_format or "'schema'" in match_format:  #schema  #output
                            flag = 1
                if isinstance(match_format, dict) and 'schema' in match_format:
                    answer = match_format['schema']
                elif flag == 1:
                    answer = match_format
                else:
                    continue
                # Create dictionary and add to list
                data = {
                    'id': id_value,
                    'trajectory': trajectory,
                    'schema': answer
                }
                data_list.append(data)
                break

    return data_list


extract_answer_from_text("../output/agent_txt/agent_chat_deepseek.txt" , '../output/test.txt')