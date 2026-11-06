"""
ISPProof — main.py
====================
الملف الرئيسي: يراقب الشبكة كل 5 ثوانٍ ويسجّل الأعطال في outages.csv.
تشغيل: python main.py
إيقاف: Ctrl+C  (يُولِّد تقرير HTML تلقائيًا عند الإيقاف)
"""

import platform       # لاكتشاف نظام التشغيل
import subprocess     # لتنفيذ أمر ping
import socket         # لاختبار DNS
import csv            # لحفظ الأعطال
import time           # للانتظار بين الفحوصات
import sys            # لقراءة وسائط سطر الأوامر مثل --speedtest
import urllib.request # لقياس سرعة التحميل
from datetime import datetime
from pathlib import Path
import report         # ملف report.py المجاور — لتوليد HTML عند الإيقاف

# ─────────────────────── الإعدادات ───────────────────────
ROUTER_IP      = "192.168.1.1"  # عنوان الراوتر المحلي
EXTERNAL_IP    = "8.8.8.8"      # خادم Google العام (للتحقق من الإنترنت)
DNS_HOST       = "google.com"   # النطاق المستخدم لفحص DNS
CHECK_INTERVAL = 5              # الفاصل بين كل فحص (ثوانٍ)
CSV_FILE       = Path("outages.csv")
SPEED_URL      = "https://speed.cloudflare.com/__down?bytes=10000000"  # تحميل 10MB
SPEED_FILE     = Path("last_speed.txt")  # ملف حفظ آخر نتيجة سرعة

# اكتشاف نظام التشغيل مرة واحدة عند بدء التشغيل
OS = platform.system()  # "Windows" أو "Darwin" (macOS) أو "Linux"


# ──────────────────────── دوال الفحص ────────────────────────

def ping(host: str) -> bool:
    """
    يرسل ping واحدًا ويُعيد True إذا نجح.
    يستخدم -n على Windows و -c على macOS/Linux.
    """
    flag = "-n" if OS == "Windows" else "-c"
    try:
        result = subprocess.run(
            ["ping", flag, "1", host],
            stdout=subprocess.DEVNULL,  # تجاهل المخرجات
            stderr=subprocess.DEVNULL,
            timeout=4                   # مهلة 4 ثوانٍ
        )
        return result.returncode == 0   # 0 = نجح
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_dns(host: str) -> bool:
    """يحاول تحويل اسم النطاق إلى IP — يُعيد True إذا نجح."""
    try:
        socket.gethostbyname(host)
        return True
    except socket.gaierror:
        return False


def measure_download_speed():
    """
    يقيس سرعة التحميل عبر تنزيل 10 ميجابايت من خادم Cloudflare.
    - يحسب الوقت المنقضي ويحوّله إلى ميجابت في الثانية (Mbps).
    - إذا فشل التحميل، يطبع 'Speed test failed' ويُعيد None دون توقف البرنامج.
    - يحفظ آخر نتيجة في last_speed.txt لعرضها في التقرير.
    """
    try:
        req = urllib.request.Request(
            SPEED_URL,
            headers={"User-Agent": "ISPProof/1.0"}
        )
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=20) as response:
            data = response.read()
        elapsed = time.time() - start_time

        if elapsed <= 0 or not data:
            print("Speed test failed")
            return None

        # تحويل البايت إلى ميجابت: (Bytes * 8) / (elapsed * 1,000,000)
        speed_mbps = round((len(data) * 8) / (elapsed * 1_000_000), 2)

        # حفظ آخر نتيجة في ملف للاستخدام في report.html
        try:
            with open(SPEED_FILE, "w", encoding="utf-8") as f:
                f.write(str(speed_mbps))
        except Exception:
            pass

        return speed_mbps
    except Exception:
        print("Speed test failed")
        return None


def diagnose():
    """
    يفحص طبقات الاتصال الثلاث ويُعيد نوع المشكلة:
      "local" — الراوتر لا يستجيب         ← مشكلة محلية
      "isp"   — الراوتر يعمل، الإنترنت لا ← مشكلة مزود الخدمة
      "dns"   — الإنترنت يعمل، DNS لا     ← مشكلة DNS
      None    — كل شيء يعمل بشكل طبيعي
    """
    if not ping(ROUTER_IP):
        return "local"
    if not ping(EXTERNAL_IP):
        return "isp"
    if not check_dns(DNS_HOST):
        return "dns"
    return None


