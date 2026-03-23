# Network Monitor Pro v2.1 - FIXED

![Network Monitor Pro](https://img.shields.io/badge/Network-Monitor%20Pro-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Version](https://img.shields.io/badge/Version-2.1--Fixed-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

**Advanced Network Monitoring Tool with Real-Time Visualization and Comprehensive Analysis**

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [User Interface Guide](#-user-interface-guide)
- [File Structure](#-file-structure)
- [Detailed Code Explanation](#-detailed-code-explanation)
- [Dependencies](#-dependencies)
- [Troubleshooting](#-troubleshooting)
- [Known Issues & Fixes](#-known-issues--fixes)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

## 📖 Overview

Network Monitor Pro is a comprehensive, feature-rich network monitoring application built with Python and Tkinter. It provides real-time network analysis, traffic visualization, performance monitoring, and security anomaly detection in an intuitive graphical interface.

### Key Capabilities:
- **Real-time Network Monitoring**: Track download/upload speeds, latency, packet loss
- **Traffic Analysis**: Visualize protocol distributions, top hosts, and port activity
- **Connection Management**: View and manage active network connections
- **Anomaly Detection**: Identify suspicious network activities and security threats
- **Performance Assessment**: Generate network health scores with recommendations
- **Data Export**: Export reports in multiple formats (CSV, JSON, PDF, PNG)

## ✨ Features

### 🎯 Core Features

1. **Dashboard**
   - Real-time speed metrics (download/upload)
   - Network quality indicators (latency, jitter, packet loss)
   - Active connections count
   - Network health score with progress bar
   - Interface selection and monitoring controls

2. **Monitoring Tab**
   - Live packet capture with filtering options
   - Real-time packet tree view
   - Protocol statistics (TCP, UDP, HTTP/HTTPS, DNS, ICMP)
   - Export captured packets to CSV

3. **Connections Tab**
   - Active network connections list
   - Process and PID information
   - Connection termination (simulated)
   - Connection details viewer
   - Export connections list

4. **Analysis Tab**
   - **Protocol Analysis**: Pie charts showing traffic distribution
   - **Traffic Analysis**: Speed timeline, top hosts, port activity, traffic composition
   - **Performance Analysis**: Latency distribution, jitter analysis, packet loss graphs
   - **Anomaly Detection**: Security threat identification and reporting

5. **Tools & Utilities**
   - Speed test functionality
   - Network health assessment
   - Traffic analysis reports
   - DNS cache flushing
   - Ping testing
   - Dark mode (coming soon)

### 🔧 Technical Features

- **Multi-platform Support**: Windows, Linux, macOS
- **Thread-safe Design**: Background monitoring with GUI updates
- **Real Data Collection**: Uses psutil for system-level network information
- **Smart Caching**: Redundant data fetching minimized
- **Demo Mode**: Functional demo data when no real data available
- **Export Capabilities**: Multiple formats supported

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Administrative privileges (for some features)

### Step-by-Step Installation

1. **Clone or Download the Project**
   ```bash
   git clone https://github.com/yourusername/network-monitor-pro.git
   cd network-monitor-pro

   Install Dependencies

bash
pip install -r requirements.txt
Or install individually:

bash
pip install matplotlib psutil numpy pillow ttkthemes
Windows Additional Setup

bash
# For WiFi information on Windows
pip install pywin32


🎮 Quick Start
Launch the Application

bash
python gui_interface.py
Initial Setup

Select your network interface from the dropdown

Click "Start Monitoring"

View real-time statistics in the Dashboard

Basic Operation

text
Dashboard → Real-time metrics
Monitoring → Live packet capture
Connections → Active connections
Analysis → Graphs and insights


## Main Window Layout

┌─────────────────────────────────────────────────────────────────┐
│  File  Tools  View  Help                                        │
├─────────────────────────────────────────────────────────────────┤
│  [📊 Dashboard] [📡 Monitoring] [🔗 Connections] [📈 Analysis]  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Interface: [Wi-Fi ▼] ▶ Start Monitoring ⟳ ⚡ 🔄         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌───────────────┐ ┌──────────────────────────────────────┐   │
│  │ Network Info  │ │         Speed Metrics                │   │
│  │ • Connection  │ │ • Download: 85.2 Mbps                │   │
│  │ • IP Address  │ │ • Upload: 22.1 Mbps                  │   │
│  │ • Gateway     │ │ • Packets/sec: 145                   │   │
│  │ • DNS Servers │ │ • Bytes/sec: 125 KB/s                │   │
│  └───────────────┘ └──────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Network Quality                      │   │
│  │ • Latency: 24 ms • Jitter: 2.1 ms                       │   │
│  │ • Packet Loss: 0.2% • Connections: 42                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Network Health                       │   │
│  │  Score: 87/100 [███████████████████░░░░░░]              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [📊 View Graphs] [🔍 Deep Analysis] [⚙️ Settings] [📋 Export] │
└─────────────────────────────────────────────────────────────────┘


## Tab Descriptions
1. Dashboard Tab
The main control center showing real-time network metrics:

Network information (IP addresses, gateway, DNS)

Speed metrics (download/upload speeds)

Quality metrics (latency, jitter, packet loss)

Health assessment with recommendations

Quick action buttons

2. Monitoring Tab
Live packet capture interface:

Filter controls (All Traffic, TCP, UDP, HTTP/HTTPS, DNS, ICMP)

Packet tree view with timestamp, source, destination, protocol, size

Real-time statistics (total packets, bytes, protocol counts)

Capture controls (start/stop, clear, export)

3. Connections Tab
Active network connection management:

Connection list with protocol, addresses, ports, status

Process name and PID information

Connection termination (simulated)

Search functionality by process name

Export connections to CSV

4. Analysis Tab
Comprehensive network analysis with four sub-tabs:

4.1 Protocol Analysis

Pie chart showing traffic distribution by protocol

Update and export functionality

Color-coded segments for easy identification

4.2 Traffic Analysis

Speed Timeline: Download/upload speeds over time

Top Hosts: Most active IP addresses

Port Activity: Most used network ports

Traffic Composition: Data volume by protocol over time

4.3 Performance Analysis

Latency Distribution: Histogram of latency values

Jitter Analysis: Latency variation over time

Packet Loss: Percentage loss over time

Statistical overlays and trend lines

4.4 Anomaly Detection

List of detected security anomalies

Severity classification (High/Medium/Low)

Detailed descriptions and recommendations

Export anomaly reports
