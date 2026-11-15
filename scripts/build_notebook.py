"""Generate the Pandas analysis notebook."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]


def cell(kind, source):
    item = {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True)}
    if kind == "code":
        item.update(execution_count=None, outputs=[])
    return item


cells = [
    cell("markdown", "# Risk analysis / 风险分析\n\nAll records are synthetic. Run from the project root or notebooks directory."),
    cell("code", """from pathlib import Path
import pandas as pd
import numpy as np
ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
DATA = ROOT / 'data'
contracts = pd.read_csv(DATA / 'contracts.csv')
vouchers = pd.read_csv(DATA / 'vouchers_and_docs.csv', parse_dates=['voucher_date'])
invoices = pd.read_csv(DATA / 'tax_and_invoices.csv', parse_dates=['invoice_date'])
cash = pd.read_csv(DATA / 'cash_flow_schedule.csv', parse_dates=['due_date', 'as_of_date'])
assert (len(contracts), len(vouchers), len(invoices), len(cash)) == (1, 840, 420, 20)
assert contracts.contract_id.is_unique and vouchers.voucher_id.is_unique and invoices.invoice_id.is_unique
assert set(vouchers.contract_id).issubset(set(contracts.contract_id))
assert set(vouchers.invoice_id).issubset(set(invoices.invoice_id))
"""),
    cell("markdown", "## Document quality / 单据质量\n\nRepeated references are review signals."),
    cell("code", """duplicate_docs = vouchers[vouchers.duplicated(['contract_id', 'document_reference'], keep=False)].sort_values('document_reference')
assert duplicate_docs.groupby(['contract_id', 'document_reference']).ngroups == 6
duplicate_docs[['voucher_id', 'document_reference', 'amount_cny']].head(12)
"""),
    cell("markdown", "## Invoice reconciliation / 发票对账\n\nCross-period dates require review but do not alone prove a violation."),
    cell("code", """voucher_totals = vouchers.groupby(['contract_id', 'invoice_id'], as_index=False)['amount_cny'].sum().rename(columns={'amount_cny': 'voucher_net_cny'})
invoice_check = invoices.merge(voucher_totals, on=['contract_id', 'invoice_id'], how='left', validate='one_to_one')
invoice_check['variance_cny'] = (invoice_check.net_amount_cny - invoice_check.voucher_net_cny).round(2)
invoice_check['cross_period_review'] = invoice_check.invoice_date.dt.to_period('M').astype(str).ne(invoice_check.service_period)
invoice_exceptions = invoice_check[invoice_check.variance_cny.abs().gt(0.009)]
assert len(invoice_exceptions) == 20
print('Invoice differences:', len(invoice_exceptions), 'Cross-period flags:', int(invoice_check.cross_period_review.sum()))
invoice_exceptions[['invoice_id', 'net_amount_cny', 'voucher_net_cny', 'variance_cny']].head()
"""),
    cell("markdown", "## Cash risk / 回款风险\n\nOnly unpaid installments past due count as overdue."),
    cell("code", """cash['calculated_outstanding_cny'] = (cash.scheduled_receivable_cny - cash.actual_receipt_cny).round(2)
assert cash.disposal_proceeds_cny.sum() == 2_000_000
assert np.allclose(cash.calculated_outstanding_cny, cash.outstanding_cny)
cash['calculated_risk'] = np.select([cash.outstanding_cny.le(0), cash.due_date.lt(cash.as_of_date)], ['paid', 'overdue'], default='future')
assert (cash.calculated_risk == cash.risk_flag).all()
cash['risk_score'] = cash.risk_flag.map({'paid': 0, 'future': 40, 'overdue': 100})
cash[['installment_year', 'outstanding_cny', 'risk_flag', 'risk_score']]
"""),
    cell("markdown", "## Forecast / 预测情景\n\nBaseline collects future installments on time; delay shifts collection one year; stress collects 80%."),
    cell("code", """future = cash[cash.due_date.gt(cash.as_of_date.iloc[0])].copy()
forecast = future[['installment_year', 'scheduled_receivable_cny']].rename(columns={'installment_year': 'year'})
forecast = forecast.merge(future[['installment_year', 'disposal_proceeds_cny']].rename(columns={'installment_year': 'year'}), on='year')
forecast['baseline_cny'] = forecast.scheduled_receivable_cny + forecast.disposal_proceeds_cny
forecast['delay_one_year_cny'] = forecast.scheduled_receivable_cny.shift(1, fill_value=0) + forecast.disposal_proceeds_cny
forecast['stress_80pct_cny'] = (forecast.scheduled_receivable_cny * 0.8 + forecast.disposal_proceeds_cny).round(2)
for name in ['baseline', 'delay_one_year', 'stress_80pct']:
    forecast[name + '_cumulative_cny'] = forecast[name + '_cny'].cumsum()
forecast[['year', 'baseline_cumulative_cny', 'delay_one_year_cumulative_cny', 'stress_80pct_cumulative_cny']]
"""),
    cell("markdown", "## Operations overview / 经营概览\n\nThe undiscounted plan surplus is scheduled installments plus terminal disposal proceeds less project cost. Voucher amounts are sample cost detail and are not deducted a second time. This is not accounting profit."),
    cell("code", """contract_value = contracts.contract_value_cny.sum()
voucher_cost = vouchers.amount_cny.sum()
project_cost = contracts.project_cost_cny.sum()
disposal_proceeds = cash.disposal_proceeds_cny.sum()
summary = pd.DataFrame([{'scheduled_receipts_cny': contract_value, 'terminal_disposal_proceeds_cny': disposal_proceeds, 'total_planned_inflow_cny': contract_value + disposal_proceeds, 'project_cost_cny': project_cost, 'voucher_detail_cny': voucher_cost, 'undiscounted_plan_surplus_cny': contract_value + disposal_proceeds - project_cost, 'actual_receipts_cny': cash.actual_receipt_cny.sum(), 'overdue_cny': cash.loc[cash.risk_flag.eq('overdue'), 'outstanding_cny'].sum()}])
summary
"""),
]

notebook = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
target = root / "notebooks" / "risk_analysis.ipynb"
target.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(target)
