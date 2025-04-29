import os
import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types

from chromadb import EmbeddingFunction

# Load variables from .env file
env = os.getenv('APP_ENV', 'dev')
dotenv_path = f'{env}.env'
load_dotenv(dotenv_path)

SOURCE_PATH = os.getenv('SOURCE_PATH')
DATABASE_PATH = os.getenv('DATABASE_PATH')
DOCUMENTS_COLLECTION = os.getenv('DOCUMENTS_COLLECTION')
QUESTIONS_COLLECTION = os.getenv('QUESTIONS_COLLECTION')

API_KEY = os.getenv('API_KEY')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')
GENERATIVE_MODEL = os.getenv('GENERATIVE_MODEL')

# Initialize the client with your API key
client = genai.Client(api_key=API_KEY)


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.client = client
        self.model = EMBEDDING_MODEL
        self.task_type = "QUESTION_ANSWERING"

    def __call__(self, texts):
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for text in texts:
            response = self.client.models.embed_content(
                model=self.model,
                contents=[text],
                config=types.EmbedContentConfig(task_type=self.task_type),
            )
            embeddings.append(response.embeddings[0].values)
        return embeddings


chromaClient = chromadb.PersistentClient(path=DATABASE_PATH)
collection = chromaClient.get_collection(name=DOCUMENTS_COLLECTION,
                                         embedding_function=GeminiEmbeddingFunction())
questions_collection = chromaClient.get_collection(
    name=QUESTIONS_COLLECTION, embedding_function=GeminiEmbeddingFunction())


def get_relevant_passage(query, collection):
    results = collection.query(query_texts=[query], n_results=1)

    try:
        return results['documents'][0][0]
    except (IndexError, KeyError, TypeError):
        return None


def get_related_questions(query):
    results = questions_collection.query(query_texts=[query], n_results=2)

    try:
        return results['documents'][0]
    except (IndexError, KeyError, TypeError):
        return []


def generate_answer(query):
    # Perform embedding search
    passage = get_relevant_passage(query, collection)
    print("Relevant passage:", passage, "\n---")

    prompt = make_prompt(query, passage)
    print(prompt)

    response = client.models.generate_content(
        model=GENERATIVE_MODEL, contents=prompt)
    # display(Markdown(answer.text))
    return response.text


def make_prompt(query, relevant_passage):
    escaped = relevant_passage.replace(
        "'", "").replace('"', "").replace("\n", " ")
    prompt = ("""You are a helpful and informative bot and your name is Boston Code and Coffee. You answer questions using text from the reference passage included below. Keep your response shorter than 120 words. Do not refer to the passage or reference text explicitly in your answers. \
        QUESTION: '{query}' \
        PASSAGE: '{relevant_passage}'
  """).format(query=query, relevant_passage=escaped)

    return prompt
