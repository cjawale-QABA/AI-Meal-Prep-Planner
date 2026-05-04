import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts import system_prompt
from prompts import schema_json

# Load environment variables from .env (if present)
load_dotenv()


def planner(user_input: dict[str, any] = None):
    if user_input is None:
        user_input = {'ethnicity': 'Asian', 'allergies': '', 'meat_pref': 'Vegetarian', 'spicy_level': 3, 'cooking_level': 'Beginner', 'equipment': ['air fryer', 'convection oven', 'induction cooktop', 'instant pot', 'wet grinder'], 'kcal': 1800, 'protein': 100, 'days': 1, 'meals_per_day': 2, 'people': 1, 'max_dishes': 1, 'store': 'Colruyt'}
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    print("Genrating meal plan")
    try:
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0,
            response_schema=schema_json, 
            response_mime_type='application/json'
        )
        # config["response_format"] = {"type": "json", "json_schema": schema_json}
        response = client.models.generate_content(
                model="gemini-flash-latest",
                # model='gemini-3.1-pro-preview',
                contents=str(user_input),
                config=config,
            )
        
        meal_plan = None
        try:
            meal_plan = json.loads(response.text)
            print("Meal Plan:", response.text)
        except:
            cleaned = response.text.replace("```json", "").replace("```", "").strip()
            meal_plan = json.loads(cleaned)
            print("Cleaned Meal Plan:", cleaned)
        return meal_plan
    except Exception as e:
        print(f"Error occurred: {e}")
        return {"error": str(e), "message": "Failed to generate meal plan"}

# planner()