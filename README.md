<div align="center">

# 🌐 Network Monitor Pro

**Advanced real-time network monitoring with traffic visualization, anomaly detection, and comprehensive performance analysis.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge)](https://github.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.1-brightgreen?style=for-the-badge)](CHANGELOG.md)

[Features](#-features) · [Installation](#-installation) · [Quick Start](#-quick-start) · [Screenshots](#-interface-overview) · [Troubleshooting](#-troubleshooting)

</div>

---

## 📖 Overview

Network Monitor Pro is a feature-rich network monitoring application built with Python and Tkinter. It provides a live, graphical view of your network — tracking speeds, connections, protocol distributions, latency, and potential security threats — all in one intuitive interface.

Whether you're a developer debugging traffic, a sysadmin monitoring infrastructure, or a power user who wants visibility into their home network, Network Monitor Pro has you covered.

---

## ✨ Features

### 📊 Real-Time Dashboard
- Live download/upload speed meters
- Latency, jitter, and packet loss indicators
- Active connection counter
- Network health score (0–100) with actionable recommendations
- Interface selector for multi-NIC systems

### 📡 Live Packet Capture
- Filter by protocol: TCP, UDP, HTTP/HTTPS, DNS, ICMP
- Timestamped packet tree with source, destination, size, and protocol
- Real-time protocol statistics
- Export captured packets to CSV

### 🔗 Connection Manager
- View all active connections with process name and PID
- Search/filter by process
- Inspect connection details
- Terminate connections (simulated)
- Export connection list to CSV

### 📈 Analysis Suite

| Sub-Tab | What You Get |
|---|---|
| **Protocol Analysis** | Pie chart of traffic by protocol |
| **Traffic Analysis** | Speed timeline, top hosts, port activity, composition over time |
| **Performance Analysis** | Latency histogram, jitter graph, packet loss trends |
| **Anomaly Detection** | Threat identification with severity levels and recommendations |

### 🛠️ Built-in Tools
- Speed test
- Network health assessment report
- DNS cache flush
- Ping tester
- Multi-format export: CSV, JSON, PDF, PNG

### ⚙️ Technical Highlights
- Multi-platform: Windows, Linux, macOS
- Thread-safe background monitoring with non-blocking GUI updates
- Real system data via `psutil`
- Demo mode when live data is unavailable
- Smart caching to minimize redundant calls

---

## 🚀 Installation

### Prerequisites

| Requirement | Details |
|---|---|
| Python | 3.8 or higher |
| pip | Latest recommended |
| Privileges | Admin/root for some features (packet capture) |

### 1 · Clone the Repository

```bash
git clone https://github.com/yourusername/network-monitor-pro.git
cd network-monitor-pro
```

### 2 · Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install matplotlib psutil numpy pillow ttkthemes
```

### 3 · Windows-Only (Optional)

For enhanced Wi-Fi information on Windows:

```bash
pip install pywin32
```

---

## ⚡ Quick Start

```bash
python gui_interface.py
```

Then:

1. **Select your network interface** from the dropdown (e.g., `Wi-Fi`, `eth0`)
2. **Click "Start Monitoring"** to begin data collection
3. **Navigate the tabs** to explore traffic, connections, and analysis

---

## 🖥️ Interface Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  File  Tools  View  Help                                        │
├─────────────────────────────────────────────────────────────────┤
│  [📊 Dashboard]  [📡 Monitoring]  [🔗 Connections]  [📈 Analysis]│
│                                                                 │
│  Interface: [Wi-Fi ▼]  ▶ Start  ⟳ Refresh  ⚡ Speed Test       │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ┌───────────────────┐  ┌──────────────────────────────────┐   │
│  │   Network Info    │  │         Speed Metrics            │   │
│  │  IP: 192.168.1.5  │  │  ↓ Download:   85.2 Mbps         │   │
│  │  GW: 192.168.1.1  │  │  ↑ Upload:     22.1 Mbps         │   │
│  │  DNS: 8.8.8.8     │  │  Packets/s:   145                │   │
│  └───────────────────┘  └──────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Latency: 24 ms · Jitter: 2.1 ms · Loss: 0.2% · 42 conn│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Health Score: 87/100  [████████████████████░░░░░]  Good       │
│                                                                 │
│  [📊 View Graphs]  [🔍 Deep Analysis]  [⚙️ Settings]  [📋 Export]│
└─────────────────────────────────────────────────────────────────┘
```

### Tab Descriptions

<details>
<summary><strong>📊 Dashboard</strong></summary>

The main control center. Shows real-time:
- Network interface information (IP, gateway, DNS)
- Download/upload speeds and packet rates
- Quality metrics: latency, jitter, packet loss, active connections
- Network health score with improvement recommendations
- Quick-action buttons for common tasks

</details>

<details>
<summary><strong>📡 Monitoring</strong></summary>

Live packet capture with:
- Protocol filter buttons (All / TCP / UDP / HTTP(S) / DNS / ICMP)
- Packet table: timestamp, source IP, destination IP, protocol, size
- Running totals: total packets, bytes transferred, per-protocol counts
- Start/Stop/Clear/Export controls

</details>

<details>
<summary><strong>🔗 Connections</strong></summary>

Full view of active network connections:
- Protocol, local/remote address and port, connection state
- Process name and PID for each connection
- Search by process name
- Export to CSV

</details>

<details>
<summary><strong>📈 Analysis</strong></summary>

Four sub-tabs for deep insight:

- **Protocol Analysis** — pie chart of traffic by protocol with export
- **Traffic Analysis** — speed timeline, top hosts, port heatmap, composition chart
- **Performance Analysis** — latency histogram, jitter timeline, packet loss graph, trend lines
- **Anomaly Detection** — flagged events with High/Medium/Low severity, descriptions, and recommended actions

</details>

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `psutil` | System-level network stats and connections |
| `matplotlib` | Graphs and charts in the Analysis tab |
| `numpy` | Numerical processing for performance metrics |
| `pillow` | Image export support |
| `ttkthemes` | Enhanced Tkinter themes |
| `pywin32` *(Windows only)* | Wi-Fi adapter details on Windows |

Install all at once:

```bash
pip install -r requirements.txt
```

---

## 🗂️ File Structure

```
network-monitor-pro/
├── gui_interface.py        # Main application entry point
├── network_monitor.py      # Core monitoring logic and data collection
├── analysis.py             # Traffic analysis and anomaly detection
├── requirements.txt        # Python dependencies
├── README.md
└── exports/                # Default directory for exported reports
```

---

## 🔧 Troubleshooting

### Permission Denied / No Packets Captured

Packet capture requires elevated privileges on most systems.

```bash
# Linux / macOS
sudo python gui_interface.py

# Windows — run your terminal as Administrator
```

### No Interfaces Showing in Dropdown

Make sure `psutil` is installed correctly:

```bash
pip install --upgrade psutil
```

Then restart the application.

### Graphs Not Rendering

`matplotlib` may be missing a backend. Install Tkinter's matplotlib backend:

```bash
pip install matplotlib --upgrade
```

On some Linux systems, you may also need:

```bash
sudo apt-get install python3-tk
```

### "Module Not Found" Error

Re-run the dependency install:

```bash
pip install -r requirements.txt
```

If the issue persists, check that you're using the correct Python environment (especially if using `conda` or `venv`).

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes with clear messages: `git commit -m "Add: description of change"`
4. Push to your fork: `git push origin feature/your-feature-name`
5. Open a Pull Request against `main`

Please follow PEP 8 style guidelines and include a brief description of what your PR does and why.

---

## 🗺️ Roadmap

- [ ] Dark mode support
- [ ] Historical data logging and playback
- [ ] Alert notifications (email / desktop)
- [ ] Plugin system for custom protocol parsers
- [ ] Web-based dashboard option

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for full details.

---

## 💬 Support

- 🐛 **Bug reports**: [Open an issue](https://github.com/yourusername/network-monitor-pro/issues)
- 💡 **Feature requests**: [Start a discussion](https://github.com/yourusername/network-monitor-pro/discussions)
- 📧 **Email**: your@email.com

---

<div align="center">

Made with ❤️ using Python · Tkinter · psutil · matplotlib

</div>
