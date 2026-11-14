"""Create a self-contained, offline four-view HTML dashboard."""

import csv
import html
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def rows(name):
    with (DATA / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def amount(value):
    return f"¥{Decimal(value):,.0f}"


def table(headers, records):
    head = "".join(f"<th>{html.escape(str(label))}</th>" for label in headers)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in record) + "</tr>" for record in records)
    return f"<div class='table-wrap'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"


contracts = rows("contracts.csv")
vouchers = rows("vouchers_and_docs.csv")
invoices = rows("tax_and_invoices.csv")
cash = rows("cash_flow_schedule.csv")
contract_value = Decimal(contracts[0]["contract_value_cny"])
voucher_total = sum((Decimal(row["amount_cny"]) for row in vouchers), Decimal(0))
actual_total = sum((Decimal(row["actual_receipt_cny"]) for row in cash), Decimal(0))
overdue_total = sum((Decimal(row["outstanding_cny"]) for row in cash if row["risk_flag"] == "overdue"), Decimal(0))

invoice_vouchers = defaultdict(lambda: Decimal(0))
for row in vouchers:
    invoice_vouchers[row["invoice_id"]] += Decimal(row["amount_cny"])
invoice_review = []
for row in invoices:
    variance = Decimal(row["net_amount_cny"]) - invoice_vouchers[row["invoice_id"]]
    cross_period = row["invoice_date"][:7] != row["service_period"]
    if variance or cross_period:
        invoice_review.append((row["invoice_id"], row["service_period"], row["invoice_date"], amount(variance), "跨期复核" if cross_period else "金额差异"))

references = Counter((row["contract_id"], row["document_reference"]) for row in vouchers)
duplicate_rows = [(row["voucher_id"], row["document_reference"], row["supplier_id"], amount(row["amount_cny"])) for row in vouchers if references[(row["contract_id"], row["document_reference"])] > 1]
suppliers = defaultdict(lambda: Decimal(0))
for row in vouchers:
    suppliers[row["supplier_id"]] += Decimal(row["amount_cny"])


def bars(values, maximum, currency=True):
    return "".join(f"<div class='bar-row'><span>{html.escape(str(label))}</span><div class='track'><div class='bar' style='width:{float(value / maximum * 100):.1f}%'></div></div><strong>{amount(value) if currency else int(value)}</strong></div>" for label, value in values)


cash_table = table(
    ["年度", "到期日", "应收", "实收", "未收", "状态"],
    [(row["installment_year"], row["due_date"], amount(row["scheduled_receivable_cny"]), amount(row["actual_receipt_cny"]), amount(row["outstanding_cny"]), row["risk_flag"]) for row in cash],
)
invoice_table = table(["发票", "服务期间", "开票日期", "差额", "提示"], invoice_review)
voucher_table = table(["凭证", "重复单据号", "供应商", "金额"], duplicate_rows)
supplier_bars = bars(sorted(suppliers.items()), max(suppliers.values()))
type_counts = Counter(row["doc_type"] for row in vouchers)
type_bars = bars([(kind, Decimal(count)) for kind, count in sorted(type_counts.items())], Decimal(max(type_counts.values())), currency=False)

