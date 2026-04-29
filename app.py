import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="CA Procurement Intelligence Portal",
    page_icon="🇨🇦",
    layout="wide"
)

# --- CONSTANTS ---
TYPE_MAP = {'S': 'Services', 'G': 'Goods', 'C': 'Construction'}
COLUMN_MAP = {
    'reference_number': 'Reference #',
    'vendor_name': 'Vendor Name',
    'original_value': 'Original Value ($)',
    'amendment_value': 'Amendment Value ($)',
    'contract_value': 'Contract Value ($)',
    'commodity_full': 'Category',
    'owner_org_title': 'Department',
    'number_of_bids': 'Bids'
}
TOOLTIPS = {
    "total_spend": "Aggregate dollar value of all contracts awarded in the selected period.",
    "contracts": "Total number of individual contracts signed between the government and vendors.",
    "avg_val": "Mathematical average cost per contract.",
    "risk_score": "Procurement health score (0–100). Higher is healthier. Penalizes low competition and high cost overruns.",
    "avg_bids": "Average number of competing vendors per contract. Below 2 indicates critically low competition.",
    "single_bid": "% of contracts where only one vendor submitted a bid. A high rate is a key risk indicator.",
    "amend_ratio": "Total amendments relative to total budget. High values indicate poor initial scoping.",
    "hhi": "Herfindahl-Hirschman Index. Above 2,500 indicates monopoly/oligopoly risk.",
    "top3": "Share of total budget held by the top 3 vendors. High concentration reduces competition."
}

# --- CHART DEFAULTS ---
CHART_LAYOUT = dict(
    paper_bgcolor='#ffffff',
    plot_bgcolor='#ffffff',
    font=dict(family='Noto Sans, sans-serif', color='#26374a', size=13),
    margin=dict(t=10, b=30, l=10, r=10),
)
AXIS_STYLE = dict(
    showgrid=True, gridcolor='#f0f0f0',
    linecolor='#e0e0e0', tickfont=dict(color='#555', size=12)
)

