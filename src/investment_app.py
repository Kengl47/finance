# streamlit_app.py
import streamlit as st
import plotly.graph_objs as go
from datetime import datetime

# ======================
# Page configuration
# ======================
st.set_page_config(page_title="Investment Dashboard", layout="wide")

# ======================
# Constants
# ======================
FIXED_TAX_RATE_PERCENT = 26.375  # 25% capital gains tax + 5.5% solidarity surcharge

# ======================
# Calculation Functions
# ======================
def wealth_over_time(start_amount, annual_interest, monthly_payment, years, tax_rate_percent):
    tax_rate = tax_rate_percent / 100
    months = years * 12
    monthly_interest = (1 + annual_interest / 100) ** (1/12) - 1
    amount = start_amount
    amounts = [start_amount]
    net_amounts = [start_amount]
    for m in range(1, months + 1):
        amount = amount * (1 + monthly_interest) + monthly_payment
        total_payments = start_amount + monthly_payment * m
        gross_profit = amount - total_payments
        taxes_paid = max(0, gross_profit * tax_rate)
        net_amount = amount - taxes_paid
        amounts.append(amount)
        net_amounts.append(net_amount)
    return amounts, net_amounts

def format_euro(amount):
    return f"{int(round(amount)):,}".replace(",", " ")

def years_to_target(start, interest, monthly_savings, target):
    months = 0
    monthly_interest = (1 + interest / 100) ** (1/12) - 1
    amount = start
    while amount < target:
        amount = amount * (1 + monthly_interest) + monthly_savings
        months += 1
    return months // 12, months % 12

def years_to_target_after_tax(start, interest, monthly_savings, target, tax_rate):
    months = 0
    monthly_interest = (1 + interest / 100) ** (1/12) - 1
    amount = start
    while True:
        amount = amount * (1 + monthly_interest) + monthly_savings
        months += 1
        total_payments = start + monthly_savings * months
        gross_profit = amount - total_payments
        taxes_paid = max(0, gross_profit * tax_rate)
        net_amount = amount - taxes_paid
        if net_amount >= target:
            break
    return months // 12, months % 12

# ======================
# UI: Page Title and Info
# ======================
st.title("Investment Dashboard")
st.markdown("""
This tool helps you visualize how your investments can grow over time. Start by entering an initial investment amount and your monthly contributions. The portfolio grows according to the annual interest rate you specify.  

Set a target amount to see how long it may take to reach your financial goal. Use the sidebar to adjust your starting amount, monthly savings, interest rate, and projection period, and watch the results update instantly.
""")

# ======================
# UI: Input controls
# ======================
with st.sidebar:
    st.header("Inputs")
    start = st.number_input("Start (€):", min_value=0, value=60000, step=1000)
    interest = st.number_input("Interest (% p.a.):", min_value=0.0, value=10.0, step=0.1, format="%.2f")
    monthly_savings = st.number_input("Monthly Savings (€):", min_value=0, value=1500, step=100)
    years = st.number_input("Projection Years:", min_value=1, value=10, step=1)
    target = st.number_input("Target (€):", min_value=0, value=500000, step=10000)
    st.markdown("---")
    if st.button("Recompute"):
        st.experimental_rerun()

# ======================
# Computation & Results
# ======================
tax_rate = FIXED_TAX_RATE_PERCENT / 100
amounts, net_amounts = wealth_over_time(start, interest, monthly_savings, years, FIXED_TAX_RATE_PERCENT)
months_list = list(range(len(amounts)))
current_year = datetime.now().year
years_labels = [str(current_year + m // 12) for m in months_list]
year_ticks = [i for i in range(len(months_list)) if (i % 12 == 0)]
year_labels = [years_labels[i] for i in year_ticks]

final_amount = amounts[-1]
gross_profit = final_amount - (start + monthly_savings * years * 12)
taxes_paid = max(0, gross_profit * tax_rate)
net_profit = gross_profit - taxes_paid
years_needed_net, months_needed_net = years_to_target_after_tax(start, interest, monthly_savings, target, tax_rate)

# ======================
# Layout: Results and Chart
# ======================
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Summary")
    st.markdown(f"**Final amount:** {format_euro(final_amount)} €")
    st.markdown(f"**Gross profit:** {format_euro(gross_profit)} €")
    st.markdown(f"**Taxes paid (est.):** {format_euro(taxes_paid)} €")
    st.markdown(f"**Net profit:** {format_euro(net_profit)} €")
    st.markdown(f"**Time to target (after tax):** {years_needed_net} years, {months_needed_net} months")

with col2:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months_list, y=amounts, mode='lines', name='Gross Wealth'))
    fig.add_trace(go.Scatter(x=months_list, y=net_amounts, mode='lines', name='Net Wealth (after taxes)'))
    fig.update_layout(
        title='Portfolio Growth Over Time',
        xaxis=dict(title='Year', tickmode='array', tickvals=year_ticks, ticktext=year_labels),
        yaxis=dict(title='Wealth (€)', range=[0, None]),
        legend_title='Legend',
        template='plotly_white',
        margin=dict(t=60, l=20, r=20, b=40),
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Note: Taxes are fixed at 26.375%, reflecting the current Bavarian rate (25% capital gains tax plus 5.5% solidarity surcharge).")
