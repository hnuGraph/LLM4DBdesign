
def get_question_analysis_prompt(question):
    question_analyzer = f"你是数据库领域中的需求分析专家。你将结合自身经验和相关理论仔细检查和分析用户需求。"
    prompt_get_question_analysis = f"请你仔细阅读此问题中的需求: '''{question}''' 利用你的专业知识, 对这个需求进行分析。注意不要输出其他无关内容，不要对需求进行扩充或者缩减。"

    return question_analyzer, prompt_get_question_analysis



def get_entity_analysis_prompt(question_analysis):
    subtask_analyzer = f"你是构建数据库概念模型的专家，你特别擅长从需求分析中识别出数据库实体。"
    prompt_get_requirement_analyses = f"我们获得了来自需求分析领域专家的分析。 \n"
    prompt_get_requirement_analyses += f"需求分析领域专家的分析结果为: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += f"你需要深入理解需求分析的内容，得到本需求中的数据库实体。特别值得注意的是，关系实体或关联实体不是数据库实体。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，[思考内容]，最终可以得出数据库实体python list格式显示为：[实体名称1、实体名称2]'''。不需要再对每个实体进行详细解释。不需要显示中括号。用中文输出。"

    return subtask_analyzer, prompt_get_requirement_analyses


def get_entity_all_analysis_prompt(question_analysis):
    data_format = '''
                  {'数据库实体1':['实体属性1', '实体属性2'],
                   '数据库实体2':['实体属性3', '实体属性4']}
                  '''
    subtask_analyzer = f"你是构建数据库概念模型的专家，你特别擅长从需求分析中识别出数据库实体及实体属性。"
    prompt_get_requirement_analyses = f"我们获得了来自需求分析领域专家的分析。 \n"
    prompt_get_requirement_analyses += f"需求分析领域专家的分析结果为: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += f"回顾需求分析专家对需求描述的分析，你需要深入理解需求分析的内容，得到本需求中的数据库实体及实体属性。需要设置编号(ID)属性。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，'''思考内容'''，最终可以得出数据库实体及其属性的json格式显示为：{data_format}''' 不要生成额外的内容。请用中文输出。"

    return subtask_analyzer, prompt_get_requirement_analyses


def get_entity_all_analysis_prompt_v1(question_analysis):
    data_format = '''
                  {'数据库实体1':['实体属性1', '实体属性2'],
                   '数据库实体2':['实体属性3', '实体属性4']}
                  '''
    subtask_analyzer = f"你是构建数据库概念模型的专家，你特别擅长从需求分析中识别出数据库实体及实体属性。"
    prompt_get_requirement_analyses = f"我们获得了来自需求分析领域专家的分析。 \n"
    prompt_get_requirement_analyses += f"需求分析领域专家的分析结果为: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += f"回顾需求分析专家对需求描述的分析，你需要深入理解需求分析的内容，得到本需求中的数据库实体及实体属性。需要设置编号(ID)属性。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，'''思考内容'''，最终可以得出数据库实体及其属性的json格式显示为：{data_format}''' 不要生成额外的内容。请用中文输出。"

    return subtask_analyzer, prompt_get_requirement_analyses

def get_entity_all_analysis_english_prompt_v1(question_analysis):
    data_format = '''
                    {'Database entity 1':['Entity attribute 1', 'Entity attribute 2'],
                    'Database entity 2':['Entity attribute 3', 'Entity attribute 4']}
                  '''
    subtask_analyzer = f"You are an expert in building database conceptual models. You are particularly good at identifying database entities and entity attributes from requirement analysis."
    prompt_get_requirement_analyses = f"We have obtained analysis from experts in the field of requirement analysis. \n"
    prompt_get_requirement_analyses += f"The analysis results of experts in the field of requirement analysis are: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += f"Review the analysis of the requirement description by the requirement analysis expert. You need to deeply understand the content of the requirement analysis and obtain the database entities and entity attributes in this requirement. You need to set the number (ID) attribute."
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step,... I can finally conclude that the JSON format of the database entity and its attributes is: {data_format}''' Do not generate additional content."
    return subtask_analyzer, prompt_get_requirement_analyses

