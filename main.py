import logging
import streamlit as st
from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import Ollama
from database import*
import os

model = os.environ.get("MODEL", "llama3.2")
llm = Ollama(model=model) 



template_test = """
You are a helpful assistant. 
Use the context provided to answer the user's question. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
Context:{context}
User Query:{user_query}"""

# Define the prompt template for the chatbot
prompt_template = PromptTemplate(input_variables=["context", "user_query"],template=template_test)

# Create an LLMChain with the prompt template
llm_chain = LLMChain(llm=llm, prompt=prompt_template)

# Streamlit UI
st.title("RAG Chatbot Interface")

# User input for the query
user_query = st.text_input("Ask me anything:")

if st.button("Send"):
    if user_query:

        # Step 3: Search for similar vectors and Extract the context
        metadata = search_similar_vectors(user_query, namespace="foundation-engineering")
        context = metadata['text']
        print("Context:", context)

        # Step 4: Generate a response from the LLM using the retrieved context
        response = llm_chain.run(context=context, user_query=user_query)
        
        # Display the response
        st.text_area("Response:", value=response, height=200)
    else:
        st.warning("Please enter a query.")



