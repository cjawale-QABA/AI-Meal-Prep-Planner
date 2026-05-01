import os
from dotenv import load_dotenv
from google import genai
from prompts import system_prompt

user_data = {
   "ethnicity":"Asian",
   "allergies":"",
   "meat_pref":"Vegetarian",
   "spicy_level":3,
   "cooking_level":"Beginner",
   "equipment":[
      "air fryer",
      "convection oven"
   ],
   "kcal":1800,
   "protein":100,
   "days":1,
   "meals_per_day":2,
   "people":1,
   "max_dishes":1,
   "store":"Colruyt"
} 

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=user_data.__repr__(),
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0,
            ),
        )
print("Response text:", response.text)