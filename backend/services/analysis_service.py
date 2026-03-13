from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from backend.utils.config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    LLM_MODEL,
    VECTOR_DB_PATH,
)

vector_store = None


def chunk_document(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    return splitter.split_text(text)


def build_vector_store(chunks):
    global vector_store

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    vector_store = FAISS.from_texts(
        chunks,
        embedding=embeddings
    )

    vector_store.save_local(VECTOR_DB_PATH)


def load_vector_store():
    global vector_store

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    vector_store = FAISS.load_local(
        VECTOR_DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )


def generate_analysis(query: str):

    llm = ChatOpenAI(model=LLM_MODEL)

    prompt = PromptTemplate(
        template="""
You are a financial analyst.

Using the financial report context below, provide:

1. A summary of the company's financial health
2. Key insights
3. Investment advice

Context:
{context}

Question:
{question}
""",
        input_variables=["context", "question"],
    )

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vector_store.as_retriever(),
        chain_type_kwargs={"prompt": prompt},
    )

    result = qa.run(query)

    return result


def analyze_financial_report(parsed_text: str, query: str):
    """
    Full RAG pipeline
    """

    chunks = chunk_document(parsed_text)

    build_vector_store(chunks)

    result = generate_analysis(query)

    return result