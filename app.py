from dotenv import load_dotenv
import os
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
openai = OpenAIEmbeddings(openai_api_key=" { mettre API : https://platform.openai.com/api-keys  (j'ai plus de crédit) }")
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain_community.llms import OpenAI
from langchain_community.callbacks import get_openai_callback


load_dotenv()
from PIL import Image
img = Image.open(r"C:\Users\LaFam\Desktop\test\image.jpg")
st.set_page_config(page_title="PDF IA", page_icon= img)
st.header("Demande au PDF📄")
pdf = st.file_uploader("Envoie PDF", type="pdf")

if pdf is not None:
    pdf_reader = PdfReader(pdf)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=10000,
        chunk_overlap=2000,
        length_function=len
    )  

    chunks = text_splitter.split_text(text)

    embeddings = OpenAIEmbeddings()
    knowledge_base = FAISS.from_texts(chunks, embeddings)

    query = st.text_input("Demande PDF")
    if query:
        docs = knowledge_base.similarity_search(query)

        llm = OpenAI()
        chain = load_qa_chain(llm, chain_type="stuff")
        response = chain.run(input_documents=docs, question=query)
           
        st.success(response)
        