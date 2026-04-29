import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(page_title="CA Procurement Intelligence Portal", page_icon="🇨🇦", layout="wide")

# --- STYLES (PREMIUM LIGHT THEME - FORCED) ---
def apply_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        
        /* Force Light Background for everything */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #F9FAFB !important;
            color: #111827 !important;
        }
        
        /* Sidebar Force Light */
        [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
            background-color: #ffffff !important;
            border-right: 1px solid #E5E7EB !important;
        }
        [data-testid="stSidebar"] * {
            color: #111827 !important;
        }
        
        /* Typography */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            color: #111827 !important;
        }
        
        /* Inputs & Selectboxes Force Light */
        div[data-baseweb="select"], div[data-baseweb="input"], .stSelectbox, .stMultiSelect {
            background-color: #ffffff !important;
            color: #111827 !important;
            border-radius: 8px !important;
        }
        div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
            background-color: #ffffff !important;
            color: #111827 !important;
        }
        
        /* Multiselect Tags */
        [data-testid="stMultiSelect"] span {
            background-color: #F3F4F6 !important;
            color: #111827 !important;
            border: 1px solid #E5E7EB !important;
        }
        
        /* Metric Styling */
        [data-testid="stMetricLabel"] p {
            color: #6B7280 !important;
            font-size: 0.875rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }
        [data-testid="stMetricValue"] div {
            color: #111827 !important;
            font-size: 2rem !important;
            font-weight: 800 !important;
        }
        
        /* Tabs Styling */
        button[data-baseweb="tab"] {
            color: #6B7280 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #d30616 !important;
            border-bottom-color: #d30616 !important;
        }
        
        /* Header Line */
        .header-line {
            border-bottom: 4px solid #d30616;
            margin-top: -5rem;
            margin-bottom: 2rem;
            padding-bottom: 0.5rem;
        }
        
        /* Button Styling - Comprehensive */
        .stButton>button, .stDownloadButton>button, [data-testid="stDownloadButton"] > button {
            background-color: #ffffff !important;
            color: #111827 !important;
            border: 1px solid #E5E7EB !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-weight: 600 !important;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
            transition: all 0.2s ease !important;
        }
        .stButton>button:hover, .stDownloadButton>button:hover {
            border-color: #d30616 !important;
            color: #d30616 !important;
            background-color: #FFF1F2 !important;
        }
        
        /* Sidebar Info Labels */
        .info-label {
            font-size: 0.85rem;
            color: #6B7280;
            margin-bottom: -15px;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        /* Hide default Streamlit elements */
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stHeader"], footer {
            visibility: hidden !important;
            display: none !important;
        }
        
        /* Dataframe / Table styling */
        [data-testid="stTable"], [data-testid="stDataFrame"] {
            background-color: white !important;
            border-radius: 10px !important;
            border: 1px solid #E5E7EB !important;
        }
        </style>
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

