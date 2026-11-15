# Power BI build guide / Power BI 搭建说明

The native [four-page PBIX](Project_Lifecycle_Financial_Operations_Analytics.pbix) contains four imported tables and twelve data-driven charts. It was refreshed and saved in Power BI Desktop on 2026-11-15. The offline [dashboard](dashboard.html) provides a separate review view.

原生 [四页 PBIX](Project_Lifecycle_Financial_Operations_Analytics.pbix) 已在 Power BI Desktop 中打开并保存，包含四张数据表和十二张图表。[离线看板](dashboard.html) 可供对照审核。

## Refreshing the delivered PBIX / 刷新交付 PBIX

The PBIX includes imported data and opens without a refresh. Its saved Excel source is `F:\node_codex\finance_model.xlsx` on the build machine. Before refreshing it on a different checkout, use **File → Options and settings → Data source settings → Change Source** in Power BI Desktop and select the checkout's `powerbi/finance_model.xlsx`, then refresh all four tables. The workbook is committed with the report.

PBIX 已内嵌数据，可直接打开。若要刷新，请在 Power BI Desktop 的数据源设置中把 Excel 源改为本地仓库的 `powerbi/finance_model.xlsx`，然后刷新四张表。

## Import / 导入

1. In Power BI Desktop, choose **Get data → Text/CSV** for each file in `data/`.
2. Set date columns to Date, `installment_year` to Whole number, and CNY amounts to Fixed decimal number. Keep IDs and `document_reference` as Text.
3. Create relationships: `contractsTable[contract_id]` one to many with each other table; `taxandinvoicesTable[invoice_id]` one to many with `vouchersanddocsTable[invoice_id]`. Use single direction from the lookup table.
4. Use `cashflowscheduleTable[as_of_date]` as a clearly visible snapshot field. It is fixed in the generated files.

## Suggested measures / 建议度量值（当前 PBIX 未内置）

```DAX
Installment Contract Value CNY = SUM(contractsTable[contract_value_cny])
Base Project Cost CNY = SUM(contractsTable[project_cost_cny])
Terminal Disposal Proceeds CNY = SUM(cashflowscheduleTable[disposal_proceeds_cny])
Planned Total Inflow CNY = [Installment Contract Value CNY] + [Terminal Disposal Proceeds CNY]
Undiscounted Plan Surplus CNY = [Planned Total Inflow CNY] - [Base Project Cost CNY]
Scheduled Receivable CNY = SUM(cashflowscheduleTable[scheduled_receivable_cny])
Actual Receipt CNY = SUM(cashflowscheduleTable[actual_receipt_cny])
Overdue CNY = CALCULATE(SUM(cashflowscheduleTable[outstanding_cny]), cashflowscheduleTable[risk_flag] = "overdue")
Invoice Count = DISTINCTCOUNT(taxandinvoicesTable[invoice_id])
Voucher Count = DISTINCTCOUNT(vouchersanddocsTable[voucher_id])
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

The revised scenario uses CNY 15 million base project cost, CNY 1.3 million annual installments for 20 years, and CNY 2 million terminal asset disposal proceeds in 2045. The resulting CNY 13 million undiscounted plan surplus is not accounting profit. Voucher amounts are sample cost detail; do not subtract them again from the base cost. Cross-period flags are review prompts, not automatic tax violations.
