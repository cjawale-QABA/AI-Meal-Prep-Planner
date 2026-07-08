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
import json

load_dotenv()

PROFILE_FILE = "profile.json"

CUISINE_OPTIONS = [
    # Catch-all
    "Mixed / No preference",
    # European
    "Belgian",
    "French",
    "Italian",
    "Spanish",
    "Greek",
    "Mediterranean",
    "German",
    "Eastern European",
    "British & Irish",
    "Scandinavian",
    "Portuguese",
    "Turkish",
    # Asian
    "Chinese",
    "Japanese",
    "Korean",
    "Thai",
    "Vietnamese",
    "Indian",
    "Pakistani",
    "Sri Lankan",
    "Filipino",
    "Indonesian & Malaysian",
    "Taiwanese",
    "Nepalese",
    # Middle Eastern & African
    "Middle Eastern",
    "Lebanese",
    "Moroccan",
    "Ethiopian & East African",
    "West African",
    "South African",
    # Americas
    "American",
    "Mexican",
    "Brazilian",
    "Peruvian",
    "Caribbean",
    # Other
    "Halal",
    "Kosher",
]

DEFAULT_PROFILE = {
    "ethnicity": "Mixed / No preference",
    "allergies": "",
    "meat_pref": "All",
    "spicy_level": 3,
    "cooking_level": "Intermediate",
    "equipment": []
}


# ---------------------------
# Profile Persistence Helpers
# ---------------------------

def load_profile() -> dict:
    """Load profile from JSON file, or return defaults if not found."""
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_PROFILE.copy()


def save_profile(data: dict):
    """Save profile dict to JSON file."""
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------
# Grocery / Display Helpers
# ---------------------------

def normalize_grocery_list(grocery_list):
    """Converts any grocery_list format into the expected flat array format."""
    if isinstance(grocery_list, list):
        normalized = []
        for item in grocery_list:
            if isinstance(item, dict):
                normalized.append(item)
            elif isinstance(item, str):
                normalized.append({"item": item, "quantity": ""})
        return normalized

    if isinstance(grocery_list, dict):
        normalized = []
        for category, items in grocery_list.items():
            if category == "notes":
                continue
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        normalized.append({"item": item, "quantity": ""})
                    elif isinstance(item, dict):
                        normalized.append(item)
        return normalized

    return []


def display_meal_plan(meal_plan):
    meal_rows = []
    for meal in meal_plan:
        day = meal["day"]
        meal_label = "Lunch" if meal["meal_number"] == 1 else "Dinner"
        recipe_name = meal["recipe_name"]
        meal_rows.append({"Day": day, "Meal": meal_label, "Meal Name": recipe_name})
    return pd.DataFrame(meal_rows)


def display_grocery_list(grocery_list):
    grocery_list = normalize_grocery_list(grocery_list)
    grocery_rows = [{"Item": item["item"], "Quantity": item["quantity"]} for item in grocery_list]
    return pd.DataFrame(grocery_rows)


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
    return df_steps.sort_values(by="Step No")


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
    return df_pre_steps.sort_values(by="Step No")


# ---------------------------
# App Setup
# ---------------------------

st.set_page_config(page_title="AI Meal Prep Planner", layout="wide")
st.title("🍱 AI Meal Prep Planner")
st.text("Plan your meals, generate grocery lists, and get cooking instructions with AI assistance!")

# Load profile into session state on first run
if "profile" not in st.session_state:
    st.session_state["profile"] = load_profile()

if "edit_profile" not in st.session_state:
    st.session_state["edit_profile"] = False

# ---------------------------
# Sidebar - Profile Section
# ---------------------------

appliance_names = [apl.capitalize() for apl in KITCHEN_APPLIANCES.keys()]

st.sidebar.header("👤 Profile")

profile = st.session_state["profile"]

# Check if profile has been filled in before (has any non-default meaningful data)
profile_saved = os.path.exists(PROFILE_FILE)

