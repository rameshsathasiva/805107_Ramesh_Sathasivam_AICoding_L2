import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.starter_pipeline import build_customer_360, clean_customers, clean_orders, clean_tickets


def test_clean_customers_standardizes_names_and_drops_missing_ids():
    customers = pd.DataFrame(
        {
            "customer_id": [" C1 ", "", "C2"],
            "customer_name": ["alice smith", None, "bob jones"],
        }
    )

    cleaned, quality = clean_customers(customers)

    assert list(cleaned["customer_name"]) == ["Alice Smith", "Bob Jones"]
    assert list(cleaned["customer_id"]) == ["C1", "C2"]
    assert quality["missing_customer_id_dropped"] == 1


def test_clean_orders_drops_bad_rows_and_computes_net_revenue():
    orders = pd.DataFrame(
        {
            "order_id": ["A1", "A1", "A2", "A3"],
            "customer_id": ["C1", "C1", "C2", "C3"],
            "order_date": ["2024-01-01", "bad-date", "2024-01-02", "2024-01-03"],
            "order_amount": [100, -5, "abc", 60],
            "quantity": [2, 0, "x", 4],
            "discount_pct": [10, "bad", None, 20],
        }
    )

    cleaned, quality = clean_orders(orders)

    assert len(cleaned) == 2
    assert quality["duplicate_order_ids_dropped"] == 1
    assert quality["invalid_order_amount_dropped"] == 1
    assert cleaned.loc[cleaned["order_id"] == "A1", "net_revenue"].iloc[0] == 90.0
    assert cleaned.loc[cleaned["order_id"] == "A3", "quantity"].iloc[0] == 4


def test_clean_tickets_parses_dates_and_validates_scores():
    tickets = pd.DataFrame(
        {
            "ticket_id": [1, 2, 3],
            "customer_id": ["C1", "", "C2"],
            "created_date": ["2024-01-01", "2024-01-02", "bad-date"],
            "resolved_date": ["2024-01-03", None, "2024-01-04"],
            "satisfaction_score": [4, 7, 2],
        }
    )

    cleaned, quality = clean_tickets(tickets)

    assert len(cleaned) == 2
    assert quality["missing_customer_id_dropped"] == 1
    assert cleaned["ticket_id"].tolist() == [1, 3]
    assert cleaned.loc[cleaned["ticket_id"] == 1, "resolution_days"].iloc[0] == 2
    assert cleaned.loc[cleaned["ticket_id"] == 3, "satisfaction_score"].iloc[0] == 2


def test_clean_orders_drops_duplicate_order_ids():
    orders = pd.DataFrame(
        {
            "order_id": ["A1", "A1", "A2"],
            "customer_id": ["C1", "C1", "C2"],
            "order_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "order_amount": [100, 120, 80],
            "quantity": [1, 1, 1],
            "discount_pct": [0, 0, 0],
        }
    )

    cleaned, quality = clean_orders(orders)

    assert len(cleaned) == 2
    assert cleaned["order_id"].nunique() == 2
    assert quality["duplicate_order_ids_dropped"] == 1


def test_clean_orders_handles_invalid_amounts_and_computes_revenue():
    orders = pd.DataFrame(
        {
            "order_id": ["A1", "A2", "A3", "A4"],
            "customer_id": ["C1", "C1", "C2", "C3"],
            "order_date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "order_amount": [100, -5, None, ""],
            "quantity": [1, 1, 1, 1],
            "discount_pct": [10, 0, 0, 0],
        }
    )

    cleaned, quality = clean_orders(orders)

    assert quality["invalid_order_amount_dropped"] == 3
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["net_revenue"] == 90.0


def test_build_customer_360_keeps_customer_with_no_orders_or_tickets():
    customers = pd.DataFrame(
        {
            "customer_id": ["C1", "C2"],
            "customer_name": ["Alice", "Bob"],
            "region": ["North", "South"],
        }
    )
    orders = pd.DataFrame(
        {
            "order_id": ["A1"],
            "customer_id": ["C1"],
            "order_date": ["2024-01-01"],
            "order_amount": [100],
            "quantity": [1],
            "discount_pct": [0],
            "net_revenue": [100],
        }
    )
    tickets = pd.DataFrame(
        {
            "ticket_id": [1],
            "customer_id": ["C1"],
            "created_date": ["2024-01-01"],
            "resolved_date": ["2024-01-02"],
            "satisfaction_score": [4],
            "resolution_days": [1],
        }
    )

    customer_360 = build_customer_360(orders, customers, tickets)

    assert customer_360["customer_id"].tolist() == ["C1", "C2"]
    assert customer_360.loc[customer_360["customer_id"] == "C2", "order_count"].iloc[0] == 0
    assert customer_360.loc[customer_360["customer_id"] == "C2", "ticket_count"].iloc[0] == 0
    assert customer_360.loc[customer_360["customer_id"] == "C2", "total_net_revenue"].iloc[0] == 0


def test_build_customer_360_has_expected_output_columns():
    customers = pd.DataFrame(
        {
            "customer_id": ["C1"],
            "customer_name": ["Alice"],
            "region": ["North"],
        }
    )
    orders = pd.DataFrame(
        {
            "order_id": ["A1"],
            "customer_id": ["C1"],
            "order_date": ["2024-01-01"],
            "order_amount": [100],
            "quantity": [1],
            "discount_pct": [0],
            "net_revenue": [100],
        }
    )
    tickets = pd.DataFrame(
        {
            "ticket_id": [1],
            "customer_id": ["C1"],
            "created_date": ["2024-01-01"],
            "resolved_date": ["2024-01-02"],
            "satisfaction_score": [4],
            "resolution_days": [1],
        }
    )

    customer_360 = build_customer_360(orders, customers, tickets)

    expected_columns = {
        "customer_id",
        "customer_name",
        "region",
        "order_count",
        "total_net_revenue",
        "average_order_value",
        "last_order_date",
        "ticket_count",
        "avg_resolution_hours",
        "avg_satisfaction_score",
        "value_tier",
        "risk_flag",
    }

    assert expected_columns.issubset(set(customer_360.columns))
