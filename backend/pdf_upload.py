import streamlit as st
from io import BytesIO
from llama_parse import LlamaParse
from langchain.text_splitter import CharacterTextSplitter
import ollama
from pinecone.grpc import PineconeGRPC as Pinecone
from openai import OpenAI
from dotenv import load_dotenv
import os 

# Load the .env file
load_dotenv()

# Initialize your parser, Pinecone index, and embedding client
parser = LlamaParse(
    api_key = os.getenv('LLAMA_PARSE_API_KEY'),
    result_type = "text"
)

client = OpenAI(
    api_key= os.getenv('OPENAI_API_KEY')
)


pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index("website-chatbot") 



# Function to chunk text
def chunk_text(text, chunk_size=300, overlap=100):
    text_splitter = CharacterTextSplitter(separator=" ", chunk_size=chunk_size, chunk_overlap=overlap)
    chunks = text_splitter.split_text(text)
    return chunks

# Function to generate embeddings
def generate_embedding(text):
    # response = ollama.embeddings(model='nomic-embed-text', prompt=text)
    # embedding = response['embedding']
    
    response = client.embeddings.create(
        model="text-embedding-ada-002",  # Use the OpenAI text-embedding-ada-002 model
        input=text,
        encoding_format="float"
    )
    
    # Extract the embedding from the response
    embedding = response.data[0].embedding
    return embedding

# Function to process file with LlamaParse and upsert chunks to Pinecone
def extract_info_by_ocr(file: BytesIO, namespace):
    vectors = []
    file_bytes = file.read()
    
    # Extract text from the PDF file using LlamaParse OCR
    documents = parser.load_data(file_bytes, extra_info={"file_name": file.name})
    text = " ".join([doc.text for doc in documents])
    
    # Split the text into chunks
    chunks = chunk_text(text)
    
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
    
    # Upsert all chunks into Pinecone
    index.upsert(vectors=vectors, namespace=namespace)

# Streamlit app
st.title("PDF to Vector Embedding and Upsert App")

# File upload
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file is not None:
    namespace = st.text_input("Enter a namespace for Pinecone upsert:", value="default_namespace")
    
    if st.button("Process PDF"):
        with st.spinner("Processing..."):
            extract_info_by_ocr(uploaded_file, namespace)
        st.success("File processed and vectors upserted to Pinecone!")
