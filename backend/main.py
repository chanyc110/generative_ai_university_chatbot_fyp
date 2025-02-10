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
# llm = Ollama(model=model)
llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv('OPENAI_API_KEY'))

template_test = """
You are a helpful assistant at the University of Nottingham Malaysia(UNM), that answers inquiries from prospective students. 
You should never talk about any other company/website/resources/books/tools or any product which is not related to Univeristy of Nottingham Malaysia.
Use the context provided to answer the user's question. 
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:{context}
User Query:{user_query}
Answer: """

prompt_template = PromptTemplate(input_variables=["context", "user_query"], template=template_test)
llm_chain = LLMChain(llm=llm, prompt=prompt_template)


@app.post("/chat")
async def chat(query: QueryRequest):
    intent = classify_user_intent(query.user_query)

    if intent == "recommendation":
        recommendation_result = recommend_courses(query.user_query)
        return {"courses": recommendation_result["courses"], "response": recommendation_result["response"]}

    # elif intent == "course_comparison":
    #     comparison_result = compare_courses(query.user_query)
    #     return {"response": comparison_result}

    else:
        # Default: Answer specific course queries using RAG
        context = search_similar_vectors(query.user_query)
        response = llm_chain.run(context=context, user_query=query.user_query)
        return {"response": response}
