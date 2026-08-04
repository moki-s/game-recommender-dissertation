import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def get_driver():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return driver


def test_connection():
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 AS number")
            record = result.single()
            print("connection worked - neo4j returned:", record["number"])
    except Exception as error:
        print("connection failed:", error)
    finally:
        driver.close()


if __name__ == "__main__":
    test_connection()
