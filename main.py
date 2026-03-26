import base64
from fastapi import FastAPI, UploadFile, File, HTTPException
from github import Github, GithubException
from pydantic import BaseModel

app = FastAPI()

# Configuration - Use environment variables in production!
GITHUB_TOKEN = "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"
REPO_NAME = "ChanukaUOJ/githubRESTAPI_CRUD"
BRANCH = "main"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

@app.post("/upload-pdf/")
async def upload_to_github(file: UploadFile = File(...)):
    # 1. Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    try:
        # 2. Read file content
        content = await file.read()
        
        # 3. Define the path where it will be stored in the repo
        file_path = f"uploads/{file.filename}"
        
        # 4. Upload to GitHub
        # Note: If the file already exists, you would need to provide the 'sha' to update it.
        repo.create_file(
            path=file_path,
            message=f"Add {file.filename} via FastAPI",
            content=content,
            branch=BRANCH
        )
        
        return {"message": "Success", "url": f"https://github.com/{REPO_NAME}/blob/{BRANCH}/{file_path}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- CREATE / UPDATE (The "Upload" Endpoint) ---
@app.post("/csv/upload")
async def upload_or_update_csv(file: UploadFile = File(...)):
    """
    Upload a CSV. If filename exists, it updates. If not, it creates.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only .csv files allowed")

    content = await file.read()
    path = f"{file.filename}"

    try:
        # 1. Try to get the existing file to find its SHA
        try:
            existing_file = repo.get_contents(path, ref=BRANCH)
            # 2. If it exists, UPDATE
            repo.update_file(
                path=path,
                message=f"Update content of {file.filename}",
                content=content,
                sha=existing_file.sha,
                branch=BRANCH
            )
            return {"action": "Updated", "filename": file.filename}
            
        except GithubException as e:
            if e.status == 404:
                # 3. If it doesn't exist, CREATE
                repo.create_file(
                    path=path,
                    message=f"Initial upload of {file.filename}",
                    content=content,
                    branch=BRANCH
                )
                return {"action": "Created", "filename": file.filename}
            raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- READ ---
@app.get("/csv/{filename}")
async def read_csv(filename: str):
    """Fetch and return the raw text of a CSV file."""
    path = f"{filename}"
    try:
        file_content = repo.get_contents(path, ref=BRANCH)
        # GitHub returns content in Base64; PyGithub's decoded_content handles it
        return {
            "filename": filename, 
            "data": file_content.decoded_content.decode("utf-8")
        }
    except:
        raise HTTPException(status_code=404, detail="File not found on GitHub")

# --- DELETE ---
@app.delete("/csv/{filename}")
async def delete_csv(filename: str):
    """Remove the CSV file from the repository."""
    path = f"{filename}"
    try:
        existing_file = repo.get_contents(path, ref=BRANCH)
        repo.delete_file(
            path=path,
            message=f"Deleted {filename}",
            sha=existing_file.sha,
            branch=BRANCH
        )
        return {"action": "Deleted", "filename": filename}
    except:
        raise HTTPException(status_code=404, detail="File not found")