
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

load_dotenv()

st.set_page_config(page_title="AI Meal Prep Planner", layout="wide")

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

equipment = st.sidebar.multiselect(
    "Available Equipment",
    KITCHEN_APPLIANCES.keys()
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
if st.button("Generate Meal Plan 🚀"):

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

    with st.spinner("Calling Gemini via REST..."):
        result = planner(user_input)

    st.success("Generated Meal Plan Successfully!")

    # ---------------------------
    # Output Tabs
    # ---------------------------
    tab1, tab2, tab3 = st.tabs(["🍽 Meal Plan", "🛒 Grocery List", "👨‍🍳 Cooking Plan"])

    with tab1:
        st.subheader("Your Meal Plan")
        st.write(result["meal_plan"])

    with tab2:
        st.subheader("Grocery List")
        st.write(result["grocery_list"])

    with tab3:
        st.subheader("Cooking Plan")
        st.write(result["batch_cooking_plan"])