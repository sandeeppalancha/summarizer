from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
# from ipynb.fs.full.summarize_docs import new_summarize_api, read_docx  # Import functions from summarizer.py
import nest_asyncio
nest_asyncio.apply()
import uvicorn
from openai import AzureOpenAI
from docx import Document 


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def new_summarize_api(text):
    api_key = 'af24db8a03ec4d7e89f72df96ed8af05'  # Replace with your actual API key
    endpoint = 'https://labnotes-instance.openai.azure.com'  # Replace with your endpoint URL
        
    client = AzureOpenAI(
        api_key=api_key,  
        api_version="2024-07-01-preview",
        azure_endpoint=endpoint
    )
    
    chat_completion = client.chat.completions.create(
        # model="labnotes-deployment",
        model="gpt-4o",
        # prompt= "Hello",
        messages=[
            # {"role": "system", "content": "You are a helpful assistant."},
            # {"role": "user", "content": f"Generate a summary with the following sections: Aim, Materials, Procedure, Results, Conclusion. In addition to this, also include specific improvements for chemists:\n\n{text}"},  
            {"role": "user", "content": f"I have provided a set of experiments including procedure, results, conclusion in separate files. Can you provide a summary of the aggregate observations across experiments? In addition to this, also include specific chemistry improvements, new synthetic approaches that I can try, and any other bases that I can use etc.:\n\n{text}"},  
             # "Please summarize the following text...  I have a blue pen, and an other blue pen & a red pen."},
        ]
        # messages=[
        #     {"role": "system", "content": "You are a helpful assistant."},
        #     {"role": "user", "content": "Knock knock."},
        #     {"role": "assistant", "content": "Who's there?"},
        #     {"role": "user", "content": "Orange."},
        # ]
    )
    return chat_completion.choices[0].message.content

def read_docx(file):
    print(4, file.filename)
    if file.filename.endswith('.docx') and not file.filename.startswith('~$'):
        # file_path = os.path.join(subdir, file)
        # Read the .docx file
        print(31)
        doc = Document(file.file)
        print(3)

        combined_text = ""
        # combined_text += '**** Experiment '+str(file_counter) +': \n' 
        # Loop through each element (paragraph or table) in document order
        for element in doc.element.body:
            if element.tag.endswith('p'):  # Paragraph
                para = element
                # Use the Document object to get the paragraph text
                combined_text += get_paragraph_text(para) + "\n"
            elif element.tag.endswith('tbl'):  # Table
                table = element
                # Extract the table data directly from the table element
                combined_text += extract_table_data(table) + "\n"

    return combined_text

def read_docx_files_in_order(root_folder):
    # Initialize an empty string to store the combined text
    combined_text = ""
    file_counter = 0

    # Walk through all subfolders and files in the root folder
    for subdir, _, files in os.walk(root_folder):
        for file in files:
            # Check if the file has a .docx extension
            if file.endswith('.docx') and not file.startswith('~$'):
                file_counter += 1
                file_path = os.path.join(subdir, file)
                # Read the .docx file
                doc = Document(file_path)

                combined_text += '**** Experiment '+str(file_counter) +': \n' 
                # Loop through each element (paragraph or table) in document order
                for element in doc.element.body:
                    if element.tag.endswith('p'):  # Paragraph
                        para = element
                        # Use the Document object to get the paragraph text
                        combined_text += get_paragraph_text(para) + "\n"
                    elif element.tag.endswith('tbl'):  # Table
                        table = element
                        # Extract the table data directly from the table element
                        combined_text += extract_table_data(table) + "\n"

    return combined_text

def get_paragraph_text(paragraph_element):
    paragraph_text = ""
    for child in paragraph_element.iter():
        if child.tag.endswith('t'):  # Text element within a paragraph
            paragraph_text += child.text if child.text else ''
    return paragraph_text

def extract_table_data(table_element):
    table_data = ""
    for row in table_element.xpath('.//w:tr'):
        row_data = []
        for cell in row.xpath('.//w:tc'):
            cell_text = "".join(cell.xpath('.//w:t/text()'))
            row_data.append(cell_text)
        table_data += "\t".join(row_data) + "\n"
    return table_data

@app.post("/summarize/")
async def summarize(files: List[UploadFile] = File(...)):
    combined_content = ""
    file_counter=0
    
    try:
        # Read content from each file and combine
        for file in files:
            file_counter += 1
            print(1)
            content = read_docx(file)
            print(2)
            combined_content +=  '**** Experiment '+str(file_counter) +': \n' + content + "\n"  # Concatenate contents with a newline
            # file.file.seek(0)

        # print(combined_content)
        # Generate a summary for the combined content
        summary = new_summarize_api(combined_content)
        
        return {"summary": summary}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    # await server.serve()#-
    server.run()
