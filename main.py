from openai import OpenAI
from dotenv import load_dotenv
import os
from mydb import execute_query, get_schema

load_dotenv()  # Load environment variables from .env file


'''
my_key=os.getenv('OPENAI_API_KEY')
print(f"my_key: {my_key}")'''
'''client=OpenAI(api_key=my_key)'''

client=OpenAI()

schema=get_schema("order")
print(schema)

def clean_sql_response(response_str: str) -> str:
    cleaned = response_str.strip()
    if cleaned.startswith("```"):
        # Remove opening ```sql or ```
        cleaned = cleaned.split("\n", 1)[-1]
    if cleaned.endswith("```"):
        # Remove closing ```
        cleaned = cleaned.rsplit("\n", 1)[0]
    return cleaned.strip()

while True:
    user_input = input("Ask away: ")
    if user_input.lower() in ['exit', 'quit']:
        print("Exiting the program.")
        break    

    question=user_input   
    final_prompt=f"""Generate a postgresql query based on this {schema} and this question: {question}"""
    responses=client.responses.create(model='gpt-5.6-sol',input=final_prompt)
    response_output_text=clean_sql_response(responses.output_text)
    print("Response:", response_output_text)
    print()