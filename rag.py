from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from indexer import get_vectorstore_raw, add_data
import os

OPEN_AI_API_KEY = os.getenv('OPEN_AI_API_KEY')
PGVECTOR_COLLECTION = os.getenv('PGVECTOR_COLLECTION')
CONNECTION_STRING = "postgresql+psycopg://webapp:KdcCAQydYH4yMYnYqAA58GOhxSYFefMZZssLpQHsv1cV@postgres-16.sliplane.app:5432/prototype"

vectorstore = get_vectorstore_raw(CONNECTION_STRING, PGVECTOR_COLLECTION)
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 20})

llm = ChatOpenAI(model_name="gpt-4o", openai_api_key=OPEN_AI_API_KEY)

template = """You are representing InsightsOut, a platform for intellectuals to engage in meaningful discourse about art and museums. InsightsOut is an online platform where individuals come together to discuss topics that impact their daily and professional lives through social media like posts and comments. As an intelligent and unbiased representative from InsightsOut, your task is to answer the following question based on the information available in the provided context. The context represents the comments by users on a given topic. 

Context:
{context}

Instructions:
1. Carefully read and consider the context provided in the comments.
2. Summarize the main points and sentiments expressed in the comments, if the question requires it.
3. Provide a detailed analysis that reflects the overall tone, common themes, and notable insights from the comments.
4. If the context does not relate with the question itself, give a general answer. Do not make any assumption about the discussions at InsightsOut outside of the context.
5. Feel free to interact like a human on general questions. Not all questions will be related to the content. Read the question carefully and if you think the question is a general one, answer it accordingly. Refrain from making any assumptions on the comments and posts of InsightsOut.

Question:
{question}

Answer:
"""

prompt = ChatPromptTemplate.from_template(template)
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

def answer_query(question):
    return rag_chain.invoke(question)


