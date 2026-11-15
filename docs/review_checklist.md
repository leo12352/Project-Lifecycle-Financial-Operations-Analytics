# Local review checklist / 本地审核清单

- Open `powerbi/dashboard.html` and inspect its four tabs; compare with the four PNG screenshots.
- Run `python scripts/validate_data.py` and confirm 1 contract, 840 vouchers, 420 invoices, and 20 installments. Confirm CNY 15 million base cost, CNY 1.3 million yearly installments, CNY 2 million disposal proceeds only in 2045, and CNY 13 million undiscounted plan surplus.
- Confirm SQL exception counts: 20 invoice differences, 6 duplicate document references, 1 overdue installment, and 80 cross-period review flags.
- Open `notebooks/risk_analysis.ipynb` and run all cells with Pandas and NumPy installed.
- Confirm every CSV row is marked `synthetic_from_ocds_example`; the source itself is a fictional OCDS example.
- Open `powerbi/Project_Lifecycle_Financial_Operations_Analytics.pbix` in Power BI Desktop and inspect all four pages and twelve charts. See `powerbi/POWER_BI_GUIDE.md` for current limits.
- Review the revised scenario locally before committing or pushing the update to the public repository.
