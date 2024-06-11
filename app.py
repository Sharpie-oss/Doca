import os
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from PIL import Image
import warnings
from PyPDF2.errors import PdfReadWarning

warnings.filterwarnings("ignore", category=PdfReadWarning)

api_key = ""

if not api_key:
    st.error("La clé API n'a pas été détécter.")
else:
    st.set_page_config(page_title="PDF QA")
    st.header("Demande📄")

    pdf = st.file_uploader("Upload PDF", type="pdf")

    if pdf is not None:
        pdf_reader = PdfReader(pdf)
        text = ""
        for i, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                else:
                    st.warning(f"Warning: Skipping page {i + 1} aucun texte trouvé.")
            except Exception as e:
                st.error(f"Erreur de lecture {i + 1}: {e}")

        if not text:
            st.error("Aucun texte trouvé dans le PDF.")
        else:
            formatted_text = text.replace('\n', '\n\n')



            text_splitter = CharacterTextSplitter(
                separator="\n",
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            chunks = text_splitter.split_text(formatted_text)

            if not chunks:
                st.error("Échec de la division du texte en chunks.")
            else:
                st.write(f"Nombres de chunks crées: {len(chunks)}")
                st.write(chunks[:3]) # retirer cette ligne si on veux pas voir les lignes au début 

                try:
                    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
                    knowledge_base = FAISS.from_texts(chunks, embeddings)

                    st.info(f"Nombre d'Embeddings: {len(chunks)}")

                    query = st.text_input("Demande PDF")
                    if query:
                        docs = knowledge_base.similarity_search(query)
                        st.write("Documents renvoyés par la recherche de similarité:")
                        for doc in docs:
                            st.write(doc.page_content.replace('\n', '\n\n'))

                        if docs:
                            llm = OpenAI(api_key=api_key)
                            chain = load_qa_chain(llm, chain_type="stuff")
                            response = chain.run(input_documents=docs, question=query)
                            st.success(response)
                        else:
                            st.error("Aucun document pertinent trouvé dans la base de données.")
                except Exception as e:
                    st.error(f"Une erreur s'est produite lors de la création des intégrations ou de la base de données: {e}")