def get_entity_all_analysis_prompt(question_analysis):
    data_format = '''
                  {'数据库实体1':['实体属性1', '实体属性2'],
                   '数据库实体2':['实体属性3', '实体属性4']}
                  '''
    subtask_analyzer = f"你是构建数据库实体-联系数据库模型的专家，你特别擅长从需求分析中识别出数据库实体集及实体集的属性。"
    prompt_get_requirement_analyses = f"实体-联系数据模型是一种高层数据模型。它将被称作实体的基本对象和这些对象之间的联系区分开来。该模型通常用于数据库模式设计的第一步。 \n"
    prompt_get_requirement_analyses += (f"我向你解释数据库中实体集和实体集属性的定义。一个实体是现实世界中可区别于所有其他对象的一个“事物”或“对象”。例如，大学中的每个人都是一个实体。"
                                        f"每个实体有一组性质，并且某些性质集合的值必须唯一地标识一个实体。例如，一个人可能具有人员编号性质，其值唯一标识了这个人。"
                                        f"因此，人员编号的值677-89-9011将唯一标识出大学中一个特定的人。类似地，课程也可以被看作实体，"
                                        f"并且课程编号唯一标识出了大学中的某个课程实体。实体可以是实实在在的，比如一个人或一本书; 实体也可以是抽象的，"
                                        f"比如课程、开设的课程段或者航班预订。\n")
    prompt_get_requirement_analyses += (f"实体集是共享相同性质或属性的、具有相同类型的实体的集合。例如，一所给定大学的所有教师的集合"
                                        f"可定义为教师实体集。类似地，学生实体集可以表示该大学中的所有学生的集合。")
    prompt_get_requirement_analyses += (f"实体通过一组属性来表示。属性是实体集中每个成员所拥有的描述性性质。为实体集设计一个属性表明数据库存储"
                                        f"关于该实体集中每个实体的类似信息，但每个实体在每个属性上可以有它自己的值。教师实体集可能具有的属性是教师编号、姓名、所属学院和薪资。\n")
    prompt_get_requirement_analyses += f"现在我们获得了来自需求分析领域专家的分析结果: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += f"你需要深入理解需求分析的内容以及实体集和实体属性的定义，得到本需求中的数据库实体集及实体集属性。需要为每个实体集设置编号(ID)属性。不要生成额外的内容。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，**思考内容...** 最终，我可以将数据库中的实体集及其属性以JSON格式呈现如下：{data_format}。''' "

    return subtask_analyzer, prompt_get_requirement_analyses




def get_entity_all_analysis_english_prompt(question_analysis):
    data_format = '''
                    {'Database entity 1':['Entity attribute 1', 'Entity attribute 2'],
                    'Database entity 2':['Entity attribute 3', 'Entity attribute 4']}
                  '''
    subtask_analyzer = (f"You are an expert in building database entity-relationship database models. "
                        f"You are particularly good at identifying database entity sets and entity set attributes from requirements analysis.")
    prompt_get_requirement_analyses = (f"The entity-relationship (E-R) model is a high-level data model. Instead of representing all data in tables, "
                                       f"it distinguishes between basic called entities, and relationships among these objects. "
                                       f"It is often used as a first step in database-schema design.\n")
    prompt_get_requirement_analyses += (f"I will explain to you the definitions of entity sets and entity set attributes in the database. \n"
                                        f"An entity is a “thing” or “object” in the real world that is distinguishable from all other objects. "
                                        f"For example, each person in a university is an entity. An entity has a set of properties, and the "
                                        f"values for some set of properties may uniquely identify an entity. For instance, a person may "
                                        f"have a person id property whose value uniquely identifies that person. Thus, the value 677-89-9011"
                                        f" for person id would uniquely identify one particular person in the university. Similarly, courses"
                                        f" can be thought of as entities, and course id uniquely identifies a course entity in the university. "
                                        f"An entity may be concrete, such as a person or a book, or it may be abstract, such as a course, "
                                        f"a course offering, or a flight reservation. ")
    prompt_get_requirement_analyses += (f"An entity set is a set of entities of the same type that share the same properties,"
                                        f"or attributes. The set of all people who are instructors at a given university, for"
                                        f"example, can be defined as the entity set instructor. Similarly, the entity set student"
                                        f"might represent the set of all students in the university")
    prompt_get_requirement_analyses += (f"An entity is represented by a set of attributes. Attributes are descriptive"
                                        f"properties possessed by each member of an entity set. The designation of an"
                                        f"attribute for an entity set expresses that the database stores similar information"
                                        f"concerning each entity in the entity set; however, each entity may have its own"
                                        f"value for each attribute. Possible attributes of the instructor entity set are ID, name,"
                                        f"dept name, and salary.")
    prompt_get_requirement_analyses += f"Now we have obtained the analysis results from experts in the field of requirement analysis: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += (f"You need to deeply understand the content of requirement analysis and the definition of entity sets and entity attributes, "
                                        f"and get the database entity sets and entity set attributes in this requirement. You need to set the number (ID) attribute for "
                                        f"each entity set. Do not generate additional content.")
    prompt_get_requirement_analyses += (f"Your output format should be'''After thinking step by step, **Thinking content...** "
                                        f"In the end, I can present the entity set and its attributes in the database in JSON format as follows: {data_format}.''' ")


    return subtask_analyzer, prompt_get_requirement_analyses



def get_verification_entity_prompt(question_analysis, entity_analyses, entity_name):
    subtask_analyzer = f"你是构建数据库概念模型的专家"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analysis}''' \n 数据库实体识别专家的分析内容为：'''{entity_analyses}''' \n"
    prompt_get_requirement_analyses += f"数据库实体识别专家认为'''{entity_name}'''是一个数据库实体 \n"
    prompt_get_requirement_analyses += f"作为一位构建数据库概念模型的专家，请仔细阅读需求分析结果和实体识别结果，并决定你的意见是否与实体识别专家的意见一致。"
    prompt_get_requirement_analyses += f"这是你判断时必须遵守的规则：1.数据库实体能对应数据库中的一张表。 2.【两】个实体之间产生的关系实体或者关联实体【不】是一个数据库实体。3.可以通过计算得出的结果不需要实体和实体表"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''在仔细阅读需求分析结果和实体识别结果后，[分析内容]，我的回答是：[yes or no]"

    return subtask_analyzer, prompt_get_requirement_analyses


def get_consensus_prompt(question_analysis, entity_analysis):
    subtask_analyzer = f"你是构建数据库概念模型的专家"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analysis}''' 我们获得了来自数据库实体识别专家的分析。 \n"
    prompt_get_requirement_analyses += f"数据库实体识别专家的分析结果为: '''{entity_analysis}''' \n"
    prompt_get_requirement_analyses += f"作为一位构建数据库概念模型的专家，请仔细阅读需求分析结果和实体识别结果，并决定你的意见是否与实体识别专家的意见一致。"
    prompt_get_requirement_analyses += f"这是你判断时必须遵守的规则：1.关系实体或者关联实体【不】是一个数据库实体。2.数据库实体中一般【不】包含来自其他实体的外键。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''在仔细阅读需求分析结果和实体识别结果后，[分析内容]，我的回答是：[yes or no]"

    return subtask_analyzer, prompt_get_requirement_analyses



def get_consensus_opinion_prompt(question_analysis, entity_analyses, quality_controller_opi):
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analysis}''' 我们获得了来自数据库实体识别专家的分析。 \n"
    prompt_get_requirement_analyses += f"数据库实体识别专家的分析结果为: '''{entity_analyses}''' \n"
    prompt_get_requirement_analyses += f"此外，我们还获得了另一位构建数据库概念模型的专家，对这个分析结果的修改建议：'''{quality_controller_opi}''' \n 确保根据修改意见对实体识别专家的分析结果进行修改，包括删除或增添实体操作。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，[思考内容]，最终可以得出修改后的数据库实体及其属性为：[{{数据库实体1:实体属性1、实体属性2}}]'''。分行显示每个实体，不需要显示中括号。用中文输出。"

    return prompt_get_requirement_analyses




