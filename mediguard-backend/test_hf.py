import os
from huggingface_hub import hf_hub_download

try:
    print("Attempting to download .env from Hugging Face Model Repository...")
    path = hf_hub_download(
        repo_id="afiBride/mediguard-models", # Fixed username casing
        filename=".env",
        repo_type="model"                   # CHANGED: From 'space' to 'model'
    )
    print(f"\n🎉 SUCCESS! Secure file downloaded to: {path}")

    with open(path, 'r') as f:
        print("\n--- File Contents ---")
        print(f.read())
except Exception as e:
    print(f"\n❌ Error downloading file: {e}")
