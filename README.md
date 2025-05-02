# rag-chatbot
Basic rag chatbot application with Python Flask

All images are from Pexels.com

# Useful software

I recommend to install the following to be able to test easily on the local server:

- VS Code obviously and Live Server extension
- an API client Bruno 
- LM Studio and Llama2 LLM

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

## Running the flask app

We can run the app from the command line.

```
(venv) C:\web\rag-chatbot>python app.py
```

The app will run with the settings indicated in this section of `app.py`.

```python
if __name__ == "__main__":
    app.run(host='192.168.0.64', port=5001, debug=DEBUG)
```