def get_entity_attribute_analysis_prompt(question_analysis, entity_analysis):
    subtask_analyzer = f"你是构建数据库概念模型的专家，你特别擅长从需求分析中识别出数据库实体的属性。"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analysis}''' 我们获得了来自数据库实体识别专家的分析。 \n"
    prompt_get_requirement_analyses += f"数据库实体识别专家的的分析结果为: '''{entity_analysis}''' \n"
    prompt_get_requirement_analyses += f"回顾需求分析专家对需求描述的分析，以及数据库实体识别专家对此需求中实体的分析，你需要深入理解需求分析的内容，精准得到本需求中的数据库实体属性。"
    prompt_get_requirement_analyses += f"特别值得注意的是，数据库实体属性在非必要场景下不单独设置编号(ID)属性。只需要识别属性，不需要识别主键。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，[思考内容]，最终可以得出数据库实体的属性为：[数据库实体:其对应的实体属性1、实体属性2]'''。分行显示每个实体，不需要显示中括号。"

    return subtask_analyzer, prompt_get_requirement_analyses



# TODO 这个肯定还需要改，对每个实体进行提问
def get_relation_analysis_prompt(question_analyses, entity_analysis):
    subtask_analyzer = f"你是构建数据库概念模型的专家，你特别擅长识别出数据库实体之间的关系。"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analyses}''' 我们获得了来自数据库实体识别专家的分析。 \n"
    prompt_get_requirement_analyses += f"数据库实体识别专家的的分析结果为: '''{entity_analysis}''' \n"
    prompt_get_requirement_analyses += f"回顾需求分析专家对需求描述的分析，以及数据库实体识别专家对此需求中实体的分析，你需要深入理解需求分析的内容，得到本需求中数据库实体之间的关系。"
    prompt_get_requirement_analyses += f"特别值得注意的是，你只需要识别具有关系的实体对以及对应的关系名称，不需要识别关系的比例。关系名称不能与实体名相同。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，'''思考内容'''，最终可以得出数据库实体关系为：[关系名称1:实体名1、实体名2]'''。每个关系间用'，'分隔，不需要显示中括号。"

    return subtask_analyzer, prompt_get_requirement_analyses


def get_relation_all_analysis_prompt(question_analyses, entity_analysis):
    subtask_analyzer = f"你是构建数据库概念模型的专家，你特别擅长识别出数据库实体之间的关系以及关系的比例类型和关系的属性。"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analyses}''' 我们获得了来自数据库实体识别专家的分析。 \n"
    prompt_get_requirement_analyses += f"数据库实体识别专家的的分析结果为: '''{entity_analysis}''' \n"
    prompt_get_requirement_analyses += f"你需要深入理解需求分析的内容，判断'''{list(entity_analysis.keys())}'''中两两实体之间是否具有关系。如果有关系，生成关系名、关系的比例类型和属于关系的属性。"
    prompt_get_requirement_analyses += f"你必须做到以下几点：1.实体名必须包含在实体识别专家的的分析结果中。2.关系名称不能与实体名相同。3.关系的比例类型包括一对一，一对多，多对一还是多对多。4.如果没有值则填空字符串"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，'''思考内容'''，最终可以得出数据库实体关系json格式显示为：[{{'某关系名称':['实体名1','实体名2'], '比例关系':'一对一', '关系属性':['属性1','属性2']}}]'''"

    return subtask_analyzer, prompt_get_requirement_analyses



# 这里有个问题就是还需要让实体跟实体比例对应起来，1：n
def get_relation_analysis_type_prompt(question_analyses, relation_analyses):
    subtask_analyzer = f"你是构建数据库概念模型的专家，你特别擅长识别出数据库关系的比例类型，如一对一，一对多，多对一还是多对多。"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analyses}''' 我们获得了来自数据库实体间关系识别专家的分析。 \n"
    prompt_get_requirement_analyses += f"数据库实体间关系识别专家的的分析结果为: '''{relation_analyses}''' \n"
    prompt_get_requirement_analyses += f"回顾需求分析专家对需求描述的分析，以及数据库实体间关系识别专家对此需求中实体关系的分析，识别关系中实体之间的比例类型，并将此比例类型作为该关系的比例类型。"
    prompt_get_requirement_analyses += f"特别值得注意的是，数据库实体间关系识别专家给出的是形如'''[关系名称1:实体名1、实体名2]'''的关系描述。每个关系只对应一种比例类型。不要更改数据库实体间关系识别专家命名的关系名称。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，[思考内容]，\n 最终可以得出数据库实体之间的比例类型为：[关系名称1:关系比例类型1]'''。每个关系间用'，'分隔，不需要显示中括号。"

    return subtask_analyzer, prompt_get_requirement_analyses



def get_relation_analysis_attribute_prompt(question_analyses, entity_attribute_analyses, relation_analyses):
    subtask_analyzer = f"你是构建数据库概念模型的专家，你特别擅长识别出数据库关系的属性。"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analyses}''' 我们获得了来自数据库实体属性识别专家和数据库实体间关系识别专家的分析。 \n"
    prompt_get_requirement_analyses += f"数据库实体属性识别专家的分析结果为: '''{entity_attribute_analyses}''' \n"
    prompt_get_requirement_analyses += f"数据库实体间关系识别专家的分析结果为: '''{relation_analyses}''' \n"
    prompt_get_requirement_analyses += f"回顾需求分析专家对需求描述的分析，以及数据库实体间关系识别专家对此需求中实体关系的分析，你需要深入理解需求分析的内容，得到符合全局设计的结果。"
    prompt_get_requirement_analyses += f"特别值得注意的是，关系属性是只属于关系的属性，它不属于任何实体。只需要识别属性，不需要识别主键。关系名称应该与数据库实体间关系识别专家的描述一致。你的所有思考内容都应该在[思考内容]中体现，而不应该在最终结论中体现。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，[思考内容]，\n 最终可以得出数据库关系的属性为：[关系名称1:关系的属性1、关系的属性2]'''。分行显示每个关系，不需要显示中括号。当没有关系属性时只需输出关系名称，不需要输出关系属性。"

    return subtask_analyzer, prompt_get_requirement_analyses



