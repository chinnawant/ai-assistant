
import shutil
import os

# Define the path to your ChromaDB storage folder
chroma_db_path = '~/Development/openai-gbt/chroma-db'

# Check if the directory exists
if os.path.exists(chroma_db_path):
    # Delete the directory and its contents
    shutil.rmtree(chroma_db_path)
    print(f"ChromaDB directory at {chroma_db_path} has been deleted.")
else:
    print(f"No ChromaDB directory found at {chroma_db_path}. Nothing to delete.")