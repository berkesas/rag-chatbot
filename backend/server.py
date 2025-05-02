import os
import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types

from chromadb import EmbeddingFunction
from datetime import datetime
import uuid
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
import base64
from PIL import Image
import numpy as np

# Load variables from .env file
env = os.getenv('APP_ENV', 'dev')
dotenv_path = f'{env}.env'
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

# Initialize the client with your API key
client = genai.Client(api_key=API_KEY)

# multimodal embedding function to embed images and text
multimodal_embedding_function = OpenCLIPEmbeddingFunction()
# loads images from the collection
data_loader = ImageLoader()


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

image_collection = chromaClient.get_collection(
    name=IMAGES_COLLECTION, embedding_function=multimodal_embedding_function)


def create_response(question):
    if question.startswith("$"):
        response = process_command(question)
    else:
        answer = generate_answer(question)
        related_questions = get_related_questions(question)
        response = {
            "source": 'server',
            "text": answer,
            "created": datetime.now().isoformat(),
            "additionalQuestions": related_questions
        }
    return response


def process_command(question):
    if question.startswith("$document_add"):
        document = question.split("|", 1)[1]
        id = str(uuid.uuid4())
        collection.add(
            documents=[document],
            ids=[id]
        )
        response = {
            "source": 'server',
            "text": "Added document: "+document+" ID:"+id,
            "created": datetime.now().isoformat(),
            "additionalQuestions": []
        }
    elif question.startswith("$document_delete"):
        id = question.split("|", 1)[1]
        collection.delete(
            ids=[id]
        )
        response = {
            "source": 'server',
            "text": "Deleted document with ID:"+id,
            "created": datetime.now().isoformat(),
            "additionalQuestions": []
        }
    elif question.startswith("$image_find"):
        image_query = question.split("|", 1)[1]
        result = image_collection.query(
            query_texts=[image_query], include=['data'], n_results=3)
        print(result)
        images = ''
        for image in result["uris"][0]:
            with open(image, "rb") as img_file:
                images += "<img style='height:200px; margin:5px;' src='data:image/jpeg;base64, " + \
                    base64.b64encode(img_file.read()).decode("utf-8") + "'>"
        response = {
            "source": 'server',
            "text": "You searched for: "+image_query+"<br><br>"+images,
            "created": datetime.now().isoformat(),
            "additionalQuestions": []
        }
    elif question.startswith("$image_similar"):
        image_name = question.split("|", 1)[1]
        query_image = np.array(Image.open(f"{IMAGE_PATH}/"+image_name))
        result = image_collection.query(
            query_images=[query_image], include=['data'], n_results=3)
        images = ''
        for image in result["uris"][0]:
            with open(image, "rb") as img_file:
                images += "<img style='height:200px; margin:5px;' src='data:image/jpeg;base64, " + \
                    base64.b64encode(img_file.read()).decode("utf-8") + "'>"
        response = {
            "source": 'server',
            "text": "You searched for: "+image_name+"<br><br>"+images,
            "created": datetime.now().isoformat(),
            "additionalQuestions": []
        }

    elif question.startswith("$web_open"):
        url = question.split("|", 1)[1]
        if not url.startswith("http"):
            url = "https://"+url
        os.startfile(url)
        response = {
            "source": 'server',
            "text": "Launching: "+url,
            "created": datetime.now().isoformat(),
            "additionalQuestions": []
        }
    else:
        response = {
            "source": 'server',
            "text": "Unrecognized command",
            "created": datetime.now().isoformat(),
            "additionalQuestions": []
        }
    return response


def get_relevant_passage(query, collection):
    # n_results number of results
    results = collection.query(query_texts=[query], n_results=2)

    try:
        return ' '.join(results['documents'][0])
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