def get_entity_functional_dependency_analysis_prompt(question_analyses, entity_attribute_analyses):
    output_format = '''
                    {
                    "实体名1": {"属性1": ["属性2"], "属性1, 属性2": ["属性4"]}, 
                    "实体名2": {"属性1": ["属性2"], "属性1": ["属性3"]}
                    }
                    '''
    subtask_analyzer = f"你是构建数据库概念模型的专家，你特别擅长识别出数据库实体属性之间的函数依赖关系。"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analyses}''' 我们获得了来自数据库实体属性识别专家的分析。 \n"
    prompt_get_requirement_analyses += f"数据库实体属性识别专家的的分析结果为: '''{entity_attribute_analyses}''' \n"
    prompt_get_requirement_analyses += f"回顾需求分析专家对需求描述的分析，以及数据库实体属性识别专家的分析，你需要深入理解需求分析的内容，得到数据库实体属性之间的函数依赖关系。"
    prompt_get_requirement_analyses += f"特别值得注意的是，函数依赖只存在于每个实体内部的属性之间。不要生成额外内容。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，'''思考内容'''，\n 最终可以得出数据库实体属性之间的函数依赖关系为：{output_format}'''"

    return subtask_analyzer, prompt_get_requirement_analyses



def get_relation_functional_dependency_analysis_prompt(question_analyses, relation_attribute_analyses):
    output_format = '''
                    {
                    "关系名1": {"属性1": ["属性2"], "属性1, 属性2": ["属性4"]}, 
                    "关系名2": {"属性1": ["属性2"], "属性1": ["属性3"]}
                    }
                    '''
    subtask_analyzer = f"你是构建数据库概念模型的专家，你特别擅长识别出数据库关系属性之间的函数依赖关系。"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analyses}''' 我们获得了来自数据库关系属性识别专家的分析。 \n"
    prompt_get_requirement_analyses += f"数据库关系属性识别专家的的分析结果为: '''{relation_attribute_analyses}''' \n 其中key值表示关系名称，value值表示关系的属性。"
    prompt_get_requirement_analyses += f"回顾需求分析专家对需求描述的分析，以及数据库关系属性识别专家的分析，你需要得到数据库关系属性{relation_attribute_analyses}中每个关系的函数依赖关系。"
    prompt_get_requirement_analyses += f"特别值得注意的是，函数依赖只存在于每个关系内部的属性之间。不要生成额外内容。如果没有提供关系属性则生成空的json。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，'''思考内容'''，最终可以得出数据库关系属性之间的函数依赖关系为：{output_format}'''。"

    return subtask_analyzer, prompt_get_requirement_analyses




def get_dependency_consensus_prompt(question_analyses, entity_attributes, entity_dependency_analyses):
    subtask_analyzer = f"你是构建数据库概念模型的专家。"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analyses}''' 我们获得了一个实体(关系)及其属性：{entity_attributes}。 \n"
    prompt_get_requirement_analyses += f"属性依赖关系识别专家的分析结果为: '''{entity_dependency_analyses}''' \n"
    prompt_get_requirement_analyses += f"你需要深入理解需求分析的内容，结合你自身丰富的经验知识，决定你的意见是否与属性依赖关系识别专家的意见一致"
    prompt_get_requirement_analyses += f"特别值得注意的是，你的所有思考内容都应该在[思考内容]中体现，"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，[思考内容]，我的回答是：[yes or no]"

    return subtask_analyzer, prompt_get_requirement_analyses



def get_relation_dependency_consensus_prompt(question_analyses, relation_attributes, relation_dependency_analyses):
    subtask_analyzer = f"你是构建数据库概念模型的专家。"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analyses}''' 我们获得了一个实体(关系)及其属性：{relation_attributes}。\n"
    prompt_get_requirement_analyses += f"属性依赖关系识别专家的分析结果为: '''{relation_dependency_analyses}''' \n"
    prompt_get_requirement_analyses += f"你需要深入理解需求分析的内容，结合你自身丰富的经验知识，你应该设想多个场景对属性依赖关系识别专家的分析结果进行判断。"
    prompt_get_requirement_analyses += f"场景包括但不限于：1.决定属性是否能唯一标识依赖属性；2. 如果将一个依赖关系转为一张表，决定属性的所有组合值是否只出现一次；..."
    prompt_get_requirement_analyses += f"特别值得注意的是，你的所有思考内容都应该在[思考内容]中体现。如果不符合场景，你的意见将与属性依赖关系识别专家的意见不一致，请问答no。如果符合场景，请回答yes。 \n"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，[思考内容]，我的回答是：[yes or no]"

    return subtask_analyzer, prompt_get_requirement_analyses

def get_dependency_consensus_opinion_prompt(question_analyses, entity_attributes, entity_dependency_analyses, quality_controller_opi):
    output_format = '''
                        {
                        "实体名1或者关系名1": {"属性1": ["属性2"], "属性1, 属性2": ["属性4"]}, 
                        }
                        '''
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analyses}''' 我们获得了一个实体及其实体属性：{entity_attributes} \n"
    prompt_get_requirement_analyses += f"属性依赖关系识别专家的分析结果为:'''{entity_dependency_analyses}''' \n"
    prompt_get_requirement_analyses += f"此外，我们还获得了另一位构建数据库概念模型的专家，对这个分析结果的修改建议：'''{quality_controller_opi}''' \n 确保根据修改意见对数据库属性依赖关系识别专家结果进行修改。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，'''思考内容'''，最终可以得出修改后的属性之间的函数依赖关系为：{output_format}'''"
    return prompt_get_requirement_analyses


def get_relation_dependency_consensus_opinion_prompt(question_analyses, relation_attributes, relation_dependency_analyses, quality_controller_opi):
    output_format = '''
                        {
                        "关系名1": {"属性1": ["属性2"], "属性1, 属性2": ["属性4"]}, 
                        }
                        '''
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analyses}''' 我们获得了一个关系及其属性：{relation_attributes} \n"
    prompt_get_requirement_analyses += f"属性依赖关系识别专家的分析结果为:'''{relation_dependency_analyses}''' \n"
    prompt_get_requirement_analyses += f"此外，我们还获得了另一位构建数据库概念模型的专家，对这个分析结果的修改建议：'''{quality_controller_opi}''' \n 确保根据修改意见对数据库属性依赖关系识别专家结果进行修改。如果没有函数依赖关系则value生成空的json。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，'''思考内容'''，最终可以得出修改后的属性之间的函数依赖关系为：{output_format}'''"
    return prompt_get_requirement_analyses

