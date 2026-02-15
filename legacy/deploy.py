import os
from huggingface_hub import HfApi

def deploy():
    token = os.getenv("HF_TOKEN")
    repo_id = "Debanik7/SPJIMR-Venue-Management"  # Based on previous context if user name is known, otherwise will try to create. 
    # Let's use a generic name first or get the user's username if possible.
    # Actually, the user just gave the key. I'll use HfApi.whoami(token) to find out the username.
    
    api = HfApi(token=token)
    try:
        user_info = api.whoami()
        username = user_info['name']
        repo_id = f"{username}/SPJIMR-Venue-Management"
        print(f"Deploying to: {repo_id}")
    except Exception as e:
        print(f"Error getting username: {e}")
        return

    # Create Repo if not exists
    try:
        api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="gradio", exist_ok=True)
        print(f"Space created or already exists: {repo_id}")
    except Exception as e:
        print(f"Error creating space: {e}")
        return

    # Files to upload
    files_to_upload = ["app.py", "requirements.txt", "spjimr_logo.png", "bookings.csv"]
    
    for file_path in files_to_upload:
        if os.path.exists(file_path):
            print(f"Uploading {file_path}...")
            api.upload_file(
                path_or_fileobj=file_path,
                path_in_repo=file_path,
                repo_id=repo_id,
                repo_type="space"
            )
        else:
            print(f"Warning: {file_path} not found.")

    print(f"Deployment complete! Check it out at https://huggingface.co/spaces/{repo_id}")

if __name__ == "__main__":
    deploy()
