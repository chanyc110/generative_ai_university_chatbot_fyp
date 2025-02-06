import os
import requests
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI


# Load environment variables
load_dotenv()

# Initialize Pinecone and OpenAI
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("website-chatbot")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Jina AI API Key & Reader URL
JINA_API_KEY = "jina_833f960bd0b94f919920f4dabb63af001uiZNzo-5urqa6K9XmLOrk5CgrbV"
JINA_READER_URL = "https://r.jina.ai/"

urls = [
    #'https://www.nottingham.edu.my/ugstudy/course/nottingham-foundation-programme',
    "https://www.nottingham.edu.my/ugstudy/course/computer-science-bsc-hons"
]

# Extract namespace from URL
def extract_namespace_from_url(url):
    return url.rstrip('/').split('/')[-1]

# Use Jina AI to extract LLM-friendly text
def extract_clean_text(url):
    full_url = f"{JINA_READER_URL}{url}"
    headers = {"Authorization": f"Bearer {JINA_API_KEY}"}

    response = requests.get(full_url, headers=headers)
    
    print(f"Status Code: {response.status_code}")  # Check if request was successful
    print(f"Raw Response: {response.text[:500]}")  # Print first 500 chars for debugging
    
    if response.status_code == 200:
        return response.text.strip()
    else:
        print(f"Failed to extract from {url}, Status Code: {response.status_code}")
        return ""
    
# Split text into meaningful chunks
def split_documents(text, chunk_size=1000, chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

# Upsert vectors to Pinecone
def upsert_vectors_to_pinecone(docs, namespace):
    print(f"\n--- Upserting {len(docs)} chunks to Pinecone under namespace '{namespace}' ---")

    vectors = []
    
    for i, doc in enumerate(docs):
        embedding_response = client.embeddings.create(
            input=doc,
            model="text-embedding-3-small"  # Specify embedding model
        )
        embedding = embedding_response.data[0].embedding
        
        vectors.append((f"{namespace}-doc-{i}", embedding, {"namespace": namespace, "content": doc}))

    index.upsert(vectors=vectors, namespace=namespace)
    print(f"--- Finished upserting {len(vectors)} vectors ---")
    
# Process and store documents
def process_and_store_documents(urls):
    for url in urls:
        namespace = extract_namespace_from_url(url)
        print(f"Processing: {url} -> Namespace: {namespace}")

        cleaned_text = extract_clean_text(url)
        if not cleaned_text:
            print(f"Skipping {url} due to extraction failure.")
            continue

        chunks = split_documents(cleaned_text)
        upsert_vectors_to_pinecone(chunks, namespace)
        
        
# GPT-based namespace selection
def determine_namespaces_with_gpt(user_query):
    available_namespaces = [
        "nottingham-foundation-programme",
        "computer-science-bsc-hons"
    ]

    system_prompt = (
        "You are an AI classifier that determines which namespaces are relevant "
        "for a user's query. Choose one or more from the following list and return "
        "a comma-separated list (e.g., 'namespace1, namespace2').\n"
        f"Available namespaces: {', '.join(available_namespaces)}"
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User query: {user_query}"}
        ],
        temperature=0
    )

    selected_namespaces = response.choices[0].message.content.strip().split(", ")
    valid_namespaces = [ns for ns in selected_namespaces if ns in available_namespaces]

    if valid_namespaces:
        print(f"Selected namespaces: {valid_namespaces}")
        return valid_namespaces
    else:
        print("GPT returned invalid namespaces. Defaulting to general query.")
        return []
    
    
# Query Pinecone based on selected namespaces
def search_similar_vectors(user_query):
    namespaces = determine_namespaces_with_gpt(user_query)
    
    if not namespaces:
        return "Sorry, I couldn't determine the relevant section. Can you clarify your query?"

    query_embedding = client.embeddings.create(
        input=user_query,
        model="text-embedding-3-small"  # Specify the embedding model
    ).data[0].embedding
    
    results = []

    for namespace in namespaces:
        res = index.query(vector=query_embedding, top_k=3, include_metadata=True, namespace=namespace)
        results.extend(res["matches"])

    # Sort results by similarity score
    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)[:3]
    context = "\n".join([match["metadata"].get("content", "") for match in sorted_results])

    return context

# Run the process to store documents
if __name__ == "__main__":
    process_and_store_documents(urls)