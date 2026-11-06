# 🩺 ISPProof

> Lightweight, cross-platform network monitor and downtime diagnostic tool with zero external dependencies.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📖 What It Does

**ISPProof** continuously monitors your network connectivity every 5 seconds. By testing three network layers in sequence—your local gateway, an external IP, and public DNS—it pinpoints the exact point of failure the moment your connection drops.

Every outage is tracked in real-time, recorded in `outages.csv` with precise timestamps and durations, and summarized in a clean, dark-mode Arabic HTML report (`report.html`).

---

## ❓ The Problem It Solves

When your internet suddenly stops working, the immediate question is:
> *"Is my Wi-Fi router down, is my ISP having an outage, or is it just a DNS glitch?"*

Instead of guessing or calling customer support without facts:
- **ISPProof diagnoses the exact root cause** in real time (`local`, `isp`, or `dns`).
- **ISPProof logs exact start and end times** for every interruption, giving you concrete evidence and downtime metrics to share with your Internet Service Provider.

---

## ✨ Features

- **Cross-Platform:** Automatically detects OS (`platform.system()`) and issues the appropriate ping syntax (`-n 1` on Windows, `-c 1` on macOS & Linux).
- **Zero Dependencies:** Built entirely with Python's standard library. No `pip install`, no virtual environment, no external packages.
- **Built-in Speed Test:** Measures download speed (10 MB via Cloudflare) once at startup or on demand via `--speedtest`, displayed in the CLI banner and HTML report.
- **3-Tier Root-Cause Diagnosis:** Accurately isolates local router failures, ISP disruptions, and DNS resolution failures.
- **Continuous Downtime Tracking:** Records start time, end time, duration (seconds), and problem classification into CSV.
- **Graceful Termination:** Pressing `Ctrl+C` closes any active outage and automatically generates the HTML report.
- **Standalone Report Generator:** Generate or regenerate `report.html` anytime via `report.py` without restarting the monitor.
- **Modern Arabic HTML Dashboard:** Clean, responsive, dark-mode interface with summary metric cards (outages, downtime, download speed) and detailed event history.

---

## 📋 Requirements

- **Python 3.9+**
- Standard Library only (`platform`, `subprocess`, `socket`, `csv`, `time`, `datetime`, `pathlib`, `sys`, `urllib`).

---

## 🚀 Installation

Clone or download the repository to your machine:

```bash
git clone https://github.com/your-username/ISPProof.git
cd ISPProof
```

No package installation is required!

---

## 💻 Usage

### 1. Start Network Monitoring

Run the main monitoring script:

**macOS / Linux:**
```bash
python3 main.py
```

**Windows:**
```cmd
python main.py
```

To stop monitoring, press **`Ctrl+C`**. ISPProof will safely close any active incident, write it to `outages.csv`, and automatically generate `report.html`.

---

### 2. Standalone Speed Test (`--speedtest`)

To test download speed once without starting continuous monitoring:

```bash
python3 main.py --speedtest
```

Output:
```text
Download speed: 23.54 Mbps
```

---

### 3. Generate / View the HTML Report

To compile or refresh the HTML report at any time from your logged outages:

```bash
# Generate report from default outages.csv
python3 report.py

# Or specify a custom CSV file
python3 report.py my_outages.csv
```

Then open `report.html` in your favorite web browser:

**macOS:**
```bash
open report.html
```

**Linux:**
```bash
xdg-open report.html
```

**Windows:**
```cmd
start report.html
```

---

## 🖥️ Example Terminal Output

