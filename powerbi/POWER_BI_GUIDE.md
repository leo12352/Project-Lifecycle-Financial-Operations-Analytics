# Power BI build guide / Power BI 搭建说明

The native [four-page PBIX](Project_Lifecycle_Financial_Operations_Analytics.pbix) contains four imported tables and twelve data-driven charts. It was opened and saved in Power BI Desktop on 2026-11-14. The offline [dashboard](dashboard.html) provides a separate review view.

原生 [四页 PBIX](Project_Lifecycle_Financial_Operations_Analytics.pbix) 已在 Power BI Desktop 中打开并保存，包含四张数据表和十二张图表。[离线看板](dashboard.html) 可供对照审核。

## Import / 导入

1. In Power BI Desktop, choose **Get data → Text/CSV** for each file in `data/`.
2. Set date columns to Date, `installment_year` to Whole number, and CNY amounts to Fixed decimal number. Keep IDs and `document_reference` as Text.
3. Create relationships: `contracts[contract_id]` one to many with each other table; `tax_and_invoices[invoice_id]` one to many with `vouchers_and_docs[invoice_id]`. Use single direction from the lookup table.
4. Use `cash_flow_schedule[as_of_date]` as a clearly visible snapshot field. It is fixed in the generated files.

## Suggested measures / 建议度量值（当前 PBIX 未内置）

```DAX
Contract Value CNY = SUM(contracts[contract_value_cny])
Voucher Cost Proxy CNY = SUM(vouchers_and_docs[amount_cny])
Margin Proxy CNY = [Contract Value CNY] - [Voucher Cost Proxy CNY]
Scheduled Receivable CNY = SUM(cash_flow_schedule[scheduled_receivable_cny])
Actual Receipt CNY = SUM(cash_flow_schedule[actual_receipt_cny])
Overdue CNY = CALCULATE(SUM(cash_flow_schedule[outstanding_cny]), cash_flow_schedule[risk_flag] = "overdue")
Invoice Count = DISTINCTCOUNT(tax_and_invoices[invoice_id])
Voucher Count = DISTINCTCOUNT(vouchers_and_docs[voucher_id])
```

For row-level invoice variance, prepare the grouped voucher sum in Power Query or use `sql/reconciliation.sql` as the exception source. Avoid a direct many-to-many relationship between vouchers and cash installments.

## Four report pages / 四个页面

The delivered PBIX has four pages with three charts each. Cards and exception tables below are suggested extensions, not yet included. The HTML dashboard, SQL, and notebook contain detailed exception analysis.

交付 PBIX 有四页、每页三张图。下表的卡片和异常表属于后续建议，当前 PBIX 尚未内置；详细异常分析见 HTML 看板、SQL 和 Notebook。


| Page | Suggested visuals |
| --- | --- |
| Operations and margin / 经营创利 | Contract, voucher-cost and margin-proxy cards; supplier expense bar chart |
| Cash risk / 回款风险 | Due, paid and overdue cards; annual installment table |
| Tax and invoices / 税票合规 | Invoice count, amount variances, cross-period review; exception table |
| Vouchers and suppliers / 凭证供应链 | Voucher count, document type mix, supplier distribution, duplicate references |

Use titles such as “simulation / 模拟数据” on all pages. Cross-period flags are review prompts, not automatic tax violations. The margin proxy is not recognized accounting profit.
