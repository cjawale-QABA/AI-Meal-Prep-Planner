import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts import system_prompt

# Load environment variables from .env (if present)
load_dotenv()


def planner(user_input: dict[str, any] = None):
    print("planner def called")
    if user_input is None:
        user_input = {'ethnicity': 'Asian', 'allergies': '', 'meat_pref': 'Vegetarian', 'spicy_level': 3, 'cooking_level': 'Beginner', 'equipment': ['air fryer', 'convection oven', 'induction cooktop', 'instant pot', 'wet grinder'], 'kcal': 1800, 'protein': 100, 'days': 1, 'meals_per_day': 2, 'people': 1, 'max_dishes': 1, 'store': 'Colruyt'}
    api_key = os.environ.get("GEMINI_API_KEY")
    print("API Key:", api_key)
    client = genai.Client(api_key=api_key)
    print("GenAI Client initialized:", client)
    print("calling generate_content")
    try:
        response = client.models.generate_content(
                model="gemini-flash-latest",
                contents=str(user_input),
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0,
                ),
            )
        # print(response.text)
        try:
            meal_plan = json.loads(response.text)
            print("Meal Plan:", meal_plan)
        except:
            cleaned = response.text.replace("```json", "").replace("```", "").strip()
            meal_plan = json.loads(cleaned)
            print("Cleaned Meal Plan:", meal_plan)
        return meal_plan
    except Exception as e:
        print(f"Error occurred: {e}")
        return {"error": str(e), "message": "Failed to generate meal plan"}

# planner()