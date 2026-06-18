# 💰 AI-Powered Expense Tracker & Budget Management System

## 📌 Overview

AI-Powered Expense Tracker is a smart financial management platform that helps users monitor their expenses, manage monthly budgets, analyze spending habits, and receive AI-driven insights.

The system combines FastAPI, Supabase, Streamlit, and Machine Learning to provide intelligent expense tracking and budget management. Users can add expenses, monitor budget utilization, detect unusual spending patterns, and receive personalized budget recommendations.

---

## 🚀 Features

### User Management

* User Registration and Login
* Secure Authentication
* Personalized Expense Tracking

### Expense Management

* Add Expenses
* Categorize Expenses
* View Expense History
* Monthly Expense Tracking

### Budget Management

* Set Monthly Budget
* Track Budget Utilization
* Monitor Remaining Budget
* Category-wise Spending Analysis

### Analytics Dashboard

* Monthly Spending Overview
* Category-wise Expense Distribution
* Budget Usage Metrics
* Spending Trends Visualization

### AI-Powered Features

#### 1. Anomaly Detection

Detects unusual or suspicious transactions using Isolation Forest.

Example:

* Normal Food Expense: ₹300 – ₹800
* Current Expense: ₹15,000
* Result: Unusual Expense Detected

#### 2. Overspending Prediction

Predicts whether the user is likely to exceed their monthly budget using Random Forest Classification.

Example:

* Budget: ₹50,000
* Current Spend: ₹42,000
* Days Remaining: 7
* Prediction: High Risk of Overspending

#### 3. Budget Recommendation

Provides personalized budget recommendations based on historical spending patterns.

Example:

* Average Monthly Spending: ₹45,000
* Recommended Budget: ₹52,000

---

## 🏗️ System Architecture

User
↓
Streamlit Frontend
↓
FastAPI Backend
↓
Supabase Database
↓
Machine Learning Models
↓
Predictions & Alerts



---

## 🤖 Machine Learning Models

### Isolation Forest

Purpose:

* Detect unusual transactions
* Identify abnormal spending behavior

Features Used:

* Amount
* Month
* Day
* DayOfWeek

Output:

* Normal Transaction
* Anomalous Transaction

---

### Random Forest Classifier

Purpose:

* Predict budget overspending

Features Used:

* Category
* Budget
* Current Spending
* Month

Output:

* Overspend
* Not Overspend

---

## 📊 Dashboard Features

* Monthly Budget
* Total Spending
* Remaining Budget
* Budget Usage Percentage
* Overspending Risk Indicator
* Anomaly Alerts
* Recommended Budget
* Category-wise Expense Charts
* Monthly Spending Trends

---

## 🔮 Future Enhancements

* Receipt OCR Integration
* Bank Statement Import
* UPI Transaction Analysis
* Email/SMS Alerts
* LLM-based Financial Assistant
* Expense Forecasting
* Multi-user Support
* Mobile Application

---

## 🎯 Objectives

* Help users manage expenses efficiently
* Improve budgeting habits
* Detect unusual spending patterns
* Provide AI-driven financial insights
* Promote better financial planning

---

## 📜 Conclusion

This project demonstrates the integration of Machine Learning, FastAPI, Supabase, and Streamlit to build an intelligent expense management platform. The system not only tracks expenses but also provides predictive analytics, anomaly detection, and personalized budget recommendations to help users make informed financial decisions.
