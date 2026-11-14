"""Build a reproducible, explicitly synthetic project finance scenario.

The vendored OCDS example supplies contract metadata and field structure. All
financial values and records in the four output CSVs are demonstration data.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "sources" / "ocds" / "implementation.json"
DATA = ROOT / "data"
CONTRACT_ID = "SIM-CN-2026-001"
START_YEAR = 2026
YEARS = 20
ANNUAL_DUE = Decimal("750000.00")
DOC_TYPES = (
    "equipment_receipt",
    "material_receipt",
    "work_order",
    "acceptance_note",
)


def money(value: Decimal | int) -> str:
    return f"{Decimal(value):.2f}"


def write_csv(name: str, rows: list[dict[str, object]], columns: list[str]) -> None:
    DATA.mkdir(exist_ok=True)
    with (DATA / name).open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def build(as_of: date) -> dict[str, int]:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    release = source["releases"][0]
    source_contract = release["contracts"][0]
    source_ocid = release["ocid"]
    origin = "synthetic_from_ocds_example"

    contracts = [{
        "contract_id": CONTRACT_ID,
        "project_name": "Long-term infrastructure operations demo",
        "currency": "CNY",
        "contract_value_cny": money(ANNUAL_DUE * YEARS),
        "start_date": f"{START_YEAR}-01-01",
        "end_date": f"{START_YEAR + YEARS - 1}-12-31",
        "installment_years": YEARS,
        "annual_receivable_cny": money(ANNUAL_DUE),
        "source_ocid": source_ocid,
        "source_contract_id": source_contract["id"],
        "source_contract_title": source_contract["title"],
        "source_contract_value": source_contract["value"]["amount"],
        "source_currency": source_contract["value"]["currency"],
        "record_origin": origin,
    }]

    rng = random.Random(20261113)
    vouchers: list[dict[str, object]] = []
    invoice_docs: dict[str, list[dict[str, object]]] = defaultdict(list)
    for year in range(START_YEAR, START_YEAR + YEARS):
        for index in range(42):
            invoice_id = f"INV-{year}-{index // 2 + 1:03d}"
            voucher_id = f"VCH-{year}-{index + 1:03d}"
            voucher_date = date(year, index % 12 + 1, 5 + (index // 12) * 5)
            amount = Decimal(rng.randint(6000, 18000))
            reference = f"DOC-{year}-{index + 1:03d}"
            if index > 0 and (year - START_YEAR) * 42 + index in {131, 262, 393, 524, 655, 786}:
                reference = f"DOC-{year}-{index:03d}"
            row = {
                "voucher_id": voucher_id,
                "contract_id": CONTRACT_ID,
                "invoice_id": invoice_id,
                "voucher_date": voucher_date.isoformat(),
                "doc_type": DOC_TYPES[index % len(DOC_TYPES)],
                "supplier_id": f"SUP-{index // 2 % 5 + 1:03d}",
                "amount_cny": money(amount),
                "document_reference": reference,
                "source_ocid": source_ocid,
                "record_origin": origin,
            }
            vouchers.append(row)
            invoice_docs[invoice_id].append(row)

    invoices: list[dict[str, object]] = []
    for invoice_id, docs in invoice_docs.items():
        service_date = max(date.fromisoformat(doc["voucher_date"]) for doc in docs)
        issued = max(date.fromisoformat(doc["voucher_date"]) for doc in docs) + timedelta(days=15)
        net_amount = sum(Decimal(doc["amount_cny"]) for doc in docs)
        rate = Decimal("0.13") if docs[0]["doc_type"] == "equipment_receipt" else Decimal("0.09")
        sequence = int(invoice_id.rsplit("-", 1)[1])
        reported_net = net_amount + (Decimal("50.00") if sequence == 7 else Decimal("0.00"))
        invoices.append({
            "invoice_id": invoice_id,
            "contract_id": CONTRACT_ID,
            "supplier_id": docs[0]["supplier_id"],
            "service_period": service_date.strftime("%Y-%m"),
            "invoice_date": issued.isoformat(),
            "invoice_type": "special_vat_demo",
            "net_amount_cny": money(reported_net),
            "tax_rate": str(rate),
            "tax_amount_cny": money(reported_net * rate),
            "gross_amount_cny": money(reported_net * (Decimal("1") + rate)),
            "source_ocid": source_ocid,
            "record_origin": origin,
        })

    cash_flow: list[dict[str, object]] = []
    for year in range(START_YEAR, START_YEAR + YEARS):
        due = date(year, 9, 30)
        actual = Decimal("600000.00") if year == START_YEAR else Decimal("0.00")
        risk = "paid" if actual >= ANNUAL_DUE else "overdue" if due < as_of else "future"
        cash_flow.append({
            "contract_id": CONTRACT_ID,
            "installment_year": year,
            "due_date": due.isoformat(),
            "scheduled_receivable_cny": money(ANNUAL_DUE),
            "actual_receipt_cny": money(actual),
            "outstanding_cny": money(ANNUAL_DUE - actual),
            "risk_flag": risk,
            "as_of_date": as_of.isoformat(),
            "source_ocid": source_ocid,
            "record_origin": origin,
        })

    outputs = {
        "contracts.csv": contracts,
        "vouchers_and_docs.csv": vouchers,
        "tax_and_invoices.csv": invoices,
        "cash_flow_schedule.csv": cash_flow,
    }
    for name, rows in outputs.items():
        write_csv(name, rows, list(rows[0]))
    return {name: len(rows) for name, rows in outputs.items()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of-date", type=date.fromisoformat, default=date(2026, 11, 13))
    args = parser.parse_args()
    for filename, count in build(args.as_of_date).items():
        print(f"{filename}: {count} rows")
