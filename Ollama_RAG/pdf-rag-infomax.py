# General steps in RAG
# 1. Intake PDF files 
# 2. Extract text from PDF Files and split into small chunks 
# 3. Send the chunks to the embedding model
# 4. Save the embeddings to a vector database
# 5. Perform similarity search on the vector database to find similar documents 
# 6. Retrieve the similar documents and present them to the user 

import os
import ollama
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_community.document_loaders import OnlinePDFLoader
from langchain_community.document_loaders import PDFPlumberLoader

document_path = "./data/SochBrochure.pdf"
model = "llama3.2"

# #Uploading local pdf file 
# if os.path.exists(document_path):
#     #loader = UnstructuredPDFLoader(file_path=document_path)
#     loader = PDFPlumberLoader(file_path=document_path)
#     data = loader.load()
#     print("Completed loading....")
# else:
#     print("Upload a PDF file")

# # Preview first page 
# content = data[0].page_content
# print(content[:1000])

loader = PDFPlumberLoader(file_path=document_path,extract_images=False)
pages = loader.load()

print(f"pages length: {len(pages)}")
all_pages = []
all_pages.extend(pages)

# Extract text from the PDF file 
#text = pages[1].page_content
#text = " ".join([page.page_content for page in all_pages])
text = pages[2].page_content
print(f"Text extracted from the PDF file: \n {text}\n")

#Prepare the prompt for the model 

prompt = f""" 
You are an AI assistant that helps with extracting information from PDF documents. 

Here is the content of the PDF file of Soch College:

{text}

Please tell me who is the founder of this college? Please summarize in one line what he wants to convey
and what is the official website of this college?

"""

try:
    response = ollama.generate(model=model, prompt=prompt)
    answer = response.get("response","")

    print(answer)

except Exception as e:
    print("error is:"+ str(e))