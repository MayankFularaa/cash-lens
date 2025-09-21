import streamlit as st
import pandas as pd
import plotly.express as px
import os
import plotly.graph_objects as go


BASE_DIR = r"C:\Users\Admin\Desktop\cash-lens"
# Build file path
data_path = os.path.join(BASE_DIR, "Data", "new_cleaned.csv")

df=pd.read_csv(data_path)

#streamlit dashboard
df['date']=pd.to_datetime(df['date'],errors='coerce')

total_income=df[df['direction']=='Credit']['amount'].sum()
total_expense=df[df['direction']=='Debit']['amount'].sum()
net_savings=total_income-total_expense
transactions_counts=len(df)

def run_dashboard():
    st.set_page_config(page_title="Cashlens Dashboard",layout='wide')


    #top bar
    st.markdown("<h1 style='text-align:center; color:Blue;'>Cashlens Dashboard</h1>", unsafe_allow_html=True)
    st.markdown('-------')

    #KPI

    col1,col2,col3,col4=st.columns(4)
    col1.metric('Total Income',f"Rs.{total_income}")
    col2.metric("Total Expense",f"Rs.{total_expense}")
    col3.metric("Net savings",f"Rs.{net_savings}")
    col4.metric("Transactions",f"{transactions_counts}")

    st.markdown('-------')

    #section 1: Income vs expense trend

    st.subheader("📈 Income vs Expense Trend")

    trend = df.groupby(['date', 'direction'])['amount'].sum().unstack(fill_value=0).reset_index()
    trend['Net'] = trend.get('Credit', 0) - trend.get('Debit', 0)

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=trend['date'], y=trend.get('Credit', 0), mode='lines+markers', name='Credit'))
    fig.add_trace(go.Scatter(x=trend['date'], y=trend.get('Debit', 0), mode='lines+markers', name='Debit'))
    fig.add_trace(go.Scatter(x=trend['date'], y=trend['Net'], mode='lines+markers', name='Net', line=dict(dash='dot')))

    fig.update_layout(
        title="Income vs Expense Trend",
        xaxis_title="Date",
        yaxis_title="Amount",
        legend_title="Type",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)


    st.markdown('-------')

    #section 2: Expense by category (donut/bar chart)
    st.subheader("Expense by category")

    expense_by_cat = df[df['direction']=='Debit'].groupby('category')['amount'].sum().reset_index()

    fig = px.pie(
        expense_by_cat,
        names='category',
        values='amount',
        hole=0.4,
        title="Expense by Category"
    )

    st.plotly_chart(fig)

    st.markdown('-------')

    #section 3: Latest Transactions
    st.subheader("Latest Transactions")
    st.dataframe(df[['id', 'text', 'amount']].tail(10))


