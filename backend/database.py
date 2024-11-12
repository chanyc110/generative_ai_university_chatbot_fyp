from pinecone.grpc import PineconeGRPC as Pinecone
import ollama
import requests
from bs4 import BeautifulSoup
from typing import Optional
from langchain.text_splitter import CharacterTextSplitter



# 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
pc = Pinecone(api_key="pcsk_nPS6S_MLDxFdbMPRtAdeJocvPqLujtFTJx2aKX5y1yndBktFf37cfNW6atk398kBPxFVb")
index = pc.Index("website-chatbot")
# namespace = 'foundation-in-science'


# List of URLs to scrape
urls = [
    # 'https://www.nottingham.edu.my/ugstudy/course/foundation-in-engineering',
    # 'https://www.nottingham.edu.my/ugstudy/course/foundation-in-arts-and-education'
    'https://www.nottingham.edu.my/ugstudy/course/foundation-in-business-and-management'
    # 'https://www.nottingham.edu.my/ugstudy/course/foundation-in-science'
    
]

def extract_info(url):
    # Send a GET request to the webpage
    response = requests.get(url)
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove script, style, and link tags
    for script_or_style in soup(['script', 'style', 'title', 'a', 'header', 'footer', 'nav', 'head', 'meta', 'link']):
        script_or_style.decompose()
        
    elements = soup.find_all(['p', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th'])
    
    content = []
    for element in elements:
        # Exclude navigation, footers, or irrelevant sections if they have identifiable classes or IDs
        if not element.get('class') or ('nav' not in element.get('class') and 'footer' not in element.get('class')):
            content.append(element.get_text(strip=True))

    # Join the content into a single string
    full_content = ' '.join(content)
    print(full_content)
    
    return full_content


def extract_info_by_class(url, target_class):
    # Send a GET request to the webpage
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove unnecessary tags globally
    for tag in soup(['script', 'style', 'title', 'a', 'header', 'footer', 'nav', 'head', 'meta', 'link']):
        tag.decompose()
        
    # Locate the section with the specified class
    target_section = soup.find('div', class_=target_class)
    if not target_section:
        print(f"Section with class '{target_class}' not found.")
        return ""
    
    # Extract relevant tags within the target section
    content = []
    for element in target_section.find_all(['p', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th']):
        text = element.get_text(strip=True)
        if text:  # Include only non-empty text
            content.append(text)
    
    # Join all text with line breaks for clarity
    full_content = ' '.join(content)
    print(full_content)
    
    return full_content



def chunk_text(text, chunk_size=500, overlap=50):
    text_splitter = CharacterTextSplitter(separator=" ", chunk_size=chunk_size, chunk_overlap=overlap)
    
    # Split the text into chunks
    chunks = text_splitter.split_text(text)
    
    # chunks = []
    # start = 0
    # while start < len(text):
    #     end = min(start + chunk_size, len(text))
    #     chunks.append(text[start:end])
    #     start += chunk_size - overlap
    
    return chunks

def generate_embedding(text):
    response = ollama.embeddings(model='nomic-embed-text', 
                                prompt= text)
    embedding = response['embedding']
    return embedding

    
namespace_mapping = {
    ("arts", "education", "foundation"): "foundation-in-arts-and-education",
    ("science", "foundation"): "foundation-in-science",
    ("business", "management", "foundation"): "foundation-in-business-and-management",
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
    vectors = []
    
    for url in urls:
        # Step 1: Scrape the content from the URL
        content = extract_info(url)
        # content = extract_info_by_class(url, 'Coursestyled__CourseStyled-sc-1twdnvy-0 jLxhcF')
        
        # Step 2: Chunk the content
        chunks = chunk_text(content)
        
        # Step 3: Embed and store each chunk's vector
        for i, chunk in enumerate(chunks):
            embedding = generate_embedding(chunk)  # Generate the embedding for the chunk
            
            # Append the chunk's data to the vectors list
            vectors.append({
                'id': f"chunk_{i}",  # Unique ID for each chunk
                'values': embedding,  # Embedding values
                'metadata': {
                    'chunk_id': i,      # The chunk ID
                    'text': chunk       # The actual chunk of text
                }
            })
            
    index.upsert(vectors=vectors, namespace=namespace)
            




"""To run"""

# process_and_store(urls, 'foundation-in-business-and-management')