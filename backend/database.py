from pinecone.grpc import PineconeGRPC as Pinecone
import ollama
import requests
from bs4 import BeautifulSoup
from typing import Optional
from langchain.text_splitter import CharacterTextSplitter
from openai import OpenAI
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings

# Load the .env file
load_dotenv()

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("website-chatbot")

client = OpenAI(
    api_key= os.getenv('OPENAI_API_KEY')
)
# namespace = 'foundation-in-science'

    

# List of URLs to scrape
urls = [
    
    'https://www.nottingham.edu.my/ugstudy/course/foundation-in-engineering',
    # 'https://www.nottingham.edu.my/ugstudy/course/foundation-in-arts-and-education'
    # 'https://www.nottingham.edu.my/ugstudy/course/foundation-in-business-and-management'
    # 'https://www.nottingham.edu.my/ugstudy/course/foundation-in-science'
]

# Function to load documents from URLs
def load_documents(urls):
    print("\n--- Loading documents from URLs ---")
    loader = WebBaseLoader(urls)
    documents = loader.load()
    print(f"Loaded {len(documents)} documents.")
    return documents

# Function to split documents into chunks
def split_documents(documents, chunk_size=1000, chunk_overlap=0):
    print("\n--- Splitting documents into chunks ---")
    text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.split_documents(documents)
    print(f"Number of document chunks: {len(docs)}")
    # print(f"Sample chunk:\n{docs[0].page_content[:200]}...\n")
    return docs


# embed
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Function to upsert vectors into Pinecone
def upsert_vectors_to_pinecone(docs, namespace="foundation-in-engineering", index=None):
    
    
    print("\n--- Upserting vectors to Pinecone ---")
    vectors = [
        (f"doc-{i}", embeddings.embed_query(doc.page_content), {"namespace": namespace, "content": doc.page_content})
        for i, doc in enumerate(docs)
    ]
    if index:
        index.upsert(vectors=vectors, namespace=namespace)
        print(f"--- Finished upserting {len(vectors)} vectors to Pinecone under namespace '{namespace}' ---")
    else:
        print("Error: Pinecone index is not provided.")

# Step 5: Query the vector store
def search_similar_vectors(user_query):
    # Create embedding for the query
    query_embedding = embeddings.embed_query(user_query)
    # Query Pinecone
    result = index.query(vector=query_embedding, top_k=3, include_metadata=True, namespace='foundation-in-engineering')
    print(result)
    # Extract content from the results
    context = "\n".join([match["metadata"].get("content", "") for match in result["matches"]])
    return context

# Main function to execute the process
def process_and_store_documents(urls, index):
    documents = load_documents(urls)
    docs = split_documents(documents)
    upsert_vectors_to_pinecone(docs, index)







    
namespace_mapping = {
    ("arts", "education", "foundation"): "foundation-in-arts-and-education",
    ("science", "foundation"): "foundation-in-science",
    ("business", "management", "foundation"): "foundation-in-business-and-management",
    ("engineering", "foundation"): "foundation-in-engineering"
}

def determine_namespace(query: str) -> Optional[str]:
    query_lower = query.lower()
    
    for keywords, namespace in namespace_mapping.items():
        # Check if all keywords in the tuple appear in the query
        if all(keyword in query_lower for keyword in keywords):
            print(f"Matched keywords {keywords}. Selected namespace: {namespace}")
            return namespace
    
    # No match found
    print("No matching namespace found for the given query.")
    return None
    


"""To run"""
