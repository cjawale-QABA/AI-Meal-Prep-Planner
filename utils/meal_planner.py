import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import Content, Part
from planner_prompt import prompt_1, prompt_2

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def planner(user_input: dict[str, any]) -> dict[str, any]:
    prompt = prompt_1.format(
        ethnicity=user_input.get('ethnicity'),
        allergies=user_input.get('allergies'),
        meat_pref=user_input.get('meat_pref'),
        spicy_level=user_input.get('spicy_level'),
        cooking_level=user_input.get('cooking_level'),
        equipment=user_input.get('equipment'),
        days=user_input.get('days'),
        max_dishes=user_input.get('max_dishes'),
        people=user_input.get('people'),
        meals_per_day=user_input.get('meals_per_day'),
        kcal=user_input.get('kcal'),
        protein=user_input.get('protein'),
        store=user_input.get('store')
    ) + prompt_2
    print(prompt)
    messages = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=messages
        )
        raw_output = response.choices[0].message.content
        try:
            meal_plan = json.loads(raw_output)
        except json.JSONDecodeError:
            # Attempt basic cleanup if model adds stray text
            cleaned = raw_output.strip().strip("```json").strip("```")
            meal_plan = json.loxads(cleaned)
        return meal_plan
    except Exception as e:
        print(f"Error occurred: {e}")
        return {"error": str(e), "message": "Failed to generate meal plan"}