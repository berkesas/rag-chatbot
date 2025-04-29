import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

import chromadb
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


def create_chroma_db(documents, DOCUMENTS_COLLECTION, db_path):
    chroma_client = chromadb.PersistentClient(path=db_path)
    try:
        chroma_client.delete_collection(name=DOCUMENTS_COLLECTION)
    except Exception as e:
        print(e)

    collection = chroma_client.create_collection(
        name=DOCUMENTS_COLLECTION, embedding_function=GeminiEmbeddingFunction())

    for i, d in enumerate(documents):
        collection.add(
            documents=d,
            ids=str(i)
        )
    return collection


def create_documents(source_path):
    documents = []
    for filename in os.listdir(source_path):
        if filename.endswith(".txt"):
            with open(os.path.join(source_path, filename), 'r', encoding="utf-8") as file:
                print('processing: ', filename)
                text_content = file.read()
                documents.append(text_content)
    return documents


# List available models
for model in client.models.list():
    for action in model.supported_actions:
        if action == "embedContent":
            print(model.name)

documents = create_documents(SOURCE_PATH)
collection = create_chroma_db(
    documents, DOCUMENTS_COLLECTION, DATABASE_PATH)

questions = [
    "Where is Boston Code and Coffee located?",
    "How many members does it have?",
    "Is it useful for Software Developers?",
    "What are the benefits for Tech Companies?",
    "When does Boston Code and Coffee meet?",
    "How can I get involved?",
    "How can my organization or business I work for help out?",
    "What are Boston Code and Coffee features?"
]

question_collection = create_chroma_db(
    questions, QUESTIONS_COLLECTION, DATABASE_PATH)
