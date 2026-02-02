# generate_embeddings.py
import numpy as np
import faiss
from database import embed, load_data

df = load_data()
course_texts = (df['Course Name'] + " " + df['Course Description'] + " " + df['Skills']).tolist()

# Generate embeddings once
embeddings = np.array([embed(t) for t in course_texts], dtype="float32")
faiss.normalize_L2(embeddings)

np.save("embeddings.npy", embeddings)

# Build FAISS and save
index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)
faiss.write_index(index, "index.faiss")
