from openai import OpenAI
import os
import subprocess
import re
from datetime import datetime
def extract_code_block(text):
    # extract mermaid codeblock
    pattern = r"```(?:\w*)\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None
def generate_er(requirement_text):
    mapping = {'gpt4': 'gpt-4o-2024-08-06',
                'chatgpt': 'gpt-3.5-turbo',
                'deepseek': 'deepseek-v3-241226'}

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),  
        base_url="https://www.dmxapi.com/v1"
    )
    prompt = """You are a professional database designer.

Given the following Entity Sets and Relationship Sets, please generate a complete and accurate Mermaid ER diagram code using `erDiagram` syntax. Follow these strict rules:

1. Use `PK` and `FK` to mark primary and foreign keys in the entity or relationship tables.
2. Use `||--o{`, `||--||`, `o{--o{` etc. to represent correct cardinality:
   - `||--o{` means one-to-many
   - `||--||` means one-to-one
   - `o{--o{` means many-to-many
3. For relationship sets, if needed, create a separate entity-like table to store relationship attributes and foreign keys.
4. Do not include any extra explanation or markdown syntax like ```mermaid. Just return the raw ER diagram code.
5. Use appropriate attribute types like `int`, `string`, `date`, `float`, etc., based on the names.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt+requirement_text,
            }
        ],
        model=mapping['gpt4'],    
    )

    # print(chat_completion.choices[0].message.content)
    mermaid_code = extract_code_block(chat_completion.choices[0].message.content)
    if mermaid_code == None:
        mermaid_code = chat_completion.choices[0].message.content
    directory = './er_data/'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{timestamp}.mmd"
    save_file_path = directory + file_name
    with open(save_file_path, "w", encoding="utf-8") as f:
        f.write(mermaid_code)

    print(f"Mermaid code已保存为 {save_file_path}")

    # 构造命令参数列表
    cmd = [
        "sudo", "docker", "run",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "-v", "./er_data:/data",
        "minlag/mermaid-cli",
        "-i", f"/data/{file_name}"
    ]

    try:
        # 执行命令
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("命令执行成功，输出:")
        print(result.stdout)
        return  directory+file_name+'.svg'
    except subprocess.CalledProcessError as e:
        print("命令执行失败，错误信息:")
        print(e.stderr)

# requirement_text = """#### Entity Sets
# (1) Student
#    - Attribute: ID, Name, Age

# (2) Course
#    - Attribute: Number, Name, Credits, Lecturer, Class Time

# #### Relationship Sets
# (1) Course Selection
#    - Object: Student, Course
#    - Cardinality Mapping: Many-to-Many
#    - Relationship Attribute: Selection Time

# (2) Course Popularity Prediction
#    - Object: Course
#    - Cardinality Mapping: Many-to-One
#    - Relationship Attribute: Popularity Score"""
# svg_path = generate_er(requirement_text)
# print(svg_path)