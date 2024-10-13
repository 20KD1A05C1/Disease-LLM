import streamlit as st
from neo4j import GraphDatabase
import requests
import json

# Neo4j connection setup
class Neo4jDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        if self.driver:
            self.driver.close()

    def run_cypher_query(self, query):
        # Run a given Cypher query and return results
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

# LLM function to generate Cypher query from the user's question
def get_query_from_llm(question):
    # Make a request to the Hugging Face API with the provided question
    headers = {
        "Authorization": f"Bearer {st.secrets["hf_api"]["hf_api_key"]}"
    }
    payload = {
        "inputs": question,
        "options": {"wait_for_model": True}
    }
    response = requests.post(
        "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
        headers=headers,
        json=payload
    )

    # Check if the response was successful
    if response.status_code == 200:
        llm_response = response.json()
        # Check if 'generated_text' is in the response
        if isinstance(llm_response, list) and len(llm_response) > 0:
            query = llm_response[0].get('generated_text', None)
        else:
            st.error("Unexpected response format from the LLM API.")
            query = None
    else:
        st.error(f"LLM API request failed with status code {response.status_code}")
        query = None
    
    return query

# Function to get disease information based on symptoms
def get_disease_from_symptoms(user_input):
    cypher_query = get_query_from_llm(user_input)
    if not cypher_query:
        st.error("Failed to generate a Cypher query.")
        return []
    
    st.write(f"Generated Cypher query: `{cypher_query}`")

    # Execute the Cypher query using Neo4j
    return db.run_cypher_query(cypher_query)

# Streamlit app layout
st.title("Disease Ontology: Symptom to Disease Finder")

# Taking Neo4j credentials from Streamlit secrets
uri = st.secrets["neo4j"]["uri"]
username = st.secrets["neo4j"]["username"]
password = st.secrets["neo4j"]["password"]

# Initialize Neo4j connection
db = Neo4jDatabase(uri, username, password)

# User input for questions/symptoms
st.write("Ask questions like 'What disease is indicated by fever and cough?' or 'Which medicines treat malaria?'")
user_input = st.text_input("Enter your question:")

# List to store previous questions and responses
if "previous_questions" not in st.session_state:
    st.session_state["previous_questions"] = []

if st.button("Search"):
    if user_input:
        # Process user input
        st.session_state["previous_questions"].append({"question": user_input, "response": None})
        results = get_disease_from_symptoms(user_input)

        if results:
            # Update the last question with the response
            st.session_state["previous_questions"][-1]["response"] = results
            st.write("Results:")
            for record in results:
                st.write(record)
        else:
            st.write("No results found for the given input.")
    else:
        st.write("Please enter a question or symptoms.")

# Display previous questions and responses
if st.session_state["previous_questions"]:
    st.write("### Previous Questions:")
    for idx, item in enumerate(st.session_state["previous_questions"], start=1):
        st.write(f"**Q{idx}:** {item['question']}")
        if item["response"]:
            for record in item["response"]:
                st.write(record)
        else:
            st.write("No results found.")

# Close the Neo4j connection
db.close()
