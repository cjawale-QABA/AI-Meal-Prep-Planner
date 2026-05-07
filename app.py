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
from utils.firebase_client import load_profile_from_firestore, save_profile_to_firestore

load_dotenv()

CUISINE_OPTIONS = [
    # Catch-all
    "Mixed / No preference",
    # European
    "Belgian", "French", "Italian", "Spanish", "Greek", "Mediterranean",
    "German", "Eastern European", "British & Irish", "Scandinavian",
    "Portuguese", "Turkish",
    # Asian
    "Chinese", "Japanese", "Korean", "Thai", "Vietnamese", "Indian",
    "Pakistani", "Sri Lankan", "Filipino", "Indonesian & Malaysian",
    "Taiwanese", "Nepalese",
    # Middle Eastern & African
    "Middle Eastern", "Lebanese", "Moroccan", "Ethiopian & East African",
    "West African", "South African",
    # Americas
    "American", "Mexican", "Brazilian", "Peruvian", "Caribbean",
    # Other
    "Halal", "Kosher",
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
# Display Helpers
# ---------------------------

def normalize_grocery_list(grocery_list):
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
        meal_label = "Lunch" if meal["meal_number"] == 1 else "Dinner"
        meal_rows.append({"Day": meal["day"], "Meal": meal_label, "Meal Name": meal["recipe_name"]})
    return pd.DataFrame(meal_rows)


def display_grocery_list(grocery_list):
    grocery_list = normalize_grocery_list(grocery_list)
    return pd.DataFrame([{"Item": i["item"], "Quantity": i["quantity"]} for i in grocery_list])


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
    return pd.DataFrame(step_rows).sort_values(by="Step No")


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
    return pd.DataFrame(prep_step_rows).sort_values(by="Step No")


# ---------------------------
# App Setup
# ---------------------------

st.set_page_config(page_title="Weekly Meal Prep Assistant", layout="wide")
st.title("🍱 AI Meal Prep Planner")

appliance_names = [apl.capitalize() for apl in KITCHEN_APPLIANCES.keys()]

# ---------------------------
# Session State Defaults
# ---------------------------

for key, val in [
    ("user", None),          # Firebase user info dict {uid, email, name, picture}
    ("profile", None),       # Profile dict loaded from Firestore
    ("edit_profile", False),
    ("profile_loaded", False),
]:
    if key not in st.session_state:
        st.session_state[key] = val


# ---------------------------
# Google Sign-In (sidebar)
# ---------------------------

st.sidebar.header("👤 Account")

if st.session_state["user"] is None:
    # ── NOT LOGGED IN ──────────────────────────────────────────
    google_client_id = st.secrets["google_oauth"]["client_id"]

    # Inject Google Identity Services button
    st.sidebar.markdown("Please sign in to save your profile.")
    st.components.v1.html(f"""
        <script src="https://accounts.google.com/gsi/client" async defer></script>
        <div id="g_id_onload"
             data-client_id="{google_client_id}"
             data-callback="handleCredentialResponse"
             data-auto_prompt="false">
        </div>
        <div class="g_id_signin"
             data-type="standard"
             data-size="large"
             data-theme="outline"
             data-text="sign_in_with"
             data-shape="rectangular"
             data-logo_alignment="left">
        </div>
        <script>
          function handleCredentialResponse(response) {{
            // Send the ID token to Streamlit via query param
            const token = response.credential;
            window.parent.postMessage({{type: "streamlit:setComponentValue", value: token}}, "*");
          }}
        </script>
    """, height=60)

    # Alternative: manual token paste (fallback for local dev)
    with st.sidebar.expander("🔧 Dev login (paste ID token)"):
        manual_token = st.text_input("Google ID token", type="password")
        if st.button("Verify token") and manual_token:
            from utils.firebase_client import verify_google_token
            decoded = verify_google_token(manual_token)
            if decoded:
                st.session_state["user"] = {
                    "uid": decoded["uid"],
                    "email": decoded.get("email", ""),
                    "name": decoded.get("name", "User"),
                    "picture": decoded.get("picture", ""),
                }
                st.rerun()

    st.stop()  # Don't render rest of app until logged in

else:
    # ── LOGGED IN ─────────────────────────────────────────────
    user = st.session_state["user"]

    # Load profile from Firestore once per session
    if not st.session_state["profile_loaded"]:
        loaded = load_profile_from_firestore(user["uid"])
        st.session_state["profile"] = loaded if loaded else DEFAULT_PROFILE.copy()
        st.session_state["profile_loaded"] = True

    # User info strip
    col_pic, col_name = st.sidebar.columns([1, 3])
    with col_pic:
        if user.get("picture"):
            st.image(user["picture"], width=40)
    with col_name:
        st.markdown(f"**{user['name']}**")
        st.caption(user["email"])

    if st.sidebar.button("🚪 Sign out", use_container_width=True):
        for key in ["user", "profile", "profile_loaded", "edit_profile"]:
            st.session_state[key] = None if key != "edit_profile" else False
        st.rerun()

    st.sidebar.divider()

    # ---------------------------
    # Sidebar - Profile Section
    # ---------------------------

    st.sidebar.header("⚙️ Profile")

    profile = st.session_state["profile"]
    profile_exists = st.session_state["profile_loaded"] and (
        load_profile_from_firestore(st.session_state["user"]["uid"]) is not None
    )

    if not profile_exists or st.session_state["edit_profile"]:
        # ── Edit / Setup Mode ───────────────────────────────
        if profile_exists:
            st.sidebar.info("✏️ Editing your profile")
        else:
            st.sidebar.info("👋 First time here! Set your preferences once.")

        saved_ethnicity = profile.get("ethnicity", "Mixed / No preference")
        ethnicity_index = CUISINE_OPTIONS.index(saved_ethnicity) if saved_ethnicity in CUISINE_OPTIONS else 0
        new_ethnicity = st.sidebar.selectbox("Type of food", CUISINE_OPTIONS, index=ethnicity_index)

        new_allergies = st.sidebar.text_input("Allergies (comma separated)", value=profile.get("allergies", ""))

        meat_options = ["Vegetarian", "Eggetarian", "Chicken", "Fish", "All"]
        new_meat_pref = st.sidebar.selectbox(
            "Meat Preference", meat_options,
            index=meat_options.index(profile.get("meat_pref", "All"))
        )

        new_spicy_level = st.sidebar.slider("Spice Level", 1, 5, value=profile.get("spicy_level", 3))

        level_options = ["Beginner", "Intermediate", "Advanced"]
        new_cooking_level = st.sidebar.selectbox(
            "Cooking Level", level_options,
            index=level_options.index(profile.get("cooking_level", "Intermediate"))
        )

        current_equipment = profile.get("equipment", [])
        new_equipment = st.sidebar.multiselect(
            "Available Equipment", appliance_names,
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
                save_profile_to_firestore(user["uid"], updated_profile)
                st.session_state["profile"] = updated_profile
                st.session_state["edit_profile"] = False
                st.rerun()
        with col2:
            if profile_exists:
                if st.button("✖ Cancel", use_container_width=True):
                    st.session_state["edit_profile"] = False
                    st.rerun()

    else:
        # ── View Mode ───────────────────────────────────────
        st.sidebar.success("✅ Profile loaded")
        st.sidebar.markdown(f"**Food type:** {profile['ethnicity']}")
        st.sidebar.markdown(f"**Meat pref:** {profile['meat_pref']}")
        st.sidebar.markdown(f"**Cooking level:** {profile['cooking_level']}")
        st.sidebar.markdown(f"**Spice level:** {'🌶' * profile['spicy_level']}")
        st.sidebar.markdown(f"**Allergies:** {profile['allergies'] or 'None'}")
        st.sidebar.markdown(f"**Equipment:** {', '.join(profile['equipment']) or 'None'}")

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
        if not profile_exists:
            st.warning("⚠️ Please save your profile first using the sidebar.")
        else:
            user_input = {
                **st.session_state["profile"],  # ethnicity, allergies, meat_pref, spicy_level, cooking_level, equipment
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