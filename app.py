import streamlit as st
import openpyxl
from collections import defaultdict
import json
import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Procurement Intelligence - Government of Canada", page_icon="CAN", layout="wide")

# Canadian Government UI Styles (CSS)
def apply_canada_styles():
        st.markdown("""
                <style>
                        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');

                                        /* Hide Streamlit Branding & Deploy Button */
                                                [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stHeader"], footer {
                                                            visibility: hidden;
                                                                        display: none;
                                                                                }

                                                                                                html, body, [class*="css"] {
                                                                                                            font-family: 'Noto Sans', sans-serif;
                                                                                                                    }
                                                                                                                            
                                                                                                                                    .header-banner {
                                                                                                                                                background-color: #f5f5f5;
                                                                                                                                                            padding: 1.5rem;
                                                                                                                                                                        border-bottom: 3px solid #d30616;
                                                                                                                                                                                    margin-bottom: 2rem;
                                                                                                                                                                                                display: flex;
                                                                                                                                                                                                            align-items: center;
                                                                                                                                                                                                                    }
                                                                                                                                                                                                                            
                                                                                                                                                                                                                                    .header-title {
                                                                                                                                                                                                                                                color: #333;
                                                                                                                                                                                                                                                            font-size: 24px;
                                                                                                                                                                                                                                                                        font-weight: bold;
                                                                                                                                                                                                                                                                                    margin-left: 15px;
                                                                                                                                                                                                                                                                                            }
                                                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                                                            .canada-flag {
                                                                                                                                                                                                                                                                                                                        color: #d30616;
                                                                                                                                                                                                                                                                                                                                    font-size: 35px;
                                                                                                                                                                                                                                                                                                                                            }
                                                                                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                                                    .metric-card {
                                                                                                                                                                                                                                                                                                                                                                background-color: white;
                                                                                                                                                                                                                                                                                                                                                                            padding: 20px;
                                                                                                                                                                                                                                                                                                                                                                                        border-radius: 5px;
                                                                                                                                                                                                                                                                                                                                                                                                    border: 1px solid #ddd;
                                                                                                                                                                                                                                                                                                                                                                                                                box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
                                                                                                                                                                                                                                                                                                                                                                                                                        }
                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                                                                                                                                                        .stMetric {
                                                                                                                                                                                                                                                                                                                                                                                                                                                    background-color: #f8f9fa;
                                                                                                                                                                                                                                                                                                                                                                                                                                                                padding: 20px;
                                                                                                                                                                                                                                                                                                                                                                                                                                                                            border-left: 5px solid #d30616;
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        border-radius: 4px;
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                }
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                [data-testid="stMetricHelpIcon"] {
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            color: #666;
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    }
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    .risk-high { color: #d30616; font-weight: normal; }
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            .risk-med { color: #f39c12; font-weight: normal; }
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    .risk-low { color: #27ae60; font-weight: normal; }
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    </style>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    <div class="header-banner">
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                <span class="canada-flag">CAN</span>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            <span class="header-title">Procurement Intelligence Portal | Portail d'intelligence en approvisionnement</span>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    </div>
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        """, unsafe_allow_html=True)

# Global Mapping for Sectors & Column Display
TYPE_MAP = {'S': 'Services', 'G': 'Goods', 'C': 'Construction'}
COLUMN_MAP = {
        'reference_number': 'Reference Number',
        'vendor_name': 'Vendor Name',
        'original_value': 'Original Value',
        'amendment_value': 'Amendment Value',
        'contract_value': 'Contract Value',
        'commodity_full': 'Procurement Category',
        'owner_org_title': 'Department Name',
        'number_of_bids': 'Number of Bids'
}

# TOOLTIPS
TOOLTIPS = {
        "total_spend": "The aggregate dollar value of all contracts awarded during the selected period.",
        "contracts": "The total number of individual legal agreements signed between the government and vendors.",
        "avg_val": "The mathematical average cost of a single contract.",
        "risk_score": "A calculated indicator of procurement health. Penalizes low competition and high cost overruns.",
        "avg_bids": "The average number of competing companies per contract. Values below 2 indicate low market competition.",
        "single_bid": "The percentage of contracts awarded where only one vendor submitted a proposal.",
        "amend_ratio": "The total value of price increases (amendments) relative to the total budget. High ratios indicate scoping issues.",
        "hhi": "Herfindahl-Hirschman Index: A measure of market concentration. Scores > 2500 suggest a monopoly/oligopoly risk.",
        "top3": "The portion of the total budget controlled by the top three largest vendors."
}

# --- DATA PROCESSING ---
@st.cache_data
def load_and_prepare_data():
        file_path = "contracts_2021_2026_cleaned.xlsx"
        try:
                    df = pd.read_excel(file_path)
                    df['commodity_full'] = df['commodity_type'].map(TYPE_MAP)
                    df['year'] = df['reporting_period'].str.extract(r'(\d{4}-\d{4})')
                    return df
except Exception as e:
        st.error(f"Error loading cleaned data: {e}")
        return pd.DataFrame()

