# Data provenance / 数据来源

## Public source

- Repository: https://github.com/open-contracting/sample-data
- Pinned commit: `703affda90d0fb16a7cbfd0ee126ac77261d3d06`
- File: `fictional-example/1.1/ocds-213czf-000-00001-06-implementation.json`
- Local copy: `sources/ocds/implementation.json`
- License: BSD 3-Clause; the original license is retained at `sources/ocds/LICENSE`.
- Nature: a **fictional** example of the Open Contracting Data Standard, not live procurement data.

The builder reads `ocid`, contract ID, title, value, and currency from the public example. The source describes an GBP 11 million, roughly one-year fictional contract and two sample implementation transactions. The 20-year CNY 15 million base-cost scenario with CNY 1.3 million annual receipts and CNY 2 million terminal disposal proceeds is **not** a conversion of that source contract. The source transactions are not copied into the analytical tables.

## Scenario assumptions

| Item | Assumption | Origin |
| --- | --- | --- |
| Base project cost | CNY 15,000,000 | Customer revision; synthetic scenario |
| Installment contract value | CNY 26,000,000 | 20 × CNY 1,300,000 |
| Terminal asset disposal proceeds | CNY 2,000,000 in 2045 | Customer revision; separate from installments |
| Term | 2026–2045, 20 annual installments | Local development requirements; specific dates simulated |
| Annual receivable | CNY 1,300,000 | Customer revision |
| Vouchers | 42 per year, 840 total | Generated with fixed seed; amounts and dates simulated |
| Invoices | One per two vouchers, 420 total; service period uses the last linked voucher date | Generated for reconciliation exercises |
| VAT rates | 13% for equipment/material pairs; 9% for work/acceptance pairs | Simplified demo assumptions; not tax advice |
| Receipts | CNY 600,000 in 2026; zero future actuals | Simulated snapshot as of 2026-11-13 |
| Exceptions | Repeated document references and invoice net amount differences | Deliberate test cases |

Every output row has `record_origin=synthetic_from_ocds_example` and `source_ocid`. These fields mean the row belongs to a scenario modeled after the public example; they **do not** claim that the row was observed in the source. There is no public record of the generated voucher, tax, or receipt values.

If the project later uses a real public transaction dataset, replace the source layer and revise this mapping before claiming real-data analysis. Preserve original identifiers, units, dates, and dataset license in that work.