def get_relation_revised_analysis_prompt(question_analyses, relation_item_analyses, entity_schemas):
    output_format = '''
                    {
                    "实体名1": {"属性": ["属性1", "属性2"], "主键": ["属性1"], "外键":[]}, 
                    "关系名2": {"属性": ["属性1", "属性2"], "主键": ["属性1"], "外键":[{"属性2":{"实体名1":"属性1"}}]}
                    }
                    '''
    subtask_analyzer = f"你是构建数据库概念模型的专家。"
    prompt_get_requirement_analyses = f"根据需求分析领域专家对需求的分析结果: '''{question_analyses}''' 我们获得了来自数据库关系识别专家的分析。 \n"
    prompt_get_requirement_analyses += f"数据库关系识别专家对某关系的分析结果为: '''{relation_item_analyses}''' \n"
    relation_name = list(relation_item_analyses.keys())[0]
    prompt_get_requirement_analyses += f"表示{relation_name}关系连接两个实体：{relation_item_analyses[relation_name]}\n"
    prompt_get_requirement_analyses += f"但是这个关系中不存在主键，这意味着这两个实体之间无法用一个关系进行连接。需要创建一个新实体。"
    prompt_get_requirement_analyses += f"这是已有的实体：{entity_schemas} \n"
    prompt_get_requirement_analyses += f"请你继续深入理解需求分析的内容，得到新的实体以及实体属性、主键、外键，关系及关系属性、主键、外键。"
    prompt_get_requirement_analyses += f"你的设计原则包括：1.实现需求描述中的功能。2.遵循前文，该关系中不存在主键，连接的两个实体无法唯一标识。2.设想多个场景，减少数据冗余。3.已有的实体不要在结果中生成。"
    prompt_get_requirement_analyses += f"你的输出格式应该为'''经过我一步一步地思考，'''思考内容'''，最终可以得出数据库关系模式为：{output_format}'''"

    return subtask_analyzer, prompt_get_requirement_analyses



# def get_direct_prompt(question):
#     direct_format = '{"关系模式名1":{"属性": ["属性名1", "属性名2"],"主键": ["属性名1"]},"关系模式名2":{"属性": ["属性名3", "属性名4"],"主键": ["属性名3", "属性名1"],"外键": {"关系模式名1": ["属性名1"]}}}'
#     prompt = f"业务需求: {question} \n 请根据业务需求，生成数据库模式。你生成的内容应该与'''{direct_format}'''的格式相同。在必要的时候才为实体添加ID属性进行标识，不需要生成任何额外的内容"
#     return prompt


def get_direct_prompt(question):
    direct_format = '''
                    {
                        'schema': 
                        {
                            "Relationship schema name 1":
                                {
                                "Attributes":["Attribute name 1", "Attribute name 2"],
                                "Primary key":["Attribute name 1"]
                                },
                            "Relationship schema name 2":
                                {
                                "Attributes":["Attribute name 3","Attribute name 4"],
                                "Primary key":["Attribute name 3","Attribute name 1"],
                                "Foreign key":{
                                        "Attribute name 4":{"Relationship schema name 1":"Attribute name 1"}
                                        }
                                }
                        }
                    }
                    '''
    example = '''
            requirement: A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, department, dormitory address. The addresses of student dormitories in the same department are the same. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
            answer: {
                        'schema': {
                            "Student":
                                {
                                    "Attributes": ['ID', 'Name', 'Age', 'Department'],
                                    "Primary key": ['ID']
                                    "Foreign key": {
                                                "Department": {"Department": "ID"}
                                                }
                                },
                            "Department":
                            {
                                "Attributes": ['ID', 'Name', 'Dormitory Adress'],
                                "Primary key": ['ID']
                            },
                            "Course":
                            {
                                "Attributes": ['Number', 'Credits', 'Lecturer', 'Class Time'],
                                "Primary key": ['Number']
                            },
                            "Course Selection":
                            {
                                    "Attributes": ['ID', 'Number', 'Selection Time'],
                                    "Primary key": ['ID', 'Number']
                                    "Foreign key": {
                                                "ID": {"Student": "ID"},
                                                "Number": {"Course": "Number"},
                                                }
                            }
                        }
                    }
              '''
    prompt = f'''
                You are a database design expert. You need to come up with database schemas that meet the requirements provided.
                requirement:{question} 
                Please generate a database schema based on requirements and the knowledge provided. The content you generate should be in the same format as {direct_format}. 
                You should pay attention to these constraints when responding:
                1. Add ID attributes to entities for identification only when necessary, without generating any additional content.
                2. If the schema describes an entity, the schema name should be a noun. If the schema describes a relationship, the schema name be a verb.
                3. All words are separated, e.g. ProductID should be Product ID.
                Here is a example:
                {example}
              '''
    return prompt



