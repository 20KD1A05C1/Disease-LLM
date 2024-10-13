import requests
import streamlit as st

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_API_ENDPOINT = st.secrets["GROQ_API_ENDPOINT"]

def generate_cypher_query(user_input):
    try:
        response = requests.post(
            GROQ_API_ENDPOINT,
            headers={'Authorization': f'Bearer {GROQ_API_KEY}'},
            json={'prompt': f"Generate a Cypher query for symptoms: {user_input}"}
        )
        response_data = response.json()
        cypher_query = response_data.get('cypher_query')
        
        # Add a check and log the response if the query is empty
        if not cypher_query:
            st.write("Groq API response:", response_data)
            st.error("The generated Cypher query is empty.")
        
        return cypher_query
    except Exception as e:
        st.error(f"Error generating Cypher query: {e}")
        return None


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
