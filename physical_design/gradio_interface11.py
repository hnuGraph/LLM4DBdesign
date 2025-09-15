import gradio as gr
import asyncio
import os
from agent_chat_physical11 import main as agent_main
import argparse
import markdown
from xhtml2pdf import pisa

CUSTOMER_DIR = 'customer_files'
EXAMPLES_DIR = 'saved_files'


def run_agent_system(model_name, database_name, requirement_text):   # database_user, database_password, database_port,
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', default=model_name)  
    parser.add_argument('--database_name', default=database_name)
    # parser.add_argument('--database_user', default=database_user)
    # parser.add_argument('--database_password', default=database_password)
    # parser.add_argument('--database_port', default=database_port)
    parser.add_argument('--requirement_text', default=requirement_text)

    args = parser.parse_args()
    
    # Run the agent system
    output_string = asyncio.run(agent_main(args))
    
    html_content = markdown.markdown(output_string, extensions=['tables', 'fenced_code'])
    styled_html = f"""
    <div style="height: 500px; overflow-y: auto; padding: 20px; border: 1px solid #ddd; border-radius: 4px;">
        {html_content}
    </div>
    """
    return styled_html, html_content
 

def markdown_to_pdf(db_name, html_content):
    if not html_content:
        return None
    
    try:
        # Create temporary directory and files
        pdf_path = os.path.join(CUSTOMER_DIR, f"{db_name}_design.pdf")  #TODO maybe markdown file is enouph
    
        full_html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 2em; }}
                h1, h2, h3, h4 {{ color: #2c3e50; }}
                code {{ background: #f8f8f8; padding: 0.2em; border-radius: 3px; }}
                pre {{ background: #f8f8f8; padding: 1em; border-radius: 5px; overflow-x: auto; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
 
        # Using pisa to convert HTML to PDF
        with open(pdf_path, "wb") as output_file:
            pisa.CreatePDF(full_html, dest=output_file, encoding="utf-8")
        
        return pdf_path
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        # If PDF generation fails, provide a Markdown file
        md_path = os.path.join(CUSTOMER_DIR, f"{db_name}_design.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return md_path


def create_interface():
    # Ensure directories exist
    for directory in [CUSTOMER_DIR, EXAMPLES_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
        
    with gr.Blocks(title="SchemaAgent: Auto Relation Database Design System") as interface:
        gr.Markdown("# SchemaAgent: Auto Relation Database Design System")
        
        with gr.Row():
            with gr.Column():
                model_name = gr.Dropdown(
                    choices=["gpt4", "chatgpt", "deepseek"],
                    value="gpt4",
                    label="Model Selection"
                )
                
                database_name = gr.Textbox(
                    value="relation_mcp_test",
                    label="Database Name"
                )

                database_management_system = gr.Dropdown(
                    choices=['MySQL'],
                    value="MySQL",
                    label="Database Management System"
                )

                requirement_text = gr.Textbox(
                    label="Requirements",
                    placeholder="Enter your database requirements here...",
                    lines=10,
                    max_lines=20,
                )
                
                submit_btn = gr.Button("Run Design Process")
            
            with gr.Column():
                output = gr.HTML(
                    value="<h4 style='padding: 20px; text-align: center; height: 80px; display: flex; align-items: center; justify-content: center; border: 1px solid #ddd; border-radius: 4px;'>The database design report will be displayed here</h4>",
                    label="Design Process Output"
                )
                
                original_html = gr.State()
                download_file = gr.File(label="Download Design File", visible=True, height=40)

        # Example Records section with improved card design
        gr.Markdown("## Example Records")

        # Create example files data
        example_data = [
            {
                "id": 1,
                "filename": "university_course_selection.pdf",
                "title": "University Course Selection System",
                "description": "A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, the name of the course chosen by the student, etc. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
            },
            {
                "id": 2,
                "filename": "factory_production.pdf", 
                "title": "Factory Production Management System",
                "description": "The business needs of a factory are as follows: the factory has multiple departments, some of which are production departments, called workshops. A department has multiple employees, and an employee belongs to only one department. Each employee has an employee number, name, date of birth, gender, telephone number and position; the factory produces a variety of products. Products have names, models, barcodes and prices. Departments need to collect parts from the warehouse and also put their products into the warehouse. Parts have names, models, barcodes and prices; each time they are collected, they need to record which parts have been collected, their quantity, the consignor, the recipient, and the collection time. When products are put into the warehouse, they also need to record which products have been put into the warehouse, their quantity, the consignor, the consignee, and the storage time. The production management information system should be able to evaluate the performance of the department."
            }
        ]

        # Create example files
        def create_example_files(examples):
            for example in examples:
                file_path = os.path.join(EXAMPLES_DIR, example["filename"])
                # Create example file if it doesn't exist
                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as f:
                        simple_html = f"<h1>{example['title']}</h1><p>{example['description']}</p>"
                        pisa.CreatePDF(simple_html, dest=f)
            
            return examples

        # Create files and get paths
        example_items = create_example_files(example_data)
        
        # Loop through examples and create a consistent display for each
        for i, example in enumerate(example_items):
            with gr.Group():
                with gr.Row():
                    # Left circle with example number
                    gr.HTML(f"""
                    <div style="display: flex; align-items: center; width: 100%; padding: 5px;">
                        <div style="background-color: #2c3e50; color: white; border-radius: 50%; width: 28px; height: 28px; 
                                    display: flex; align-items: center; justify-content: center; margin-right: 15px; flex-shrink: 0;">
                            <span style="font-weight: bold; font-size: 14px; color: white;">{example['id']}</span>
                        </div>
                        <div style="font-weight: bold; font-size: 16px; color: #2c3e50;">
                            {example['title']}
                        </div>
                    </div>
                    """)
                
                # Description row with horizontal scrolling
                with gr.Row():
                    gr.HTML(f"""
                    <div style="padding: 0 10px 10px 10px; width: 100%;">
                        <div style="overflow-y: auto; max-height: 80px; padding: 5px 0; margin: 5px 0; color: #444;">
                            {example['description']}
                        </div>
                    </div>
                    """)
                
                # Download button with full width
                with gr.Row():
                    gr.File(
                        value=os.path.join(EXAMPLES_DIR, example["filename"]),
                        label=f"Download {example['title']}",
                        height=50,
                        elem_id=f"download_{example['id']}"
                    )
        
        submit_btn.click(
            fn=run_agent_system,
            inputs=[model_name, database_name, requirement_text],
            outputs=[output, original_html],
        ).then(
            fn=markdown_to_pdf,
            inputs=[database_name, original_html],
            outputs=[download_file]
        )
    
    return interface

if __name__ == "__main__":
    interface = create_interface()
    interface.launch(
        share=True, 
        server_name='0.0.0.0', 
        server_port=5000
    )