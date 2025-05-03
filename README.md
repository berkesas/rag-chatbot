# RAG-chatbot
Basic RAG chatbot demo application with Python Flask. This application was presented at Boston Code and Coffee meetup on May 3, 2025 in Cambridge, MA.

All images are from Pexels.com. Copyright TBA.

Textual data belong to Boston Code and Coffee community and the website.

This code is for demonstration purposes only. It shows basic ideas that need to be developed further for production purposes. The code is not based on coding best-practices. Instead it focuses in quick and dirty setup for a basic functional system.

## Useful software

Although not necessary, I recommend to install the following to be able to test easily on the local server:

- VS Code obviously and Live Server extension
- LM Studio and Llama2 LLM
- an API client Bruno 

## Safety and security

Parts of this code uses paid API services. Do not share your API_KEY with others. In production environment change the following parts in `app.py` to limit requests only from authorized domains. Put your own domains instead of `*` which allows all domains.

```python
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

host_questions = {}


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods",
                         "GET, POST, OPTIONS")  # * for all
    return response
```

## Get the repo

```bash
>git clone https://github.com/berkesas/rag-chatbot.git
```
## Install `pip` and `venv`

Normally Python 3.3+ come with these pre-installed. Install pip and venv if for some reason you don't have it.

```bash
python -m ensurepip --default-pip
pip install virtualenv
```

## Creating a virtual environment

First let's create a virtual environment isolated from your system-level installation of Python. In the application folder, we use the `venv` module to create a virtual environment called `venv`. Let's assume your folder is `C:\web\rag-chatbot`.

```bash
C:\web\rag-chatbot>python -m venv venv
```

We need to activate it with the following:

On Windows

```bash
C:\web\rag-chatbot>venv\Scripts\activate
```

On Linux

```bash
/var/www/rag-chatbot$ source venv/bin/activate
```

## Running LM Studio

LM Studio allows you to load an LLM model and run a server with LLM REST API endpoint. You can get it free at [lmstudio.ai](https://lmstudio.ai/).

- Install LM Studio.
- Download `LLama-2 7B Chat` LLM model or any other model of your preference.
- Load the model
- Go to Developer tab and click 'Status: stopped' and make it run the server. The indicator will change to active green.

This enables the following endpoints:

GET http://127.0.0.1:1234/v1/models  
POST http://127.0.0.1:1234/v1/chat/completions  
POST http://127.0.0.1:1234/v1/completions  
POST http://127.0.0.1:1234/v1/embeddings  

This demo interacts with these endpoints. You can check if LM Studio is running properly by just browsing to http://127.0.0.1:1234/v1/models. It will list the models available.

Depending on your LM Studio setup you need to adjust the following lines in `local_dev.env` or `dev.env`:

```python
EMBEDDING_MODEL='text-embedding-nomic-embed-text-v1.5'
GENERATIVE_MODEL='smollm-360m-instruct-v0.2'
# GENERATIVE_MODEL='deepseek-r1-distill-qwen-7b'
# GENERATIVE_MODEL='llama-2-7b-chat'
LOCAL_EMBEDDING_API_ENDPOINT='http://127.0.0.1:1234/v1'
LOCAL_GENERATIVE_API_ENDPOINT='http://127.0.0.1:1234/v1/chat/completions'
```

You can monitor the log of your LLM in LM Studio Developer tab and control its behavior using `Inference` section on the Developer tab.

You can run LM Studio server on the local network so that you can have a setup where the backend server is on a different device (therefore IP) than the frontend.

You can use any local LLM server, but you will need to do the necessary adjustments in the files.

## Using the remote LLM API endpoint

Testing remotely requires to setup your own Google service API key in the `dev.env` file.

First you need to create an API key for the service.

- Sign in to Google Cloud.
- Go to Google Cloud Console Dashboard.
- Create a new project (https://console.cloud.google.com/projectcreate).
- Go to your project dashboard and click `Explore and Enable APIs`.
- Enable `Gemini API` by searching for it.
- On your API page, click `Credentials` and then `+Create credentials`>API Key. This will create an API key you can use to access this service. 

Modify the dev.env or local_dev.env file using the API key generated above. Do not share this key publicly.

```python
API_KEY='your-api-key'
EMBEDDING_MODEL='models/text-embedding-004'
GENERATIVE_MODEL='gemini-2.0-flash'
```

## Installing required Python packages

We'll install flask, flask-cors, dotenv, chromadb, google-genai packages.

**flask** - creates a basic web server to run Python files.

**flask-cors** - enables cross-server communication so that your backend and frontend can run on different domains.

**dotenv** - enables usage of .env files to differentiate development and production environments and store configuration parameters in a separate file instead of hardcoding into your application code.

**chromadb** - enables storage and retrieval of embeddings in vector database

**google-genai** - enables using Google Generative AI API

We'll use requirements.txt file because there are many interdependent packages 

```
(venv) C:\web\rag-chatbot>pip install -r requirements.txt
```

## Running the Flask app (backend)

This demo uses different `.env` files to configure the app. It uses `APP_ENV` environment variable to load from either `dev.env` or `local_dev.env`.

You can change the `APP_ENV` variable, with the following command in VS Code terminal:

```bash
>$env:APP_ENV="local_dev"
```

You can see the current value of the `APP_ENV` variable:

```bash
>echo $env:APP_ENV
```

## Creating the vector database

This demo uses chromadb as its vector database. `local_db.py` or `db.py` creates the initial database from the source files. It uses the files in `rag-source` and `rag-images` files, creates embeddings and puts them vector database collections. 

To create the initial database run the database file with the following command. It can take some time to load the required Python packages in memory and you will see console output indicating that the collections are created. This is a pre-requisite step for running the chatbot server app below.

```bash
>python db.py
```

You can modify the source text files or add new files in `rag-source` and `rag-images` folders.

This demo creates three collections:

- documents-collection - for textual data
- questions-collection - to store proposed questions
- images-collection - to store image embeddings

The demo supports text and image modalities.

## Running the app 
We can run the app from the command line.

```
(venv) C:\web\rag-chatbot>python app.py
```

The app will run with the settings indicated in this section of `app.py`.

```python
if __name__ == "__main__":
    app.run(host='192.168.0.64', port=5001, debug=DEBUG)
```

## Running the app with local or remote servers

Depending on whether you run a local server or access remote endpoint you need to adjust this line in `app.py` file. Comment out the unused line and remove the comment from the file you want to use.

```python
from local_server import create_response
# from server import create_response
```

## Running the frontend

Open the frontend folder in VS Code. Open `fullwindow.html` and click `Go Live` (requires Live Server). Any other HTTP server should work.

If you are running on different IPs. Modify the `chat.js` file, especially the following part:

```js
const chatApi = 'http://10.10.193.224:5001/api/chat';
```

## Testing queries

You can ask any question to the chatbot and it will try to answer. Local LLM servers with LM Studio may run slow due to limited compute power. You can observer the log on LM Studio Developer tab and `app.py` also prints logs to the console.

To add a document use this custom command in the chatbot question box:

```
$document_add|New piece of information you want to add to the collection
```

To search for an image:

```
$image_find|animals
```

To find similar images:

```
$image_similar|paris.jpg
```

These custom commands can be modified by you in any form. They are not part of a set API, it is up to your imagination to develop this app further.

## What's in the future

We discussed briefly during the meetup and in the future this can be converted into a full-fledged open-source chatbot creation framework.