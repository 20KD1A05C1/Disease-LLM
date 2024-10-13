import streamlit as st
from neo4j import GraphDatabase
import groq
import re

# Initialize Groq client
groq_api_key = st.secrets["GROQ_API_KEY"]
client = groq.Client(api_key=groq_api_key)

# Initialize Neo4j connection
neo4j_uri = st.secrets["NEO4J_URI"]
neo4j_user = st.secrets["NEO4J_USER"]
neo4j_password = st.secrets["NEO4J_PASSWORD"]

def get_neo4j_driver():
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        # Verify the connection
        with driver.session() as session:
            session.run("RETURN 1")
        return driver
    except Exception as e:
        st.error(f"Failed to connect to Neo4j: {str(e)}")
        return None

driver = get_neo4j_driver()

def generate_cypher_query(symptoms):
    try:
        prompt = f"""Generate a Cypher query to find diseases INDICATES by the following symptoms: {symptoms}
        The query should:
        1. Match nodes labeled as 'symptom' that match the given symptoms
        2. Find 'disease' nodes that are connected to these symptoms
        3. Return the disease names and their related symptoms
        4. Limit the results to 5 diseases

        Respond ONLY with the Cypher query, no explanations or additional text."""

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates Cypher queries for Neo4j. Respond only with the query, no additional text."},
                {"role": "user", "content": prompt}
            ],
            model="mixtral-8x7b-32768",
            max_tokens=200
        )
        
        # Extract the Cypher query from the response
        query = response.choices[0].message.content.strip()
        st.write(f"Debug - Generated Query: {cypher_query}")
        
        # Basic validation: check if the query starts with a valid Cypher keyword
        valid_start_keywords = ['MATCH', 'CALL', 'CREATE', 'MERGE']
        if not any(query.upper().startswith(keyword) for keyword in valid_start_keywords):
            raise ValueError("Generated query does not appear to be valid Cypher")
        
        return query
    except Exception as e:
        st.error(f"Error generating Cypher query: {str(e)}")
        return None

def query_neo4j(cypher_query):
    if driver is None:
        return []
    try:
        with driver.session() as session:
            result = session.run(cypher_query)
            return [record for record in result]
    except Exception as e:
        st.error(f"Error querying Neo4j: {str(e)}")
        return []

def formulate_answer(question, database_result):
    try:
        prompt = f"""Question: {question}
        Database result: {database_result}
        Please formulate a helpful answer based on this information. If no results were found, suggest that the user try rephrasing their symptoms or consult a medical professional."""
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant. Provide informative answers based on the given database results."},
                {"role": "user", "content": prompt}
            ],
            model="mixtral-8x7b-32768",
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error formulating answer: {str(e)}")
        return "I'm sorry, but I couldn't process your request at this time. Please try again later."

st.title("Medical Symptom Checker")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What symptoms are you experiencing?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate Cypher query
    cypher_query = generate_cypher_query(prompt)

    if cypher_query:
        # Query Neo4j database
        db_result = query_neo4j(cypher_query)

        # Formulate answer
        answer = formulate_answer(prompt, db_result)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(answer)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": answer})
    else:
        st.error("Unable to process your request at this time. Please try again later.")

# Close Neo4j connection when the app is done
if driver:
    driver.close()
