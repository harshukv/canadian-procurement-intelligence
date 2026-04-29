import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="CA Procurement Intelligence Portal", page_icon="🇨🇦", layout="wide")

# --- CONSTANTS ---
TYPE_MAP = {'S': 'Services', 'G': 'Goods', 'C': 'Construction'}
COLUMN_MAP = {
    'reference_number': 'Reference #', 'vendor_name': 'Vendor Name',
    'original_value': 'Original Value ($)', 'amendment_value': 'Amendment Value ($)',
    'contract_value': 'Contract Value ($)', 'commodity_full': 'Category',
    'owner_org_title': 'Department', 'number_of_bids': 'Bids'
}

# --- STYLES ---
def apply_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&display=swap');
        
        /* 1. Global Reset to Light Mode */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
            background-color: #ffffff !important;
            color: #26374a !important;
            font-family: 'Noto Sans', sans-serif !important;
        }

        /* 2. Sidebar Force Light */
        [data-testid="stSidebar"] {
            background-color: #f8f9fa !important;
            border-right: 1px solid #e0e0e0 !important;
        }
        [data-testid="stSidebar"] * {
            color: #26374a !important;
        }

        /* 3. Metric Cards (fixing the white-on-white bug) */
        [data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e0e0e0 !important;
            border-left: 5px solid #d30616 !important;
            padding: 20px !important;
            border-radius: 4px !important;
        }
        [data-testid="stMetricValue"] div {
            color: #26374a !important;
            font-weight: 700 !important;
        }
        [data-testid="stMetricLabel"] p {
            color: #666666 !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            font-size: 0.8rem !important;
        }

        /* 4. Official Government Header */
        .gov-header {
            background-color: #ffffff !important;
            border-bottom: 4px solid #d30616;
            padding: 1.5rem 2rem;
            margin: -6rem -5rem 2rem -5rem; /* Removes default Streamlit gaps */
            display: flex; align-items: center; gap: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        /* 5. Tabs */
        button[data-baseweb="tab"] {
            color: #26374a !important;
            font-weight: 600 !important;
        }
        button[aria-selected="true"] {
            color: #d30616 !important;
            border-bottom-color: #d30616 !important;
        }

        /* 6. Clean Tables */
        .stTable {
            border: 1px solid #eee !important;
        }
        th {
            background-color: #f8f9fa !important;
            color: #26374a !important;
        }

        /* Hide Streamlit Branding */
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stHeader"], footer {
            visibility: hidden !important; display: none !important;
        }
        </style>
        
        <div class="gov-header">
            <img src="https://www.canada.ca/etc/designs/canada/wet-boew/assets/sig-blk-en.svg" height="45">
            <div style="font-size:1.6rem; font-weight:700; color:#26374a; border-left:2px solid #d30616; padding-left:20px;">
                Procurement Intelligence Portal
                <div style="font-size:0.75rem; color:#d30616; text-transform:uppercase; letter-spacing:1px; margin-top:4px;">
                    Transparency & Fiscal Oversight
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- DATA ---
def load_data():
    try:
        df = pd.read_excel("contracts_2021_2026_cleaned.xlsx")
        df['commodity_full'] = df['commodity_type'].map(TYPE_MAP).fillna(df['commodity_type'])
        df['year'] = df['reporting_period'].astype(str).str.extract(r'(\d{4}-\d{4})')
        for col in ['contract_value', 'original_value', 'amendment_value']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['number_of_bids'] = pd.to_numeric(df['number_of_bids'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame()

def calculate_kpis(df):
    if df.empty: return {k: 0 for k in ["total_spend", "contracts", "avg_val", "amend_ratio", "avg_bids", "hhi", "top3", "risk_score", "single_bid"]}
    total_spend = df['contract_value'].sum()
    n = len(df)
    avg_val = df['contract_value'].mean()
    amend_ratio = (df['amendment_value'].sum() / total_spend * 100) if total_spend > 0 else 0
    avg_bids = df['number_of_bids'].mean()
    single_bid = (len(df[df['number_of_bids'] == 1]) / n * 100) if n > 0 else 0
    vpct = df.groupby('vendor_name')['contract_value'].sum() / total_spend * 100 if total_spend > 0 else 0
    hhi = (vpct ** 2).sum()
    top3 = vpct.sort_values(ascending=False).head(3).sum()
    risk = 0
    if avg_bids < 1.6: risk += 25
    if single_bid > 60: risk += 20
    if amend_ratio > 12: risk += 25
    if hhi > 2000: risk += 30
    return {"total_spend": total_spend, "contracts": n, "avg_val": avg_val, "amend_ratio": amend_ratio, "avg_bids": avg_bids, "hhi": hhi, "top3": top3, "risk_score": risk, "single_bid": single_bid}

# --- MAIN ---
def main():
    apply_styles()
    df = load_data()
    if df.empty: return

    # Sidebar
    with st.sidebar:
        st.markdown("### 🏛️ Dashboard Controls")
        all_years = sorted(df['year'].dropna().unique().tolist())
        selected_year = st.selectbox("Fiscal Year", all_years, index=len(all_years)-1)
        all_depts = sorted(df['owner_org_title'].dropna().unique().tolist())
        selected_dept = st.multiselect("Departments", all_depts, default=all_depts)
        st.markdown("---")
        st.write(f"📂 **Total Records:** {len(df):,}")

    # Filter
    f_df = df[df['year'] == selected_year]
    if selected_dept:
        f_df = f_df[f_df['owner_org_title'].isin(selected_dept)]

    kpis = calculate_kpis(f_df)

    with st.sidebar:
        st.write(f"📅 **Filtered Count:** {len(f_df):,}")

    t1, t2, t3 = st.tabs(["📊 Summary", "🔍 Risk Analysis", "🏢 Vendor Intel"])

    with t1:
        st.markdown(f"### 📈 Performance: Fiscal Year {selected_year}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Spend", f"${kpis['total_spend']/1e6:.1f}M")
        m2.metric("Contracts", f"{kpis['contracts']:,}")
        m3.metric("Avg Value", f"${kpis['avg_val']/1e3:.1f}K")
        m4.metric("Integrity Score", f"{100-kpis['risk_score']}/100")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Spend by Category**")
            cat = f_df.groupby('commodity_full')['contract_value'].sum().reset_index()
            fig = px.bar(cat, x='commodity_full', y='contract_value', color_discrete_sequence=['#d30616'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#26374a', margin=dict(t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("**Top Departments**")
            dept = f_df.groupby('owner_org_title')['contract_value'].sum().sort_values(ascending=False).head(10).reset_index()
            fig2 = px.bar(dept, y='owner_org_title', x='contract_value', orientation='h', color_discrete_sequence=['#26374a'])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#26374a', margin=dict(t=0, b=0))
            st.plotly_chart(fig2, use_container_width=True)

    with t2:
        st.markdown("### 🔍 Risk Indicators")
        r1, r2, r3 = st.columns(3)
        r1.metric("Avg Bids", f"{kpis['avg_bids']:.2f}")
        r2.metric("Single-Bid %", f"{kpis['single_bid']:.1f}%")
        r3.metric("Amendment Ratio", f"{kpis['amend_ratio']:.1f}%")

        st.markdown("**High-Risk Flags (>50% Amendment Growth)**")
        high_risk = f_df[f_df['amendment_value'] > (f_df['original_value'] * 0.5)].head(15)
        if not high_risk.empty:
            st.table(high_risk[['reference_number', 'vendor_name', 'original_value', 'amendment_value']].rename(columns=COLUMN_MAP))
        else:
            st.info("No high-risk contracts flagged in this selection.")

    with t3:
        st.markdown("### 🏢 Vendor Market Share")
        v1, v2 = st.columns(2)
        v1.metric("Top 3 Market Share", f"{kpis['top3']:.1f}%")
        v2.metric("Market HHI", f"{kpis['hhi']:.0f}")

        st.markdown("**Top 20 Vendors by Fiscal Volume**")
        top_v = f_df.groupby('vendor_name')['contract_value'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(20).reset_index()
        if not top_v.empty:
            top_v.columns = ['Vendor Name', 'Total Spend ($)', 'Contracts']
            top_v['Total Spend ($)'] = top_v['Total Spend ($)'].apply(lambda x: f"${x:,.0f}")
            st.table(top_v)

if __name__ == "__main__":
    main()
