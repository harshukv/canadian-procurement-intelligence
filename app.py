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
        self.multi_cell(0, 
