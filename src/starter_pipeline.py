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

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"


def _load_excel_dataset(name, file_name):
    path = DATA_DIR / file_name

    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")

    try:
        df = pd.read_excel(path)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Required input file not found: {path}") from exc
    except ImportError as exc:
        raise ImportError(
            f"Unable to load '{path}' because a required Excel engine is missing: {exc}"
        ) from exc
    except ValueError as exc:
        raise ValueError(f"Failed to read Excel file '{path}': {exc}") from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise RuntimeError(f"Unexpected error while loading '{path}': {exc}") from exc

    if df.empty:
        raise ValueError(f"Loaded dataset '{name}' from '{path}' is empty.")

    return df


def load_sources():
    try:
        orders = _load_excel_dataset("orders", "orders_source.xlsx")
        customers = _load_excel_dataset("customers", "customers_source.xlsx")
        tickets = _load_excel_dataset("tickets", "support_tickets_source.xlsx")
    except (FileNotFoundError, ImportError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    return orders, customers, tickets


def clean_customers(customers):
    customers = customers.copy()
    quality_report = {"rows_input": len(customers)}

    customers["customer_name"] = customers["customer_name"].fillna("Unknown Customer")
    customers["customer_name"] = customers["customer_name"].astype(str).str.strip().str.title()

    customers["customer_id"] = customers["customer_id"].astype("string").str.strip()
    customers["customer_id"] = customers["customer_id"].replace({"": pd.NA})

    missing_customer_id_mask = customers["customer_id"].isna()
    quality_report["missing_customer_id_dropped"] = int(missing_customer_id_mask.sum())
    customers = customers.loc[~missing_customer_id_mask].copy()

    quality_report["rows_output"] = len(customers)
    return customers, quality_report


def clean_orders(orders):
    orders = orders.copy()
    quality_report = {"rows_input": len(orders)}

    orders["order_id"] = orders["order_id"].astype("string").str.strip()
    duplicate_order_mask = orders["order_id"].duplicated(keep="first")
    quality_report["duplicate_order_ids_dropped"] = int(duplicate_order_mask.sum())
    orders = orders.loc[~duplicate_order_mask].copy()

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")

    orders["customer_id"] = orders["customer_id"].astype("string").str.strip()
    orders["customer_id"] = orders["customer_id"].replace({"": pd.NA})
    missing_customer_id_mask = orders["customer_id"].isna()
    quality_report["missing_customer_id_dropped"] = int(missing_customer_id_mask.sum())
    orders = orders.loc[~missing_customer_id_mask].copy()

    orders["order_amount"] = pd.to_numeric(orders["order_amount"], errors="coerce")
    invalid_amount_mask = orders["order_amount"].isna() | orders["order_amount"].lt(0)
    quality_report["invalid_order_amount_dropped"] = int(invalid_amount_mask.sum())
    orders = orders.loc[~invalid_amount_mask].copy()

    orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce")
    invalid_quantity_mask = orders["quantity"].isna() | orders["quantity"].lt(1)
    quality_report["invalid_quantity_replaced"] = int(invalid_quantity_mask.sum())
    orders.loc[invalid_quantity_mask, "quantity"] = 1

    orders["discount_pct"] = pd.to_numeric(orders["discount_pct"], errors="coerce")
    invalid_discount_mask = orders["discount_pct"].isna()
    quality_report["invalid_discount_replaced"] = int(invalid_discount_mask.sum())
    orders["discount_pct"] = orders["discount_pct"].fillna(0)
    orders["discount_pct"] = orders["discount_pct"].clip(lower=0, upper=100)

    orders["net_revenue"] = orders["order_amount"] * (1 - orders["discount_pct"] / 100)

    quality_report["rows_output"] = len(orders)
    return orders, quality_report


def clean_tickets(tickets):
    tickets = tickets.copy()
    quality_report = {"rows_input": len(tickets)}

    tickets["customer_id"] = tickets["customer_id"].astype("string").str.strip()
    tickets["customer_id"] = tickets["customer_id"].replace({"": pd.NA})
    missing_customer_id_mask = tickets["customer_id"].isna()
    quality_report["missing_customer_id_dropped"] = int(missing_customer_id_mask.sum())
    tickets = tickets.loc[~missing_customer_id_mask].copy()

    tickets["created_date"] = pd.to_datetime(tickets["created_date"], errors="coerce")
    tickets["resolved_date"] = pd.to_datetime(tickets["resolved_date"], errors="coerce")
    quality_report["invalid_created_or_resolved_dates"] = int(
        tickets[["created_date", "resolved_date"]].isna().any(axis=1).sum()
    )

    tickets["resolution_days"] = (
        tickets["resolved_date"] - tickets["created_date"]
    ).dt.days
    tickets.loc[tickets["resolved_date"].isna(), "resolution_days"] = pd.NA

    tickets["satisfaction_score"] = pd.to_numeric(tickets["satisfaction_score"], errors="coerce")
    invalid_satisfaction_mask = tickets["satisfaction_score"].isna() | (
        tickets["satisfaction_score"] < 1
    ) | (tickets["satisfaction_score"] > 5)
    quality_report["invalid_satisfaction_score_replaced"] = int(invalid_satisfaction_mask.sum())
    tickets.loc[invalid_satisfaction_mask, "satisfaction_score"] = pd.NA

    quality_report["rows_output"] = len(tickets)
    return tickets, quality_report


def build_customer_360(orders, customers, tickets):
    order_summary = (
        orders.groupby("customer_id", dropna=False)
        .agg(
            order_count=("order_id", "count"),
            total_net_revenue=("net_revenue", "sum"),
            average_order_value=("net_revenue", "mean"),
            last_order_date=("order_date", "max"),
        )
        .reset_index()
    )

    ticket_summary = (
        tickets.groupby("customer_id", dropna=False)
        .agg(
            ticket_count=("ticket_id", "count"),
            avg_resolution_hours=("resolution_days", lambda s: s.mean() * 24 if s.notna().any() else 0),
            avg_satisfaction_score=("satisfaction_score", "mean"),
        )
        .reset_index()
    )

    customer_360 = customers.merge(order_summary, on="customer_id", how="left")
    customer_360 = customer_360.merge(ticket_summary, on="customer_id", how="left")

    numeric_columns = [
        "order_count",
        "total_net_revenue",
        "average_order_value",
        "ticket_count",
        "avg_resolution_hours",
        "avg_satisfaction_score",
    ]
    for column in numeric_columns:
        customer_360[column] = customer_360[column].fillna(0)

    customer_360["last_order_date"] = pd.to_datetime(customer_360["last_order_date"], errors="coerce")
    customer_360["value_tier"] = pd.cut(
        customer_360["total_net_revenue"],
        bins=[-1, 100, 1000, float("inf")],
        labels=["Low", "Medium", "High"],
        right=True,
    )

    customer_360["risk_flag"] = (
        customer_360["avg_satisfaction_score"].fillna(5) < 3
    )

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


def save_outputs(customer_360, kpi_summary, region_revenue, category_revenue, data_quality_report):
    """Write pipeline outputs to the outputs directory."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    customer_360.to_csv(OUTPUT_DIR / "customer_360.csv", index=False)
    kpi_summary.to_csv(OUTPUT_DIR / "kpi_summary.csv", index=False)
    region_revenue.to_csv(OUTPUT_DIR / "region_revenue.csv", index=False)
    category_revenue.to_csv(OUTPUT_DIR / "category_revenue.csv", index=False)

    quality_df = pd.DataFrame(
        [
            {"dataset": dataset_name, **metrics}
            for dataset_name, metrics in data_quality_report.items()
        ]
    )
    quality_df.to_csv(OUTPUT_DIR / "data_quality_report.csv", index=False)


def main():
    orders, customers, tickets = load_sources()
    customers, customer_quality = clean_customers(customers)
    orders, order_quality = clean_orders(orders)
    tickets, ticket_quality = clean_tickets(tickets)

    quality_report = {
        "customers": customer_quality,
        "orders": order_quality,
        "tickets": ticket_quality,
    }

    customer_360 = build_customer_360(orders, customers, tickets)
    kpi_summary, region_revenue, category_revenue = build_dashboard_outputs(customer_360, orders)
    save_outputs(customer_360, kpi_summary, region_revenue, category_revenue, quality_report)

    print("Pipeline complete. Outputs written to the outputs folder.")
    print("Data quality report:")
    print(quality_report)


if __name__ == "__main__":
    main()

