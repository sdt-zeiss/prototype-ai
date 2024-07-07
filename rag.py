from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from indexer import get_vectorstore_raw, add_data
import os

OPEN_AI_API_KEY = os.getenv('OPEN_AI_API_KEY')
PGVECTOR_COLLECTION = os.getenv('PGVECTOR_COLLECTION') 
CONNECTION_STRING = os.getenv('DATABASE_URL')

vectorstore = get_vectorstore_raw(CONNECTION_STRING, PGVECTOR_COLLECTION)
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 500})

llm = ChatOpenAI(model_name="gpt-4o", openai_api_key=OPEN_AI_API_KEY)

template = """You are representing InsightsOut, a platform for intellectuals to engage in meaningful discourse about art and museums. InsightsOut is an online platform where individuals come together to discuss topics that impact their daily and professional lives through social media like posts and comments. As an intelligent and unbiased representative from InsightsOut, your task is to answer the following question based on the information available in the provided discussions. The discussions represents the comments by users on a given topic.

Discussions:
{context}

Instructions:
1. Carefully read and consider the discussions provided in the comments. Some of them might not be relevant so feel free to discard irrelevant information.
2. Summarize the main points and sentiments expressed in the comments, if the question requires it. 
3. Provide a detailed analysis that reflects the overall tone, common themes, and notable insights from the comments. If the question demands analysis of the sentiment, consider the discussions and give a hollistic detailed analysis.
4. If the discussions does not relate with the question itself, give a general answer. Do not make any assumption about the discussions at InsightsOut outside of the discussions.
5. Feel free to interact like a human on general questions. Not all questions will be related to the content. Read the question carefully and if you think the question is a general one, answer it accordingly. Refrain from making any assumptions on the comments and posts of InsightsOut.
6. Please provide your answer in HTML format without any markdown or code block syntax. Use appropriate HTML tags such as <p> for paragraphs, <ul> for lists, <strong> for bold text, and <em> for italic text. Use line breaks <BR> after each paragraph and always use bullet points for enlisting subtopic information.

Question:
{question}

Answer:
"""

prompt = ChatPromptTemplate.from_template(template)

def format_docs(docs):
    docs = "\n\n".join(doc.page_content for doc in docs)
    print(len(docs))
    return docs

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

def answer_query(question):
    return rag_chain.invoke(question)
