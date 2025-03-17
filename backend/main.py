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
    session_id: str
    user_query: str
    user_features: Optional[Dict[str, str]] = None

# Model configuration and prompt template
model = os.environ.get("MODEL", "llama3.2")
# llm = Ollama(model=model)
llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv('OPENAI_API_KEY'))

template_test = """
You are a helpful assistant at the University of Nottingham Malaysia(UNM), that answers inquiries from prospective students. 
You should never talk about any other company/website/resources/books/tools or any product which is not related to Univeristy of Nottingham Malaysia.
Use the provided context and chat history to answer the user's query.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Chat History:
{chat_history}

Context:
{context}

User Query:
{user_query}

User's Sentiment:
The user's current sentiment is **{sentiment}**.

Your responses should be tailored to the user's sentiment:
- If the sentiment is **positive**, match their enthusiasm while keeping responses professional.
- If the sentiment is **negative**, respond with empathy and reassurance.

Answer:
If the following sources contain relevant links to more information, include them in your response:

Sources:
{sources}
"""

prompt_template = PromptTemplate(input_variables=["chat_history","context", "user_query", "sources", "sentiment"], template=template_test)
llm_chain = LLMChain(llm=llm, prompt=prompt_template)


@app.post("/chat")
async def chat(query: QueryRequest):
    
    session_id = query.session_id
    print(f"🚀 Backend received session_id: {session_id}")
    
    # Retrieve chat history
    chat_history = retrieve_memory(session_id)
    
    # Analyze sentiment
    sentiment = analyze_sentiment(query.user_query)
    print(f"Detected Sentiment: {sentiment}")
    
    # Store sentiment in session history
    update_sentiment(session_id, sentiment)
    
    # Count the number of negative/very negative messages
    negative_count = sum(1 for s in user_sentiment_history[session_id] if s in ["negative"])
    
    # If user has sent 2 or more negative messages, provide human support
    if negative_count >= 2:
        contact_info = (
            "😞 I'm really sorry that you're having a frustrating experience. "
            "I want to make sure you get the help you need. You can reach out to our support team:\n\n"
            "**📧 Email:** support@nottingham.edu.my\n"
            "**📞 Phone:** +60 3-8924 8000\n"
            "**⏳ Office Hours:** Mon-Fri, 9 AM - 5 PM (MYT)\n\n"
            "Please feel free to contact them directly, and they'll assist you as soon as possible."
        )
        update_memory(session_id, query.user_query, contact_info)
        
        # Reset sentiment history after sending human assistance message
        user_sentiment_history[session_id] = []
        
        return {"response": contact_info}
    
    if query.user_features:
        intent = "recommendation"
    else:
        intent = classify_user_intent(query.user_query)
    
    
    print(f"User Intent: {intent}")

    if intent == "recommendation":
        recommendation_result = recommend_courses(query.user_query, query.user_features)
        chatbot_response = recommendation_result["response"]
        update_memory(session_id, query.user_query, chatbot_response)
        return {
            "courses": recommendation_result.get("courses", []),
            "response": recommendation_result["response"],
            "feature_selection": recommendation_result.get("feature_selection")  # will be present if user_features is None
        }
    else:
        # Default: Answer specific course queries using RAG
        search_result = search_similar_vectors(query.user_query, chat_history)
        print(search_result)
        
        # If no relevant namespace was found, return early
        if not search_result["sources"] and search_result["response_text"]:
            print("No relevant namespace found. Generating LLM response dynamically.")
            dynamic_template = """
            You are a helpful assistant for the University of Nottingham Malaysia (UNM).
            
            The user's query did not match any specific information in the database. However, respond appropriately based on sentiment.
            You should never talk about any other company/website/resources/books/tools or any product which is not related to Univeristy of Nottingham Malaysia.

            ### User's Sentiment:
            The user's sentiment is classified as **{sentiment}**.

            #### Response Guidelines:
            - **Positive Sentiment:** Acknowledge enthusiasm and encourage them to ask more questions.
            - **Negative Sentiment:** Respond with empathy, acknowledge frustration, and guide them to help.

            ### User Query:
            {user_query}

            ### Answer:
            """
            chatbot_response = llm_chain.run(chat_history=chat_history,user_query=query.user_query,sentiment=sentiment,template=dynamic_template)
            update_memory(session_id, query.user_query, chatbot_response)
            return {"response": chatbot_response}
        
        
        response_text = llm_chain.run(chat_history=chat_history, context=search_result["response_text"], user_query=query.user_query, sources=search_result["sources"], sentiment=sentiment)

        # Store the response in memory
        update_memory(session_id, query.user_query, response_text)
        
        return {"response": response_text}
