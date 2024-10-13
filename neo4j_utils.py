from neo4j import GraphDatabase
import streamlit as st

# Using secrets for sensitive information
NEO4J_URI = st.secrets["NEO4J_URI"]
NEO4J_USER = st.secrets["NEO4J_USER"]
NEO4J_PASSWORD = st.secrets["NEO4J_PASSWORD"]

def query_neo4j(cypher_query):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run(cypher_query)
        data = result.data()
    driver.close()
    return data
