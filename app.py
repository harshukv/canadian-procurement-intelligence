import streamlit as st
import pandas as pd
import plotly.express as px

# Official Canadian Government Theme
st.set_page_config(page_title="Procurement Intelligence Portal", page_icon="CAN", layout="wide")

st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
            .stMetric { background-color: white; padding: 15px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
                h1, h2, h3 { color: #d33; }
                    </style>
                    """, unsafe_allow_html=True)

st.title("Procurement Intelligence Portal | Portail d'intelligence en approvisionnement")

# Sidebar Filters
st.sidebar.header("Filters")
fiscal_year = st.sidebar.selectbox("Fiscal Year", ["2021-2022", "2022-2023", "2023-2024", "2024-2025", "2025-2026"], index=4, help="Select the fiscal year for analysis.")
dept = st.sidebar.multiselect("Department", ["Agriculture and Agri-Food Canada", "Administrative Tribunals Support Service", "Atlantic Canada Opportunities Agency", "Accessibility Standards Canada"], default=["Agriculture and Agri-Food Canada"], help="Select departments to compare.")
], default=["Agriculture and Agri-Food Canada"], help="Select departments to compare.")

# Tabs
tab1, tab2, tab3 = st.tabs(["Executive Summary", "Risk & Competition", "Vendor Intelligence"])

with tab1:
      st.subheader(f"Fiscal Year {fiscal_year} Performance Overview")
      col1, col2, col3, col4 = st.columns(4)
      col1.metric("Total Spend", "$4.7M", "-59.8%", help="Total dollar value of all contracts.")
      col2.metric("Total Contracts", "92", help="Total number of contracts awarded.")
      col3.metric("Average Contract Value", "$51.3K", help="Average value per contract.")
      col4.metric("System Integrity Score", "80/100", help="Procurement health indicator (0-100).")

    # Placeholder Charts
      c1, c2 = st.columns(2)
      with c1:
                st.write("### Spending by Category")
                df_cat = pd.DataFrame({'Category': ['IT Services', 'Office Supplies', 'Consulting', 'Research'], 'Value': [1200000, 800000, 1500000, 1200000]})
                fig1 = px.pie(df_cat, values='Value', names='Category', color_discrete_sequence=px.colors.qualitative.Reds)
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
          st.write("### Top 10 Spending Organizations")
                      df_org = pd.DataFrame({'Org': ['AAFC', 'ATSSC', 'ACOA', 'ASC'], 'Spend': [9000000, 500000, 400000, 300000]})
        fig2 = px.bar(df_org, x='Org', y='Spend', color_discrete_sequence=['#d33'])
        st.plotly_chart(fig2, use_container_width=True)
with tab2:
      st.subheader("Risk & Competition Metrics")
    st.write("Detailed risk analysis including HHI and single-bid rates.")

with tab3:
      st.subheader("Vendor Intelligence")
    st.write("Analysis of vendor concentration and top performers.")
