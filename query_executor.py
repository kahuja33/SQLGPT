from openai import OpenAI
from dotenv import load_dotenv
import os
from mydb import execute_query, get_schema
import pandas as pd

load_dotenv()

client = OpenAI()

schema = get_schema("order")
print("=" * 80)
print("TABLE SCHEMA")
print("=" * 80)
print(schema)
print()

def clean_sql_response(response_str: str) -> str:
    cleaned = response_str.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("\n", 1)[0]
    return cleaned.strip()

while True:
    user_input = input("Ask away: ")
    if user_input.lower() in ['exit', 'quit']:
        print("Exiting the program.")
        break

    question = user_input
    final_prompt = f"""Generate a postgresql query based on this {schema} and this question: {question}

IMPORTANT: Always use 'public.order' (with schema prefix) instead of just 'order' to avoid reserved keyword issues."""
    responses = client.responses.create(model='gpt-5.6-sol', input=final_prompt)
    response_output_text = clean_sql_response(responses.output_text)

    print()
    print("=" * 80)
    print("GENERATED QUERY")
    print("=" * 80)
    print(response_output_text)
    print()

    try:
        print("=" * 80)
        print("QUERY RESULTS")
        print("=" * 80)
        result_df = execute_query(response_output_text)

        if len(result_df) == 0:
            print("No results returned.")
        else:
            print(result_df.to_string(index=False))
            print()
            print(f"Total rows: {len(result_df)}")

    except Exception as e:
        print(f"ERROR executing query: {str(e)}")
        print("Please check your query and try again.")

    print()