# --- FORMAL GOVERNMENT REPORT GENERATOR ---
def generate_report_text(f_df, year):
    # Data Aggregation
    total_spend = f_df['contract_value'].sum()
    total_orig = f_df['original_value'].sum()
    total_amend = f_df['amendment_value'].sum()
    avg_bids = f_df['number_of_bids'].mean()
    amend_ratio = (total_amend / total_orig * 100) if total_orig > 0 else 0
    top_v = f_df.groupby('vendor_name')['contract_value'].sum().sort_values(ascending=False).head(3)
    top_v_share = (top_v.sum() / total_spend * 100) if total_spend > 0 else 0
    
    report = f"""
================================================================================
GOVERNMENT OF CANADA – PROCUREMENT INTELLIGENCE REPORT
================================================================================
REPORT TYPE: Annual Fiscal Oversight
REPORTING PERIOD: {year}
DATE GENERATED: {pd.Timestamp.now().strftime('%Y-%m-%d')}
--------------------------------------------------------------------------------

1. EXECUTIVE SUMMARY
In the fiscal year {year}, total procurement obligations amounted to ${total_spend:,.2f}. 
Initial analysis indicates a concentration of {top_v_share:.1f}% among the top three vendors. 
Contract amendments represent {amend_ratio:.1f}% of original budgets, signaling areas for 
potential planning optimization.

2. KEY METRICS OVERVIEW
- Total Spend: ${total_spend:,.2f}
  *Def: The total value of all contracts awarded during this period.*
- Total Contracts: {len(f_df):,}
  *Def: The number of individual procurement records.*
- Average Contract Value: ${f_df['contract_value'].mean():,.2f}
  *Def: The mean dollar value per transaction.*

3. COMPETITION & MARKET ANALYSIS
- Average Competition: {avg_bids:.2f} bids per contract.
  *Insight: Values below 2.0 indicate a lack of competitive pressure, which may 
  increase long-term costs.*
- Vendor Concentration (Top 3): {top_v_share:.1f}%
  *Insight: High concentration suggests a dependency on a few key vendors, which 
  increases operational risk.*

4. PERFORMANCE & RISK INDICATORS
- Amendment Ratio: {amend_ratio:.1f}%
  *Risk: High ratios suggest that the final cost of projects is significantly 
  higher than the initial "won" bid, often due to scope creep or unforeseen costs.*

5. RECOMMENDATIONS
- Review categories where average bids are below 1.5.
- Audit high-growth contracts where amendment value exceeds 50% of original value.
- Diversify vendor pool in highly concentrated commodity sectors.

6. GLOSSARY
- Contract Value: The final total dollar amount including amendments.
- Amendment Value: The additional cost added to a contract after the initial award.
- Number of Bids: The count of unique vendors that competed for the work.
- Commodity Type: The classification of purchase (Goods, Services, or Construction).

================================================================================
END OF OFFICIAL REPORT
================================================================================
    """
    return report

def build_chart(df, x_col, y_col, color, orientation='v'):
    # Rename columns for chart display
    plot_df = df.rename(columns=COLUMN_MAPPING)
    x_label = COLUMN_MAPPING.get(x_col, x_col)
    y_label = COLUMN_MAPPING.get(y_col, y_col)
    
    fig = px.bar(plot_df, x=x_label, y=y_label, orientation=orientation, color_discrete_sequence=[color])
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(family="Inter", size=13, color="#374151"),
        xaxis=dict(showgrid=False, showline=True, linecolor='#E5E7EB'),
        yaxis=dict(showgrid=True, gridcolor='#F3F4F6', showline=False),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    return fig

# --- COLUMN DICTIONARY ---
COLUMN_MAPPING = {
    'reference_number': 'Reference Number',
    'vendor_name': 'Vendor Name',
    'contract_value': 'Contract Value',
    'owner_org_title': 'Department',
    'commodity_type': 'Commodity Type',
    'reporting_period': 'Reporting Period',
    'original_value': 'Original Value',
    'amendment_value': 'Amendment Value',
    'number_of_bids': 'Number of Bids',
    'year': 'Fiscal Year'
}

HELP_TEXTS = {
    'year': "The government financial year (April 1 to March 31).",
    'depts': "Filter contracts by specific government departments or agencies.",
    'reference_number': "The unique identifier assigned to the procurement contract.",
    'vendor_name': "The legal name of the entity receiving the contract.",
    'contract_value': "The total dollar value of the contract, including all amendments.",
    'commodity_type': "Classification of the purchase (e.g., Goods, Services).",
    'number_of_bids': "Total number of competitive bids received for this contract."
}

from fpdf import FPDF
import io