page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>长期项目财务运营分析 · 演示看板</title>
<style>
:root{{font-family:Segoe UI,'Microsoft YaHei',sans-serif;color:#14263b;background:#f3f6fa}}
*{{box-sizing:border-box}}body{{margin:0}}header{{background:#132b46;color:white;padding:24px 4vw}}h1{{margin:0;font-size:26px}}header p{{margin:8px 0 0;color:#c7d8ea}}nav{{display:flex;gap:8px;flex-wrap:wrap;padding:12px 4vw;background:white;position:sticky;top:0;box-shadow:0 2px 8px #12263c15}}button{{border:0;border-radius:8px;padding:10px 16px;background:#e8eef5;color:#17314d;cursor:pointer;font-size:14px}}button.active{{background:#176a91;color:white}}main{{padding:24px 4vw;max-width:1500px;margin:auto}}section{{display:none}}section.active{{display:block}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:18px 0}}.card,.panel{{background:white;border:1px solid #e1e8ef;border-radius:12px;padding:18px;box-shadow:0 2px 6px #14263b0a}}.card small{{color:#62768b}}.card strong{{display:block;font-size:26px;margin-top:7px}}.panel{{margin:18px 0}}h2{{margin:4px 0 12px}}h3{{margin:0 0 16px}}.bar-row{{display:grid;grid-template-columns:160px 1fr 110px;align-items:center;gap:12px;margin:12px 0}}.track{{height:12px;background:#e9eff5;border-radius:8px;overflow:hidden}}.bar{{height:100%;background:#298caf;border-radius:8px}}.bar-row strong{{text-align:right;font-size:13px}}.table-wrap{{overflow:auto;max-height:550px}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #e9eef3;white-space:nowrap}}th{{background:#f4f8fb;position:sticky;top:0}}.note{{color:#546b7f;line-height:1.6}}footer{{padding:20px 4vw;color:#60758a}}@media(max-width:600px){{.bar-row{{grid-template-columns:100px 1fr}}.bar-row strong{{grid-column:2;text-align:left}}}}
</style></head><body>
<header><h1>长期项目财务运营分析</h1><p>Project Lifecycle Financial Operations Analytics · 模拟数据 · 截止日期 {cash[0]['as_of_date']}</p></header>
<nav><button class="active" data-page="overview">经营与创利</button><button data-page="cash">现金流风险</button><button data-page="tax">发票与税务</button><button data-page="vouchers">凭证与供应链</button></nav>
<main>
<section id="overview" class="active"><h2>经营与创利概览</h2><div class="grid"><div class="card"><small>合同总额</small><strong>{amount(contract_value)}</strong></div><div class="card"><small>凭证成本代理值</small><strong>{amount(voucher_total)}</strong></div><div class="card"><small>毛利代理值</small><strong>{amount(contract_value-voucher_total)}</strong></div><div class="card"><small>已收款</small><strong>{amount(actual_total)}</strong></div></div><div class="panel"><h3>供应商凭证金额</h3>{supplier_bars}</div><p class="note">毛利代理值仅为合同额减去模拟凭证金额，不等于会计利润；未包含财务费用、税费、期间费用等。</p></section>
<section id="cash"><h2>长周期现金流风险</h2><div class="grid"><div class="card"><small>应收总额</small><strong>{amount(contract_value)}</strong></div><div class="card"><small>已收款</small><strong>{amount(actual_total)}</strong></div><div class="card"><small>逾期未收</small><strong>{amount(overdue_total)}</strong></div><div class="card"><small>分期年数</small><strong>{len(cash)}</strong></div></div><div class="panel"><h3>分期计划</h3>{cash_table}</div><p class="note">future 代表未到期计划，不计作逾期。风险判断基于生成数据中的截止日期。</p></section>
<section id="tax"><h2>跨期发票与税务合规监控</h2><div class="grid"><div class="card"><small>发票总数</small><strong>{len(invoices)}</strong></div><div class="card"><small>金额差异</small><strong>{sum(Decimal(row['net_amount_cny']) != invoice_vouchers[row['invoice_id']] for row in invoices)}</strong></div><div class="card"><small>跨期复核</small><strong>{sum(row['invoice_date'][:7] != row['service_period'] for row in invoices)}</strong></div></div><div class="panel"><h3>发票复核清单</h3>{invoice_table}</div><p class="note">跨期仅是复核提示，不自动判定税务违规。税率为简化演示假设。</p></section>
<section id="vouchers"><h2>原始凭证与供应链监盘</h2><div class="grid"><div class="card"><small>凭证总数</small><strong>{len(vouchers)}</strong></div><div class="card"><small>重复单据号组</small><strong>{sum(count>1 for count in references.values())}</strong></div><div class="card"><small>供应商数</small><strong>{len(suppliers)}</strong></div></div><div class="panel"><h3>单据类型数量</h3>{type_bars}</div><div class="panel"><h3>重复单据号复核</h3>{voucher_table}</div></section>
</main><footer>公开来源为 Open Contracting Partnership 的虚构 OCDS 示例。所有分析记录均为本项目生成的模拟数据。此页面可离线打开。</footer>
<script>document.querySelectorAll('nav button').forEach(b=>b.addEventListener('click',()=>{{document.querySelectorAll('nav button,main section').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.page).classList.add('active')}}));</script>
</body></html>"""

target = ROOT / "powerbi" / "dashboard.html"
target.write_text(page, encoding="utf-8")
print(target)
