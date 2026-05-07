import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth


def _init_firebase():
    """Initialize Firebase app once using Streamlit secrets."""
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
        })
        firebase_admin.initialize_app(cred)


def get_firestore():
    """Return a Firestore client, initializing Firebase if needed."""
    _init_firebase()
    return firestore.client()


# ---------------------------
# Profile CRUD
# ---------------------------

def load_profile_from_firestore(uid: str) -> dict | None:
    """
    Load profile for a given user uid from Firestore.
    Returns the profile dict, or None if no profile exists yet.
    """
    db = get_firestore()
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        data = doc.to_dict()
        return data.get("profile", None)
    return None


def save_profile_to_firestore(uid: str, profile: dict):
    """
    Save (or overwrite) the profile for a given user uid in Firestore.
    Uses merge=True so other future fields on the user doc are not wiped.
    """
    db = get_firestore()
    db.collection("users").document(uid).set(
        {"profile": profile},
        merge=True
    )


# ---------------------------
# Google Auth token verification
# ---------------------------

def verify_google_token(id_token: str) -> dict | None:
    """
    Verify a Google ID token using Firebase Auth.
    Returns the decoded token dict (contains uid, email, name, picture),
    or None if verification fails.
    """
    _init_firebase()
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return None