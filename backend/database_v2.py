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
    # 'https://www.nottingham.edu.my/ugstudy/course/nottingham-foundation-programme',
    # "https://www.nottingham.edu.my/ugstudy/course/computer-science-bsc-hons",
    # "https://www.nottingham.edu.my/ugstudy/course/computer-science-with-artificial-intelligence-bsc-hons",
    # "https://www.nottingham.edu.my/pgstudy/course/research/computer-science-mphil-phd",
    # "https://www.nottingham.edu.my/Study/Fees-and-Scholarships/Scholarships/Foundation-undergraduate-scholarships.aspx",
    "https://www.nottingham.edu.my/Study/Make-an-enquiry/Enquire-now.aspx"
    # https://www.nottingham.edu.my/Study/How-to-apply/When-to-apply.aspx
    
    # facilities
    # "https://www.nottingham.edu.my/CurrentStudents/Facilities/Sport/Sport.aspx",
    # "https://www.nottingham.edu.my/CurrentStudents/Facilities/Sport/Swimming-pool.aspx",
    # "https://www.nottingham.edu.my/CurrentStudents/Facilities/Health.aspx",
    # "https://www.nottingham.edu.my/CurrentStudents/Facilities/Prayer.aspx",
    # "https://www.nottingham.edu.my/CurrentStudents/Facilities/amenities.aspx"
    
    # current students
    #
]

# Extract namespace from URL
def extract_namespace_from_url(url):
    namespace=  url.rstrip('/').split('/')[-1]
    return namespace.replace(".aspx", "")  # Remove .aspx if it exists

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
def upsert_vectors_to_pinecone(docs, namespace, source_url):
    print(f"\n--- Upserting {len(docs)} chunks to Pinecone under namespace '{namespace}' ---")

    vectors = []
    
    for i, doc in enumerate(docs):
        embedding_response = client.embeddings.create(
            input=doc,
            model="text-embedding-3-small"  # Specify embedding model
        )
        embedding = embedding_response.data[0].embedding
        
        vectors.append((f"{namespace}-doc-{i}", embedding, {"namespace": namespace, "content": doc, "source_url": source_url}))

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
        upsert_vectors_to_pinecone(chunks, namespace, url)
        
        

def process_and_store_documents_with_namespace(urls, custom_namespace):
    """
    Processes and stores documents from URLs into a specified namespace.
    
    Parameters:
        urls (list): List of URLs to scrape.
        custom_namespace (str): The namespace where the extracted data should be stored.
    """
    for url in urls:
        namespace = custom_namespace  # Use the user-defined namespace
        print(f"Processing: {url} -> Namespace: {namespace}")

        cleaned_text = extract_clean_text(url)
        if not cleaned_text:
            print(f"Skipping {url} due to extraction failure.")
            continue

        chunks = split_documents(cleaned_text)
        upsert_vectors_to_pinecone(chunks, namespace, url)
        

# Run the process to store documents
if __name__ == "__main__":
    #process_and_store_documents(urls)
    process_and_store_documents_with_namespace(urls, "contact-information")  # Store in a custom namespace