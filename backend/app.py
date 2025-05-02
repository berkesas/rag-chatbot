import os
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask,  jsonify, make_response, request
from flask_cors import CORS
from local_server import create_response
# from server import create_response

# Load variables from .env file
env = os.getenv('APP_ENV', 'local_dev')
dotenv_path = f'{env}.env'
print("Loading environment:", dotenv_path)
load_dotenv(dotenv_path)

DEBUG = os.getenv('DEBUG')
LOG_FILE = os.getenv('LOG_FILE')
MAX_QUESTIONS = int(os.getenv('MAX_QUESTIONS'))

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

host_questions = {}


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods",
                         "GET, POST, OPTIONS")  # * for all
    return response


@app.route("/")
def hello_world():
    return "<p>This is API service</p>"


@app.route("/api/chat", methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    elif request.method == 'POST':
        data = request.get_json()
        # print(data)
        question = data.get('text')
        host_questions[request.headers['Host']] = host_questions.get(
            request.headers['Host'], 0) + 1

        if host_questions[request.headers['Host']] < MAX_QUESTIONS:
            response = create_response(question)
            record_question(LOG_FILE, question+"\n"+str(response), request)
        else:
            response = {
                "source": 'server',
                "text": "Sorry, you have reached your question limit. Please try again later.",
                "created": datetime.now().isoformat(),
                "additionalQuestions": []
            }
    return jsonify([response])


@app.route("/api/chattest", methods=['POST', 'OPTIONS'])
def chattest():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    elif request.method == 'POST':
        data = request.get_json()
        # print(data)
        question = data.get('text')
        answer = "This is a test endpoint. Your question was: "+question
        response = {
            "source": 'server',
            "text": answer,
            "created": datetime.now().isoformat(),
            "additionalQuestions": ['Question 1', 'Question 2']
        }
    return jsonify([response])


def record_question(file, question, request):
    with open(file, 'a') as file:
        # if behind a proxy
        ip = request.headers.get('X-Forwarded-For')

        if ip:
            ip = ip.split(',')[0]  # Get the real client IP
        else:
            ip = request.remote_addr  # Fallback to direct IP

        file.write(
            question+";"+str(ip)+";"+str(datetime.now())+"\n")


if __name__ == "__main__":
    app.run(host='192.168.0.64', port=5001, debug=DEBUG)
