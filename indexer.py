from langchain_community.document_loaders import DataFrameLoader
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import psycopg2
import pandas as pd

OPEN_AI_API_KEY = os.getenv('OPEN_AI_API_KEY')
PGVECTOR_COLLECTION = os.getenv('PGVECTOR_COLLECTION')

def load_dataframe(dataframe):
    loader = DataFrameLoader(dataframe, page_content_column="text")
    data = loader.load()
    return data

def split(data):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )
    all_splits = text_splitter.split_documents(data)
    return all_splits

def create_and_get_vectorstore(docs, connection_string, collection_name=PGVECTOR_COLLECTION, pre_delete_collection=False):
    embeddings = OpenAIEmbeddings(openai_api_key=OPEN_AI_API_KEY)
    vecdb = PGVector.from_documents(
        embedding=embeddings,
        documents=docs,
        collection_name=collection_name,
        connection=connection_string,
        pre_delete_collection=pre_delete_collection
    )
    return vecdb

def get_vectorstore_raw(connection_string, collection_name=PGVECTOR_COLLECTION):
    embeddings = OpenAIEmbeddings(openai_api_key=OPEN_AI_API_KEY)
    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection_string,
    )
    return vectorstore

def add_data(dataframe, connection_string, collection_name=PGVECTOR_COLLECTION):
    # Returns vectorstore after adding data to pgvector, WARNING: it will delete and overwrite the collection
    data = load_dataframe(dataframe)
    splits = split(data)
    vectorstore = create_and_get_vectorstore(splits, connection_string, collection_name, pre_delete_collection=True)
    return vectorstore

def preprocess_comments(connection_string, collection_name=PGVECTOR_COLLECTION):
    try:
        # Load comments table
        conn = psycopg2.connect(connection_string)
        query = "SELECT id, content FROM comments"
        df = pd.read_sql(query, conn)
        df = df.rename(columns={'content': 'text'})
        vecdb = add_data(df, connection_string, collection_name)
        conn.close()
    except Exception as e:
        return {"status": "error", "message": f"Error executing query: {e}"}
    return True