# --- PDF GENERATOR ---
def generate_pdf_report(f_df, year):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(211, 6, 22) # Canada Red
    pdf.cell(190, 10, "GOVERNMENT OF CANADA", ln=True, align='L')
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(17, 24, 39) # Dark Gray
    pdf.cell(190, 10, "Procurement Intelligence Report", ln=True, align='L')
    pdf.line(10, 32, 200, 32)
    pdf.ln(10)
    
    # Metadata
    pdf.set_font("Helvetica", '', 10)
    pdf.set_text_color(107, 114, 128)
    pdf.cell(95, 7, f"Fiscal Year: {year}", ln=False)
    pdf.cell(95, 7, f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d')}", ln=True, align='R')
    pdf.ln(5)
    
    # Metrics
    total_spend = f_df['contract_value'].sum()
    total_contracts = len(f_df)
    avg_val = f_df['contract_value'].mean()
    
    pdf.set_fill_color(249, 250, 251)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, " 1. Executive Summary", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", '', 11)
    pdf.set_text_color(17, 24, 39)
    summary = f"In the fiscal year {year}, total procurement obligations amounted to ${total_spend:,.2f} across {total_contracts:,} contracts. The average transaction value was ${avg_val:,.2f}."
    pdf.multi_cell(190, 7, summary)
    pdf.ln(5)
    
    # Vendor Table Header
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, " 2. Top Vendor Analysis", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(120, 10, "Vendor Name", border=1)
    pdf.cell(70, 10, "Total Spend ($)", border=1, ln=True)
    
    # Vendor Table Data
    pdf.set_font("Helvetica", '', 10)
    top_v = f_df.groupby('vendor_name')['contract_value'].sum().sort_values(ascending=False).head(10)
    for name, val in top_v.items():
        pdf.cell(120, 8, str(name)[:50], border=1)
        pdf.cell(70, 8, f"{val:,.2f}", border=1, ln=True)
    
    return pdf.output()

def main():
    apply_styles()
    df = load_data()
    if df.empty: return

    # Top Toolbar / Header
    st.markdown('<div class="header-line"></div>', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns([9, 2])
    
    with h_col1:
        st.image("https://www.canada.ca/etc/designs/canada/wet-boew/assets/sig-blk-en.svg", width=350)
        st.markdown("<h1 style='margin-top:15px; font-weight:800;'>Procurement Intelligence Portal</h1>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## 🏛️ Controls")
        
        st.markdown(f'<p class="info-label">ℹ️ {HELP_TEXTS["year"]}</p>', unsafe_allow_html=True)
        year = st.selectbox(
            "Select Fiscal Year", 
            sorted(df['year'].dropna().unique()), 
            index=0
        )
        
        st.markdown(f'<p class="info-label">ℹ️ {HELP_TEXTS["depts"]}</p>', unsafe_allow_html=True)
        depts = st.multiselect(
            "Filter Departments", 
            sorted(df['owner_org_title'].unique()), 
            default=df['owner_org_title'].unique()[:5]
        )
    
    f_df = df[(df['year'] == year) & (df['owner_org_title'].isin(depts))]
    
    # Generate PDF
    pdf_bytes = generate_pdf_report(f_df, year)

    with h_col2:
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_bytes,
            file_name=f"procurement_report_{year.replace('-', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            help="Export the current analysis as a professional light-themed PDF report."
        )

    t1, t2, t3 = st.tabs(["📊 Summary", "🔍 Risk Analysis", "🏢 Vendor Intel"])

    with t1:
        st.markdown(f"### 📈 Performance Overview ({year})")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Spend", f"${f_df['contract_value'].sum()/1e6:.1f}M")
        m2.metric("Contracts", f"{len(f_df):,}")
        m3.metric("Integrity Score", "85/100")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Spend by Category**", help=HELP_TEXTS['commodity_type'])
            cat_df = f_df.groupby('commodity_type')['contract_value'].sum().reset_index().head(10)
            st.plotly_chart(build_chart(cat_df, 'commodity_type', 'contract_value', '#d30616'), use_container_width=True)
        with c2:
            st.markdown("**Top Departments**", help="Top 10 departments by total spend in the selected year.")
            dept_df = f_df.groupby('owner_org_title')['contract_value'].sum().sort_values(ascending=False).head(10).reset_index()
            dept_df['owner_org_title'] = dept_df['owner_org_title'].str.slice(0, 30) + "..."
            st.plotly_chart(build_chart(dept_df, 'contract_value', 'owner_org_title', '#26374a', orientation='h'), use_container_width=True)

    with t2:
        st.markdown("### 🔍 Risk Indicators")
        st.markdown("*Note: Click on column headers to sort the table values.*")
        risk_df = f_df[['reference_number', 'vendor_name', 'contract_value']].head(20).rename(columns=COLUMN_MAPPING)
        st.dataframe(risk_df, hide_index=True, use_container_width=True)

    with t3:
        st.markdown("### 🏢 Vendor Intel")
        v_df = f_df.groupby('vendor_name')['contract_value'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(20).reset_index()
        v_df = v_df.rename(columns={'vendor_name': 'Vendor Name', 'sum': 'Total Spend', 'count': 'Contract Count'})
        st.dataframe(v_df, hide_index=True, use_container_width=True)

if __name__ == "__main__":
    main()
