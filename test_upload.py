import requests

files = {'file': open('c:/Users/ap080/OneDrive/Desktop/Legal-Ai-Platform/Sample_Employment_Contract.pdf', 'rb')}
data = {'task_type': 'analyze_contract'}

try:
    response = requests.post('http://localhost:8000/api/upload', files=files, data=data)
    print(response.status_code)
    print(response.json())
except Exception as e:
    print(e)
