"""
ISPProof — report.py
======================
مولّد تقرير HTML باللغة العربية.
يقرأ outages.csv ويكتب report.html.

الاستخدام المباشر:
    python report.py               ← يولّد report.html من outages.csv
    python report.py my_data.csv   ← يولّد من ملف CSV آخر
"""

import csv
import sys
from datetime import datetime
from pathlib import Path


# ─── الثوابت ───
HTML_OUT   = Path("report.html")
SPEED_FILE = Path("last_speed.txt")

# ترجمة أنواع الأعطال إلى العربية
TYPE_AR = {
    "local": "مشكلة محلية (راوتر)",
    "isp":   "مشكلة مزود الخدمة",
    "dns":   "مشكلة DNS",
}


def _get_last_speed() -> str:
    """يقرأ آخر نتيجة لسرعة التحميل تم قياسها وحفظها."""
    if SPEED_FILE.exists():
        try:
            val = SPEED_FILE.read_text(encoding="utf-8").strip()
            if val:
                return f"{val} Mbps"
        except Exception:
            pass
    return "غير متوفر"


def _fmt_duration(total_seconds: float) -> str:
    """يحوّل عدد الثواني إلى صيغة 'Xس Xد Xث' مقروءة."""
    h, rem = divmod(int(total_seconds), 3600)
    m, s   = divmod(rem, 60)
    return f"{h}س {m}د {s}ث"


def _build_rows(outages: list[dict]) -> str:
    """يبني صفوف <tr> لجدول HTML من قائمة الأعطال."""
    if not outages:
        return '<tr><td colspan="4" class="ok">&#x2714; لا توجد أعطال مسجّلة</td></tr>'

    rows = ""
    for o in outages:
        label = TYPE_AR.get(o["type"], o["type"])
        rows += (
            f'<tr>'
            f'<td>{o["start_time"]}</td>'
            f'<td>{o["end_time"]}</td>'
            f'<td>{o["duration_seconds"]}ث</td>'
            f'<td>{label}</td>'
            f'</tr>\n'
        )
    return rows


def generate(csv_path: Path = Path("outages.csv")):
    """
    الدالة الرئيسية:
    1. تقرأ csv_path
    2. تحسب إجمالي الأعطال ووقت التوقف
    3. تكتب report.html
    """

    # ── قراءة البيانات ──
    outages    = []
    total_secs = 0.0

    if csv_path.exists():
        with open(csv_path, "r", encoding="utf-8") as f:
            first_line = f.readline()
            if first_line:
                f.seek(0)
                has_header = "start_time" in first_line
                reader = csv.DictReader(
                    f,
                    fieldnames=["start_time", "end_time", "duration_seconds", "type"] if not has_header else None
                )
                for row in reader:
                    if row.get("start_time") == "start_time":
                        continue
                    val = row.get("duration_seconds")
                    if val is None:
                        continue
                    try:
                        dur = float(val)
                    except (ValueError, TypeError):
                        continue
                    outages.append(row)
                    total_secs += dur
    else:
        print(f"[تحذير] الملف '{csv_path}' غير موجود — سيُنشأ تقرير فارغ.")

    # ── إحصائيات ──
    total_outages = len(outages)
    total_str     = _fmt_duration(total_secs)
    rows_html     = _build_rows(outages)
    speed_display = _get_last_speed()
    generated_at  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── قالب HTML ──
    html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>تقرير ISPProof</title>
  <style>
    /* ─── إعادة الضبط والأساس ─── */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Segoe UI", Tahoma, Arial, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      padding: 2.5rem 2rem;
      direction: rtl;
      min-height: 100vh;
    }}

    /* ─── رأس الصفحة ─── */
    header {{ margin-bottom: 2rem; }}
    h1 {{ font-size: 2rem; color: #38bdf8; }}
    .subtitle {{ color: #64748b; font-size: 0.875rem; margin-top: 0.25rem; }}

    /* ─── بطاقات الإحصائيات ─── */
    .cards {{
      display: flex;
      gap: 1.25rem;
      flex-wrap: wrap;
      margin-bottom: 2.5rem;
    }}
    .card {{
      flex: 1;
      min-width: 160px;
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 14px;
      padding: 1.4rem 1.75rem;
    }}
    .card .label {{ color: #94a3b8; font-size: 0.8rem; margin-bottom: 0.4rem; }}
    .card .value {{ font-size: 2.1rem; font-weight: 700; }}
    .card.danger .value {{ color: #f87171; }}  /* أحمر للأعطال */
    .card.info   .value {{ color: #38bdf8; }}  /* أزرق للوقت */
    .card.speed  .value {{ color: #34d399; }}  /* أخضر للسرعة */

    /* ─── الجدول ─── */
    .table-wrap {{
      border-radius: 14px;
      overflow: hidden;
      border: 1px solid #334155;
    }}
    table {{ width: 100%; border-collapse: collapse; background: #1e293b; }}
    thead th {{
      background: #0369a1;
      color: #f0f9ff;
      padding: 0.75rem 1rem;
      text-align: right;
      font-size: 0.875rem;
      font-weight: 600;
    }}
    tbody td {{
      padding: 0.7rem 1rem;
      font-size: 0.875rem;
      border-bottom: 1px solid #1e3a5f30;
    }}
    tbody tr:last-child td {{ border-bottom: none; }}
    tbody tr:hover td {{ background: #263347; }}

    /* ─── خلية "لا توجد أعطال" ─── */
    td.ok {{
      text-align: center;
      color: #4ade80;
      padding: 2rem;
      font-size: 1rem;
    }}

    /* ─── تذييل ─── */
    footer {{
      margin-top: 2rem;
      text-align: center;
      color: #334155;
      font-size: 0.75rem;
    }}
  </style>
</head>
<body>

  <header>
    <h1>&#x1FA7A; ISPProof &mdash; تقرير الشبكة</h1>
    <p class="subtitle">تاريخ التقرير: {generated_at}</p>
  </header>

  <!-- بطاقات الإحصائيات -->
  <div class="cards">
    <div class="card danger">
      <div class="label">إجمالي الأعطال</div>
      <div class="value">{total_outages}</div>
    </div>
    <div class="card info">
      <div class="label">إجمالي وقت التوقف</div>
      <div class="value">{total_str}</div>
    </div>
    <div class="card speed">
      <div class="label">سرعة التحميل (Download)</div>
      <div class="value">{speed_display}</div>
    </div>
  </div>

  <!-- جدول الأعطال التفصيلي -->
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>وقت البداية</th>
          <th>وقت الانتهاء</th>
          <th>المدة</th>
          <th>نوع العطل</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>

  <footer>ISPProof &bull; Python Standard Library Only</footer>

</body>
</html>
"""

    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"[report] ✔ تم إنشاء التقرير: {HTML_OUT.resolve()}")
    print(f"[report]   أعطال: {total_outages} | توقف: {total_str}")


# ── تشغيل مباشر ──
if __name__ == "__main__":
    # قبول مسار CSV اختياري من سطر الأوامر
    csv_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outages.csv")
    generate(csv_file)
