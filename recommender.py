import faiss
from database import load_data,  embed, load_index
import numpy as np

df = load_data()
index = load_index()
def recommend_courses(query: str, top_k: int = 5):
    print(query)
    # Embed search query
    query_vector = embed(query).reshape(1, -1)
    faiss.normalize_L2(query_vector)

    scores, indices = index.search(query_vector, top_k)
    results = []

    for i in indices[0]:
        course = df.iloc[i]
        results.append({
            "Course Name": course['Course Name'],
            "Course Description": course['Course Description'],
            "Skills": course['Skills']
        })
    print(results)
    return results