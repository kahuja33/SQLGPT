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

while True:
    user_input = input("Ask away: ")
    if user_input.lower() in ['exit', 'quit']:
        print("Exiting the program.")
        break    

    question=user_input   
    final_prompt=f"""Generate a postgresql query based on this {schema} and this question: {question}"""
    responses=client.responses.create(model='gpt-5.6-sol',input=final_prompt)

    print(responses.output_text)
    print()