import requests
import os

url = "http://localhost:8000/api/upload"

# Create a dummy text file to upload
with open("dummy_upload.txt", "w") as f:
    f.write("This is a confidential agreement containing the unique phrase AutoIngestionTest99.\n\nIt ensures that the Vector DB ingestion pipeline is functioning as expected by storing embeddings.")

# Upload via multipart form
with open("dummy_upload.txt", "rb") as f:
    files = {"file": ("dummy_upload.txt", f, "text/plain")}
    data = {"task_type": "analyze_contract"}
    
    print("Uploading file to /api/upload...")
    response = requests.post(url, files=files, data=data)
    
if response.status_code == 200:
    print("Upload successful!")
    print("Background task should now be ingesting this into ChromaDB.")
else:
    print(f"Failed with status: {response.status_code}")
    print(response.text)

# Cleanup
if os.path.exists("dummy_upload.txt"):
    os.remove("dummy_upload.txt")
