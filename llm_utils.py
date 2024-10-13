import requests

# Replace with your actual Groq API details
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_API_ENDPOINT = st.secrets["GROQ_API_ENDPOINT"]

def generate_cypher_query(user_input):
    # Call the LLM with the user's input to generate the Cypher query
    response = requests.post(
        GROQ_API_ENDPOINT,
        headers={'Authorization': f'Bearer {GROQ_API_KEY}'},
        json={'prompt': f"Generate a Cypher query for symptoms: {user_input}"}
    )
    cypher_query = response.json().get('cypher_query')
    return cypher_query

def format_answer(user_input, disease_data):
    # Call the LLM to generate a user-friendly response based on the query result
    response = requests.post(
        GROQ_API_ENDPOINT,
        headers={'Authorization': f'Bearer {GROQ_API_KEY}'},
        json={
            'prompt': f"Based on the symptoms: {user_input}, the retrieved data: {disease_data}. Formulate a detailed answer."
        }
    )
    answer = response.json().get('formatted_answer')
    return answer