def get_direct_few_shot_prompt(question):
    direct_format = '''
                    {
                        'schema': 
                        {
                            "Relationship schema name 1":
                                {
                                "Attributes":["Attribute name 1", "Attribute name 2"],
                                "Primary key":["Attribute name 1"]
                                },
                            "Relationship schema name 2":
                                {
                                "Attributes":["Attribute name 3","Attribute name 4"],
                                "Primary key":["Attribute name 3","Attribute name 1"],
                                "Foreign key":{
                                        "Attribute name 4":{"Relationship schema name 1":"Attribute name 1"}
                                        }
                                }
                        }
                    }
                    '''
    example = '''
            example 1:
            requirement: A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, department, dormitory address. The addresses of student dormitories in the same department are the same. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
            answer: {
                        'schema': {
                            "Student":
                                {
                                    "Attributes": ['ID', 'Name', 'Age', 'Department'],
                                    "Primary key": ['ID']
                                    "Foreign key": {
                                                "Department": {"Department": "ID"}
                                                }
                                },
                            "Department":
                            {
                                "Attributes": ['ID', 'Name', 'Dormitory Adress'],
                                "Primary key": ['ID']
                            },
                            "Course":
                            {
                                "Attributes": ['Number', 'Credits', 'Lecturer', 'Class Time'],
                                "Primary key": ['Number']
                            },
                            "Course Selection":
                            {
                                    "Attributes": ['ID', 'Number', 'Selection Time'],
                                    "Primary key": ['ID', 'Number']
                                    "Foreign key": {
                                                "ID": {"Student": "ID"},
                                                "Number": {"Course": "Number"},
                                                }
                            }
                        }
                    }
              example 2:
              requirement: The business requirements of a warehouse management system are described as follows: a warehousing company manages multiple warehouses, each of which has a warehouse number, address, and capacity. The company has multiple loaders, each of which has a number, name, and phone number. Cargo has ID and Name. Each inbound and outbound task needs to record the warehouse number, loader information, cargo information, quantity, and time. The system needs to support real-time monitoring and performance evaluation of warehouses and loading and unloading tasks.
              answer: {
                    "Warehouse":
                    {
                        "Attribute":
                        [
                            "Warehouse Number",
                            "Address",
                            "Capacity"
                        ],
                        "Primary key":
                        [
                            "Warehouse Number"
                        ],
                        "Foreign key":
                        {}
                    },
                    "Cargo":
                    {
                        "Attribute":
                        [
                            "Cargo ID",
                            "Cargo Name"
                        ],
                        "Primary key":
                        [
                            "Cargo ID"
                        ],
                        "Foreign key":
                        {}
                    },
                    "Loader":
                    {
                        "Attribute":
                        [
                            "Name",
                            "Phone",
                            "Loader ID"
                        ],
                        "Primary key":
                        [
                            "Loader ID"
                        ],
                        "Foreign key":
                        {}
                    },
                    "inbound outbound record":
                    {
                        "Attribute":
                        [
                            "Transaction ID",
                            "Time",
                            "Warehouse number",
                            "Transaction type"
                        ],
                        "Primary key":
                        [
                            "Transaction ID"
                        ],
                        "Foreign key":
                        {
                            "Warehouse number":
                            {
                                "Warehouse": "Warehouse number"
                            }
                        }
                    },
                    "goods inbound outbound record":
                    {
                        "Attribute":
                        [
                            "Goods ID",
                            "Transaction ID",
                            "Quantity"
                        ],
                        "Primary key":
                        [
                            "Goods ID",
                            "Transaction ID"
                        ],
                        "Foreign key":
                        {
                            "Transaction ID":
                            {
                                "inbound outbound record": "Transaction ID"
                            },
                            "Goods ID":
                            {
                                "Goods": "Goods ID"
                            }
                        }
                    },
                    "Stevedores Transaction record":
                    {
                        "Attribute":
                        [
                            "Stevedores ID",
                            "Transaction ID"
                        ],
                        "Primary key":
                        [
                            "Stevedores ID",
                            "Transaction ID"
                        ],
                        "Foreign key":
                        {
                            "Transaction ID":
                            {
                                "Transaction record": "Transaction ID"
                            },
                            "Stevedores ID":
                            {
                                "Stevedores": "Stevedores ID"
                            }
                        }
                    }
                }
              example 3:
              requirement: Business requirement description of grassroots organization election management system: A grassroots mass autonomous organization needs to manage the election process, including candidates, voters and voting records. Candidates have candidate numbers, names, genders, dates of birth and positions; voters have voter numbers, names, genders, dates of birth and contact information; a voter can only vote for one candidate, and voters also need to record voting time and voting location when voting. The system can count the number of votes for each candidate.,
              answer: {
                    "Candidate":
                    {
                        "Attribute":
                        [
                            "Candidate Number",
                            "Name",
                            "Gender",
                            "Date of Birth",
                            "Position"
                        ],
                        "Primary key":
                        [
                            "Candidate Number"
                        ],
                        "Foreign key":
                        {}
                    },
                    "Voter":
                    {
                        "Attribute":
                        [
                            "Voter Number",
                            "Name",
                            "Gender",
                            "Date of Birth",
                            "Contact Information",
                            "Candidate Number",
                            "Voting Time",
                            "Voting Location"
                        ],
                        "Primary key":
                        [
                            "Voter Number"
                        ],
                        "Foreign key":
                        {
                            "Candidate Number":
                            {
                                "Candidate": "Candidate Number"
                            }
                        }
                    }
                }
              '''
    prompt = f'''
                You are a database design expert. You need to come up with database schemas that meet the requirements provided.
                requirement:{question} 
                Please generate a database schema based on requirements and the knowledge provided. The content you generate should be in the same format as {direct_format}. 
                You should pay attention to these constraints when responding:
                1. Add ID attributes to entities for identification only when necessary, without generating any additional content.
                2. If the schema describes an entity, the schema name should be a noun. If the schema describes a relationship, the schema name be a verb.
                3. All words are separated, e.g. ProductID should be Product ID.
                Here is a example:
                {example}
              '''
    return prompt




def get_cot_prompt_chinese(question):
    json_format = '{"关系模式名1":{"属性": ["属性名1", "属性名2"],"主键": ["属性名1"]},"关系模式名2":{"属性": ["属性名3", "属性名4"],"主键": ["属性名3", "属性名1"],"外键": {"关系模式名1": ["属性名1"]}}}'
    cot_format = f"思考: [一步一步地思考内容] \n" \
                f"数据库模式: {json_format}"
    prompt = f"需求: {question} \n" \
        f"让我们一步一步地解决这个问题，以确保我们得到正确的答案。请用中文输出。" \
        f"你生成的内容应该与'''{cot_format}'''的格式相同，不要生成不符合格式的内容。"
    return prompt



