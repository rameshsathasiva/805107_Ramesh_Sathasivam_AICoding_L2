from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
CUSTOMER_360_PATH = OUTPUT_DIR / "customer_360.csv"
KPI_PATH = OUTPUT_DIR / "kpi_summary.csv"
REGION_REVENUE_PATH = OUTPUT_DIR / "region_revenue.csv"
CATEGORY_REVENUE_PATH = OUTPUT_DIR / "category_revenue.csv"

st.set_page_config(page_title="Customer 360", layout="wide")
st.title("Customer 360 Dashboard")

if not CUSTOMER_360_PATH.exists():
    st.warning("No customer_360.csv file found. Please run the pipeline first.")
    st.stop()

customer_360 = pd.read_csv(CUSTOMER_360_PATH)
if KPI_PATH.exists():
    kpi_summary = pd.read_csv(KPI_PATH)
else:
    kpi_summary = pd.DataFrame(columns=["metric", "value"])

if REGION_REVENUE_PATH.exists():
    region_revenue = pd.read_csv(REGION_REVENUE_PATH)
else:
    region_revenue = pd.DataFrame(columns=["region", "total_net_revenue", "customers"])

if CATEGORY_REVENUE_PATH.exists():
    category_revenue = pd.read_csv(CATEGORY_REVENUE_PATH)
else:
    category_revenue = pd.DataFrame(columns=["product_category", "total_net_revenue", "orders"])

for column in ["region", "segment", "industry", "value_tier"]:
    if column in customer_360.columns:
        customer_360[column] = customer_360[column].fillna("Unknown")

st.sidebar.header("Filters")
region_filter = st.sidebar.multiselect("Region", sorted(customer_360["region"].dropna().unique().tolist()))
segment_filter = st.sidebar.multiselect("Segment", sorted(customer_360["segment"].dropna().unique().tolist()))
industry_filter = st.sidebar.multiselect("Industry", sorted(customer_360["industry"].dropna().unique().tolist()))
value_tier_filter = st.sidebar.multiselect("Value Tier", sorted(customer_360["value_tier"].dropna().unique().tolist()))

filtered_df = customer_360.copy()
if region_filter:
    filtered_df = filtered_df[filtered_df["region"].isin(region_filter)]
if segment_filter:
    filtered_df = filtered_df[filtered_df["segment"].isin(segment_filter)]
if industry_filter:
    filtered_df = filtered_df[filtered_df["industry"].isin(industry_filter)]
if value_tier_filter:
    filtered_df = filtered_df[filtered_df["value_tier"].isin(value_tier_filter)]

metric_map = {
    "Total Customers": "customers",
    "Total Net Revenue": "total_net_revenue",
    "Average Order Value": "average_order_value",
    "Average Satisfaction Score": "average_satisfaction_score",
}

kpi_values = {}
for metric_name, metric_key in metric_map.items():
    if not kpi_summary.empty:
        match = kpi_summary[kpi_summary["metric"] == metric_key]
        if not match.empty:
            kpi_values[metric_name] = float(match.iloc[0]["value"])
        else:
            kpi_values[metric_name] = 0.0
    else:
        kpi_values[metric_name] = 0.0

cols = st.columns(4)
for index, (label, value) in enumerate(kpi_values.items()):
    with cols[index]:
        st.metric(label=label, value=f"{value:,.2f}" if "Revenue" in label or "Value" in label else f"{value:,.2f}")

st.subheader("Revenue by Region")
if not region_revenue.empty:
    st.bar_chart(region_revenue.set_index("region")["total_net_revenue"])
else:
    st.info("No regional revenue data available yet.")

st.subheader("Revenue by Product Category")
if not category_revenue.empty:
    st.bar_chart(category_revenue.set_index("product_category")["total_net_revenue"])
else:
    st.info("No category revenue data available yet.")

st.subheader("Customer Detail Table")
if filtered_df.empty:
    st.info("No customers match the selected filters.")
else:
    styled_df = filtered_df.copy()
    styled_df = styled_df.style.apply(
        lambda row: ["background-color: #ffe5e5" if row["risk_flag"] else "" for _ in row],
        axis=1,
    )
    st.dataframe(styled_df, use_container_width=True)

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download filtered customers as CSV",
        data=csv_data,
        file_name="filtered_customer_360.csv",
        mime="text/csv",
    )
