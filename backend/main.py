import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import Ollama # Assumes you have a compatible Ollama client
from fastapi.middleware.cors import CORSMiddleware
from database import*
from database import namespace

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust this to match your frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    user_query: str

# Model configuration and prompt template
model = os.environ.get("MODEL", "llama3.2")
llm = Ollama(model=model)

template_test = """
You are a helpful assistant. 
Use the context provided to answer the user's question. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
Context:{context}
User Query:{user_query}"""

prompt_template = PromptTemplate(input_variables=["context", "user_query"], template=template_test)
llm_chain = LLMChain(llm=llm, prompt=prompt_template)


@app.post("/chat")
async def chat(query: QueryRequest):
    context = search_similar_vectors(query.user_query, namespace=namespace)
    print("Context:", context)
    response = llm_chain.run(context=context, user_query=query.user_query)
    return {"response": response}