def get_cot_prompt(question):
    direct_format = '''
                        {
                            "Thinking Step": <Your thinking steps>, 
                            "schema": 
                            {
                                "Relationship schema name 1":
                                    {
                                    "Attributes":["Attribute name 1", "Attribute name 2"],
                                    "Primary key":["Attribute name 1"]
                                    },
                                "Relationship schema name 2":
                                    {
                                    "Attributes":["Attribute name 3","Attribute name 4"],
                                    "Primary key":["Attribute name 3","Attribute name 1"],
                                    "Foreign key":{
                                            "Attribute name 4":{"Relationship schema name 1":"Attribute name 1"}
                                            }
                                    }
                            }
                        }
                        '''

    example = '''
            requirement: A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, department, dormitory address. The addresses of student dormitories in the same department are the same. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
            answer: {
                        "Thinking Step": "Step 1: Identify key entities from the requirement. The entities are Student, Department, Course, and Course Selection.\n Step 2: Define attributes for each entity. For Student, include ID, Name, Age, and Department. For Department, include ID, Name, and Dormitory Address. For Course, include Number, Credits, Lecturer, and Class Time. For Course Selection, include Student ID, Course Number, and Selection Time.\n Step 3: Define primary keys for each table. For Student, the primary key is ID. For Department, the primary key is ID. For Course, the primary key is Number. For Course Selection, the composite primary key is Student ID and Course Number.\n Step 4: Establish foreign key relationships. The Student table has a foreign key to the Department table. The Course Selection table has foreign keys to both the Student and Course tables.\n Step 5: Normalize the database to avoid redundancy. Dormitory Address is stored in the Department table, as all students in the same department share the same address. The Course Selection table captures the many-to-many relationship between students and courses.\n Step 6: Consider how to handle course popularity prediction. Course popularity can be derived from the Course Selection table by counting the number of students enrolled in each course, although it's not explicitly stored in the schema. "
                        'schema': {
                            "Student":
                                {
                                    "Attributes": ['ID', 'Name', 'Age', 'Department'],
                                    "Primary key": ['ID']
                                    "Foreign key": {
                                                "Department": {"Department": "ID"}
                                                }
                                },
                            "Department":
                            {
                                "Attributes": ['ID', 'Name', 'Dormitory Address'],
                                "Primary key": ['ID']
                            },
                            "Course":
                            {
                                "Attributes": ['Number', 'Credits', 'Lecturer', 'Class Time'],
                                "Primary key": ['Number']
                            },
                            "Course Selection":
                            {
                                    "Attributes": ['ID', 'Number', 'Selection Time'],
                                    "Primary key": ['ID', 'Number']
                                    "Foreign key": {
                                                "ID": {"Student": "ID"},
                                                "Number": {"Course": "Number"},
                                                }
                            }
                        }
                    }
              '''

    prompt = f'''
                You are a database design expert. You need to come up with database schemas that meet the requirements provided.
                Requirement: {question} 
                Let's solve this problem step by step to ensure that we get the correct answer." 
                The content you generate should be in the same format as {direct_format}. Do not generate content that does not conform to the format.
                You should pay attention to these constraints when responding:
                1. Add ID attributes to entities for identification only when necessary, without generating any additional content.
                2. If the schema describes an entity, the schema name should be a noun. If the schema describes a relationship, the schema name be a verb.
                3. All words are separated, e.g. ProductID should be Product ID.
                Here is a example:
                {example}
            '''

    return prompt







