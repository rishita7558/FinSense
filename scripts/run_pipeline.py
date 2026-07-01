import requests

url = "http://127.0.0.1:8000/upload_audio"

file = {"file": open("data/sample_audio/sample.wav", "rb")}

response = requests.post(url, files=file)

print(response.json())
