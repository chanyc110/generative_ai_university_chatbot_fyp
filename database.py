from pinecone.grpc import PineconeGRPC as Pinecone
import ollama
import requests
from bs4 import BeautifulSoup


pc = Pinecone(api_key="pcsk_nPS6S_MLDxFdbMPRtAdeJocvPqLujtFTJx2aKX5y1yndBktFf37cfNW6atk398kBPxFVb")
index = pc.Index("website-chatbot")
namespace = 'foundation-engineering'


# List of URLs to scrape
urls = [
    'https://www.nottingham.edu.my/ugstudy/course/foundation-in-engineering'
    # Add more URLs as needed
]

def extract_info(url):
    # Send a GET request to the webpage
    response = requests.get(url)
    
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Example: Extract all paragraphs from the page
    paragraphs = soup.find_all('p')
    content = ' '.join([p.get_text() for p in paragraphs])
    print(content)
    
    return content


def chunk_text(text, chunk_size=512, overlap=100):
    
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap  # Move start forward, overlapping by the specified amount
    return chunks

def generate_embedding(text):
    response = ollama.embeddings(model='mxbai-embed-large', 
                                prompt='Represent this sentence for searching relevant passages:' + text)
    embedding = response['embedding']
    return embedding

def upsert_chunk_to_pinecone( embedding, url, chunk_id, chunk_text, namespace):

    upsert_data = [
        {
            'id': f"{url}_chunk_{chunk_id}",  # Unique ID for each chunk
            'values': embedding,
            'metadata': {
                'source_url': url,
                'chunk_id': chunk_id,
                'text': chunk_text
            }
        }
    ]
    
    # Upsert data into Pinecone under the specified namespace
    index.upsert(vectors=upsert_data, namespace=namespace)
    
    
def search_similar_vectors(query, namespace, top_k=3):
    query_embedding = generate_embedding(query)
    search_results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True, namespace=namespace)
    print(search_results)
    return search_results['matches'][0]['metadata']
    
def process_and_store(urls, namespace):
    for url in urls:
        # Step 1: Scrape the content from the URL
        content = extract_info(url)
        
        # Step 2: Chunk the content
        chunks = chunk_text(content)
        
        # Step 3: Embed and upsert each chunk
        for i, chunk in enumerate(chunks):
            embedding = generate_embedding(chunk)
            upsert_chunk_to_pinecone(embedding, url, i, chunk, namespace)
            
            
            
def delete_namespace(index, namespace):
    
    index.delete(namespace=namespace, delete_all=True) 
    print(f"Namespace '{namespace}' has been deleted.")           



"""To run"""

# process_and_store(urls, namespace)
# delete_namespace(index, namespace)
    