from sentence_transformers import SentenceTransformer, util
from PIL import Image
import time
import json
import os
import zipfile
from natsort import natsorted
import numpy as np
import shutil
import argparse

def read_categories_from_file(file_path):
    """
    Read a text file with categories and return them in a list format.
    
    :param file_path: Path to the text file containing categories.
    :return: List of categories.
    """
    with open(file_path, 'r') as file:
        categories = [line.strip() for line in file if line.strip()]
        return categories

# Path to LVIS categories   
categories_file_path = "LVIS_categories_final.txt"
categories = read_categories_from_file(categories_file_path)

# Load CLIP model
model = SentenceTransformer('clip-ViT-L-14')
# Encode the categories
text_emb = model.encode(categories)
print("Text Embedding Done")

def get_top_3_average_embedding_categories(folder_path):
    """
    Take a folder name as input, embed the first 10 PNG files in the folder,
    average the embeddings, and return the top 3 categories in a JSON file format.
    
    
    :param folder_path: Path to the folder containing PNG files.
    """
    embeddings = []
    png_files = [file_name for file_name in natsorted(os.listdir(folder_path)) if file_name.endswith('.png')][:10]
    for file_name in png_files:
        image_file = os.path.join(folder_path, file_name)
        # Load and encode the image
        img_emb = model.encode(Image.open(image_file))
        embeddings.append(img_emb)
    
    if not embeddings:
        print("No PNG files found.")
        return
    
    # Compute the average embedding
    avg_emb = np.mean(embeddings, axis=0)
    # Compute cosine similarity
    cos_scores = util.cos_sim(avg_emb, text_emb)[0]
    
    # Get top 3 categories
    top_3_idx = cos_scores.argsort(descending=True)[:3]
    top_3_categories = [categories[idx] for idx in top_3_idx]
    
    # Prepare the result dictionary
    result = {
        'top_3_categories': top_3_categories,
    }
    
    # Save the result to a JSON file
    json_file_path = os.path.join(folder_path, "average_LVIS_categories.json")
    with open(json_file_path, 'w') as json_file:
        json.dump(result, json_file, indent=4)
    

def unzip_folder(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def zip_folder(folder_path):
    folder_name = os.path.basename(folder_path.rstrip('/'))
    zip_name = f"{folder_name}.zip"
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, os.path.join(folder_path, '..')))

def process_all_subfolders(parent_folder_path):
    """
    Take parent folder name as input, unzip the file, generate categories and zip it
    
    :param folder_path: Path to the folder containing zipped files.
    """

    os.chdir(parent_folder_path)

    # List all files in the directory and filter for zip files
    files = os.listdir(parent_folder_path)
    zip_files = [file for file in files if file.endswith('.zip')]

    # Unzip all zip files and delete them
    for zip_file in zip_files:
        zip_path = os.path.join(parent_folder_path, zip_file)
        unzip_folder(zip_path, os.getcwd())
        os.remove(zip_path)
        print(f"Unzipped and deleted file: {zip_file}")

    # Process each subfolder
    for root, dirs, files in os.walk(parent_folder_path):
        for dir_name in dirs:
            folder_path = os.path.join(root, dir_name)
            get_top_3_average_embedding_categories(folder_path)
            zip_folder(folder_path)
            shutil.rmtree(folder_path)
            print(f"Processed and deleted folder: {folder_path}")
        break  # Avoid descending into sub-subfolders


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Process all subfolders in a given folder path.')
    parser.add_argument('folder_path', type=str, help='The path to the parent folder')

    # Parse the arguments
    args = parser.parse_args()
    parent_folder_path = args.folder_path

    # Measure the time taken to process the folder
    start_time = time.time()
    process_all_subfolders(parent_folder_path)
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Print the elapsed time
    print(f"Time taken to process the folder: {elapsed_time:.2f} seconds")

if __name__ == '__main__':
    main()