# --- STYLES ---
def apply_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700;800&display=swap');

        /* ── BASE ── */
        html, body { background-color: #f0f2f5 !important; font-family: 'Noto Sans', sans-serif !important; }

        [data-testid="stApp"], [data-testid="stAppViewContainer"],
        [data-testid="stMain"], [data-testid="stMainBlockContainer"],
        [data-testid="stVerticalBlock"], .main, .block-container {
            background-color: #f0f2f5 !important;
            font-family: 'Noto Sans', sans-serif !important;
            color: #26374a !important;
            padding-top: 0 !important;
        }

        /* ── SIDEBAR ── */
        section[data-testid="stSidebar"] > div {
            background-color: #ffffff !important;
            border-right: 1px solid #dde3ea !important;
            padding-top: 0 !important;
        }
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] .stCaption { color: #26374a !important; }
        .sidebar-filter-label {
            font-size: 0.68rem; font-weight: 700; letter-spacing: 1.2px;
            text-transform: uppercase; color: #999 !important;
            margin: 16px 0 4px 0; display: block;
        }

        /* ── HIDE CHROME ── */
        [data-testid="stToolbar"], [data-testid="stDecoration"],
        [data-testid="stHeader"], footer {
            visibility: hidden !important; display: none !important;
        }

        /* ── DROPDOWNS & MULTISELECT ── */
        div[data-baseweb="select"] > div,
        div[data-baseweb="popover"], div[data-baseweb="menu"] {
            background-color: #ffffff !important;
            color: #26374a !important;
            border-color: #c8d0d8 !important;
            border-radius: 6px !important;
        }
        [data-baseweb="tag"] {
            background-color: #eef1f5 !important;
            color: #26374a !important;
            border: 1px solid #c0ccd8 !important;
            border-radius: 4px !important;
            font-size: 0.78rem !important;
        }
        [data-baseweb="tag"] span, [data-baseweb="tag"] svg {
            color: #26374a !important; fill: #26374a !important;
        }
        ul[role="listbox"], li[role="option"] {
            background-color: #ffffff !important; color: #26374a !important;
        }
        li[role="option"]:hover { background-color: #f2f5f8 !important; }

        /* ── METRIC CARDS ── */
        [data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-left: 4px solid #d30616 !important;
            border-radius: 8px !important;
            padding: 18px 20px !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
        }
        [data-testid="stMetricLabel"] p {
            color: #607080 !important; font-size: 0.82rem !important;
            font-weight: 700 !important; text-transform: uppercase;
            letter-spacing: 0.6px;
        }
        [data-testid="stMetricValue"] {
            color: #1a2a3a !important; font-weight: 800 !important; font-size: 2rem !important;
        }
        [data-testid="stMetricDelta"] { font-size: 0.85rem !important; }
        [data-testid="stMetricDelta"] svg { display: none; }

        /* ── SECTION LABELS ── */
        .sec-label {
            font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
            letter-spacing: 1.4px; color: #d30616; margin-bottom: 4px;
        }
        .sec-title {
            font-size: 1.25rem; font-weight: 700; color: #26374a;
            margin-bottom: 16px; padding-bottom: 10px;
            border-bottom: 1px solid #e8ecf0;
        }
        .chart-label {
            font-size: 0.88rem; font-weight: 700; color: #445566;
            text-transform: uppercase; letter-spacing: 0.5px;
            margin-bottom: 6px;
        }

        /* ── TABS ── */
        [data-baseweb="tab-list"] {
            background-color: #ffffff !important;
            border-bottom: 2px solid #e0e6ec !important;
            padding: 0 8px !important;
        }
        [data-baseweb="tab"] {
            background-color: #ffffff !important;
            color: #607080 !important;
            font-weight: 700 !important; font-size: 1rem !important;
            padding: 14px 24px !important;
            border-bottom: 3px solid transparent !important;
        }
        [aria-selected="true"][data-baseweb="tab"] {
            color: #d30616 !important;
            border-bottom: 3px solid #d30616 !important;
        }
        [data-testid="stTabsContent"] {
            background-color: #f0f2f5 !important;
            padding-top: 20px !important;
        }

        /* ── BODY TEXT & CAPTIONS ── */
        p, li, .stCaption, .stMarkdown p { font-size: 0.95rem !important; }
        small, .stCaption { font-size: 0.82rem !important; color: #667788 !important; }
        label { font-size: 0.9rem !important; font-weight: 600 !important; }
        h3 { font-size: 1.3rem !important; }

        /* ── PLOTLY ── */
        iframe, .js-plotly-plot, .plotly-graph-div {
            background-color: #ffffff !important;
            border-radius: 8px !important;
        }

        /* ── DATAFRAMES ── */
        [data-testid="stDataFrame"],
        [data-testid="stDataFrame"] > div,
        .dvn-scroller, .dvn-head, .dvn-body {
            background-color: #ffffff !important; color: #26374a !important;
        }

        /* ── ALERTS ── */
        [data-testid="stAlert"] {
            border-radius: 8px !important; font-size: 0.88rem !important;
        }

        hr { border-color: #e2e8f0 !important; }

        /* ── HEADER ── */
        .gov-header {
            background-color: #ffffff;
            border-bottom: 3px solid #d30616;
            padding: 0.8rem 1.5rem;
            display: flex; align-items: center;
            box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        }
        .gov-header-inner { display: flex; align-items: center; gap: 1.2rem; }
        .gov-divider { width: 1px; height: 32px; background: #d30616; }
        .gov-title { color: #26374a; font-size: 1.25rem; font-weight: 800; line-height: 1.2; }
        .gov-subtitle { color: #777; font-size: 0.72rem; margin-top: 3px;
            text-transform: uppercase; letter-spacing: 0.6px; }

        /* ── FOOTER ── */
        .gov-footer {
            margin-top: 48px; padding: 14px 1.5rem;
            border-top: 2px solid #d30616; background: #ffffff;
            display: flex; justify-content: space-between; align-items: center;
            font-size: 0.72rem; color: #888;
        }
        </style>

        <div class="gov-header">
            <div class="gov-header-inner">
                <img src="https://www.canada.ca/etc/designs/canada/wet-boew/assets/sig-blk-en.svg"
                     alt="Government of Canada" style="height:34px; width:auto;" />
                <div class="gov-divider"></div>
                <div>
                    <div class="gov-title">CA Procurement Intelligence Portal</div>
                    <div class="gov-subtitle">Public Spending Transparency &amp; Analytics</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


# --- DATA ---
@st.cache_data
def load_and_prepare_data():
    try:
        df = pd.read_excel("contracts_2021_2026_cleaned.xlsx")
        df['commodity_full'] = df['commodity_type'].map(TYPE_MAP).fillna(df['commodity_type'])
        df['year'] = df['reporting_period'].astype(str).str.extract(r'(\d{4}-\d{4})')
        for col in ['contract_value', 'original_value', 'amendment_value']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['number_of_bids'] = pd.to_numeric(df['number_of_bids'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"❌ Could not load data: {e}")
        return pd.DataFrame()


def calculate_kpis(df):
    if df.empty:
        return {k: 0 for k in ["total_spend", "contracts", "avg_val", "amendment_ratio",
                                "avg_bids", "hhi", "top_3_share", "risk_score", "single_bid_rate"]}
    total_spend = df['contract_value'].sum()
    n = len(df)
    avg_val = df['contract_value'].mean() if n > 0 else 0
    amendment_ratio = (df['amendment_value'].sum() / total_spend * 100) if total_spend > 0 else 0
    bids = df['number_of_bids'].dropna()
    avg_bids = bids.mean() if not bids.empty else 0
    single_bid_rate = (len(df[df['number_of_bids'] == 1]) / n * 100) if n > 0 else 0
    vpct = df.groupby('vendor_name')['contract_value'].sum() / total_spend * 100 if total_spend > 0 else 0
    hhi = (vpct ** 2).sum()
    top_3_share = vpct.sort_values(ascending=False).head(3).sum()
    risk = 0
    if avg_bids < 1.6: risk += 25
    if single_bid_rate > 60: risk += 20
    if amendment_ratio > 12: risk += 25
    if hhi > 2000: risk += 30
    return dict(total_spend=total_spend, contracts=n, avg_val=avg_val,
                amendment_ratio=amendment_ratio, avg_bids=avg_bids, hhi=hhi,
                top_3_share=top_3_share, risk_score=risk, single_bid_rate=single_bid_rate)


def section(label, title):
    st.markdown(f"<div class='sec-label'>{label}</div><div class='sec-title'>{title}</div>",
                unsafe_allow_html=True)


def chart_label(text):
    st.markdown(f"<div class='chart-label'>{text}</div>", unsafe_allow_html=True)


# --- MAIN ---
def main():
    apply_styles()

    df = load_and_prepare_data()
    if df.empty:
        st.warning("No data available. Ensure `contracts_2021_2026_cleaned.xlsx` is in the repo.")
        return

    # ── SIDEBAR ──
    with st.sidebar:
        st.image("https://www.canada.ca/etc/designs/canada/wet-boew/assets/sig-blk-en.svg", width=170)
        st.markdown("<hr style='margin:10px 0; border-color:#eee;'>", unsafe_allow_html=True)
        st.markdown("<span class='sidebar-filter-label'>Analysis Filters</span>", unsafe_allow_html=True)

        all_years = sorted(df['year'].dropna().unique().tolist())
        selected_year = st.selectbox("📅 Fiscal Year", all_years,
                                     index=len(all_years) - 1,
                                     help=TOOLTIPS['total_spend'])

        all_depts = sorted(df['owner_org_title'].dropna().unique().tolist())
        selected_dept = st.multiselect("🏛 Department", all_depts, default=all_depts,
                                       help="Select departments to analyze.")

        st.markdown("<hr style='margin:10px 0; border-color:#eee;'>", unsafe_allow_html=True)
        n_sel = len(selected_dept) if selected_dept else 0
        st.caption(f"**{n_sel}** dept(s) · {selected_year}")
        st.caption("Source: Government of Canada Open Data")

    # ── FILTER ──
    year_df = df[df['year'] == selected_year]
    final_df = year_df[year_df['owner_org_title'].isin(selected_dept)] if selected_dept else year_df

    if final_df.empty:
        st.warning("No data for the selected filters. Try adjusting your selection.")
        return

    # ── PREV YEAR ──
    prev_kpis = None
    try:
        p = selected_year.split('-')
        prev_str = f"{int(p[0])-1}-{int(p[1])-1}"
        prev_df = df[df['year'] == prev_str]
        if selected_dept:
            prev_df = prev_df[prev_df['owner_org_title'].isin(selected_dept)]
        if not prev_df.empty:
            prev_kpis = calculate_kpis(prev_df)
    except Exception:
        pass

    kpis = calculate_kpis(final_df)

    # ── TABS ──
    tab1, tab2, tab3 = st.tabs([
        "📊  Executive Summary",
        "🔍  Risk & Competition",
        "🏢  Vendor Intelligence"
    ])

    # ════════════════════════════════════════
    # TAB 1 — EXECUTIVE SUMMARY
    # ════════════════════════════════════════
    with tab1:
        section(f"Fiscal Year {selected_year}", "Performance Overview")

        growth = 0.0
        if prev_kpis and prev_kpis['total_spend'] > 0:
            growth = (kpis['total_spend'] - prev_kpis['total_spend']) / prev_kpis['total_spend'] * 100

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Spend", f"${kpis['total_spend']/1e6:.1f}M",
                  delta=f"{growth:+.1f}% vs prior year", help=TOOLTIPS['total_spend'])
        m2.metric("Total Contracts", f"{kpis['contracts']:,}", help=TOOLTIPS['contracts'])
        m3.metric("Avg Contract Value", f"${kpis['avg_val']/1e3:.1f}K", help=TOOLTIPS['avg_val'])
        rs = kpis['risk_score']
        risk_label = "🟢 LOW RISK" if rs < 40 else ("🟡 MEDIUM RISK" if rs < 70 else "🔴 HIGH RISK")
        m4.metric("System Integrity", f"{100-rs}/100", delta=risk_label, help=TOOLTIPS['risk_score'])

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)

        with c1:
            chart_label("Spending by Category")
            cat = final_df.groupby('commodity_full')['contract_value'].sum().reset_index() \
                          .sort_values('contract_value', ascending=False)
            fig = px.bar(cat, x='commodity_full', y='contract_value',
                         color_discrete_sequence=['#d30616'],
                         labels={'commodity_full': '', 'contract_value': 'Spend ($)'})
            fig.update_layout(**CHART_LAYOUT, showlegend=False, height=280)
            fig.update_xaxes(**AXIS_STYLE)
            fig.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            chart_label("Top Spending Departments")
            dept = final_df.groupby('owner_org_title')['contract_value'].sum() \
                           .sort_values(ascending=False).head(10).reset_index()
            fig2 = px.bar(dept, y='owner_org_title', x='contract_value', orientation='h',
                          color_discrete_sequence=['#26374a'],
                          labels={'owner_org_title': '', 'contract_value': 'Spend ($)'})
            fig2.update_layout(**CHART_LAYOUT, height=280)
            fig2.update_yaxes(categoryorder='total ascending', **AXIS_STYLE)
            fig2.update_xaxes(**AXIS_STYLE)
            st.plotly_chart(fig2, use_container_width=True)

        section("Year-on-Year", "Annual Spending Trend")
        trend = df.groupby('year')['contract_value'].sum().reset_index().sort_values('year')
        fig3 = px.line(trend, x='year', y='contract_value', markers=True,
                       color_discrete_sequence=['#d30616'],
                       labels={'year': 'Fiscal Year', 'contract_value': 'Total Spend ($)'})
        fig3.update_traces(line=dict(width=3), marker=dict(size=8))
        fig3.update_layout(**CHART_LAYOUT, height=280)
        fig3.update_xaxes(**AXIS_STYLE)
        fig3.update_yaxes(**AXIS_STYLE)
        st.plotly_chart(fig3, use_container_width=True)

    # ════════════════════════════════════════
    # TAB 2 — RISK & COMPETITION
    # ════════════════════════════════════════
    with tab2:
        section("Risk Analysis", "Competition & Fiscal Health Indicators")

        r1, r2, r3 = st.columns(3)
        r1.metric("Avg Bids / Contract", f"{kpis['avg_bids']:.2f}", help=TOOLTIPS['avg_bids'])
        r2.metric("Single-Bid Rate", f"{kpis['single_bid_rate']:.1f}%", help=TOOLTIPS['single_bid'])
        r3.metric("Amendment Ratio", f"{kpis['amendment_ratio']:.1f}%", help=TOOLTIPS['amend_ratio'])

        st.info("💡 **Insight:** A high single-bid rate (>60%) combined with high amendment ratios "
                "signals vendor lock-in risk, low competition, and potential budget overruns.")

        section("Bid Distribution", "Competing Bids per Contract")
        bids_filtered = final_df['number_of_bids'].dropna()
        if not bids_filtered.empty:
            fig4 = px.histogram(bids_filtered, nbins=15,
                                color_discrete_sequence=['#d30616'],
                                labels={'value': 'Number of Bids', 'count': 'Contracts'})
            fig4.update_layout(**CHART_LAYOUT, height=280)
            fig4.update_xaxes(**AXIS_STYLE)
            fig4.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig4, use_container_width=True)

        section("Audit Flags", "High-Amendment Contracts — Flagged for Review")
        st.caption("Contracts where amendment value > 50% of original contract value.")
        mask = (final_df['original_value'] > 0) & \
               (final_df['amendment_value'] > final_df['original_value'] * 0.5)
        high_risk = final_df[mask].copy()

        if not high_risk.empty:
            cols = [c for c in ['reference_number', 'vendor_name', 'original_value',
                                 'amendment_value', 'commodity_full'] if c in high_risk.columns]
            disp = high_risk[cols].rename(columns=COLUMN_MAP).head(20).copy()
            for col in ['Original Value ($)', 'Amendment Value ($)']:
                if col in disp.columns:
                    disp[col] = disp[col].apply(lambda x: f'${x:,.0f}')
            st.dataframe(disp, hide_index=True, use_container_width=True, height=380)
        else:
            st.success("✅ No contracts flagged under current filters.")

    # ════════════════════════════════════════
    # TAB 3 — VENDOR INTELLIGENCE
    # ════════════════════════════════════════
    with tab3:
        section("Market Dynamics", "Vendor Concentration & Market Analysis")

        v1, v2 = st.columns(2)
        v1.metric("Top 3 Vendor Share", f"{kpis['top_3_share']:.1f}%", help=TOOLTIPS['top3'])
        v2.metric("Market HHI", f"{kpis['hhi']:.0f}", help=TOOLTIPS['hhi'])

        hhi = kpis['hhi']
        if hhi < 1500:
            st.success(f"✅ HHI = {hhi:.0f} — Competitive market. Low concentration risk.")
        elif hhi < 2500:
            st.warning(f"⚠️ HHI = {hhi:.0f} — Moderately concentrated market.")
        else:
            st.error(f"🚨 HHI = {hhi:.0f} — Highly concentrated. Monopoly/oligopoly risk.")

        chart_label("Top 15 Vendors by Spend")
        top_v = final_df.groupby('vendor_name')['contract_value'].sum() \
                        .sort_values(ascending=False).head(15).reset_index()
        fig5 = px.bar(top_v, y='vendor_name', x='contract_value', orientation='h',
                      color_discrete_sequence=['#d30616'],
                      labels={'vendor_name': '', 'contract_value': 'Total Spend ($)'})
        fig5.update_layout(**CHART_LAYOUT, height=420)
        fig5.update_yaxes(categoryorder='total ascending', **AXIS_STYLE)
        fig5.update_xaxes(**AXIS_STYLE)
        st.plotly_chart(fig5, use_container_width=True)

        section("Top Vendors", "Leading Vendors by Fiscal Volume")
        tbl = final_df.groupby('vendor_name')['contract_value'].agg(['sum', 'count']) \
                      .sort_values('sum', ascending=False).head(20).reset_index()
        tbl.columns = ['Vendor Name', 'Total Spend', 'Contracts']
        tbl['Market Share (%)'] = (tbl['Total Spend'] / kpis['total_spend'] * 100).round(2)
        tbl['Total Spend'] = tbl['Total Spend'].apply(lambda x: f'${x:,.0f}')
        tbl['Market Share (%)'] = tbl['Market Share (%)'].apply(lambda x: f'{x:.2f}%')
        st.dataframe(tbl, hide_index=True, use_container_width=True, height=480)

        st.markdown("""
            <div class="gov-footer">
                <span>&#127464;&#127462; Government of Canada &nbsp;&middot;&nbsp; Procurement Intelligence Portal</span>
                <span>Data: Public Services &amp; Procurement Canada &nbsp;&middot;&nbsp; Open Government Licence</span>
            </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
