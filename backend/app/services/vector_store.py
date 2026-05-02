import faiss
import numpy as np

index = None
stored_data = []
file_registry = set()


def create_vector_store(embeddings, chunks, filename):
    global index, stored_data, file_registry

    # 🚫 Prevent duplicate indexing
    if filename in file_registry:
        print(f"⚠️ File already indexed: {filename}")
        return

    dimension = len(embeddings[0])

    if index is None:
        index = faiss.IndexFlatL2(dimension)

    embeddings_np = np.array(embeddings).astype("float32")
    index.add(embeddings_np)

    for i, chunk in enumerate(chunks):
        stored_data.append({
            "page_content": chunk,
            "metadata": {
                "source": filename,
                "chunk_id": i
            }
        })

    file_registry.add(filename)

    print(f"✅ Indexed file: {filename}")
    print(f"📦 Total chunks: {len(stored_data)}")


def similarity_search_with_score(query, get_embedding_fn, k=3, filter_files=None):
    if index is None or len(stored_data) == 0:
        return []

    query_embedding = get_embedding_fn(query)
    query_np = np.array([query_embedding]).astype("float32")

    distances, indices = index.search(query_np, k * 2)  # 🔥 get more results

    results = []

    for i, idx in enumerate(indices[0]):
        if idx >= len(stored_data):
            continue

        doc = stored_data[idx]

        # 🔹 OPTIONAL: filter by selected files
        if filter_files:
            if doc["metadata"]["source"] not in filter_files:
                continue

        # 🔹 Convert distance → similarity
        score = 1 / (1 + distances[0][i])

        results.append((doc, score))

    return results[:k]


def get_all_files():
    return list(file_registry)