def get_cot_few_shot_prompt(question):
    direct_format = '''
                        {
                            "Thinking Step": <Your thinking steps>, 
                            "schema": 
                            {
                                "Relationship schema name 1":
                                    {
                                    "Attributes":["Attribute name 1", "Attribute name 2"],
                                    "Primary key":["Attribute name 1"]
                                    },
                                "Relationship schema name 2":
                                    {
                                    "Attributes":["Attribute name 3","Attribute name 4"],
                                    "Primary key":["Attribute name 3","Attribute name 1"],
                                    "Foreign key":{
                                            "Attribute name 4":{"Relationship schema name 1":"Attribute name 1"}
                                            }
                                    }
                            }
                        }
                        '''
    example = '''
            example 1:
            requirement: A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, department, dormitory address. The addresses of student dormitories in the same department are the same. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
            answer: {
                        "Thinking Step": "Step 1: Identify key entities from the requirement. The entities are Student, Department, Course, and Course Selection. \n Step 2: Define attributes for each entity. For Student, include ID, Name, Age, and Department. For Department, include ID, Name, and Dormitory Address. For Course, include Number, Credits, Lecturer, and Class Time. For Course Selection, include Student ID, Course Number, and Selection Time. \n Step 3: Define primary keys for each table. For Student, the primary key is ID. For Department, the primary key is ID. For Course, the primary key is Number. For Course Selection, the composite primary key is Student ID and Course Number. \nStep 4: Establish foreign key relationships. The Student table has a foreign key to the Department table. The Course Selection table has foreign keys to both the Student and Course tables.\n Step 5: Normalize the database to avoid redundancy. Dormitory Address is stored in the Department table, as all students in the same department share the same address. The Course Selection table captures the many-to-many relationship between students and courses.\n Step 6: Consider how to handle course popularity prediction. Course popularity can be derived from the Course Selection table by counting the number of students enrolled in each course, although it's not explicitly stored in the schema. "
                        'schema': {
                            "Student":
                                {
                                    "Attributes": ['ID', 'Name', 'Age', 'Department'],
                                    "Primary key": ['ID']
                                    "Foreign key": {
                                                "Department": {"Department": "ID"}
                                                }
                                },
                            "Department":
                            {
                                "Attributes": ['ID', 'Name', 'Dormitory Address'],
                                "Primary key": ['ID']
                            },
                            "Course":
                            {
                                "Attributes": ['Number', 'Credits', 'Lecturer', 'Class Time'],
                                "Primary key": ['Number']
                            },
                            "Course Selection":
                            {
                                    "Attributes": ['ID', 'Number', 'Selection Time'],
                                    "Primary key": ['ID', 'Number']
                                    "Foreign key": {
                                                "ID": {"Student": "ID"},
                                                "Number": {"Course": "Number"},
                                                }
                            }
                        }
                    }
            example 2:
            requirement: The business requirements of a warehouse management system are described as follows: a warehousing company manages multiple warehouses, each of which has a warehouse number, address, and capacity. The company has multiple loaders, each of which has a number, name, and phone number. Cargo has ID and Name. Each inbound and outbound task needs to record the warehouse number, loader information, cargo information, quantity, and time. The system needs to support real-time monitoring and performance evaluation of warehouses and loading and unloading tasks.
            answer: {
                    "Thinking Step": "Step 1: Identify key entities from the requirement. The entities are Warehouse, Cargo, Loader, Inbound/Outbound Record, Goods Inbound/Outbound Record, and Stevedores Transaction Record. \n Step 2: Define attributes for each entity. For Warehouse, include Warehouse Number, Address, and Capacity. For Cargo, include Cargo ID and Cargo Name. For Loader, include Loader ID, Name, and Phone Number. For Inbound/Outbound Record, include Transaction ID, Time, Warehouse Number, and Transaction Type. For Goods Inbound/Outbound Record, include Goods ID, Transaction ID, and Quantity. For Stevedores Transaction Record, include Stevedores ID and Transaction ID. \n  Step 3: Define primary keys for each table. For Warehouse, the primary key is Warehouse Number. For Cargo, the primary key is Cargo ID. For Loader, the primary key is Loader ID. For Inbound/Outbound Record, the primary key is Transaction ID. For Goods Inbound/Outbound Record, the composite primary key is Goods ID and Transaction ID. For Stevedores Transaction Record, the composite primary key is Stevedores ID and Transaction ID. \n Step 4: Establish foreign key relationships. The Inbound/Outbound Record table has a foreign key to the Warehouse table. The Goods Inbound/Outbound Record table has foreign keys to both the Inbound/Outbound Record and Cargo tables. The Stevedores Transaction Record table has foreign keys to the Inbound/Outbound Record and Loader tables. \n Step 5: Normalize the database to avoid redundancy. Information about warehouses, cargo, and loaders are stored in separate tables, and related records are connected via foreign keys. The Goods Inbound/Outbound Record and Stevedores Transaction Record tables help track the relationship between tasks, goods, and workers. \n Step 6: Consider how to handle performance evaluation and real-time monitoring. Performance data can be derived from the transaction logs and be used to evaluate the efficiency of warehouses and loaders.",
                    "schema":
                    {
                        "Warehouse":
                        {
                            "Attribute":
                            [
                                "Warehouse Number",
                                "Address",
                                "Capacity"
                            ],
                            "Primary key":
                            [
                                "Warehouse Number"
                            ],
                            "Foreign key":
                            {}
                        },
                        "Cargo":
                        {
                            "Attribute":
                            [
                                "Cargo ID",
                                "Cargo Name"
                            ],
                            "Primary key":
                            [
                                "Cargo ID"
                            ],
                            "Foreign key":
                            {}
                        },
                        "Loader":
                        {
                            "Attribute":
                            [
                                "Name",
                                "Phone",
                                "Loader ID"
                            ],
                            "Primary key":
                            [
                                "Loader ID"
                            ],
                            "Foreign key":
                            {}
                        },
                        "inbound outbound record":
                        {
                            "Attribute":
                            [
                                "Transaction ID",
                                "Time",
                                "Warehouse number",
                                "Transaction type"
                            ],
                            "Primary key":
                            [
                                "Transaction ID"
                            ],
                            "Foreign key":
                            {
                                "Warehouse number":
                                {
                                    "Warehouse": "Warehouse number"
                                }
                            }
                        },
                        "goods inbound outbound record":
                        {
                            "Attribute":
                            [
                                "Goods ID",
                                "Transaction ID",
                                "Quantity"
                            ],
                            "Primary key":
                            [
                                "Goods ID",
                                "Transaction ID"
                            ],
                            "Foreign key":
                            {
                                "Transaction ID":
                                {
                                    "inbound outbound record": "Transaction ID"
                                },
                                "Goods ID":
                                {
                                    "Goods": "Goods ID"
                                }
                            }
                        },
                        "Stevedores Transaction record":
                        {
                            "Attribute":
                            [
                                "Stevedores ID",
                                "Transaction ID"
                            ],
                            "Primary key":
                            [
                                "Stevedores ID",
                                "Transaction ID"
                            ],
                            "Foreign key":
                            {
                                "Transaction ID":
                                {
                                    "Transaction record": "Transaction ID"
                                },
                                "Stevedores ID":
                                {
                                    "Stevedores": "Stevedores ID"
                                }
                            }
                        }
                    }
                }
              example 3:
              requirement: Business requirement description of grassroots organization election management system: A grassroots mass autonomous organization needs to manage the election process, including candidates, voters and voting records. Candidates have candidate numbers, names, genders, dates of birth and positions; voters have voter numbers, names, genders, dates of birth and contact information; a voter can only vote for one candidate, and voters also need to record voting time and voting location when voting. The system can count the number of votes for each candidate.,
              answer: {
                    "Thinking Step": "Step 1: Identify key entities from the requirement. The entities are Candidate, Voter, and Voting Record. \n Step 2: Define attributes for each entity. For Candidate, include Candidate Number, Name, Gender, Date of Birth, and Position. For Voter, include Voter Number, Name, Gender, Date of Birth, and Contact Information. For Voting Record, include Voter Number, Candidate Number, Voting Time, and Voting Location. \n Step 3: Define primary keys for each table. For Candidate, the primary key is Candidate Number. For Voter, the primary key is Voter Number. For Voting Record, the composite primary key is Voter Number.\n Step 4: Establish foreign key relationships. The Voting Record table has foreign keys to both the Voter and Candidate tables. \n Step 5: Normalize the database to avoid redundancy. Candidate and Voter information are stored separately to ensure efficient data management. The Voting Record table captures the relationship between voters and candidates while also storing voting details. \n Step 6: Consider how to handle vote counting. The system can derive the number of votes for each candidate by aggregating records in the Voting Record table, rather than storing it explicitly in the schema.",
                    "schema":
                    {
                        "Candidate":
                        {
                            "Attribute":
                            [
                                "Candidate Number",
                                "Name",
                                "Gender",
                                "Date of Birth",
                                "Position"
                            ],
                            "Primary key":
                            [
                                "Candidate Number"
                            ],
                            "Foreign key":
                            {}
                        },
                        "Voter":
                        {
                            "Attribute":
                            [
                                "Voter Number",
                                "Name",
                                "Gender",
                                "Date of Birth",
                                "Contact Information",
                                "Candidate Number",
                                "Voting Time",
                                "Voting Location"
                            ],
                            "Primary key":
                            [
                                "Voter Number"
                            ],
                            "Foreign key":
                            {
                                "Candidate Number":
                                {
                                    "Candidate": "Candidate Number"
                                }
                            }
                        }
                    }
                }
              '''

    prompt = f'''
                You are a database design expert. You need to come up with database schemas that meet the requirements provided.
                Requirement: {question} 
                Let's solve this problem step by step to ensure that we get the correct answer." 
                The content you generate should be in the same format as {direct_format}. Do not generate content that does not conform to the format.
                You should pay attention to these constraints when responding:
                1. Add ID attributes to entities for identification only when necessary, without generating any additional content.
                2. If the schema describes an entity, the schema name should be a noun. If the schema describes a relationship, the schema name be a verb.
                3. All words are separated, e.g. ProductID should be Product ID.
                Here is a example:
                {example}
            '''

    return prompt



def get_pseudo_code_prompt(question, code_path):
    role = f"你是构建数据库关系模型的专家，你能依据代码逻辑不断演算，最终得到输出。"
    with open(code_path, 'r', encoding='utf-8') as f:
        code_prompt = f.read()
    code_prompt += f'\n >>>generate_schema_from_text({question})'
    return role, code_prompt