# ──────────────────────── إعداد CSV ────────────────────────

HEADER = ["start_time", "end_time", "duration_seconds", "type"]

def init_csv():
    """يُنشئ ملف CSV بأعمدة الرأس إذا لم يكن موجودًا أو يضيف الرأس إذا كان مفقودًا."""
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HEADER)
        return

    # إذا كان الملف موجودًا، نتحقق من وجود سطر الرأس
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    if not lines or not lines[0].startswith("start_time"):
        new_content = ",".join(HEADER) + "\n" + (content if content else "")
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            f.write(new_content)


def log_outage(start: datetime, end: datetime, outage_type: str):
    """يكتب سطرًا واحدًا في CSV يوثّق العطل المنتهي."""
    duration = round((end - start).total_seconds(), 1)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            start.strftime("%Y-%m-%d %H:%M:%S"),
            end.strftime("%Y-%m-%d %H:%M:%S"),
            duration,
            outage_type,
        ])
    print(f"  [CSV] عطل مسجَّل | نوع: {outage_type} | مدة: {duration}ث")


# ──────────────────────── الحلقة الرئيسية ────────────────────────

def main():
    """
    حلقة المراقبة الرئيسية:
    - تقيس سرعة التحميل لمرة واحدة فقط عند بدء التشغيل.
    - تفحص الشبكة كل CHECK_INTERVAL ثانية.
    - تتذكر متى بدأ العطل وما نوعه.
    - تُسجّل العطل في CSV بمجرد انتهائه.
    - عند الضغط على Ctrl+C تُنهي أي عطل مفتوح وتولّد التقرير.
    """
    init_csv()

    # قياس سرعة الإنترنت لمرة واحدة عند بدء التشغيل
    speed = measure_download_speed()

    print("=" * 50)
    print(f"  ISPProof | نظام: {OS}")
    if speed is not None:
        print(f"  Download speed: {speed} Mbps")
    print(f"  الراوتر : {ROUTER_IP}")
    print(f"  خارجي   : {EXTERNAL_IP}  |  DNS: {DNS_HOST}")
    print(f"  الفاصل  : كل {CHECK_INTERVAL} ثوانٍ")
    print("  Ctrl+C للإيقاف وتوليد التقرير")
    print("=" * 50 + "\n")

    outage_start = None   # وقت بداية العطل الحالي
    outage_type  = None   # نوع العطل الحالي

    try:
        while True:
            now    = datetime.now()
            status = diagnose()

            if status is None:
                # ✔ الشبكة تعمل
                if outage_start:
                    # كان هناك عطل — أُغلق الآن، سجّله
                    log_outage(outage_start, now, outage_type)
                    outage_start = None
                    outage_type  = None
                print(f"[{now.strftime('%H:%M:%S')}] ✔ الشبكة سليمة")
            else:
                # ✘ توجد مشكلة
                if outage_start is None:
                    # عطل جديد — ابدأ التتبع
                    outage_start = now
                    outage_type  = status
                    print(f"[{now.strftime('%H:%M:%S')}] ✘ عطل جديد → {status}")
                else:
                    elapsed = round((now - outage_start).total_seconds())
                    print(f"[{now.strftime('%H:%M:%S')}] ✘ عطل مستمر ({status}) منذ {elapsed}ث")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n[!] تم الإيقاف.")
        # أغلق أي عطل لم يُسجَّل بعد
        if outage_start:
            log_outage(outage_start, datetime.now(), outage_type)
        # ولّد التقرير تلقائيًا
        report.generate(CSV_FILE)


if __name__ == "__main__":
    # إذا تم تمرير الوسيط --speedtest، نقيس السرعة فقط ونخرج دون بدء المراقبة
    if "--speedtest" in sys.argv:
        speed = measure_download_speed()
        if speed is not None:
            print(f"Download speed: {speed} Mbps")
        sys.exit(0)

    main()
