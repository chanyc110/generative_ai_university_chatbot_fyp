from openai import OpenAI
from dotenv import load_dotenv
from pinecone import Pinecone
import os
import pandas as pd
import joblib

# Load environment variables
load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("website-chatbot")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load the pre-trained model (assumed to be saved already)
model_path = "C:\\Users\\PC 5\\Desktop\\fyp_new_version\\course_recommendation_model.pkl"
optimized_model = joblib.load(model_path)
print("Model loaded successfully!")


# GPT-based namespace selection
def determine_namespaces_with_gpt(user_query):
    # Define available namespaces with descriptions
    available_namespaces = {
        "nottingham-foundation-programme": "Foundation program details including entry requirements for foundation-level students. The Nottingham Foundation Programme is a pre-university course designed to prepare students for undergraduate studies at the University of Nottingham Malaysia. It provides foundational knowledge across various disciplines, allowing students to develop academic and subject-specific skills. Students must meet specific entry requirements for their chosen undergraduate program. ",
        "computer-science-bsc-hons": "Undergraduate computer science program details, including entry requirements, course structure, and modules.",
        "computer-science-with-artificial-intelligence-bsc-hons": "Undergraduate AI-focused computer science program details, including entry requirements, course structure, and modules.",
        "computer-science-mphil-phd": "Postgraduate computer science research program details.",
        "Foundation-undergraduate-scholarships": "Information about foundation and undergraduate scholarships available at the university.",
        "contact-information": "Only has contact information of the university (email, phone numbers), campus location, and office hours.",
        "campus-facilities": "Information about the facilities available on campus, including sports facilities, health services, prayer rooms, and amenities."
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

    context = []
    sources = set()

    for match in sorted_results:
        content = match["metadata"].get("content", "")
        source_url = match["metadata"].get("source_url", "")

        if source_url:
            sources.add(source_url)

        context.append(content)

    response_text = "\n".join(context)

    # Format sources into clickable links
    source_links = "\n".join([f"- [More Info]({url})" for url in sources])

    return {
        "response_text": response_text,
        "sources": source_links
    }


def recommend_courses(user_query, user_features=None):
    
    # If user_features are not provided, return feature selection options
    if not user_features:
        return {
            "courses": [],
            "response": "To recommend a course, please select your answers below:",
            "feature_selection": {
                "MathsAptitude": ["low", "medium", "high"],
                "Interest": ["General computer science", "AI", "research and advanced studies"],
                "HighestQualification": ["high school", "college", "diploma", "degree"],
                "ComputerScienceRelated": ["Yes", "No", "N/A"]
            }
        }
    
    # Otherwise, predict the course using the pre-trained model.
    # Make sure the keys match your training feature names exactly.
    user_df = pd.DataFrame([user_features])
    predicted_course = optimized_model.predict(user_df)[0]
    predicted_probabilities = optimized_model.predict_proba(user_df)[0]
    classes = optimized_model.named_steps['classifier'].classes_
    
    # Build a response string showing probabilities
    response_text = f"Based on your selections, the recommended course is **{predicted_course}**.\n\n"
    response_text += "Confidence levels:\n"
    
    courses = []
    for course, prob in zip(classes, predicted_probabilities):
        response_text += f"- {course}: {prob * 100:.2f}%\n"
        courses.append({"course": course, "probability": round(prob * 100, 2)})
    
    return {"courses": courses, "response": response_text}









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
