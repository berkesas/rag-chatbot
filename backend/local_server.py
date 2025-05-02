import os
import requests
from openai import OpenAI
import chromadb
from dotenv import load_dotenv
from chromadb import EmbeddingFunction
from datetime import datetime
import uuid
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
import base64
from PIL import Image
import numpy as np
import re

# Load variables from .env file
env = os.getenv('APP_ENV', 'local_dev')
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

LOCAL_EMBEDDING_API_ENDPOINT = os.getenv('LOCAL_EMBEDDING_API_ENDPOINT')
LOCAL_GENERATIVE_API_ENDPOINT = os.getenv('LOCAL_GENERATIVE_API_ENDPOINT')

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


chromaClient = chromadb.PersistentClient(path=DATABASE_PATH)
collection = chromaClient.get_collection(name=DOCUMENTS_COLLECTION,
                                         embedding_function=LocalEmbeddingFunction())
questions_collection = chromaClient.get_collection(
    name=QUESTIONS_COLLECTION, embedding_function=LocalEmbeddingFunction())

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
            "text": "Deleted document: ID:"+id,
            "created": datetime.now().isoformat(),
            "additionalQuestions": []
        }
    elif question.startswith("$image_find"):
        image_query = question.split("|", 1)[1]
        result = image_collection.query(
            query_texts=[image_query], include=['data'], n_results=3)
        print(result)
        images = "<div class='flex'>"
        for image in result["uris"][0]:
            with open(image, "rb") as img_file:
                images += "<img style='height:200px; margin:5px;' src='data:image/jpeg;base64, " + \
                    base64.b64encode(img_file.read()).decode("utf-8") + "'>"
        images += "</div>"
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
        images = "<div class='flex'>"
        for image in result["uris"][0]:
            with open(image, "rb") as img_file:
                images += "<img style='height:200px; margin:5px;' src='data:image/jpeg;base64, " + \
                    base64.b64encode(img_file.read()).decode("utf-8") + "'>"
        images += "</div>"
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

    data = {
        "model": GENERATIVE_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(LOCAL_GENERATIVE_API_ENDPOINT, json=data, headers={
                             "Content-Type": "application/json"})
    response_data = response.json()
    raw_content = response_data["choices"][0]["message"]["content"]

    return raw_content


def make_prompt(query, relevant_passage):
    escaped = relevant_passage.replace(
        "'", "").replace('"', "").replace("\n", " ")
    prompt = ("""[INST] <<SYS>>
    You are a helpful and knowledgeable assistant. Use only the provided context to answer the user's question. If the context does not contain the answer, say "I don't know based on the given information. Do not use phrases like "based on the context" or "based on the information provided" in your answer. Present URLs as clickable links"
    <</SYS>>

    Context:
    {relevant_passage}

    Question:
    {query}
    [/INST]
  """).format(query=query, relevant_passage=escaped)

    return prompt
