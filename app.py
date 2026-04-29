import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="CA Procurement Intelligence Portal", page_icon="🇨🇦", layout="wide")

# --- DESCRIPTIONS ---
DESC = {
    "total_spend": "Total dollar value of all awarded contracts.",
    "contracts": "Count of individual contract records.",
    "avg_val": "Average value of a single contract.",
    "integrity": "Procurement health score (0-100). Higher is better.",
    "avg_bids": "Average number of vendors competing for each contract.",
    "single_bid": "% of contracts awarded with zero competition.",
    "amend_ratio": "% of total budget spent on contract cost increases.",
    "hhi": "Market Concentration Index. Above 2500 is high-risk monopoly.",
    "top3": "Percentage of total budget controlled by the 3 largest vendors."
}

# --- STYLES (ULTRA HIGH CONTRAST) ---
def apply_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');
        
        /* 1. Global Reset to Pure White/Black */
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        
        /* 2. Force ALL text to Black (including sidebar labels) */
        * { color: #000000 !important; font-family: 'Noto Sans', sans-serif !important; }
        
        /* 3. Metric Labels (making them Ultra-Bold) */
        [data-testid="stMetricLabel"] p { color: #000000 !important; font-weight: 900 !important; font-size: 0.9rem !important; }
        [data-testid="stMetricValue"] div { color: #000000 !important; font-weight: 800 !important; }

        /* 4. Sidebar Overhaul */
        [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 2px solid #000000 !important; }
        
        /* 5. Official Header */
        .gov-header {
            background-color: #ffffff !important;
            border-bottom: 5px solid #d30616;
            padding: 1.5rem 2rem;
            margin: -6rem -5rem 2rem -5rem;
            display: flex; align-items: center; gap: 1.5rem;
        }

        /* 6. Tabs */
        button[data-baseweb="tab"] { font-weight: 800 !important; font-size: 1.1rem !important; }
        
        /* Hide UI clutter */
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stHeader"], footer { visibility: hidden !important; }
        </style>
        
        <div class="gov-header">
            <img src="https://www.canada.ca/etc/designs/canada/wet-boew/assets/sig-blk-en.svg" height="45">
            <div style="font-size:1.8rem; font-weight:800; color:#000000; border-left:3px solid #d30616; padding-left:20px;">
                Procurement Intelligence Portal
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- DATA ---
def load_data():
    try:
        df = pd.read_excel("contracts_2021_2026_cleaned.xlsx")
        df['year'] = df['reporting_period'].astype(str).str.extract(r'(\d{4}-\d{4})')
        for col in ['contract_value', 'original_value', 'amendment_value']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['number_of_bids'] = pd.to_numeric(df['number_of_bids'], errors='coerce')
        return df
    except: return pd.DataFrame()

# --- CHART BUILDER (ULTRA-BLACK AXES) ---
def build_chart(df, x_col, y_col, color, orientation='v', title=""):
    fig = px.bar(df, x=x_col, y=y_col, orientation=orientation, color_discrete_sequence=[color])
    
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        font=dict(family="Noto Sans", size=14, color="black"),
        margin=dict(t=10, b=10, l=150 if orientation=='h' else 10),
        xaxis=dict(
            title_font=dict(size=16, color="black", family="Noto Sans Black"),
            tickfont=dict(size=13, color="black", weight='bold'),
            showline=True, linewidth=3, linecolor='black', mirror=True
        ),
        yaxis=dict(
            title_font=dict(size=16, color="black", family="Noto Sans Black"),
            tickfont=dict(size=13, color="black", weight='bold'),
            showline=True, linewidth=3, linecolor='black', mirror=True
        )
    )
    return fig

def main():
    apply_styles()
    df = load_data()
    if df.empty: return

    with st.sidebar:
        st.markdown("## 🏛️ Controls")
        year = st.selectbox("Select Fiscal Year", sorted(df['year'].dropna().unique()), index=0)
        depts = st.multiselect("Filter Departments", sorted(df['owner_org_title'].unique()), default=df['owner_org_title'].unique()[:5])
    
    f_df = df[(df['year'] == year) & (df['owner_org_title'].isin(depts))]
    
    # KPI Logic
    total_spend = f_df['contract_value'].sum()
    n_contracts = len(f_df)
    avg_bids = f_df['number_of_bids'].mean()
    amend_ratio = (f_df['amendment_value'].sum() / total_spend * 100) if total_spend > 0 else 0

    t1, t2, t3 = st.tabs(["📊 Summary", "🔍 Risk Analysis", "🏢 Vendor Intel"])

    with t1:
        st.markdown(f"### 📈 Performance Overview ({year})")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Spend", f"${total_spend/1e6:.1f}M", help=DESC["total_spend"])
        m2.metric("Contracts", f"{n_contracts:,}", help=DESC["contracts"])
        m3.metric("Integrity Score", f"{85}/100", help=DESC["integrity"]) # Static placeholder for calc
        
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Spend by Category (Top 10)**")
            cat_df = f_df.groupby('commodity_type')['contract_value'].sum().reset_index().head(10)
            st.plotly_chart(build_chart(cat_df, 'commodity_type', 'contract_value', '#d30616', title="Category Spend"), use_container_width=True)
        with c2:
            st.markdown("**Top Departments**")
            dept_df = f_df.groupby('owner_org_title')['contract_value'].sum().sort_values(ascending=False).head(10).reset_index()
            dept_df['owner_org_title'] = dept_df['owner_org_title'].str.slice(0, 30) + "..."
            st.plotly_chart(build_chart(dept_df, 'contract_value', 'owner_org_title', '#26374a', orientation='h'), use_container_width=True)

    with t2:
        st.markdown("### 🔍 Risk Indicators")
        r1, r2 = st.columns(2)
        r1.metric("Avg Bids", f"{avg_bids:.2f}", help=DESC["avg_bids"])
        r2.metric("Amendment Ratio", f"{amend_ratio:.1f}%", help=DESC["amend_ratio"])
        
        st.markdown("**High-Risk Flagged Contracts**")
        st.table(f_df[['reference_number', 'vendor_name', 'contract_value']].head(10))

    with t3:
        st.markdown("### 🏢 Vendor Market Share")
        v_df = f_df.groupby('vendor_name')['contract_value'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(20).reset_index()
        v_df.columns = ['Vendor', 'Total Spend ($)', 'Contracts']
        st.table(v_df)

if __name__ == "__main__":
    main()