def calculate_kpis(df):
        total_spend = df['contract_value'].sum()
        total_contracts = len(df)
        avg_val = df['contract_value'].mean()
        total_amendments = df['amendment_value'].sum()
        amendment_ratio = (total_amendments / total_spend) * 100 if total_spend > 0 else 0
        bids_data = df['number_of_bids'].dropna()
        avg_bids = bids_data.mean() if not bids_data.empty else 0
        single_bid_rate = (len(df[df['number_of_bids'] == 1]) / len(df)) * 100
        vendor_shares = df.groupby('vendor_name')['contract_value'].sum()
        vendor_shares_pct = (vendor_shares / total_spend) * 100
        hhi = (vendor_shares_pct**2).sum()
        top_3_share = vendor_shares_pct.sort_values(ascending=False).head(3).sum()
        risk_score = 0
        if avg_bids < 1.6: risk_score += 25
                if single_bid_rate > 60: risk_score += 20
                        if amendment_ratio > 12: risk_score += 25
                                if hhi > 2000: risk_score += 30
                                        return {
                                                    "total_spend": total_spend, "contracts": total_contracts, "avg_val": avg_val,
                                                    "amendment_ratio": amendment_ratio, "avg_bids": avg_bids, "hhi": hhi,
                                                    "top_3_share": top_3_share, "risk_score": risk_score, "single_bid_rate": single_bid_rate
                                        }

# --- MAIN APP ---
def main():
        apply_canada_styles()
    df = load_and_prepare_data()
    if df.empty: return

    # Sidebar Filters
    with st.sidebar:
                st.image("https://www.canada.ca/etc/designs/canada/wet-boew/assets/sig-blk-en.svg", width=200)
                st.markdown("---")
                st.header("Search Filters")
                all_years = sorted(df['year'].unique().tolist())
                selected_year = st.selectbox("Fiscal Year", all_years, index=len(all_years)-1, help="Filter data by the government fiscal year.")
                all_depts = sorted(df['owner_org_title'].unique().tolist())
                selected_dept = st.multiselect("Department", all_depts, default=all_depts[:2], help="Select one or more government organizations to analyze.")

    # Filter Data
    year_df = df[df['year'] == selected_year]
    final_df = year_df[year_df['owner_org_title'].isin(selected_dept)] if selected_dept else year_df

    # Previous Year for Growth
    try:
                prev_year_str = f"{int(selected_year.split('-')[0])-1}-{int(selected_year.split('-')[1])-1}"
                prev_df = df[df['year'] == prev_year_str]
                if selected_dept: prev_df = prev_df[prev_df['owner_org_title'].isin(selected_dept)]
                            prev_kpis = calculate_kpis(prev_df) if not prev_df.empty else None
    except: prev_kpis = None

    current_kpis = calculate_kpis(final_df)

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["Executive Summary", "Risk & Competition", "Vendor Intelligence"])

    with tab1:
                st.markdown(f"### Fiscal Year {selected_year} Performance Overview")
        growth = ((current_kpis['total_spend'] - prev_kpis['total_spend']) / prev_kpis['total_spend']) * 100 if prev_kpis else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Spend", f"${current_kpis['total_spend']/1e6:.1f}M", delta=f"{growth:+.1f}% Growth", help=TOOLTIPS['total_spend'])
        m2.metric("Total Contracts", f"{current_kpis['contracts']:,}", help=TOOLTIPS['contracts'])
        m3.metric("Average Contract Value", f"${current_kpis['avg_val']/1e3:.1f}K", help=TOOLTIPS['avg_val'])

        rs = current_kpis['risk_score']
        rs_class = "risk-low" if rs < 40 else "risk-med" if rs < 70 else "risk-high"
        m4.markdown(f"**System Integrity Score** (i)\\n<h2 class='{rs_class}' style='margin-top:0;'>{100-rs}/100</h2>", unsafe_allow_html=True)
        st.caption(f"Insight: {TOOLTIPS['risk_score']}")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
                        st.write("**Spending by Category**")
                        cat_data = final_df.groupby('commodity_full')['contract_value'].sum().reset_index()
                        fig_cat = px.bar(cat_data, x='commodity_full', y='contract_value', color_discrete_sequence=['#d30616'], labels={'commodity_full': 'Sector', 'contract_value': 'Spend ($)'})
                        fig_cat.update_layout(showlegend=False, margin=dict(t=10, b=10))
                        st.plotly_chart(fig_cat, use_container_width=True)
                    with c2:
                                    st.write("**Top 10 Spending Organizations**")
                                    dept_data = final_df.groupby('owner_org_title')['contract_value'].sum().sort_values(ascending=False).head(10).reset_index()
                                    fig_dept = px.bar(dept_data, y='owner_org_title', x='contract_value', orientation='h', color_discrete_sequence=['#333'])
                                    fig_dept.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Total Spend ($)", yaxis_title="")
                                    st.plotly_chart(fig_dept, use_container_width=True)

    with tab2:
                st.markdown("### Competition & Fiscal Risk Analysis")
                r1, r2, r3 = st.columns(3)
        r1.metric("Average Bids per Contract", f"{current_kpis['avg_bids']:.2f}", help=TOOLTIPS['avg_bids'])
        r2.metric("Single-Bid Rate", f"{current_kpis['single_bid_rate']:.1f}%", help=TOOLTIPS['single_bid'])
        r3.metric("Amendment-to-Spend Ratio", f"{current_kpis['amendment_ratio']:.1f}%", help=TOOLTIPS['amend_ratio'])


    with tab3:
                st.markdown("### Market Dynamics & Vendor Concentration")
        v1, v2 = st.columns(2)
        v1.metric("Top 3 Vendor Market Share", f"{current_kpis['top_3_share']:.1f}%", help=TOOLTIPS['top3'])
        v2.metric("Market Concentration (HHI)", f"{current_kpis['hhi']:.0f}", help=TOOLTIPS['hhi'])

        st.write("**Top Vendors by Fiscal Volume**")
        top_vendors = final_df.groupby('vendor_name')['contract_value'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(15).reset_index()
        top_vendors.columns = ['Vendor Name', 'Total Spend ($)', 'Contract Count']
        st.dataframe(top_vendors.style.format({'Total Spend ($)': '${:,.2f}'}), hide_index=True, use_container_width=True)

if __name__ == "__main__":
        main()
