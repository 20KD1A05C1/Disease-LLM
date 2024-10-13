import streamlit as st
from neo4j import GraphDatabase
import groq

# Initialize Groq client
groq_api_key = st.secrets["GROQ_API_KEY"]
client = groq.Client(api_key=groq_api_key)

# Initialize Neo4j connection
neo4j_uri = st.secrets["NEO4J_URI"]
neo4j_user = st.secrets["NEO4J_USER"]
neo4j_password = st.secrets["NEO4J_PASSWORD"]

# Neo4j schema information
neo4j_schema = """
Nodes:
1. Symptom
2. Disease
3. Medicine

Relationships:
1. (Symptom)-[INDICATES]->(Disease)
2. (Disease)-[TREATED_BY]->(Medicine)
"""

def get_neo4j_driver():
    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        # Verify the connection
        with driver.session() as session:
            session.run("RETURN 1")
        return driver
    except Exception as e:
        #st.write("eeror1 teja")
        st.error(f"Failed to connect to Neo4j: {str(e)}")
        return None

driver = get_neo4j_driver()

def generate_cypher_query(symptoms):
    try:
        prompt = f"""Given the following Neo4j database schema:

{neo4j_schema}

Generate a Cypher query to find diseases and their treatments related to the following symptoms: {symptoms}

The query should:
1. Match nodes labeled as 'Symptom' that match the given symptoms
2. Find 'Disease' nodes that are connected to these symptoms via the 'INDICATES' relationship
3. Find 'Medicine' nodes that are connected to the diseases via the 'TREATED_BY' relationship
4. Return the disease names, their related symptoms, and recommended medicines
5. Limit the results to 5 diseases

Respond ONLY with the Cypher query, no explanations or additional text."""

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates Cypher queries for Neo4j. Respond only with the query, no additional text."},
                {"role": "user", "content": prompt}
            ],
            model="mixtral-8x7b-32768",
            max_tokens=300
        )
        
        # Extract the Cypher query from the response
        query = response.choices[0].message.content.strip()
        #st.write(query)
        # Basic validation: check if the query starts with a valid Cypher keyword
        valid_start_keywords = ['MATCH', 'CALL', 'CREATE', 'MERGE']
        #if not any(query.upper().startswith(keyword) for keyword in valid_start_keywords):
            #raise ValueError("Generated query does not appear to be valid Cypher")
        
        return query
    except Exception as e:
        st.write("eeror2 teja")
        st.error(f"Error generating Cypher query: {str(e)}")
        return None

def query_neo4j(query):
    if not query:
        st.error("The provided query is empty. Please check the input.")
        return []
    
    if driver is None:
        st.error("Neo4j driver is not initialized. Please ensure the connection is set up correctly.")
        return []

    try:
        with driver.session() as session:
            result = session.run(query)
            data = [record.data() for record in result]
            if not data:
                st.warning("No data returned for the provided query.")
            return data
    except Exception as e:
        st.error(f"Error querying Neo4j: {str(e)}")
        st.write("Error details:")
        st.write(f"Query: {query}")
        return []

def formulate_answer(question, database_result):
    try:
        prompt = f"""Question: {question}
        Database result: {database_result}
        Please formulate a helpful answer based on this information. Include the following in your response:
        1. The diseases that match the symptoms
        2. A brief explanation of how the symptoms relate to each disease
        3. Recommended medicines for each disease
        If no results were found, suggest that the user try rephrasing their symptoms or consult a medical professional.
        
        Important: Always include a disclaimer that this information is for educational purposes only and should not replace professional medical advice."""
        
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful medical assistant. Provide informative answers based on the given database results."},
                {"role": "user", "content": prompt}
            ],
            model="mixtral-8x7b-32768",
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.write("eeror4 teja")
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
    cypher_query = generate_cypher_query(prompt).strip()
    #st.write(f"Debug - Generated Query 1: {cypher_query}")

    if cypher_query:
        # Display the generated query (for debugging)
        #st.write(f"Debug - Generated Query: {cypher_query}")
        

        # Query Neo4j database
        db_result = query_neo4j(cypher_query.strip())

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

