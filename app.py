import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from fpdf import FPDF
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="CA Procurement Intelligence Portal", page_icon="🇨🇦", layout="wide")

# --- STYLES ---
def apply_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;700&display=swap');
        .stApp { background-color: #ffffff !important; color: #000000 !important; }
        * { color: #000000 !important; font-family: 'Noto Sans', sans-serif !important; }
        [data-testid="stMetricLabel"] p { color: #000000 !important; font-weight: 900 !important; }
        [data-testid="stMetricValue"] div { color: #000000 !important; font-weight: 800 !important; }
        [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 2px solid #000000 !important; }
        .header-line { border-bottom: 5px solid #d30616; margin-top: -6rem; margin-bottom: 2rem; padding-bottom: 1rem; }
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stHeader"], footer { visibility: hidden !important; }
        </style>
    """, unsafe_allow_html=True)

# --- DATA ---
def load_data():
    try:
        df = pd.read_excel("contracts_2021_2026_cleaned.xlsx")
        df['year'] = df['reporting_period'].astype(str).str.extract(r'(\d{4}-\d{4})')
        for col in ['contract_value', 'original_value', 'amendment_value', 'number_of_bids']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

# --- OFFICIAL PDF GENERATOR ---
class ProcurementPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('helvetica', 'I', 8)
            self.cell(0, 10, 'Official Procurement Intelligence Report - Restricted', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('helvetica', 'B', 14)
        self.set_text_color(211, 6, 22) # Canada Red
        self.cell(0, 10, label, 0, 1, 'L')
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def chapter_body(self, text):
        self.set_font('helvetica', '', 11)
        self.multi_cell(0, 6, text)
        self.ln()

def generate_pdf_report(f_df, year):
    total_spend = f_df['contract_value'].sum()
    total_orig = f_df['original_value'].sum()
    total_amend = f_df['amendment_value'].sum()
    avg_bids = f_df['number_of_bids'].mean()
    amend_ratio = (total_amend / total_orig * 100) if total_orig > 0 else 0
    top_v = f_df.groupby('vendor_name')['contract_value'].sum().sort_values(ascending=False).head(3)
    top_v_share = (top_v.sum() / total_spend * 100) if total_spend > 0 else 0
    avg_val = f_df['contract_value'].mean()

    pdf = ProcurementPDF()
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font('helvetica', 'B', 24)
    pdf.multi_cell(0, 15, "Government of Canada\nProcurement Intelligence Report", align='C')
    pdf.ln(10)
    pdf.set_font('helvetica', '', 16)
    pdf.cell(0, 10, f"Fiscal Year: {year}", ln=1, align='C')
    pdf.cell(0, 10, f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d')}", ln=1, align='C')
    
    pdf.add_page()
    pdf.chapter_title("1. EXECUTIVE SUMMARY")
    summary = (f"During the fiscal year {year}, the Government of Canada committed a total of "
               f"${total_spend:,.2f} across {len(f_df):,} contract actions. Key observations include "
               f"a vendor concentration of {top_v_share:.1f}% among the top partners and an "
               f"amendment-to-original budget ratio of {amend_ratio:.1f}%.")
    pdf.chapter_body(summary)

    pdf.chapter_title("2. KEY METRICS OVERVIEW")
    pdf.chapter_body(f"Total Spend: ${total_spend:,.2f}\n"
                     f"Number of Contracts: {len(f_df):,}\n"
                     f"Average Contract Value: ${avg_val:,.2f}")

    pdf.chapter_title("3. COMPETITION & RISK ANALYSIS")
    risk_text = (f"Average Bids per Contract: {avg_bids:.2f}\n"
                 f"Amendment Ratio: {amend_ratio:.1f}%")
    pdf.chapter_body(risk_text)

    pdf.chapter_title("4. GLOSSARY")
    glossary = ("Contract Value: Final total dollar amount including amendments.\n"
                "Amendment Value: Costs added after initial award.\n"
                "Number of Bids: Count of vendors competing for the work.")
    pdf.chapter_body(glossary)
    return pdf.output()

def main():
    apply_styles()
    df = load_data()
    if df.empty: return

    st.markdown('<div class="header-line"></div>', unsafe_allow_html=True)
    h_col1, h_col2 = st.columns([9, 2])
    
    with h_col1:
        st.image("https://www.canada.ca/etc/designs/canada/wet-boew/assets/sig-blk-en.svg", width=350)
        st.markdown("<h1 style='margin-top:15px; font-weight:800;'>Procurement Intelligence Portal</h1>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## 🏛️ Controls")
        year = st.selectbox("Select Fiscal Year", sorted(df['year'].dropna().unique()), index=0)
        depts = st.multiselect("Filter Departments", sorted(df['owner_org_title'].unique()), default=df['owner_org_title'].unique()[:5])
    
    f_df = df[(df['year'] == year) & (df['owner_org_title'].isin(depts))]
    
    try:
        report_pdf = generate_pdf_report(f_df, year)
        with h_col2:
            st.download_button(
                label="📥 Download PDF",
                data=report_pdf,
                file_name=f"official_report_{year.replace('-', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Report generation error: {e}")

    t1, t2, t3 = st.tabs(["📊 Summary", "🔍 Risk Analysis", "🏢 Vendor Intel"])

    with t1:
        st.markdown(f"### 📈 Performance Overview ({year})")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Spend", f"${f_df['contract_value'].sum()/1e6:.1f}M")
        m2.metric("Contracts", f"{len(f_df):,}")
        m3.metric("Integrity Score", "85/100")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Spend by Category**")
            cat_df = f_df.groupby('commodity_type')['contract_value'].sum().reset_index().head(10)
            fig = px.bar(cat_df, x='commodity_type', y='contract_value', color_discrete_sequence=['#d30616'])
            fig.update_layout(paper_bgcolor='white', plot_bgcolor='white', font_color='black')
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("**Top Departments**")
            dept_df = f_df.groupby('owner_org_title')['contract_value'].sum().sort_values(ascending=False).head(10).reset_index()
            fig2 = px.bar(dept_df, y='owner_org_title', x='contract_value', orientation='h', color_discrete_sequence=['#26374a'])
            fig2.update_layout(paper_bgcolor='white', plot_bgcolor='white', font_color='black')
            st.plotly_chart(fig2, use_container_width=True)

    with t2:
        st.markdown("### 🔍 Risk Indicators")
        st.table(f_df[['reference_number', 'vendor_name', 'contract_value']].head(10))

    with t3:
        st.markdown("### 🏢 Vendor Intel")
        v_df = f_df.groupby('vendor_name')['contract_value'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(20).reset_index()
        st.table(v_df)

if __name__ == "__main__":
    main()
