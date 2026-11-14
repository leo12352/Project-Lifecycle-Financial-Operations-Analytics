-- Run after importing the four CSV files as tables with matching filenames
-- (without .csv). This query uses SQLite syntax and returns review exceptions.
-- Amounts in the CSV are stored as decimal text; CAST is for demo queries only.
-- For production accounting, store integer cents or use a decimal-aware engine.

WITH voucher_totals AS (
    SELECT invoice_id,
           contract_id,
           ROUND(SUM(CAST(amount_cny AS REAL)), 2) AS voucher_net
    FROM vouchers_and_docs
    GROUP BY invoice_id, contract_id
),
invoice_variance AS (
    SELECT 'invoice_amount_difference' AS exception_type,
           i.invoice_id AS record_id,
           i.contract_id,
           ROUND(CAST(i.net_amount_cny AS REAL) - COALESCE(v.voucher_net, 0), 2)
               AS difference_cny,
           'Invoice net differs from linked voucher sum' AS detail
    FROM tax_and_invoices AS i
    LEFT JOIN voucher_totals AS v
      ON i.invoice_id = v.invoice_id AND i.contract_id = v.contract_id
    WHERE v.invoice_id IS NULL
       OR ABS(CAST(i.net_amount_cny AS REAL) - v.voucher_net) > 0.009
),
duplicate_documents AS (
    SELECT 'duplicate_document_reference' AS exception_type,
           document_reference AS record_id,
           contract_id,
           0.0 AS difference_cny,
           'Repeated document reference within contract' AS detail
    FROM vouchers_and_docs
    GROUP BY contract_id, document_reference
    HAVING COUNT(*) > 1
),
orphan_vouchers AS (
    SELECT 'missing_invoice' AS exception_type,
           v.voucher_id AS record_id,
           v.contract_id,
           CAST(v.amount_cny AS REAL) AS difference_cny,
           'Voucher invoice ID has no matching invoice' AS detail
    FROM vouchers_and_docs AS v
    LEFT JOIN tax_and_invoices AS i
      ON v.invoice_id = i.invoice_id AND v.contract_id = i.contract_id
    WHERE i.invoice_id IS NULL
),
overdue_cash AS (
    SELECT 'overdue_receivable' AS exception_type,
           CAST(installment_year AS TEXT) AS record_id,
           contract_id,
           CAST(outstanding_cny AS REAL) AS difference_cny,
           'Outstanding installment past due as of snapshot date' AS detail
    FROM cash_flow_schedule
    WHERE due_date < as_of_date AND CAST(outstanding_cny AS REAL) > 0
),
tax_calculation AS (
    SELECT 'tax_calculation_difference' AS exception_type,
           invoice_id AS record_id,
           contract_id,
           ROUND(CAST(tax_amount_cny AS REAL) - CAST(net_amount_cny AS REAL) * CAST(tax_rate AS REAL), 2) AS difference_cny,
           'Tax amount differs from net amount times rate' AS detail
    FROM tax_and_invoices
    WHERE ABS(CAST(tax_amount_cny AS REAL) - CAST(net_amount_cny AS REAL) * CAST(tax_rate AS REAL)) > 0.011
),
cross_period AS (
    SELECT 'cross_period_invoice_review' AS exception_type,
           invoice_id AS record_id,
           contract_id,
           0.0 AS difference_cny,
           'Invoice month differs from service period; review only' AS detail
    FROM tax_and_invoices
    WHERE SUBSTR(invoice_date, 1, 7) <> service_period
)
SELECT * FROM invoice_variance
UNION ALL SELECT * FROM duplicate_documents
UNION ALL SELECT * FROM orphan_vouchers
UNION ALL SELECT * FROM overdue_cash
UNION ALL SELECT * FROM tax_calculation
UNION ALL SELECT * FROM cross_period
ORDER BY exception_type, record_id;
