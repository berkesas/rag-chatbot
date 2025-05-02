import requests

# model_name = "deepseek-r1-distill-qwen-7b"
model_name = "smollm-360m-instruct-v0.2"
endpoint = "http://localhost:1234/v1/chat/completions"
headers = {"Content-Type": "application/json"}


def generate_answer_local(question):
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": question}]
    }

    response = requests.post(endpoint, json=data, headers=headers)
    response_data = response.json()
    return response_data["choices"][0]["message"]["content"]
