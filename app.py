import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Procurement Intelligence - Government of Canada",
    page_icon="🇨🇦",
    layout="wide"
)

# --- CONSTANTS ---
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

TOOLTIPS = {
    "total_spend": "The aggregate dollar value of all contracts awarded during the selected period.",
    "contracts": "The total number of individual legal agreements signed between the government and vendors.",
    "avg_val": "The mathematical average cost of a single contract.",
    "risk_score": "A calculated indicator of procurement health (0-100). A higher score means better health. Penalizes low competition and high cost overruns.",
    "avg_bids": "The average number of competing companies per contract. Values below 2 indicate critically low market competition.",
    "single_bid": "The percentage of contracts awarded where only one vendor submitted a proposal. A high rate is a key risk indicator.",
    "amend_ratio": "The total value of price increases (amendments) relative to the total budget. High ratios indicate poor initial scoping.",
    "hhi": "Herfindahl-Hirschman Index: Measures market concentration. Scores above 2,500 indicate a monopoly or oligopoly risk.",
    "top3": "The share of the total budget controlled by the top three largest vendors. High concentration reduces competitive pressure."
}

# --- STYLES ---
def apply_canada_styles():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;600;700&display=swap');

        /* Hide Streamlit chrome */
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stHeader"],
        footer { visibility: hidden; display: none; }

        html, body, [class*="css"] {
            font-family: 'Noto Sans', sans-serif;
        }

        .header-banner {
            background-color: #f5f5f5;
            padding: 1.2rem 2rem;
            border-bottom: 4px solid #d30616;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .header-title {
            color: #26374a;
            font-size: 1.3rem;
            font-weight: 700;
        }
        .header-subtitle {
            color: #555;
            font-size: 0.85rem;
        }

        .stMetric {
            background-color: #ffffff;
            padding: 18px;
            border-left: 5px solid #d30616;
            border-radius: 4px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }

        .risk-high { color: #d30616; font-weight: 600; }
        .risk-med  { color: #e37c22; font-weight: 600; }
        .risk-low  { color: #278400; font-weight: 600; }

        .stTabs [data-baseweb="tab"] {
            font-size: 0.95rem;
            font-weight: 600;
            color: #26374a;
        }
        </style>

        <div class="header-banner">
            <span style="font-size:2.2rem;">🇨🇦</span>
            <div>
                <div class="header-title">
                    Procurement Intelligence Portal &nbsp;|&nbsp; Portail d'intelligence en approvisionnement
                </div>
                <div class="header-subtitle">
                    Government of Canada &nbsp;·&nbsp; Public Spending Transparency Dashboard
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
        df['contract_value'] = pd.to_numeric(df['contract_value'], errors='coerce').fillna(0)
        df['original_value'] = pd.to_numeric(df['original_value'], errors='coerce').fillna(0)
        df['amendment_value'] = pd.to_numeric(df['amendment_value'], errors='coerce').fillna(0)
        df['number_of_bids'] = pd.to_numeric(df['number_of_bids'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"❌ Could not load data file: {e}")
        return pd.DataFrame()


def calculate_kpis(df):
    if df.empty:
        return {k: 0 for k in ["total_spend", "contracts", "avg_val", "amendment_ratio",
                                "avg_bids", "hhi", "top_3_share", "risk_score", "single_bid_rate"]}

    total_spend = df['contract_value'].sum()
    total_contracts = len(df)
    avg_val = df['contract_value'].mean() if total_contracts > 0 else 0
    total_amendments = df['amendment_value'].sum()
    amendment_ratio = (total_amendments / total_spend * 100) if total_spend > 0 else 0

    bids_data = df['number_of_bids'].dropna()
    avg_bids = bids_data.mean() if not bids_data.empty else 0
    single_bid_count = len(df[df['number_of_bids'] == 1])
    single_bid_rate = (single_bid_count / total_contracts * 100) if total_contracts > 0 else 0

    vendor_shares = df.groupby('vendor_name')['contract_value'].sum()
    vendor_pct = (vendor_shares / total_spend * 100) if total_spend > 0 else vendor_shares * 0
    hhi = (vendor_pct ** 2).sum()
    top_3_share = vendor_pct.sort_values(ascending=False).head(3).sum()

    risk_score = 0
    if avg_bids < 1.6:
        risk_score += 25
    if single_bid_rate > 60:
        risk_score += 20
    if amendment_ratio > 12:
        risk_score += 25
    if hhi > 2000:
        risk_score += 30

    return {
        "total_spend": total_spend,
        "contracts": total_contracts,
        "avg_val": avg_val,
        "amendment_ratio": amendment_ratio,
        "avg_bids": avg_bids,
        "hhi": hhi,
        "top_3_share": top_3_share,
        "risk_score": risk_score,
        "single_bid_rate": single_bid_rate
    }


# --- MAIN ---
def main():
    apply_canada_styles()

    df = load_and_prepare_data()
    if df.empty:
        st.warning("No data available. Please ensure `contracts_2021_2026_cleaned.xlsx` is present.")
        return

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://www.canada.ca/etc/designs/canada/wet-boew/assets/sig-blk-en.svg", width=200)
        st.markdown("---")
        st.header("🔎 Filters")

        all_years = sorted(df['year'].dropna().unique().tolist())
        selected_year = st.selectbox(
            "Fiscal Year",
            all_years,
            index=len(all_years) - 1,
            help="Filter data by the government fiscal year."
        )

        all_depts = sorted(df['owner_org_title'].dropna().unique().tolist())
        selected_dept = st.multiselect(
            "Department",
            all_depts,
            default=all_depts,
            help="Select one or more government organizations to analyze."
        )
        st.markdown("---")
        st.caption("Data Source: Government of Canada Open Data")

    # --- FILTER DATA ---
    year_df = df[df['year'] == selected_year]
    final_df = year_df[year_df['owner_org_title'].isin(selected_dept)] if selected_dept else year_df

    if final_df.empty:
        st.warning("No data found for the selected filters. Try adjusting your selection.")
        return

    # --- PREVIOUS YEAR KPIs ---
    prev_kpis = None
    try:
        parts = selected_year.split('-')
        prev_year_str = f"{int(parts[0]) - 1}-{int(parts[1]) - 1}"
        prev_df = df[df['year'] == prev_year_str]
        if selected_dept:
            prev_df = prev_df[prev_df['owner_org_title'].isin(selected_dept)]
        if not prev_df.empty:
            prev_kpis = calculate_kpis(prev_df)
    except Exception:
        prev_kpis = None

    current_kpis = calculate_kpis(final_df)

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs([
        "📊 Executive Summary",
        "🔍 Risk & Competition",
        "🏢 Vendor Intelligence"
    ])

    # ===== TAB 1: EXECUTIVE SUMMARY =====
    with tab1:
        st.markdown(f"### Fiscal Year {selected_year} — Performance Overview")

        growth = 0.0
        if prev_kpis and prev_kpis['total_spend'] > 0:
            growth = (current_kpis['total_spend'] - prev_kpis['total_spend']) / prev_kpis['total_spend'] * 100

        m1, m2, m3, m4 = st.columns(4)
        m1.metric(
            "Total Spend",
            f"${current_kpis['total_spend'] / 1e6:.1f}M",
            delta=f"{growth:+.1f}% vs prior year",
            help=TOOLTIPS['total_spend']
        )
        m2.metric(
            "Total Contracts",
            f"{current_kpis['contracts']:,}",
            help=TOOLTIPS['contracts']
        )
        m3.metric(
            "Average Contract Value",
            f"${current_kpis['avg_val'] / 1e3:.1f}K",
            help=TOOLTIPS['avg_val']
        )

        rs = current_kpis['risk_score']
        integrity = 100 - rs
        risk_label = "🟢 LOW RISK" if rs < 40 else ("🟡 MEDIUM RISK" if rs < 70 else "🔴 HIGH RISK")
        m4.metric(
            "System Integrity Score",
            f"{integrity}/100",
            delta=risk_label,
            help=TOOLTIPS['risk_score']
        )

        st.markdown("---")
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Spending by Procurement Category**")
            cat_data = (
                final_df.groupby('commodity_full')['contract_value']
                .sum()
                .reset_index()
                .sort_values('contract_value', ascending=False)
            )
            fig_cat = px.bar(
                cat_data,
                x='commodity_full',
                y='contract_value',
                color_discrete_sequence=['#d30616'],
                labels={'commodity_full': 'Category', 'contract_value': 'Total Spend ($)'}
            )
            fig_cat.update_layout(showlegend=False, margin=dict(t=10, b=10), plot_bgcolor='white')
            st.plotly_chart(fig_cat, use_container_width=True)

        with c2:
            st.markdown("**Top Spending Departments**")
            dept_data = (
                final_df.groupby('owner_org_title')['contract_value']
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
            )
            fig_dept = px.bar(
                dept_data,
                y='owner_org_title',
                x='contract_value',
                orientation='h',
                color_discrete_sequence=['#26374a'],
                labels={'owner_org_title': '', 'contract_value': 'Total Spend ($)'}
            )
            fig_dept.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(t=10, b=10), plot_bgcolor='white')
            st.plotly_chart(fig_dept, use_container_width=True)

        # Yearly trend
        st.markdown("**Annual Spending Trend**")
        trend_df = df.groupby('year')['contract_value'].sum().reset_index().sort_values('year')
        fig_trend = px.line(
            trend_df,
            x='year',
            y='contract_value',
            markers=True,
            color_discrete_sequence=['#d30616'],
            labels={'year': 'Fiscal Year', 'contract_value': 'Total Spend ($)'}
        )
        fig_trend.update_layout(plot_bgcolor='white', margin=dict(t=10, b=10))
        st.plotly_chart(fig_trend, use_container_width=True)

    # ===== TAB 2: RISK & COMPETITION =====
    with tab2:
        st.markdown("### Competition & Fiscal Risk Analysis")

        r1, r2, r3 = st.columns(3)
        r1.metric("Average Bids per Contract", f"{current_kpis['avg_bids']:.2f}", help=TOOLTIPS['avg_bids'])
        r2.metric("Single-Bid Rate", f"{current_kpis['single_bid_rate']:.1f}%", help=TOOLTIPS['single_bid'])
        r3.metric("Amendment-to-Spend Ratio", f"{current_kpis['amendment_ratio']:.1f}%", help=TOOLTIPS['amend_ratio'])

        st.info(
            "💡 **Stakeholder Insight:** A high Single-Bid Rate (above 60%) combined with a high Amendment Ratio "
            "indicates a serious risk of vendor lock-in, poor market competition, and budget overruns."
        )

        # Bids distribution
        st.markdown("**Distribution of Bids per Contract**")
        bids_filtered = final_df['number_of_bids'].dropna()
        if not bids_filtered.empty:
            fig_bids = px.histogram(
                bids_filtered,
                nbins=20,
                color_discrete_sequence=['#d30616'],
                labels={'value': 'Number of Bids', 'count': 'Number of Contracts'}
            )
            fig_bids.update_layout(plot_bgcolor='white', margin=dict(t=10, b=10))
            st.plotly_chart(fig_bids, use_container_width=True)

        st.markdown("**High-Amendment Contracts — Flagged for Audit**")
        st.caption("Contracts where the amendment value exceeds 50% of the original value.")
        mask = (final_df['original_value'] > 0) & \
               (final_df['amendment_value'] > final_df['original_value'] * 0.5)
        high_risk = final_df[mask].copy()

        if not high_risk.empty:
            cols = [c for c in ['reference_number', 'vendor_name', 'original_value', 'amendment_value', 'commodity_full'] if c in high_risk.columns]
            display_df = high_risk[cols].rename(columns=COLUMN_MAP).head(20)
            st.dataframe(display_df, hide_index=True, use_container_width=True)
        else:
            st.success("✅ No high-amendment contracts flagged for the selected filters.")

    # ===== TAB 3: VENDOR INTELLIGENCE =====
    with tab3:
        st.markdown("### Market Dynamics & Vendor Concentration")

        v1, v2 = st.columns(2)
        v1.metric("Top 3 Vendor Market Share", f"{current_kpis['top_3_share']:.1f}%", help=TOOLTIPS['top3'])
        v2.metric("Market Concentration (HHI)", f"{current_kpis['hhi']:.0f}", help=TOOLTIPS['hhi'])

        hhi_val = current_kpis['hhi']
        if hhi_val < 1500:
            st.success(f"✅ HHI = {hhi_val:.0f} — Competitive market (< 1,500). Low concentration risk.")
        elif hhi_val < 2500:
            st.warning(f"⚠️ HHI = {hhi_val:.0f} — Moderately concentrated market (1,500–2,500).")
        else:
            st.error(f"🚨 HHI = {hhi_val:.0f} — Highly concentrated market (> 2,500). Monopoly risk.")

        # Top vendors chart
        top_vendors_agg = (
            final_df.groupby('vendor_name')['contract_value']
            .sum()
            .sort_values(ascending=False)
            .head(15)
            .reset_index()
        )
        fig_vendors = px.bar(
            top_vendors_agg,
            y='vendor_name',
            x='contract_value',
            orientation='h',
            color_discrete_sequence=['#d30616'],
            labels={'vendor_name': 'Vendor', 'contract_value': 'Total Spend ($)'}
        )
        fig_vendors.update_layout(yaxis={'categoryorder': 'total ascending'}, plot_bgcolor='white', margin=dict(t=10, b=10))
        st.plotly_chart(fig_vendors, use_container_width=True)

        st.markdown("**Top Vendors by Fiscal Volume**")
        top_vendors_table = (
            final_df.groupby('vendor_name')['contract_value']
            .agg(['sum', 'count'])
            .sort_values('sum', ascending=False)
            .head(20)
            .reset_index()
        )
        top_vendors_table.columns = ['Vendor Name', 'Total Spend ($)', 'Contract Count']
        top_vendors_table['Market Share (%)'] = (
            top_vendors_table['Total Spend ($)'] / current_kpis['total_spend'] * 100
        ).round(2)
        st.dataframe(
            top_vendors_table.style.format({
                'Total Spend ($)': '${:,.0f}',
                'Market Share (%)': '{:.2f}%'
            }),
            hide_index=True,
            use_container_width=True
        )


if __name__ == "__main__":
    main()
