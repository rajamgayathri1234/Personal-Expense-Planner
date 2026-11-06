import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from db import get_connection, init_database
from auth import render_auth_page, logout
from finance import (
    get_month_summary,
    get_expense_summary,
    get_transactions,
    add_expense,
    add_income,
    get_monthly_income,
    get_user_details,
    update_user_details,
    get_budget_rows,
    save_budget,
    get_monthly_trend,
    save_monthly_income,
    add_bulk_expenses,
    get_monthly_expense_history
)

st.set_page_config(page_title="Personal Expense Planner", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: Inter, sans-serif; }
[data-testid="stAppViewContainer"] { background: #f7f8fc; }
[data-testid="stSidebar"] { background: linear-gradient(180deg,#3c1c70 0%,#281052 100%); }
[data-testid="stSidebar"] * { color: #fff !important; }
[data-testid="stSidebar"] button {
    background-color: white !important;
    color: #39206f !important;
    border: 1px solid white !important;
    border-radius: 10px !important;
}

[data-testid="stSidebar"] button p {
    color: #39206f !important;
}

[data-testid="stSidebar"] button:hover {
    background-color: #eee8fa !important;
    color: #39206f !important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 { color:white; }
.block-container { padding-top: 1.35rem; max-width: 1600px; }
div[data-testid="stMetric"] { background: white; border:1px solid #e8e5f2; padding:18px 18px; border-radius:16px; box-shadow:0 2px 8px #34205c0a; }
div[data-testid="stMetricLabel"] { color:#43305e; font-weight:600; }
div[data-testid="stMetricValue"] { color:#21143c; font-weight:800; }
div.stButton > button[kind="primary"] { background:#6237b7; border-color:#6237b7; border-radius:10px; }
div.stButton > button { border-radius:10px; }
h1,h2,h3 { color:#17132f; }
.card-title {font-size:18px;font-weight:700;color:#21143c;margin-bottom:12px;}
.insight {background:linear-gradient(100deg,#ebe5ff,#f5f1ff);border:1px solid #ded4ff;border-radius:18px;padding:20px 24px;color:#21143c;}
.small-muted {color:#746b83;font-size:14px;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def money(value):
    return f"₹{float(value or 0):,.0f}"

def ensure_db():
    try:
        init_database()
        return True
    except Exception as e:
        st.error("Could not connect to MySQL. Check your .env settings and make sure MySQL Server is running.")
        with st.expander("Connection details"):
            st.code(str(e))
        st.info("First create the database by importing sql/schema.sql into MySQL Workbench, then update your .env file.")
        return False

if "user" not in st.session_state:
    st.session_state.user = None

if not ensure_db():
    st.stop()

if not st.session_state.user:
    render_auth_page()
    st.stop()

user = st.session_state.user
user_id = user["user_id"]
today = date.today()

with st.sidebar:
    st.markdown("## 💳 Personal")
    st.markdown("## Expense Planner")
    st.markdown("---")
    nav_items = [
        ("🏠", "Home"), ("🗓️", "Expenses"), ("➕", "Additional Income"),
        ("✨", "AI Analysis"), ("▤", "Monthly Reports"), ("👤", "User Details")
    ]
    if "page" not in st.session_state:
        st.session_state.page = "Home"
    for icon, label in nav_items:
        if st.button(f"{icon}   {label}", key=f"nav_{label}", use_container_width=True,
                     type="primary" if st.session_state.page == label else "secondary"):
            st.session_state.page = label
            st.rerun()
    st.markdown("---")
    st.caption(f"Signed in as {user['name']}")
    if st.button("↪  Logout", use_container_width=True):
        logout()

page = st.session_state.page

if page == "Home":
    header_left, header_right = st.columns([4,1.6])
    with header_left:
        st.markdown("# 🏠 Home Dashboard")
        st.markdown("<p class='small-muted'>Track your spending, income and savings at a glance</p>", unsafe_allow_html=True)
    with header_right:
        selected_month = st.date_input("Select month", value=today.replace(day=1), key="dash_month")
    month_start = selected_month.replace(day=1)
    summary = get_month_summary(user_id, month_start)
    income = summary["income"]
    expenses = summary["expenses"]
    savings = income - expenses
    recommended = max(0, income * 0.25)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💰 Total Income", money(income))
    c2.metric("🛒 Total Expenses", money(expenses))
    c3.metric("🐷 Total Savings", money(savings))
    c4.metric("🎯 Recommended Savings", money(recommended))
    st.write("")
    left,right = st.columns([1,1.12], gap="medium")
    with left:
        st.markdown("### Monthly Expense Summary")
        exp_df = get_expense_summary(user_id, month_start)
        if exp_df.empty:
            st.info("No expenses recorded for this month yet. Add an expense to see your summary.")
        else:
            exp_df["Difference (₹)"] = exp_df["planned"] - exp_df["actual"]
            view = exp_df.rename(columns={"category":"Category","planned":"Planned (₹)","actual":"Actual (₹)"})
            view["Difference (₹)"] = view["Difference (₹)"].map(lambda x: f"{x:,.0f}")
            view["Planned (₹)"] = view["Planned (₹)"].map(lambda x: f"{x:,.0f}")
            view["Actual (₹)"] = view["Actual (₹)"].map(lambda x: f"{x:,.0f}")
            st.dataframe(view[["Category","Planned (₹)","Actual (₹)","Difference (₹)"]], use_container_width=True, hide_index=True)
    with right:
        st.markdown("### Planned vs Actual Expenses")
        if not exp_df.empty:
            chart_df = exp_df.melt(id_vars="category", value_vars=["planned","actual"], var_name="Type", value_name="Amount")
            chart_df["Type"] = chart_df["Type"].map({"planned":"Planned","actual":"Actual"})
            fig = px.bar(chart_df, x="category", y="Amount", color="Type", barmode="group",
                         color_discrete_map={"Planned":"#7651c9","Actual":"#f36aa8"})
            fig.update_layout(height=350, margin=dict(l=5,r=5,t=15,b=5), plot_bgcolor="white",
                              paper_bgcolor="white", legend_title_text="", xaxis_title="Expense Category",
                              yaxis_title="Amount (₹)", font=dict(color="#25183d"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Your planned-versus-actual chart will appear here.")
    st.markdown("<div class='insight'><h3>🤖 AI Insight</h3><b>You are within your planned budget.</b><br/>Your estimated monthly savings are " + money(savings) + ". Review the AI Analysis page for personalized saving suggestions.</div>", unsafe_allow_html=True)



elif page == "Expenses":
    st.title("🗓️ Expenses Management")
    st.caption("Enter planned and actual expenses for each category.")

    # Expense entry form
    with st.form("monthly_expense_form"):

        st.markdown("### 1. Select Expense Date")

        expense_date = st.date_input(
            "Expense Date",
            value=today,
            key="expense_entry_date"
        )

        st.markdown("### 2. Enter Planned and Actual Expenses")

        categories = [
            "Food",
            "Rent",
            "Health",
            "Shopping",
            "Groceries",
            "Transport",
            "Others"
        ]

        expenses = {}
        planned_expenses = {}

        for category in categories:
            st.markdown(f"**{category}**")

            col1, col2 = st.columns(2)

            with col1:
                planned_expenses[category] = st.number_input(
                    f"Planned Amount (₹) - {category}",
                    min_value=0.0,
                    step=100.0,
                    key=f"planned_{category}"
                )

            with col2:
                expenses[category] = st.number_input(
                    f"Actual Amount (₹) - {category}",
                    min_value=0.0,
                    step=100.0,
                    key=f"actual_{category}"
                )

        total_planned = sum(planned_expenses.values())
        total_expenses = sum(expenses.values())

        st.divider()
        st.markdown("### 3. Monthly Summary")

        col1, col2 = st.columns(2)

        col1.metric(
            "Total Planned Expenses",
            f"₹{total_planned:,.2f}"
        )

        col2.metric(
            "Total Actual Expenses",
            f"₹{total_expenses:,.2f}"
        )

        submitted = st.form_submit_button(
            "Save All Expenses",
            type="primary",
            use_container_width=True
        )

    # Save records after the form is submitted
    if submitted:
        if total_expenses <= 0:
            st.error("Please enter at least one actual expense.")
        else:
            try:
                add_bulk_expenses(
                    user_id,
                    expenses,
                    planned_expenses,
                    expense_date
                )

                st.success("Expenses saved successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"Unable to save records: {e}")

    # Monthly expense history
    st.divider()
    st.markdown("### 📋 Monthly Expense History")

    history_month = st.date_input(
        "Select History Month",
        value=today.replace(day=1),
        key="history_month"
    )

    history = get_monthly_expense_history(
        user_id,
        history_month.replace(day=1)
    )

    if history.empty:
        st.info("No expense records found for this month.")
    else:
        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Total Recorded Expenses",
            f"₹{history['Amount (₹)'].sum():,.2f}"
        )

        st.download_button(
            "Download Expense History",
            history.to_csv(index=False).encode("utf-8"),
            file_name="monthly_expense_history.csv",
            mime="text/csv"
        )

elif page == "Additional Income":
    st.title("➕ Additional Income")
    st.caption("Record salary, freelance income, bonuses and other earnings.")

    with st.form("income_form"):
        amount = st.number_input(
            "Income Amount (₹)",
            min_value=0.0,
            step=500.0
        )

        source = st.selectbox(
            "Income Source",
            ["Salary", "Freelance", "Bonus", "Business", "Interest", "Other"]
        )

        income_date = st.date_input(
            "Received Date",
            value=today
        )

        note = st.text_input("Description (optional)")

        submitted = st.form_submit_button(
            "Save Income",
            type="primary",
            use_container_width=True
        )

    if submitted:
        if amount <= 0:
            st.error("Please enter an income amount greater than zero.")
        else:
            try:
                add_income(user_id, amount, source, income_date, note)
                st.success("Income saved successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Unable to save income: {e}")

    st.markdown("### Income History")
    tx = get_transactions(user_id, "income")

    if tx.empty:
        st.info("No additional income records yet.")
    else:
        st.dataframe(tx, use_container_width=True, hide_index=True)


elif page == "AI Analysis":
    st.title("✨ AI Analysis")
    st.caption("Financial insights based on your recorded transactions.")

    selected = st.date_input(
        "Analysis Month",
        value=today.replace(day=1),
        key="ai_month"
    )

    month = selected.replace(day=1)
    summary = get_month_summary(user_id, month)
    exp_df = get_expense_summary(user_id, month)

    income = summary["income"]
    expenses = summary["expenses"]
    savings = income - expenses

    st.metric("Total Income", money(income))
    st.metric("Total Expenses", money(expenses))
    st.metric("Estimated Savings", money(savings))

    if income <= 0:
        st.info("Add income records to receive financial insights.")
    else:
        if expenses > income:
            st.error("Your expenses are higher than your income.")
        else:
            st.success("Your expenses are within your recorded income.")

        savings_rate = (savings / income) * 100

        if savings_rate < 20:
            st.warning("Your savings rate is below 20%. Try reducing unnecessary spending.")
        else:
            st.success(f"Your savings rate is {savings_rate:.1f}%.")

    if not exp_df.empty:
        st.markdown("### Category-wise Suggestions")

        for _, row in exp_df.iterrows():
            if row["planned"] > 0 and row["actual"] > row["planned"]:
                st.warning(
                    f"{row['category']}: You spent "
                    f"{money(row['actual'] - row['planned'])} "
                    "above your planned amount."
                )

    st.caption("These are rule-based financial suggestions, not advice from a connected AI model.")


elif page == "Monthly Reports":
    st.title("📊 Monthly Reports")

    selected = st.date_input(
        "Choose Report Month",
        value=today.replace(day=1),
        key="report_month"
    )

    month = selected.replace(day=1)
    summary = get_month_summary(user_id, month)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Income", money(summary["income"]))
    col2.metric("Total Expenses", money(summary["expenses"]))
    col3.metric(
        "Net Savings",
        money(summary["income"] - summary["expenses"])
    )

    exp_df = get_expense_summary(user_id, month)

    if not exp_df.empty:
        st.markdown("### Category-wise Expense Report")

        report = exp_df.rename(
            columns={
                "category": "Category",
                "planned": "Planned Amount (₹)",
                "actual": "Actual Amount (₹)"
            }
        )

        st.dataframe(
            report,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Monthly Report",
            exp_df.to_csv(index=False).encode("utf-8"),
            file_name=f"expense_report_{month:%Y_%m}.csv",
            mime="text/csv"
        )
    else:
        st.info("No expense records found for this month.")


elif page == "User Details":
    st.title("👤 User Details")

    details = get_user_details(user_id) or {}

    with st.form("profile_form"):
        name = st.text_input(
            "Full Name",
            value=details.get("name", "")
        )

        email = st.text_input(
            "Email",
            value=details.get("email", "")
        )

        monthly_income = st.number_input(
            "Expected Monthly Income (₹)",
            min_value=0.0,
            value=float(details.get("monthly_income") or 0)
        )

        submitted = st.form_submit_button(
            "Save Details",
            type="primary"
        )

    if submitted:
        try:
            update_user_details(
                user_id,
                name.strip(),
                email.strip(),
                monthly_income
            )

            st.session_state.user["name"] = name.strip()
            st.success("Your details have been updated.")
            st.rerun()

        except Exception as e:
            st.error(f"Unable to update details: {e}")

    st.divider()
    st.markdown("### Monthly Category Budgets")

    budgets = get_budget_rows(user_id) or {}

    with st.form("budget_form"):
        budget_values = {}

        for cat in [
            "Food", "Rent", "Health", "Shopping",
            "Groceries", "Transport", "Others"
        ]:
            budget_values[cat] = st.number_input(
                f"{cat} Budget (₹)",
                min_value=0.0,
                value=float(budgets.get(cat, 0) or 0),
                step=100.0,
                key=f"budget_{cat}"
            )

        save = st.form_submit_button(
            "Save Monthly Budgets",
            type="primary"
        )

    if save:
        try:
            for cat, val in budget_values.items():
                save_budget(user_id, cat, val)

            st.success("Monthly budgets saved successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Unable to save budgets: {e}")
