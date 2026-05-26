import os
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv

def sync_vault_secrets():
    # Force check for the token in the current process environment
    hf_token = os.getenv("HF_TOKEN")
    
    if hf_token:
        try:
            print("Attempting connection to Hugging Face Model Vault...")
            secrets_path = hf_hub_download(
                repo_id="afiBride/mediguard-models", 
                filename=".env",
                repo_type="model",                  
                token=hf_token
            )
            load_dotenv(secrets_path)
            print("🎉 Successfully synced OpenAI and Pinecone keys from Hugging Face Model Vault.")
            print(f"Verified OPENAI_API_KEY is loaded: {bool(os.getenv('OPENAI_API_KEY'))}")
            print(f"Verified PINECONE_API_KEY is loaded: {bool(os.getenv('PINECONE_API_KEY'))}")
        except Exception as e:
            print(f"❌ Vault sync failed: {e}. Defaulting to local workspace env variables.")
            load_dotenv()
    else:
        print("⚠️ No HF_TOKEN detected in environment variable map. Falling back to local .env")
        load_dotenv()

if __name__ == "__main__":
    sync_vault_secrets()
