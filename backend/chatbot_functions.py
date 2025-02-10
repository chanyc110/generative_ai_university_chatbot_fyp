from openai import OpenAI
from dotenv import load_dotenv
from pinecone import Pinecone
import os

# Load environment variables
load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("website-chatbot")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




# GPT-based namespace selection
def determine_namespaces_with_gpt(user_query):
    # Define available namespaces with descriptions
    available_namespaces = {
        "nottingham-foundation-programme": "Foundation program details including entry requirements for foundation-level students. The Nottingham Foundation Programme is a pre-university course designed to prepare students for undergraduate studies at the University of Nottingham Malaysia. It provides foundational knowledge across various disciplines, allowing students to develop academic and subject-specific skills. Students must meet specific entry requirements for their chosen undergraduate program. ",
        "computer-science-bsc-hons": "Undergraduate computer science program details, including entry requirements, course structure, and modules.",
        "computer-science-with-artificial-intelligence-bsc-hons": "Undergraduate AI-focused computer science program details, including entry requirements, course structure, and modules.",
        "computer-science-mphil-phd": "Postgraduate computer science research program details.",
        "Foundation-undergraduate-scholarships": "Information about foundation and undergraduate scholarships available at the university."
    }

    system_prompt = (
        "You are an AI classifier that determines the most relevant namespace(s) based on the user's query. "
        "Each namespace represents a category of information about university courses. Select the correct namespaces based on the query's intent.\n"
        "Here is a list of available namespaces and what they contain:\n\n"
    )

    for namespace, description in available_namespaces.items():
        system_prompt += f"Namespace: {namespace}\nDescription: {description}\n\n"

    system_prompt += (
        "Choose one or more namespaces that best match the user's query. "
        "Return only the namespace names, separated by commas (e.g., 'computer-science-bsc-hons, computer-science-with-artificial-intelligence-bsc-hons'). "
        "Do NOT include any explanations or extra words—just return the namespace names."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User query: {user_query}"}
        ],
        temperature=0
    )

    selected_namespaces = response.choices[0].message.content.strip().split(", ")
    valid_namespaces = [ns for ns in selected_namespaces if ns in available_namespaces]

    if valid_namespaces:
        print(f"Selected namespaces: {valid_namespaces}")
        return valid_namespaces
    else:
        print("GPT returned invalid namespaces. Defaulting to general query.")
    



# Query Pinecone based on selected namespaces
def search_similar_vectors(user_query):
    namespaces = determine_namespaces_with_gpt(user_query)
    
    if not namespaces:
        return "Sorry, I couldn't determine the relevant section. Can you clarify your query?"

    query_embedding = client.embeddings.create(
        input=user_query,
        model="text-embedding-3-small"  # Specify the embedding model
    ).data[0].embedding
    
    results = []

    for namespace in namespaces:
        res = index.query(vector=query_embedding, top_k=3, include_metadata=True, namespace=namespace)
        results.extend(res["matches"])

    # Sort results by similarity score
    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)[:3]
    context = "\n".join([match["metadata"].get("content", "") for match in sorted_results])

    return context


def recommend_courses(user_query):
    
    course_names= determine_namespaces_with_gpt(user_query) # list of recommended courses
    
    if not course_names:
        return {"courses": [], "response": "I'm not sure which courses fit your interests. Can you provide more details?"}

    context = search_similar_vectors(user_query)
    
    if not context:
        return {"courses": [], "response": "I couldn't find any relevant courses. Please refine your interests."}
    
    
    recommendation_prompt = (
        "You are an AI assistant that provides personalized course recommendations. "
        "Based on the user's interests, explain why the following courses are suitable for them.\n\n"
        f"Relevant Course Information:\n{context}\n\n"
        "Explain why these courses match the user's query. Provide a brief structured, engaging, and personalized response."
    )
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": recommendation_prompt},
            {"role": "user", "content": f"User query: {user_query}"}
        ],
        temperature=0
    )

    explanation = response.choices[0].message.content.strip()

    # Step 5: Return response with recommended courses and explanation
    return {
        "courses": course_names,
        "response": explanation
    }





# def compare_courses(user_query):
    
#     course_names = determine_namespaces_with_gpt(user_query)
    
#     if not course_names:
#         return {"courses": [], "response": "I'm not sure which courses fit your interests. Can you provide more details?"}

#     context = search_similar_vectors(user_query)
    
#     if not context:
#         return {"courses": [], "response": "I couldn't find any relevant courses. Please refine your interests."}
    
    




def classify_user_intent(user_query):
    system_prompt = (
        "You are an AI assistant that classifies user intent for a university chatbot. "
        "Decide if the query is:\n"
        "- 'course_info' if the user is asking about details of a specific course or the query is a FAQ.\n"
        "- 'course_comparison' if the user is comparing two or more courses.\n"
        "- 'recommendation' if the user is looking for course suggestions based on their interests.\n"
        "Return only 'course_info', 'course_comparison', or 'recommendation' as the response."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User query: {user_query}"}
        ],
        temperature=0
    )

    intent = response.choices[0].message.content.strip().lower()
    
    if intent in ["course_info", "recommendation"]:
        print(intent)
        return intent
    else:
        return "course_info"  # Default
