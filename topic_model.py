from bertopic.representation import KeyBERTInspired
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
# from sklearn.feature_extraction.text import CountVectorizer
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance, OpenAI, PartOfSpeech
from bertopic import BERTopic
import logging
import openai
from bertopic.backend import OpenAIBackend
from bertopic.vectorizers import ClassTfidfTransformer
import psycopg2
from sqlalchemy import create_engine
from openai_client import prompt_chatgpt, prompt_dalle
import pandas as pd
import uuid
from datetime import datetime
import os

OPEN_AI_API_KEY = os.getenv('OPEN_AI_API_KEY')
logger = logging.getLogger(__name__)

# Configure logging to write to the console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TopicModel():
    """
    Class for topic modeling based on BERTopic.

    Attributes:
        data (pandas.DataFrame): Input data.
        is_fitted (bool): Flag indicating whether the model has been fitted.
        topic_model (BERTopic): BERTopic model instance.
    """
    
    def __init__(self, data) -> None:
        """
        Initialize the TopicModel class.
        """
        self.is_fitted = False
        self.data = data
        self._fit_topic_model(self)

    def _fit_topic_model(self, mmr_diversity=0.3, pos_model='en_core_web_sm'):
        """
        Fit the BERTopic model.
        
        Returns:
            tuple: Tuple containing topics and probabilities.
        """

        logger.info("Fitting topic model...")

        # Define docs
        docs = self._get_docs()

        try:
            # Define representation models
            keybert_model = KeyBERTInspired()
            mmr_model = MaximalMarginalRelevance(diversity=mmr_diversity)
            # pos_model = PartOfSpeech(pos_model)

            representation_model = {
                "KeyBERT": keybert_model,
                # "MMR": mmr_model,
                # "POS": pos_model
            }

            # Pre-calculate embeddings
            # embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            # embeddings = embedding_model.encode(docs, show_progress_bar=True)

            EMBEDDING_MODEL = "text-embedding-3-large"

            client = openai.OpenAI(api_key=OPEN_AI_API_KEY)
            embedding_model = OpenAIBackend(client, EMBEDDING_MODEL)

            ctfidf_model = ClassTfidfTransformer()

            # Define UMAP and HDBSCAN models
            umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine', random_state=42)
            hdbscan_model = HDBSCAN(min_cluster_size=15, metric='euclidean', cluster_selection_method='eom', prediction_data=True)

            self.topic_model = BERTopic(representation_model=keybert_model,
                                        embedding_model=embedding_model,
                                        umap_model=umap_model,
                                        top_n_words=10,
                                        ctfidf_model=ctfidf_model,
                                        hdbscan_model=hdbscan_model,
                                        )
            self.topic_model.fit(docs)
        except Exception as e: 
            raise e


    def get_topics(self):
        if not self.is_fitted:
            self._fit_topic_model()
    
        topics = self.topic_model.fit(self._get_docs())
        self.is_fitted = True
        return topics
    

    def get_topics_over_time(self, num_bins=20):
        """
        Get topics over time.

        Args:
            num_bins (int): Number of time bins.

        Returns:
            dict: Dictionary containing topics over time.
        """
        logger.info("Generating topics over time...")
        docs = self._get_docs()
        if not self.is_fitted:
            self._fit_topic_model()
        
        timestamps = self.data['Timestamp']
        topics_over_time = self.topic_model.topics_over_time(docs, timestamps, nr_bins=num_bins)

        return topics_over_time


    def _get_docs(self):
        """
        Get documents from input data.

        Returns:
            numpy.ndarray: Array containing document texts.
        """
        logger.info("Fetching docs...")
        return self.data


    def generate_topic_prompts(self):
        """
        Generate prompts for summarizing topics.

        Returns:
            list: List of prompts for each topic.
        """
        logger.info("Generating topic prompts...")
        topics = self.topic_model.get_topic_info()
        prompts = []

        # For each topic, prompt ChatGPT for summary
        for topic_num in range(len(topics)):
            docs_list = topics.iloc[topic_num]['Representative_Docs']
            keywords = topics.iloc[topic_num]['Representation']
            
            prompt = f"""I have a topic that contains the following documents:  {docs_list}

            The topic is described by the following keywords: {keywords}

            Based on the information above, extract a short but highly descriptive topic label of at most 5 words. Summarize the above topic in a paragraph as per the documents provided. Make sure it is in the following format:
            topic: <topic label>
            summary : <summary>
            """
            prompts.append(prompt)

        return prompts
    

    def get_summaries(self):
        summaries = []
        sum2post = []
        prompts = self.generate_topic_prompts()
        for prompt in prompts:
            messages = [
                {"role": "system", "content": prompt}
            ]
            new_topic = prompt_chatgpt(messages=messages).choices[0].message.content

            post_conversion_prompt = f"""I have the following summary of a document after analyzing and performing topic modeling into it. The modeling was done on a podcast transcript and the theme of the conversation is represented in the following - {new_topic}. Generate a social media post for this given topic. This post should consist of a thought provoking scenario, demanding user's engagement and contribution towards the theme. Make sure the topic represents an open ended question and allows the users to answer at a meta level. Use a small title of at most 5 words that perfectly describes the theme of the post. Consider [SEP] to be a special character and make sure it is in the following format:
            Title : <post_title> [SEP] Post : <post_caption>
            """
            summaries.append(new_topic)
            messages = [
                    {"role": "system", "content": post_conversion_prompt}
                ]
            final_response = prompt_chatgpt(messages=messages).choices[0].message.content
            sum2post.append(final_response)
            
        # return final_response.split('[SEP]')
        return sum2post
    

    def get_posts(self):
        summaries = self.get_summaries()
        print(summaries)
        logger.info('Generating post images...')
        posts = {}
        for summary in summaries[:10]:
            split_summary = summary.split('[SEP]')
            post_theme = split_summary[0]
            post_content = split_summary[1]
            post_prompt = f"You are a content creator of a social media forum. You lead a community of people who are interested in the topic: \"{post_theme}\". As your next post, I have the following post content: \"{post_content}\". To make this post capable of inducing a thought provoking scenario, that demands user\'s engagement and contribution towards the theme, you need to create an appropriate image artwork which captures the essence of the post. Make sure the artwork represents an abstract artifact and supports the users to think at a meta level."
            
            post_url = prompt_dalle(post_prompt)
            post = {
                'content' : post_content,
                'image_url': post_url
            }
            posts[post_theme] = post
        self.export_posts(posts)
        return posts


    def export_posts(self, posts):
        """
        Export topics to PostgreSQL table.
        """
        print("exporting posts...")
        # Database credentials
        POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
        POSTGRES_USER = os.getenv('POSTGRES_USER')
        POSTGRES_HOST = os.getenv('POSTGRES_HOST')
        POSTGRES_DB_NAME = os.getenv('POSTGRES_DB_NAME')
        POSTGRES_PORT = os.getenv('POSTGRES_PORT')

        # Create the database connection
        engine = create_engine(f'postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB_NAME}')

        TABLE_NAME = 'posts'
        df_posts = []
        for topic, post in posts.items():
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            post_content = f"{post['content'].split(':')[-1]} \n Image: {post['image_url']}"
            post = {
                "id": str(uuid.uuid4()),
                "created_at": current_timestamp,
                "updated_at": current_timestamp,
                "title": topic.split(': ')[-1],
                "content": post_content,
                "type": "Story",
                "author_id": "clwaic21v000btf01eydoklol",
                "status": "ai_generated_unreviewed",
                "image_id": '' # TODO : Upload to s3
            }
            df_posts.append(post)
        df = pd.DataFrame(df_posts)
        df.to_sql(TABLE_NAME, engine, if_exists='append', index=False)
        print('Exported to PostgreSQL.')