import os
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import OpenAI
from langchain.schema import Document 
import pandas as pd
import warnings
from PyPDF2.errors import PdfReadWarning

warnings.filterwarnings("ignore", category=PdfReadWarning)

api_key = ""

def process_pdf(uploaded_file):
    text = ""
    pdf_reader = PdfReader(uploaded_file)
    for i, page in enumerate(pdf_reader.pages):
        try:
            page_text = page.extract_text()
            if page_text:
                text += page_text
            else:
                st.warning(f"Warning: Skipping page {i + 1} aucun texte trouvé.")
        except Exception as e:
            st.error(f"Erreur de lecture {i + 1}: {e}")
    return text

def process_excel(uploaded_file):
    data_dict = {}
    people_counts = {}
    df = pd.read_excel(uploaded_file)
    people_counts = df['Groupe'].value_counts().to_dict()
    for index, row in df.iterrows():
        group = row['Groupe']
        if group not in data_dict:
            data_dict[group] = []
        data_dict[group].append(row['Displayname'])
    return data_dict, people_counts

def create_embeddings(text, api_key):
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)
    chunks = text_splitter.split_text(text)
    if not chunks:
        st.error("Échec de la division du texte en chunks.")
        return None, None
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    knowledge_base = FAISS.from_texts(chunks, embeddings)
    return knowledge_base, chunks

def main():
    st.set_page_config(page_title="Document QA")
    st.header("Demande📄")

    uploaded_file = st.file_uploader("Upload PDF or Excel", type=["pdf", "xlsx"])
    if not api_key:
        st.error("La clé API n'a pas été détectée.")
        return

    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            text = process_pdf(uploaded_file)
            if text:
                formatted_text = text.replace('\n', '\n\n')
                knowledge_base, chunks = create_embeddings(formatted_text, api_key)
                if knowledge_base and chunks:
                    st.write(f"Nombres de chunks créés: {len(chunks)}")
                    #st.write(chunks[:3])  # retirer cette ligne si on ne veut pas voir les lignes au début
                    query = st.text_input("Demande Document")
                    if query:
                        docs = knowledge_base.similarity_search(query)
                        st.write("Documents renvoyés par la recherche de similarité:")
                        for doc in docs:
                            st.write(doc.page_content.replace('\n', '\n\n'))
                        if docs:
                            llm = OpenAI(api_key=api_key)
                            chain = load_qa_chain(llm, chain_type="stuff")
                            documents = [Document(page_content=doc.page_content, metadata={}) for doc in docs]
                            response = chain.invoke({"input_documents": documents, "question": query})
                            st.success(response['output_text'])
                        else:
                            st.error("Aucun document pertinent trouvé dans la base de données.")
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            data_dict, people_counts = process_excel(uploaded_file)
            st.write("Counts for each group:")
            for group, count in people_counts.items():
                st.write(f"{group}: {count}")
            query = st.text_input("Posez une question sur les données")
            if query:
                llm = OpenAI(api_key=api_key)
                context = "\n".join([f"{name} is in {group}" for group, names in data_dict.items() for name in names])
                documents = [Document(page_content=context, metadata={})]
                chain = load_qa_chain(llm, chain_type="stuff")
                response = chain.invoke({"input_documents": documents, "question": query})
                st.success(response['output_text'])

if __name__ == "__main__":
    main()
