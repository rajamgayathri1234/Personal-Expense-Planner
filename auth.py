import re, os, hmac, hashlib, secrets
import streamlit as st
from db import get_connection

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()
    return f"{salt}${digest}"

def verify_password(password, stored):
    try:
        salt, expected = stored.split("$", 1)
        actual = hash_password(password, salt).split("$", 1)[1]
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def register_user(name, email, password):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users(name,email,password_hash) VALUES(%s,%s,%s)",
                    (name, email.lower(), hash_password(password)))
        conn.commit()
        return True, {"user_id": cur.lastrowid, "name": name, "email": email.lower()}
    except Exception as exc:
        conn.rollback()
        if "Duplicate" in str(exc):
            return False, "An account with this email already exists."
        return False, f"Could not create account: {exc}"
    finally:
        conn.close()

def authenticate_user(email, password):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT user_id,name,email,password_hash FROM users WHERE email=%s", (email.lower(),))
        user = cur.fetchone()
        if user and verify_password(password, user["password_hash"]):
            return True, {"user_id": user["user_id"], "name": user["name"], "email": user["email"]}
        return False, "Incorrect email or password."
    finally:
        conn.close()

def render_auth_page():
    st.markdown("<div style='height:7vh'></div>", unsafe_allow_html=True)
    left, center, right = st.columns([1,1.15,1])
    with center:
        st.markdown("""
<div style='text-align:center;padding:25px 10px 12px'>
    <h1 style='color:#38206f'>Personal Expense Planner</h1>
    <p style='color:#756a88'>Track your income, expenses and savings.</p>
</div>
""", unsafe_allow_html=True)
        mode = st.radio("Choose action", ["Login", "Register"], horizontal=True, label_visibility="collapsed")
        with st.container(border=True):
            if mode == "Login":
                email = st.text_input("Email", key="auth_email")
                password = st.text_input("Password", type="password", key="auth_password")
                if st.button("Login", type="primary", use_container_width=True):
                    if not email.strip() or not password:
                        st.error("Enter your email and password.")
                    elif not EMAIL_RE.match(email.strip()):
                        st.error("Enter a valid email address.")
                    else:
                        ok, result = authenticate_user(email.strip(), password)
                        if ok:
                            st.session_state.user = result
                            st.session_state.page = "Home"
                            st.rerun()
                        else:
                            st.error(result)
            else:
                name = st.text_input("Full name", key="reg_name")
                email = st.text_input("Email", key="reg_email")
                password = st.text_input("Password (minimum 8 characters)", type="password", key="reg_password")
                confirm = st.text_input("Confirm password", type="password", key="reg_confirm")
                if st.button("Create Account", type="primary", use_container_width=True):
                    if not name.strip() or not email.strip() or not password or not confirm:
                        st.error("Complete all fields.")
                    elif not EMAIL_RE.match(email.strip()):
                        st.error("Enter a valid email address.")
                    elif len(password) < 8:
                        st.error("Password must contain at least 8 characters.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    else:
                        ok, result = register_user(name.strip(), email.strip(), password)
                        if ok:
                            st.session_state.user = result
                            st.session_state.page = "Home"
                            st.success("Account created.")
                            st.rerun()
                        else:
                            st.error(result)

def logout():
    st.session_state.user = None
    st.session_state.page = "Home"
    st.rerun()