```text
==================================================
  ISPProof | نظام: Darwin
  الراوتر : 192.168.1.1
  خارجي   : 8.8.8.8  |  DNS: google.com
  الفاصل  : كل 5 ثوانٍ
  Ctrl+C للإيقاف وتوليد التقرير
==================================================

[12:30:00] ✔ الشبكة سليمة
[12:30:05] ✔ الشبكة سليمة
[12:30:10] ✘ عطل جديد → isp
[12:30:15] ✘ عطل مستمر (isp) منذ 5ث
[12:30:20] ✘ عطل مستمر (isp) منذ 10ث
  [CSV] عطل مسجَّل | نوع: isp | مدة: 15.2ث
[12:30:25] ✔ الشبكة سليمة
^C
[!] تم الإيقاف.
[report] ✔ تم إنشاء التقرير: /path/to/report.html
[report]   أعطال: 1 | توقف: 0س 0د 15ث
```

---

## 📊 Diagnostic Logic: How to Read Results

ISPProof evaluates network health hierarchically every 5 seconds:

```
                  ┌────────────────────────┐
                  │ Ping Router 192.168.1.1 │
                  └───────────┬────────────┘
                              │
                    Fails     │     Succeeds
           ┌──────────────────┴──────────────────┐
           ▼                                     ▼
     ┌───────────┐                      ┌─────────────────┐
     │   LOCAL   │                      │ Ping IP 8.8.8.8 │
     │  Problem  │                      └────────┬────────┘
     └───────────┘                               │
                                       Fails     │     Succeeds
                              ┌──────────────────┴──────────────────┐
                              ▼                                     ▼
                        ┌───────────┐                     ┌───────────────────┐
                        │    ISP    │                     │ Resolve google.com │
                        │  Problem  │                     └─────────┬─────────┘
                        └───────────┘                               │
                                                          Fails     │     Succeeds
                                                 ┌──────────────────┴──────────────────┐
                                                 ▼                                     ▼
                                           ┌───────────┐                         ┌───────────┐
                                           │    DNS    │                         │  ALL OK   │
                                           │  Problem  │                         │ Healthy ✔ │
                                           └───────────┘                         └───────────┘
```

| Status | Meaning | What is Likely Wrong? |
|---|---|---|
| `local` | **Local / Router Problem** | Router is unresponsive. Check Wi-Fi connection, Ethernet cable, or reboot the router. |
| `isp` | **ISP / Provider Problem** | Router is online, but external internet (`8.8.8.8`) is unreachable. The issue is with your ISP, modem, or fiber link. |
| `dns` | **DNS Problem** | Internet connection is up, but domain resolution fails. Your DNS server is down, blocked, or misconfigured. |
| `None` | **Healthy** | All checks passed successfully. |

---

## 📁 Repository Structure

| File | Description |
|---|---|
| `main.py` | Main daemon that runs the 5-second monitoring loop, detects OS, diagnoses network state, and logs outages. |
| `report.py` | Standalone report module that reads `outages.csv` and builds the responsive Arabic HTML dashboard. |
| `outages.csv` | *(Generated)* Comma-separated log file storing `start_time`, `end_time`, `duration_seconds`, and `type`. |
| `last_speed.txt` | *(Generated)* Caches the most recent download speed measurement (in Mbps). |
| `report.html` | *(Generated)* Self-contained Arabic dashboard displaying aggregate statistics and incident history. |
| `.gitignore` | Prevents generated files (`outages.csv`, `report.html`) and Python cache from entering version control. |
| `README.md` | Comprehensive documentation and guide. |

---

## 🔧 Troubleshooting: Different Router IP

By default, ISPProof checks `192.168.1.1`. If your router uses a different IP address (e.g., `192.168.0.1` or `10.0.0.1`):

### 1. Find Your Default Gateway IP

- **Windows:**
  ```cmd
  ipconfig
  ```
  Look for **Default Gateway**.

- **macOS:**
  ```bash
  netstat -nr | grep default
  # or
  ipconfig getoption en0 router
  ```

- **Linux:**
  ```bash
  ip route | grep default
  ```

### 2. Update `main.py`

Open `main.py` and modify line 19:

```python
# Change from:
ROUTER_IP = "192.168.1.1"

# To your router's IP, for example:
ROUTER_IP = "192.168.0.1"
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

```text
MIT License

Copyright (c) 2026 ISPProof Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
