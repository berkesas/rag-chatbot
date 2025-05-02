import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb import EmbeddingFunction
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader

# Load variables from .env file
env = os.getenv('APP_ENV', 'local_dev')
dotenv_path = f'{env}.env'
print(dotenv_path)
load_dotenv(dotenv_path)

SOURCE_PATH = os.getenv('SOURCE_PATH')
IMAGE_PATH = os.getenv('IMAGE_PATH')
DATABASE_PATH = os.getenv('DATABASE_PATH')
DOCUMENTS_COLLECTION = os.getenv('DOCUMENTS_COLLECTION')
QUESTIONS_COLLECTION = os.getenv('QUESTIONS_COLLECTION')
IMAGES_COLLECTION = os.getenv('IMAGES_COLLECTION')

API_KEY = os.getenv('API_KEY')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')
GENERATIVE_MODEL = os.getenv('GENERATIVE_MODEL')

LOCAL_EMBEDDING_API_ENDPOINT = os.getenv('LOCAL_EMBEDDING_API_ENDPOINT')

# multimodal embedding function to embed images and text
multimodal_embedding_function = OpenCLIPEmbeddingFunction()
# loads images from the collection
data_loader = ImageLoader()


class LocalEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.client = OpenAI(
            base_url=LOCAL_EMBEDDING_API_ENDPOINT,
            api_key=API_KEY
        )
        self.model = EMBEDDING_MODEL

    def __call__(self, texts):
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for text in texts:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            embeddings.append(response.data[0].embedding)
        return embeddings


def create_chroma_db(documents, collection_name, db_path):
    chroma_client = chromadb.PersistentClient(path=db_path)
    try:
        chroma_client.delete_collection(name=collection_name)
    except Exception as e:
        print(e)

    collection = chroma_client.create_collection(
        name=collection_name, embedding_function=LocalEmbeddingFunction())

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


def create_image_collection(collection_name, db_path, image_path, image_loader):
    chroma_client = chromadb.PersistentClient(path=db_path)
    try:
        chroma_client.delete_collection(name=collection_name)
    except Exception as e:
        print(e)

    collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=multimodal_embedding_function,
        data_loader=image_loader)

    image_uris = sorted([os.path.join(image_path, image_name)
                        for image_name in os.listdir(image_path)])
    ids = [str(i) for i in range(len(image_uris))]

    for i in range(len(image_uris)):
        print('processing image: ', image_uris[i])
        collection.add(ids=[str(i)], uris=[image_uris[i]])

    return collection


documents = create_documents(SOURCE_PATH)
collection = create_chroma_db(
    documents, DOCUMENTS_COLLECTION, DATABASE_PATH)

questions = [
    "Where is Boston Code and Coffee located?",
    "How many members does Boston Code and Coffee have?",
    "Is it useful for Software Developers?",
    "What are the benefits for Tech Companies?",
    "When does Boston Code and Coffee meet?",
    "How can I get involved?",
    "How can my organization or business I work for help out?",
    "What are Boston Code and Coffee features?",
    "Does Boston Code and Coffee have website?"
]

question_collection = create_chroma_db(
    questions, QUESTIONS_COLLECTION, DATABASE_PATH)

images_collection = create_image_collection(
    IMAGES_COLLECTION, DATABASE_PATH, IMAGE_PATH, data_loader)
