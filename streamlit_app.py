import streamlit as st
import requests
from neo4j import GraphDatabase

class Neo4jDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        if self.driver:
            self.driver.close()

    def run_query(self, query):
        with self.driver.session() as session:
            result = session.run(query)
            return [{"disease": record["disease"], "medicines": record["medicines"]} for record in result]

# Neo4j credentials from Streamlit secrets
uri = st.secrets["neo4j"]["uri"]
username = st.secrets["neo4j"]["username"]
password = st.secrets["neo4j"]["password"]

# Initialize the Neo4j connection
db = Neo4jDatabase(uri, username, password)



# Hugging Face API setup
HF_API_KEY = st.secrets["hf_api"]["api_key"]
HF_API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}"
}

def query_huggingface(payload):
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.json()

# Function to send a question to Hugging Face LLM and retrieve the structured query (Cypher)
def get_query_from_llm(question):
    payload = {"inputs": question}
    llm_response = query_huggingface(payload)
    
    # Extract the Cypher query from the response
    query = llm_response.get('generated_text', None)
    
    return query



# Function to handle the full pipeline: LLM -> Cypher -> Neo4j -> Answer
def get_disease_from_symptoms(question):
    # Step 1: Convert the question to a Cypher query
    cypher_query = get_query_from_llm(question)
    
    if cypher_query:
        # Step 2: Run the Cypher query on Neo4j
        results = db.run_query(cypher_query)
        
        # Step 3: Format the response for the user
        if results:
            response = f"Based on your symptoms, you may have the following disease(s):\n"
            for result in results:
                response += f"Disease: {result['disease']}, Medicines: {', '.join(result['medicines'])}\n"
            return response
        else:
            return "No disease found for the given symptoms."
    else:
        return "Unable to process your query."









# Streamlit App Layout
st.title("Disease Ontology Application")

# Store previous questions in session state
if "history" not in st.session_state:
    st.session_state.history = []

# User input for a question (symptoms)
user_input = st.text_input("Enter your symptoms as a question:")

if st.button("Submit"):
    if user_input:
        # Process the user's question through the full pipeline
        answer = get_disease_from_symptoms(user_input)
        
        # Update history
        st.session_state.history.append({"question": user_input, "answer": answer})
        
        # Display the answer
        st.write(f"Answer: {answer}")
    else:
        st.write("Please enter a question.")

# Display previous questions and answers
st.write("Previous questions:")
for item in st.session_state.history:
    st.write(f"Q: {item['question']}")
    st.write(f"A: {item['answer']}")