if not profile_saved or st.session_state["edit_profile"]:
    # --- Edit / Setup Mode ---
    if profile_saved:
        st.sidebar.info("✏️ Editing your profile")
    else:
        st.sidebar.info("👋 Welcome! Please set up your profile once.")

    saved_ethnicity = profile.get("ethnicity", "Mixed / No preference")
    ethnicity_index = CUISINE_OPTIONS.index(saved_ethnicity) if saved_ethnicity in CUISINE_OPTIONS else 0
    new_ethnicity = st.sidebar.selectbox(
        "Type of food",
        CUISINE_OPTIONS,
        index=ethnicity_index
    )

    new_allergies = st.sidebar.text_input(
        "Allergies (comma separated)",
        value=profile.get("allergies", "")
    )

    new_meat_pref = st.sidebar.selectbox(
        "Meat Preference",
        ["Vegetarian", "Eggetarian", "Chicken", "Fish", "All"],
        index=["Vegetarian", "Eggetarian", "Chicken", "Fish", "All"].index(profile.get("meat_pref", "All"))
    )

    new_spicy_level = st.sidebar.slider(
        "Spice Level", 1, 5,
        value=profile.get("spicy_level", 3)
    )

    new_cooking_level = st.sidebar.selectbox(
        "Cooking Level",
        ["Beginner", "Intermediate", "Advanced"],
        index=["Beginner", "Intermediate", "Advanced"].index(profile.get("cooking_level", "Intermediate"))
    )

    current_equipment = profile.get("equipment", [])
    new_equipment = st.sidebar.multiselect(
        "Available Equipment",
        appliance_names,
        default=[e for e in current_equipment if e in appliance_names]
    )

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("💾 Save Profile", use_container_width=True):
            updated_profile = {
                "ethnicity": new_ethnicity,
                "allergies": new_allergies,
                "meat_pref": new_meat_pref,
                "spicy_level": new_spicy_level,
                "cooking_level": new_cooking_level,
                "equipment": new_equipment
            }
            save_profile(updated_profile)
            st.session_state["profile"] = updated_profile
            st.session_state["edit_profile"] = False
            st.rerun()

    with col2:
        if profile_saved:
            if st.button("✖ Cancel", use_container_width=True):
                st.session_state["edit_profile"] = False
                st.rerun()

else:
    # --- View Mode: compact summary ---
    st.sidebar.success("✅ Profile loaded")
    st.sidebar.markdown(f"**Food type:** {profile['ethnicity']}")
    st.sidebar.markdown(f"**Meat pref:** {profile['meat_pref']}")
    st.sidebar.markdown(f"**Cooking level:** {profile['cooking_level']}")
    st.sidebar.markdown(f"**Spice level:** {'🌶' * profile['spicy_level']}")
    allergy_text = profile['allergies'] if profile['allergies'] else "None"
    st.sidebar.markdown(f"**Allergies:** {allergy_text}")
    equipment_text = ", ".join(profile['equipment']) if profile['equipment'] else "None"
    st.sidebar.markdown(f"**Equipment:** {equipment_text}")

    if st.sidebar.button("✏️ Edit Profile", use_container_width=True):
        st.session_state["edit_profile"] = True
        st.rerun()

st.sidebar.divider()

# ---------------------------
# Sidebar - Meal Planning
# ---------------------------

st.sidebar.header("🍽 Meal Planning")

kcal = st.sidebar.number_input("Kcal per day", 1000, 4000, 1800)
protein = st.sidebar.number_input("Protein (g/day)", 50, 200, 100)
with st.container():
    st.sidebar.write("Select type of meals:")
    meal_types = st.sidebar.multiselect("Meal Types", ["Breakfast", "Lunch", "Dinner", "Snacks"], default=["Lunch", "Dinner"])
days = st.sidebar.slider("Number of days", 1, 7, 3)
# meals_per_day = st.sidebar.selectbox("Meals per day", [2, 3, 4])
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

    if not profile_saved and not os.path.exists(PROFILE_FILE):
        st.warning("⚠️ Please save your profile first using the sidebar before generating a meal plan.")
    else:
        # Merge profile + meal planning inputs
        user_input = {
            **st.session_state["profile"],   # ethnicity, allergies, meat_pref, spicy_level, cooking_level, equipment
            "kcal": kcal,
            "protein": protein,
            "days": days,
            "meal_types": meal_types,
            # "meals_per_day": meals_per_day,
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
        meal_plan_tab, grocery_list_tab, cooking_plan_tab = st.tabs(
            ["🍽 Meal Plan", "🛒 Grocery List", "👨‍🍳 Cooking Plan"]
        )

        with meal_plan_tab:
            st.subheader("Meal Plan")
            st.dataframe(display_meal_plan(result["meal_plan"]))

        with grocery_list_tab:
            st.subheader("Grocery List")
            st.dataframe(display_grocery_list(result["grocery_list"]))

        with cooking_plan_tab:
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
                st.subheader("Cooking Plan (Today)")
                st.dataframe(display_batch_cooking_plan(result["batch_cooking_plan"]))

