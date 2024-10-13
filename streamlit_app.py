import streamlit as st
from neo4j_utils import query_neo4j
from llm_utils import generate_cypher_query, format_answer

# Streamlit App
st.title("Symptom-based Disease Query Chatbot")

# User Input
user_input = st.text_input("Describe your symptoms:")

if st.button("Submit"):
    if user_input:
        st.write("Processing your input...")

        # Step 1: Generate Cypher query using LLM (Groq API)
        cypher_query = generate_cypher_query(user_input)
        st.write("Generated Cypher Query:", cypher_query)

        # Step 2: Query the Neo4j database
        disease_data = query_neo4j(cypher_query)

        # Step 3: Formulate a well-structured answer using LLM (Groq API)
        final_answer = format_answer(user_input, disease_data)

        # Display the answer
        st.write("**Answer:**", final_answer)
    else:
        st.write("Please enter symptoms to proceed.")
