"""Validate keys and scenario invariants for the four generated CSV files."""

from __future__ import annotations

import csv
import sqlite3
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path


DATA = Path(__file__).resolve().parents[1] / "data"


def read(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    contracts = read("contracts.csv")
    vouchers = read("vouchers_and_docs.csv")
    invoices = read("tax_and_invoices.csv")
    cash = read("cash_flow_schedule.csv")
    require((len(contracts), len(vouchers), len(invoices), len(cash)) == (1, 840, 420, 20), "unexpected row counts")

    contract_ids = {row["contract_id"] for row in contracts}
    invoice_ids = {row["invoice_id"] for row in invoices}
    require(len(invoice_ids) == len(invoices), "duplicate invoice IDs")
    require(len({row["voucher_id"] for row in vouchers}) == len(vouchers), "duplicate voucher IDs")
    require(len({(row["contract_id"], row["installment_year"]) for row in cash}) == len(cash), "duplicate installment keys")
    require(all(row["contract_id"] in contract_ids for row in vouchers + invoices + cash), "orphan contract ID")
    require(all(row["invoice_id"] in invoice_ids for row in vouchers), "orphan invoice ID")
    require(all(row["record_origin"] == "synthetic_from_ocds_example" for row in contracts + vouchers + invoices + cash), "unlabeled generated record")

    contract_value = Decimal(contracts[0]["contract_value_cny"])
    project_cost = Decimal(contracts[0]["project_cost_cny"])
    scheduled = sum(Decimal(row["scheduled_receivable_cny"]) for row in cash)
    require(project_cost == Decimal("15000000.00"), "project cost must be CNY 15 million")
    require(contract_value == scheduled == Decimal("26000000.00"), "contract and installment total differ")
    require(all(Decimal(row["scheduled_receivable_cny"]) == Decimal("1300000.00") for row in cash), "annual installment must be CNY 1.3 million")
    require(Decimal(contracts[0]["terminal_disposal_proceeds_cny"]) == Decimal("2000000.00"), "terminal disposal amount mismatch")
    require(sum(Decimal(row["disposal_proceeds_cny"]) for row in cash) == Decimal("2000000.00"), "terminal disposal total mismatch")
    require(all(Decimal(row["disposal_proceeds_cny"]) == (Decimal("2000000.00") if row["installment_year"] == "2045" else Decimal("0.00")) for row in cash), "disposal must be in final year only")
    require(scheduled + Decimal(contracts[0]["terminal_disposal_proceeds_cny"]) - project_cost == Decimal("13000000.00"), "simplified undiscounted surplus mismatch")
    require(all(Decimal(row["scheduled_receivable_cny"]) - Decimal(row["actual_receipt_cny"]) == Decimal(row["outstanding_cny"]) for row in cash), "outstanding amount mismatch")

    voucher_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    for row in vouchers:
        voucher_totals[row["invoice_id"]] += Decimal(row["amount_cny"])
    differences = [row["invoice_id"] for row in invoices if Decimal(row["net_amount_cny"]) != voucher_totals[row["invoice_id"]]]
    duplicate_references = [key for key, count in Counter((row["contract_id"], row["document_reference"]) for row in vouchers).items() if count > 1]
    require(len(differences) == 20, "expected one invoice variance per year")
    require(len(duplicate_references) == 6, "expected six duplicate document references")

    db = sqlite3.connect(":memory:")
    for name, rows in (
        ("contracts", contracts),
        ("vouchers_and_docs", vouchers),
        ("tax_and_invoices", invoices),
        ("cash_flow_schedule", cash),
    ):
        columns = list(rows[0])
        db.execute(f"CREATE TABLE {name} ({', '.join(column + ' TEXT' for column in columns)})")
        db.executemany(
            f"INSERT INTO {name} VALUES ({', '.join('?' for _ in columns)})",
            [[row[column] for column in columns] for row in rows],
        )
    query = (DATA.parent / "sql" / "reconciliation.sql").read_text(encoding="utf-8")
    exception_counts = Counter(row[0] for row in db.execute(query))
    require(exception_counts["invoice_amount_difference"] == 20, f"unexpected SQL exceptions: {exception_counts}")
    require(exception_counts["duplicate_document_reference"] == 6, f"unexpected SQL exceptions: {exception_counts}")
    require(exception_counts["overdue_receivable"] == 1, f"unexpected SQL exceptions: {exception_counts}")
    require(exception_counts["tax_calculation_difference"] == 0, f"unexpected SQL exceptions: {exception_counts}")
    require(exception_counts["cross_period_invoice_review"] > 0, f"unexpected SQL exceptions: {exception_counts}")
    print("Validated: 1 contract, 840 vouchers, 420 invoices, 20 installments")
    print(f"SQL exceptions: {dict(exception_counts)}")


if __name__ == "__main__":
    main()
