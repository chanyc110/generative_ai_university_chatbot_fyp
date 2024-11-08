from pinecone.grpc import PineconeGRPC as Pinecone
import ollama
import requests
from bs4 import BeautifulSoup
from typing import Optional



pc = Pinecone(api_key="pcsk_nPS6S_MLDxFdbMPRtAdeJocvPqLujtFTJx2aKX5y1yndBktFf37cfNW6atk398kBPxFVb")
index = pc.Index("website-chatbot")
# namespace = 'foundation-in-science'


# List of URLs to scrape
urls = [
    # 'https://www.nottingham.edu.my/ugstudy/course/foundation-in-engineering',
    # 'https://www.nottingham.edu.my/ugstudy/course/foundation-in-arts-and-education'
    # 'https://www.nottingham.edu.my/ugstudy/course/foundation-in-business-and-management',
    'https://www.nottingham.edu.my/ugstudy/course/foundation-in-science'
    
]

def extract_info(url):
    # Send a GET request to the webpage
    response = requests.get(url)
    
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove script, style, and link tags
    for script_or_style in soup(['script', 'style', 'title', 'a']):
        script_or_style.decompose()
    
    # Example: Extract all paragraphs from the page
    elements = soup.find_all(['p', 'ul', 'ol', 'li', 'div', 'span'])
    
    content = []
    for element in elements:
        # Exclude navigation, footers, or irrelevant sections if they have identifiable classes or IDs
        if not element.get('class') or ('nav' not in element.get('class') and 'footer' not in element.get('class')):
            content.append(element.get_text(strip=True))
            
    # Join the content into a single string
    full_content = ' '.join(content)
    print(full_content)
    
    return full_content


def chunk_text(text, chunk_size=300, overlap=150):
    
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def generate_embedding(text):
    response = ollama.embeddings(model='mxbai-embed-large', 
                                prompt='Represent this sentence for searching relevant passages:' + text)
    embedding = response['embedding']
    return embedding

def upsert_chunk_to_pinecone( embedding, url, chunk_id, chunk_text, namespace):

    upsert_data = [
        {
            'id': f"chunk_{chunk_id}",  # Unique ID for each chunk
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
    
    
namespace_mapping = {
    ("arts", "education", "foundation"): "foundation-in-arts-and-education",
    ("science", "foundation"): "foundation-in-science",
    "engineering": "foundation-in-engineering",
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
    
def search_similar_vectors(query,top_k=3):
    namespace = determine_namespace(query)
    
    query_embedding = generate_embedding(query)
    search_results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True, namespace=namespace)
    print(search_results)
    
    combined_context = ' '.join(
        [result['metadata']['text'] for result in search_results['matches'] if 'text' in result['metadata']]
    )
    return combined_context
    
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