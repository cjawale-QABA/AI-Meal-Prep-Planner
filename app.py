
import streamlit as st
from utils.mock_generator import generate_mock_plan
from utils.meal_planner import planner
from google import genai
import os
from google.genai import types
from prompts import system_prompt
from dotenv import load_dotenv
from appliances import KITCHEN_APPLIANCES
from datetime import datetime
import pandas as pd

load_dotenv()


def normalize_grocery_list(grocery_list):
    """Converts any grocery_list format into the expected flat array format."""
    
    # Already correct format — list of dicts
    if isinstance(grocery_list, list):
        normalized = []
        for item in grocery_list:
            if isinstance(item, dict):
                normalized.append(item)
            elif isinstance(item, str):
                # List of plain strings — wrap them
                normalized.append({
                    "item": item,
                    "quantity": "",
                    # "brand_pref": ""
                })
        return normalized

    # Nested object format e.g. {"produce": [...], "pantry": [...]}
    if isinstance(grocery_list, dict):
        normalized = []
        for category, items in grocery_list.items():
            if category == "notes":
                continue  # skip notes field
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        normalized.append({
                            "item": item,
                            "quantity": "",
                            # "brand_pref": ""
                        })
                    elif isinstance(item, dict):
                        normalized.append(item)
        return normalized

    return []




def display_meal_plan(meal_plan):
    meal_rows = []
    for meal in meal_plan:
        print(meal.keys())
        day = meal["day"]
        meal_label = "Lunch" if meal["meal_number"] == 1 else "Dinner"
        recipe_name = meal["recipe_name"]
        print(f"Day: {day}, Meal: {meal_label}, Recipe Name: {recipe_name}")
        meal_rows.append({
            "Day": day,
            "Meal": meal_label,
            "Meal Name": recipe_name
        })
    df_meals = pd.DataFrame(meal_rows)
    return df_meals



def display_grocery_list(grocery_list):
    grocery_list = normalize_grocery_list(grocery_list) 
    grocery_rows = []
    for item in grocery_list:
        grocery_rows.append({
            "Item": item["item"],
            "Quantity": item["quantity"],
            # "Brand Preference": item["brand_pref"]
        })
    df_grocery = pd.DataFrame(grocery_rows)
    return df_grocery



def display_batch_cooking_plan(cooking_plan):
    step_rows = []
    for step in cooking_plan:
        step_rows.append({
            "Step No": step["step"],
            "Action": step["instruction"],
            "Appliance": step["appliance_used"],
            "Method": step["method_used"],
            "Substitution": step["substitution_applied"],
        })
    df_steps = pd.DataFrame(step_rows)
    df_steps = df_steps.sort_values(by="Step No")
    return df_steps



def display_pre_prep_plan(pre_prep_plan):
    prep_step_rows = []
    for step in pre_prep_plan:
        prep_step_rows.append({
            "Step No": step["step"],
            "Action": step["action"],
            "Duration": step["duration"],
            "Storage": step["storage"],
            "Appliance": step["appliance"]
        })
    df_pre_steps = pd.DataFrame(prep_step_rows)
    df_pre_steps = df_pre_steps.sort_values(by="Step No")
    return df_pre_steps


st.set_page_config(page_title="Weekly Meal Prep Assistant", layout="wide")

st.title("🍱 AI Meal Prep Planner")

# ---------------------------
# Sidebar - User Inputs
# ---------------------------
st.sidebar.header("User Preferences")

ethnicity = st.sidebar.selectbox(
    "Type of food",
    ["Asian", "Mediterranean", "Belgian", "Mixed"]
)

allergies = st.sidebar.text_input("Allergies (comma separated)")

meat_pref = st.sidebar.selectbox(
    "Meat Preference",
    ["Vegetarian", "Eggetarian", "Chicken", "Fish", "All"]
)

spicy_level = st.sidebar.slider("Spice Level", 1, 5, 3)

cooking_level = st.sidebar.selectbox(
    "Cooking Level",
    ["Beginner", "Intermediate", "Advanced"]
)

appliance_names = list(apl.capitalize() for apl in KITCHEN_APPLIANCES.keys())
equipment = st.sidebar.multiselect(
    "Available Equipment",
    appliance_names
)

# ---------------------------
# Meal Planning Inputs
# ---------------------------
st.sidebar.header("Meal Planning")

kcal = st.sidebar.number_input("Kcal per day", 1000, 4000, 1800)
protein = st.sidebar.number_input("Protein (g/day)", 50, 200, 100)

days = st.sidebar.slider("Number of days", 1, 7, 3)
meals_per_day = st.sidebar.selectbox("Meals per day", [2, 3, 4])
people = st.sidebar.number_input("Number of people", 1, 6, 1)

max_dishes = st.sidebar.slider("Max dishes", 1, 10, 5)

store = st.sidebar.selectbox(
    "Preferred Store",
    ["Colruyt", "Delhaize", "Carrefour", "Aldi", "Lidl", "Spar", "Other"]
)

# ---------------------------
# Generate Button
# ---------------------------
if st.button("Prepare meal plan 🍳"):

    user_input = {
        "ethnicity": ethnicity,
        "allergies": allergies,
        "meat_pref": meat_pref,
        "spicy_level": spicy_level,
        "cooking_level": cooking_level,
        "equipment": equipment,
        "kcal": kcal,
        "protein": protein,
        "days": days,
        "meals_per_day": meals_per_day,
        "people": people,
        "max_dishes": max_dishes,
        "store": store
    }

    with st.spinner("Consulting our Chef 🧑‍🍳 agent..."):
        result = planner(user_input)

    st.success("Generated Meal Plan Successfully!")

    # ---------------------------
    # Output Tabs
    # ---------------------------
    meal_plan, grocery_list, cooking_plan = st.tabs(["🍽 Meal Plan", "🛒 Grocery List", "👨‍🍳 Cooking Plan"])

    with meal_plan:
        # st.subheader("Your Meal Plan")
        st.subheader("Meal Plan")
        # st.write(result["meal_plan"])
        st.dataframe(display_meal_plan(result["meal_plan"]))

    with grocery_list:
        st.subheader("Grocery List")
        st.dataframe(display_grocery_list(result["grocery_list"]))

    with cooking_plan:
        st.subheader("Cooking Plan")
        if result.get("pre_prep_plan"):
            pre_prep_tab, cooking_tab = st.tabs(["🥣 Pre-Prep Plan", "👨‍🍳 Cooking Plan"])
            with pre_prep_tab:
                st.subheader("Pre-Prep Plan (Today)")
                st.dataframe(display_pre_prep_plan(result["pre_prep_plan"]))
            with cooking_tab:
                st.subheader("Cooking Plan (Tomorrow)")
                st.dataframe(display_batch_cooking_plan(result["batch_cooking_plan"]))
        else:
            st.write("No pre-prep planning needed.")
            with cooking_plan:
                st.subheader("Cooking Plan (Today)")
                st.dataframe(display_batch_cooking_plan(result["batch_cooking_plan"]))





