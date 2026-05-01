import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts import system_prompt

# api_key = os.environ.get("GEMINI_API_KEY")
# client = genai.Client(api_key=api_key)

def planner(user_input: dict[str, any]):
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
            model="gemini-flash-latest",
            contents="explain me the benefits of a balanced diet.",
        )
    print(str(response))
    # print(system_prompt)
    # response = client.models.generate_content(
    #             model="gemini-flash-latest",
    #             contents=str(user_input),
    #             config=types.GenerateContentConfig(
    #                 system_instruction=system_prompt,
    #                 temperature=0,
    #             ),
    #         )
    
    return response.text

    # prompt = prompt_1.format(
    #     ethnicity=user_input.get('ethnicity'),
    #     allergies=user_input.get('allergies'),
    #     meat_pref=user_input.get('meat_pref'),
    #     spicy_level=user_input.get('spicy_level'),
    #     cooking_level=user_input.get('cooking_level'),
    #     equipment=user_input.get('equipment'),
    #     days=user_input.get('days'),
    #     max_dishes=user_input.get('max_dishes'),
    #     people=user_input.get('people'),
    #     meals_per_day=user_input.get('meals_per_day'),
    #     kcal=user_input.get('kcal'),
    #     protein=user_input.get('protein'),
    #     store=user_input.get('store')
    # ) + prompt_2
    # print(prompt)
    prompt = f"""
                USER INPUT:
                - Ethnicity / cuisine preference: {user_input['ethnicity']}
                - Allergies: {user_input['allergies']}
                - Meat preference: {user_input['meat_pref']}
                - Spicy level: {user_input['spicy_level']}
                - Cooking level: {user_input['cooking_level']}
                - Available equipment: {user_input['equipment']}
                - Number of days: {user_input['days']}
                - Max number of dishes: {user_input['max_dishes']}
                - Number of people: {user_input['people']}
                - Meals per day: {user_input['meals_per_day']}
                - Daily calorie target: {user_input['kcal']}
                - Daily protein target: {user_input['protein']}
                - Preferred grocery store: {user_input['store']}
                """
    
    # print("Constructed prompt: ", prompt)
    # print("User input: ", user_input)
    # print("System prompt: ", system_prompt)
    # print("API key: ", api_key)
    # messages = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    # print("Messages: ", messages)
    try:
        print(user_input)
        user_data = {'ethnicity': 'Asian', 'allergies': '', 'meat_pref': 'Vegetarian', 'spicy_level': 3, 'cooking_level': 'Beginner', 'equipment': ['air fryer', 'convection oven'], 'kcal': 1800, 'protein': 100, 'days': 1, 'meals_per_day': 2, 'people': 1, 'max_dishes': 1, 'store': 'Colruyt'}
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=str(user_data),
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0,
            ),
        )
        print("Response text:", response.text)
        raw_output = response.text
        try:
            meal_plan = json.loads(raw_output)
        except:
            cleaned = raw_output.replace("```json", "").replace("```", "").strip()
            meal_plan = json.loads(cleaned)
        return meal_plan
    except Exception as e:
        print(f"Error occurred: {e}")
        return {"error": str(e), "message": "Failed to generate meal plan"}