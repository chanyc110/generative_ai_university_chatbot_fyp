import os
from fastapi import FastAPI
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.llms import Ollama # Assumes you have a compatible Ollama client
from fastapi.middleware.cors import CORSMiddleware
from database_v2 import*
from chatbot_functions import*
from openai import OpenAI
from langchain.chat_models import ChatOpenAI
from typing import Optional, Dict

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
    user_features: Optional[Dict[str, str]] = None

# Model configuration and prompt template
model = os.environ.get("MODEL", "llama3.2")
# llm = Ollama(model=model)
llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv('OPENAI_API_KEY'))

template_test = """
You are a helpful assistant at the University of Nottingham Malaysia(UNM), that answers inquiries from prospective students. 
You should never talk about any other company/website/resources/books/tools or any product which is not related to Univeristy of Nottingham Malaysia.
Use the context provided to answer the user's question. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:{context}
User Query:{user_query}
Answer: 

If the following sources contain relevant links to more information, include them in your response:

Sources:
{sources}
"""

prompt_template = PromptTemplate(input_variables=["context", "user_query", "sources"], template=template_test)
llm_chain = LLMChain(llm=llm, prompt=prompt_template)


@app.post("/chat")
async def chat(query: QueryRequest):
    intent = classify_user_intent(query.user_query)

    if intent == "recommendation":
        recommendation_result = recommend_courses(query.user_query, query.user_features)
        return {
            "courses": recommendation_result.get("courses", []),
            "response": recommendation_result["response"],
            "feature_selection": recommendation_result.get("feature_selection")  # will be present if user_features is None
        }
    else:
        # Default: Answer specific course queries using RAG
        search_result = search_similar_vectors(query.user_query)
        response_text = llm_chain.run(context=search_result["response_text"], user_query=query.user_query, sources=search_result["sources"])

        return {"response": response_text}
