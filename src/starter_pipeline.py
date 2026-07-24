"""
Project AI Native: AI-Assisted Coding Assignment

Starter pipeline for a small Customer 360 analytics use case.

Learners should use an AI coding assistant to complete, refactor, test,
and document this pipeline.

Expected usage after completion:
    python src/starter_pipeline.py

Input sources:
    data/orders_source.csv
    data/customers_source.csv
    data/support_tickets_source.csv

Expected outputs:
    outputs/customer_360.csv
    outputs/kpi_summary.csv
    outputs/region_revenue.csv
    outputs/category_revenue.csv
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"


def load_sources():
    orders = pd.read_csv(DATA_DIR / "orders_source.csv")
    customers = pd.read_csv(DATA_DIR / "customers_source.csv")
    tickets = pd.read_csv(DATA_DIR / "support_tickets_source.csv")
    return orders, customers, tickets


def clean_orders(orders):

    orders["customer_id"] = orders["customer_id"].str.strip()
    orders["customer_name"] = orders["customer_name"].str.title()
    orders["net_revenue"] = orders["order_amount"] - (
        orders["order_amount"] * orders["discount_pct"] / 100
    )
    return orders


def clean_customers(customers):
    customers["customer_name"] = customers["customer_name"].str.title()
    return customers


def clean_tickets(tickets):
    tickets["resolution_days"] = (
        pd.to_datetime(tickets["resolved_date"]) - pd.to_datetime(tickets["created_date"])
    ).dt.days
    return tickets


def build_customer_360(orders, customers, tickets):
    order_summary = (
        orders.groupby("customer_id")
        .agg(
            order_count=("order_id", "count"),
            total_net_revenue=("net_revenue", "sum"),
            average_order_value=("net_revenue", "mean"),
            last_order_date=("order_date", "max"),
        )
        .reset_index()
    )

    ticket_summary = (
        tickets.groupby("customer_id")
        .agg(
            ticket_count=("ticket_id", "count"),
            avg_resolution_days=("resolution_days", "mean"),
            avg_satisfaction_score=("satisfaction_score", "mean"),
        )
        .reset_index()
    )

    customer_360 = customers.merge(order_summary, on="customer_id", how="left")
    customer_360 = customer_360.merge(ticket_summary, on="customer_id", how="left")

    return customer_360


def build_dashboard_outputs(customer_360, orders):
    
    kpi_summary = pd.DataFrame(
        [
            {
                "metric": "customers",
                "value": customer_360["customer_id"].nunique(),
            },
            {
                "metric": "total_net_revenue",
                "value": customer_360["total_net_revenue"].sum(),
            },
            {
                "metric": "average_order_value",
                "value": customer_360["average_order_value"].mean(),
            },
            {
                "metric": "average_satisfaction_score",
                "value": customer_360["avg_satisfaction_score"].mean(),
            },
        ]
    )

    region_revenue = (
        customer_360.groupby("region")
        .agg(total_net_revenue=("total_net_revenue", "sum"), customers=("customer_id", "count"))
        .reset_index()
    )

    category_revenue = (
        orders.groupby("product_category")
        .agg(total_net_revenue=("net_revenue", "sum"), orders=("order_id", "count"))
        .reset_index()
    )

    return kpi_summary, region_revenue, category_revenue


def save_outputs(customer_360, kpi_summary, region_revenue, category_revenue):
    """Write pipeline outputs."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    customer_360.to_csv(OUTPUT_DIR / "customer_360.csv", index=False)
    kpi_summary.to_csv(OUTPUT_DIR / "kpi_summary.csv", index=False)
    region_revenue.to_csv(OUTPUT_DIR / "region_revenue.csv", index=False)
    category_revenue.to_csv(OUTPUT_DIR / "category_revenue.csv", index=False)


def main():
    orders, customers, tickets = load_sources()
    orders = clean_orders(orders)
    customers = clean_customers(customers)
    tickets = clean_tickets(tickets)
    customer_360 = build_customer_360(orders, customers, tickets)
    kpi_summary, region_revenue, category_revenue = build_dashboard_outputs(customer_360, orders)
    save_outputs(customer_360, kpi_summary, region_revenue, category_revenue)
    print("Pipeline complete. Outputs written to the outputs folder.")


if __name__ == "__main__":
    main()

