from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

'''
my_key=os.getenv('OPENAI_API_KEY')
print(f"my_key: {my_key}")'''
'''client=OpenAI(api_key=my_key)'''

client=OpenAI()

responses=client.responses.create(model='gpt-5.6-sol',input="tell me about genai in 20 words")

print(responses.output_text)