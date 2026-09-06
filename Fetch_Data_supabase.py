import os
import requests

# Replace with your actual Supabase Anon Key or load it from an environment variable
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5yZ2twYmpncXd3dmVqd3F5b2pvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg1ODgxNDIsImV4cCI6MjEwNDE2NDE0Mn0.9tiWOtcgLUg07Wu5cGLDsQtLIwWlslpUPXQkrDQUrpw"

url = "https://nrgkpbjgqwwvejwqyojo.supabase.co/rest/v1/order?select=*"




headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
}

try:
  response = requests.get(url, headers=headers)
  # Raise an exception for HTTP error codes (4xx or 5xx)
  response.raise_for_status()

  # Parse the JSON response
  orders = response.json()
  print(f"Successfully fetched {len(orders)} rows:")

  # Print the first few records as an example
  for order in orders[:5]:
    print(order)

except requests.exceptions.RequestException as e:
  print(f"Error fetching data: {e}")