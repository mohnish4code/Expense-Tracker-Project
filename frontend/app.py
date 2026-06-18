import streamlit as st

st.set_page_config(
    page_title="AI Expense Tracker",
    layout="wide"
)

st.title("AI Based Expense Tracker")

st.subheader("Dashboard")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Monthly Budget",
        "₹50,000"
    )

with col2:
    st.metric(
        "Spent",
        "₹32,500"
    )

with col3:
    st.metric(
        "Remaining",
        "₹17,500"
    )

with col4:
    st.metric(
        "Usage",
        "65%"
    )


st.markdown("---")

st.subheader("🤖 AI Insights")

col1, col2, col3 = st.columns(3)

with col1:
    st.warning(
        "Overspending Risk: 78%"
    )

with col2:
    st.error(
        "3 Anomalies Detected"
    )

with col3:
    st.success(
        "Recommended Budget: ₹55,000"
    )

st.markdown("---")

st.subheader("➕ Add Expense")

amount = st.number_input(
    "Amount",
    min_value=0
)

category = st.selectbox(
    "Category",
    [
        "Food & Groceries",
        "Rent",
        "Transport",
        "Shopping",
        "Healthcare",
        "Entertainment"
    ]
)

if st.button("Add Expense"):

    st.success(
        f"Expense Added: ₹{amount}"
    )

import requests

