import pandas as pd
import faiss
import numpy as np
from openai import OpenAI
from config import Config

def get_client():
    api_key = Config.OPENAI_API_KEY
    print("API KEY LOADED:", api_key)
    return OpenAI(api_key=api_key)

def embed(text):
    client = get_client()
    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(res.data[0].embedding).astype('float32')

# Load dataset file
def load_data():
    DATASET_PATH = "dataset.csv"

    df = pd.read_csv(DATASET_PATH)
    df.fillna("", inplace=True)
    return df

# Generate embedding
def build_index(df):
    course_texts = (df['Course Name'] + " " + df['Course Description'] + " " + df['Skills']).tolist()

    embeddings = np.array([embed(t) for t in course_texts], dtype="float32")
    print(embeddings)
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index

def load_index():
    return faiss.read_index("index.faiss")



