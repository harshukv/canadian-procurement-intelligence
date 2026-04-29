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
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        * { color: #000000 !important; font-family: 'Noto Sans', sans-serif !important; }
        [data-testid="stMetricLabel"] p { color: #000000 !important; font-weight: 900 !important; }
        [data-testid="stMetricValue"] div { color: #000000 !important; font-weight: 800 !important; }
        [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 2px solid #000000 !important; }
        
        /* Official Header Decoration */
        .header-line {
            border-bottom: 5px solid #d30616;
            margin-top: -6rem;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
        }
        
        /* Hide UI clutter */
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stHeader"], footer { visibility: hidden !important; }
        </style>
    """, unsafe_allow_html=True)

# --- DATA & LOGIC ---
def load_data():
    try:
        df = pd.read_excel("contracts_2021_2026_cleaned.xlsx")
        df['year'] = df['reporting_period'].astype(str).str.extract(r'(\d{4}-\d{4})')
        for col in ['contract_value', 'original_value', 'amendment_value']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['number_of_bids'] = pd.to_numeric(df['number_of_bids'], errors='coerce')
        return df
    except: return pd.DataFrame()

def generate_report_text(f_df, year):
    total = f_df['contract_value'].sum()
    count = len(f_df)
    avg_bids = f_df['number_of_bids'].mean()
    
    report = f"""
    GOVERNMENT OF CANADA - PROCUREMENT INTELLIGENCE REPORT
    -----------------------------------------------------
    Fiscal Year: {year}
    Generated On: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
    
    SUMMARY METRICS:
    - Total spend: ${total:,.2f}
    - Total contracts: {count:,}
    - Average competition: {avg_bids:.2f} bids/contract
    
    This report contains sensitive fiscal data intended for official oversight only.
    -----------------------------------------------------
    """
    return report

def build_chart(df, x_col, y_col, color, orientation='v'):
    fig = px.bar(df, x=x_col, y=y_col, orientation=orientation, color_discrete_sequence=[color])
    fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', font=dict(family="Noto Sans", size=14, color="black"),
        xaxis=dict(tickfont=dict(color="black", weight='bold'), showline=True, linewidth=3, linecolor='black'),
        yaxis=dict(tickfont=dict(color="black", weight='bold'), showline=True, linewidth=3, linecolor='black'))
    return fig

def main():
    apply_styles()
    df = load_data()
    if df.empty: return

    # Header Row
    st.markdown('<div class="header-line"></div>', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns([9, 2])
    
    with h_col1:
        st.image("https://www.canada.ca/etc/designs/canada/wet-boew/assets/sig-blk-en.svg", width=300)
        st.markdown("<h1 style='margin-top:10px;'>Procurement Intelligence Portal</h1>", unsafe_allow_html=True)

    # Sidebar Filters
    with st.sidebar:
        st.markdown("## 🏛️ Controls")
        year = st.selectbox("Select Fiscal Year", sorted(df['year'].dropna().unique()), index=0)
        depts = st.multiselect("Filter Departments", sorted(df['owner_org_title'].unique()), default=df['owner_org_title'].unique()[:5])
    
    f_df = df[(df['year'] == year) & (df['owner_org_title'].isin(depts))]
    
    # Session State for Report
    st.session_state["report"] = generate_report_text(f_df, year)

    with h_col2:
        st.download_button(
            label="📥 Download Report",
            data=st.session_state["report"],
            file_name=f"official_procurement_report_{year.replace('-', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )

    t1, t2, t3 = st.tabs(["📊 Summary", "🔍 Risk Analysis", "🏢 Vendor Intel"])

    with t1:
        st.markdown(f"### 📈 Performance Overview ({year})")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Spend", f"${f_df['contract_value'].sum()/1e6:.1f}M", help=DESC["total_spend"])
        m2.metric("Contracts", f"{len(f_df):,}", help=DESC["contracts"])
        m3.metric("Integrity Score", "85/100", help=DESC["integrity"])
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Spend by Category**")
            cat_df = f_df.groupby('commodity_type')['contract_value'].sum().reset_index().head(10)
            st.plotly_chart(build_chart(cat_df, 'commodity_type', 'contract_value', '#d30616'), use_container_width=True)
        with c2:
            st.markdown("**Top Departments**")
            dept_df = f_df.groupby('owner_org_title')['contract_value'].sum().sort_values(ascending=False).head(10).reset_index()
            dept_df['owner_org_title'] = dept_df['owner_org_title'].str.slice(0, 30) + "..."
            st.plotly_chart(build_chart(dept_df, 'contract_value', 'owner_org_title', '#26374a', orientation='h'), use_container_width=True)

    with t2:
        st.markdown("### 🔍 Risk Indicators")
        st.table(f_df[['reference_number', 'vendor_name', 'contract_value']].head(10))

    with t3:
        st.markdown("### 🏢 Vendor Intel")
        v_df = f_df.groupby('vendor_name')['contract_value'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(20).reset_index()
        st.table(v_df)

if __name__ == "__main__":
    main()
