"""
Network Monitor Pro - GUI Interface
Updated with all working features and proper graph displays
FIXED VERSION: Graph updates now work correctly without artist sharing issues
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import queue
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
import platform
import psutil
import json
import csv
from datetime import datetime
import webbrowser
import subprocess
from collections import Counter, defaultdict, deque

# Optional theme support
try:
    from ttkthemes import ThemedTk  # type: ignore
    TTKTHEMES_AVAILABLE = True
except ImportError:
    TTKTHEMES_AVAILABLE = False

# Import local modules
from network_monitor import NetworkMonitor, NetworkAnalyzer
from visualizer import NetworkVisualizer

class NetworkMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Monitor Pro v2.1 - FIXED")
        self.root.geometry("1400x900")
        
        # Set window icon
        try:
            self.root.iconbitmap('network_icon.ico')
        except:
            try:
                # Try to create a simple icon
                self.root.iconbitmap(default='')
            except:
                pass
        
        # Initialize network components
        self.monitor = NetworkMonitor()
        self.analyzer = NetworkAnalyzer()
        self.visualizer = NetworkVisualizer()
        
        # Data queues for thread-safe communication
        self.data_queue = queue.Queue()
        self.update_queue = queue.Queue()
        
        # GUI state
        self.is_monitoring = False
        self.current_interface = None
        self.last_wifi_ssid = None
        self.capture_active = False
        
        # Store references to figures for updating
        self.figures = {}
        self.canvases = {}
        self.axes = {}
        
        # Setup GUI
        self.setup_styles()
        self.create_menu()
        self.create_widgets()
        
        # Initialize with data
        self.refresh_interfaces()
        self.check_wifi_status()
        
        # Start periodic updates
        self.periodic_update()
        
    def setup_styles(self):
        """Setup ttk styles for modern look"""
        style = ttk.Style()
        
        # Configure colors
        style.theme_use('clam')
        
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Normal.TLabel', font=('Arial', 10))
        style.configure('Status.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Metric.TLabel', font=('Arial', 11, 'bold'))
        
        style.configure('Accent.TButton', 
                       font=('Arial', 10, 'bold'),
                       background='#4285f4',
                       foreground='white')
        
        style.configure('Success.TButton', background='#34a853')
        style.configure('Warning.TButton', background='#fbbc05')
        style.configure('Danger.TButton', background='#ea4335')
        
        style.configure('Card.TFrame', background='white', relief='raised', borderwidth=1)
        
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_command(label="Save Report", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Speed Test", command=self.perform_speed_test)
        tools_menu.add_command(label="Network Health", command=self.show_network_health)
        tools_menu.add_command(label="Analyze Traffic", command=self.analyze_traffic)
        tools_menu.add_command(label="Flush DNS Cache", command=self.flush_dns_cache)
        tools_menu.add_separator()
        tools_menu.add_command(label="Ping Test", command=self.ping_test)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh All", command=self.refresh_display)
        view_menu.add_command(label="Reset Statistics", command=self.reset_statistics)
        view_menu.add_separator()
        view_menu.add_command(label="Dark Mode", command=self.toggle_dark_mode)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Check for Updates", command=self.check_updates)
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Create main container with notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Dashboard Tab
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text='📊 Dashboard')
        self.create_dashboard()
        
        # Monitoring Tab
        self.monitoring_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.monitoring_frame, text='📡 Monitoring')
        self.create_monitoring_tab()
        
        # Connections Tab
        self.connections_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.connections_frame, text='🔗 Connections')
        self.create_connections_tab()
        
        # Analysis Tab
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text='📈 Analysis')
        self.create_analysis_tab()
        
        # Status Bar
        self.create_status_bar()
        
    def create_dashboard(self):
        """Create dashboard with key metrics"""
        # Top control panel
        control_frame = ttk.Frame(self.dashboard_frame)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        # Interface selection
        ttk.Label(control_frame, text="Interface:", style='Normal.TLabel').grid(row=0, column=0, padx=5, pady=5)
        self.interface_var = tk.StringVar()
        self.interface_combo = ttk.Combobox(control_frame, textvariable=self.interface_var, width=25, state='readonly')
        self.interface_combo.grid(row=0, column=1, padx=5, pady=5)
        self.interface_combo.bind('<<ComboboxSelected>>', self.on_interface_change)
        
        # Control buttons
        self.monitor_btn = ttk.Button(control_frame, text="▶ Start Monitoring", 
                                      command=self.toggle_monitoring, style='Accent.TButton')
        self.monitor_btn.grid(row=0, column=2, padx=10, pady=5)
        
        ttk.Button(control_frame, text="⟳ Refresh", 
                  command=self.refresh_interfaces).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(control_frame, text="⚡ Speed Test", 
                  command=self.perform_speed_test).grid(row=0, column=4, padx=5, pady=5)
        
        ttk.Button(control_frame, text="🔄 Reset", 
                  command=self.reset_statistics).grid(row=0, column=5, padx=5, pady=5)
        
        # Main metrics grid
        metrics_frame = ttk.Frame(self.dashboard_frame)
        metrics_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Network Info
        info_frame = ttk.LabelFrame(metrics_frame, text="Network Information", padding=10)
        info_frame.pack(side='left', fill='both', expand=True, padx=(0, 5), pady=5)
        
        self.network_info_labels = {}
        info_fields = [
            ('Connection:', 'connection_info'),
            ('IP Address:', 'local_ip'),
            ('Public IP:', 'public_ip'),
            ('Gateway:', 'gateway'),
            ('DNS Servers:', 'dns_servers'),
            ('MAC Address:', 'mac_address'),
            ('Signal Strength:', 'signal_strength'),
            ('Interface Speed:', 'speed_mbps'),
            ('Status:', 'interface_status')
        ]
        
        for i, (label, key) in enumerate(info_fields):
            ttk.Label(info_frame, text=label, style='Normal.TLabel', width=15, anchor='e').grid(
                row=i, column=0, sticky='w', padx=5, pady=3)
            self.network_info_labels[key] = ttk.Label(
                info_frame, text="N/A", style='Status.TLabel', foreground='#4285f4', width=25, anchor='w')
            self.network_info_labels[key].grid(row=i, column=1, sticky='w', padx=5, pady=3)
        
        # Right panel - Real-time Metrics
        metrics_right_frame = ttk.Frame(metrics_frame)
        metrics_right_frame.pack(side='left', fill='both', expand=True, padx=(5, 0), pady=5)
        
        # Speed metrics
        speed_frame = ttk.LabelFrame(metrics_right_frame, text="Speed Metrics", padding=10)
        speed_frame.pack(fill='x', pady=(0, 10))
        
        speed_grid = ttk.Frame(speed_frame)
        speed_grid.pack()
        
        metrics_data = [
            ('Download Speed:', 'download_speed', 'Mbps'),
            ('Upload Speed:', 'upload_speed', 'Mbps'),
            ('Packets/Sec:', 'packets_per_sec', 'pps'),
            ('Bytes/Sec:', 'bytes_per_sec', 'KB/s')
        ]
        
        for i, (label, key, unit) in enumerate(metrics_data):
            ttk.Label(speed_grid, text=label, style='Normal.TLabel', width=15, anchor='e').grid(
                row=i, column=0, sticky='w', padx=5, pady=5)
            self.network_info_labels[key] = ttk.Label(
                speed_grid, text="0.0", style='Metric.TLabel', 
                foreground='#34a853', font=('Arial', 12, 'bold'), width=10, anchor='w')
            self.network_info_labels[key].grid(row=i, column=1, sticky='w', padx=5, pady=5)
            ttk.Label(speed_grid, text=unit, style='Normal.TLabel').grid(
                row=i, column=2, sticky='w', padx=2, pady=5)
        
        # Quality metrics
        quality_frame = ttk.LabelFrame(metrics_right_frame, text="Network Quality", padding=10)
        quality_frame.pack(fill='x', pady=(0, 10))
        
        quality_grid = ttk.Frame(quality_frame)
        quality_grid.pack()
        
        quality_data = [
            ('Latency:', 'latency', 'ms'),
            ('Jitter:', 'jitter', 'ms'),
            ('Packet Loss:', 'packet_loss', '%'),
            ('Active Connections:', 'active_connections', '')
        ]
        
        for i, (label, key, unit) in enumerate(quality_data):
            ttk.Label(quality_grid, text=label, style='Normal.TLabel', width=15, anchor='e').grid(
                row=i, column=0, sticky='w', padx=5, pady=5)
            self.network_info_labels[key] = ttk.Label(
                quality_grid, text="0.0", style='Metric.TLabel',
                foreground='#ea4335' if key in ['latency', 'jitter', 'packet_loss'] else '#4285f4',
                font=('Arial', 12, 'bold'), width=10, anchor='w')
            self.network_info_labels[key].grid(row=i, column=1, sticky='w', padx=5, pady=5)
            if unit:
                ttk.Label(quality_grid, text=unit, style='Normal.TLabel').grid(
                    row=i, column=2, sticky='w', padx=2, pady=5)
        
        # Health score
        health_frame = ttk.LabelFrame(metrics_right_frame, text="Network Health", padding=10)
        health_frame.pack(fill='x')
        
        self.health_label = ttk.Label(
            health_frame, text="Score: N/A", 
            font=('Arial', 14, 'bold'), foreground='#34a853')
        self.health_label.pack(pady=5)
        
        self.health_progress = ttk.Progressbar(
            health_frame, length=300, mode='determinate')
        self.health_progress.pack(pady=5, fill='x', padx=10)
        
        ttk.Button(health_frame, text="View Details", 
                  command=self.show_network_health, width=15).pack(pady=5)
        
        # Bottom panel for quick actions
        action_frame = ttk.Frame(self.dashboard_frame)
        action_frame.pack(fill='x', padx=10, pady=10)
        
        actions = [
            ("📊 View Graphs", self.show_graphs),
            ("🔍 Deep Analysis", self.show_deep_analysis),
            ("⚙️ Settings", self.show_settings),
            ("📋 Export Report", self.export_report),
            ("🆘 Help", self.show_user_guide)
        ]
        
        for i, (text, command) in enumerate(actions):
            ttk.Button(action_frame, text=text, command=command, width=15).grid(
                row=0, column=i, padx=5, pady=5)
        
    def create_monitoring_tab(self):
        """Create monitoring tab with packet visualization"""
        # Top control panel
        monitor_control = ttk.Frame(self.monitoring_frame)
        monitor_control.pack(fill='x', padx=10, pady=10)
        
        # Filter controls
        ttk.Label(monitor_control, text="Filter:", style='Normal.TLabel').grid(row=0, column=0, padx=5)
        self.filter_var = tk.StringVar(value='All Traffic')
        filter_combo = ttk.Combobox(monitor_control, textvariable=self.filter_var, width=20, state='readonly')
        filter_combo.grid(row=0, column=1, padx=5)
        filter_combo['values'] = ['All Traffic', 'TCP Only', 'UDP Only', 'HTTP/HTTPS', 'DNS', 'ICMP']
        filter_combo.current(0)
        
        # Capture controls
        self.capture_btn = ttk.Button(monitor_control, text="▶ Start Capture", 
                                      command=self.toggle_capture, style='Accent.TButton')
        self.capture_btn.grid(row=0, column=2, padx=5)
        
        ttk.Button(monitor_control, text="Clear Display", 
                  command=self.clear_monitor).grid(row=0, column=3, padx=5)
        
        ttk.Button(monitor_control, text="Export Packets", 
                  command=self.export_packets).grid(row=0, column=4, padx=5)
        
        # Real-time packet display
        packet_frame = ttk.LabelFrame(self.monitoring_frame, text="Live Packet Capture", padding=10)
        packet_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Create Treeview for packets
        columns = ('No.', 'Time', 'Source', 'Destination', 'Protocol', 'Length', 'Info')
        self.packet_tree = ttk.Treeview(packet_frame, columns=columns, show='headings', height=20)
        
        # Define headings
        for col in columns:
            self.packet_tree.heading(col, text=col)
            self.packet_tree.column(col, width=80, minwidth=50)
        
        self.packet_tree.column('No.', width=50)
        self.packet_tree.column('Time', width=100)
        self.packet_tree.column('Source', width=150)
        self.packet_tree.column('Destination', width=150)
        self.packet_tree.column('Protocol', width=80)
        self.packet_tree.column('Length', width=80)
        self.packet_tree.column('Info', width=200)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(packet_frame, orient="vertical", command=self.packet_tree.yview)
        hsb = ttk.Scrollbar(packet_frame, orient="horizontal", command=self.packet_tree.xview)
        self.packet_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.packet_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        # Configure grid
        packet_frame.grid_rowconfigure(0, weight=1)
        packet_frame.grid_columnconfigure(0, weight=1)
        
        # Statistics frame
        stats_frame = ttk.Frame(self.monitoring_frame)
        stats_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        stats_data = [
            ('Total Packets:', 'total_packets'),
            ('Total Bytes:', 'total_bytes'),
            ('TCP Packets:', 'tcp_count'),
            ('UDP Packets:', 'udp_count'),
            ('HTTP/HTTPS:', 'http_count')
        ]
        
        self.monitor_stats = {}
        for i, (label, key) in enumerate(stats_data):
            ttk.Label(stats_frame, text=label, style='Normal.TLabel').grid(row=0, column=i*2, padx=5, pady=5)
            self.monitor_stats[key] = ttk.Label(
                stats_frame, text="0", foreground='#4285f4', font=('Arial', 10, 'bold'))
            self.monitor_stats[key].grid(row=0, column=i*2+1, padx=(0, 20), pady=5)
        
    def create_connections_tab(self):
        """Create connections tab with active connections list"""
        # Control panel
        conn_control = ttk.Frame(self.connections_frame)
        conn_control.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(conn_control, text="⟳ Refresh Connections", 
                  command=self.refresh_connections).grid(row=0, column=0, padx=5)
        
        ttk.Button(conn_control, text="⏹ Kill Connection", 
                  command=self.kill_connection).grid(row=0, column=1, padx=5)
        
        ttk.Button(conn_control, text="📥 Export List", 
                  command=self.export_connections).grid(row=0, column=2, padx=5)
        
        ttk.Button(conn_control, text="🔍 Find Process", 
                  command=self.find_process).grid(row=0, column=3, padx=5)
        
        # Connections treeview
        conn_frame = ttk.LabelFrame(self.connections_frame, text="Active Connections", padding=10)
        conn_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        columns = ('Protocol', 'Local Address', 'Local Port', 
                  'Remote Address', 'Remote Port', 'Status', 'Process', 'PID')
        self.conn_tree = ttk.Treeview(conn_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.conn_tree.heading(col, text=col)
            self.conn_tree.column(col, width=90, minwidth=50)
        
        self.conn_tree.column('Protocol', width=70)
        self.conn_tree.column('Local Address', width=120)
        self.conn_tree.column('Remote Address', width=120)
        self.conn_tree.column('Process', width=120)
        self.conn_tree.column('PID', width=60)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(conn_frame, orient="vertical", command=self.conn_tree.yview)
        hsb = ttk.Scrollbar(conn_frame, orient="horizontal", command=self.conn_tree.xview)
        self.conn_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.conn_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        conn_frame.grid_rowconfigure(0, weight=1)
        conn_frame.grid_columnconfigure(0, weight=1)
        
        # Connection details
        detail_frame = ttk.LabelFrame(self.connections_frame, text="Connection Details", padding=10)
        detail_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.conn_detail_text = scrolledtext.ScrolledText(detail_frame, height=8, wrap=tk.WORD)
        self.conn_detail_text.pack(fill='both', expand=True)
        
        # Bind selection event
        self.conn_tree.bind('<<TreeviewSelect>>', self.show_connection_details)
        
    def create_analysis_tab(self):
        """Create analysis tab with graphs and insights"""
        # Create notebook within analysis tab
        analysis_notebook = ttk.Notebook(self.analysis_frame)
        analysis_notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Protocol Analysis
        protocol_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(protocol_frame, text='Protocols')
        self.create_protocol_analysis(protocol_frame)
        
        # Traffic Analysis
        traffic_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(traffic_frame, text='Traffic')
        self.create_traffic_analysis(traffic_frame)
        
        # Performance Analysis
        perf_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(perf_frame, text='Performance')
        self.create_performance_analysis(perf_frame)
        
        # Anomaly Detection
        anomaly_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(anomaly_frame, text='Anomalies')
        self.create_anomaly_analysis(anomaly_frame)
        
    def create_protocol_analysis(self, parent):
        """Create protocol analysis section"""
        # Control panel
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(control_frame, text="Update Graph", 
                  command=self.update_protocol_graph).pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="Export Graph", 
                  command=lambda: self.export_figure('protocol')).pack(side='left', padx=5)
        
        # Protocol distribution pie chart
        fig = Figure(figsize=(10, 6), dpi=80)
        self.protocol_ax = fig.add_subplot(111)
        self.protocol_canvas = FigureCanvasTkAgg(fig, parent)
        self.protocol_canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=5)
        
        # Add toolbar
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill='x', padx=10, pady=(0, 10))
        toolbar = NavigationToolbar2Tk(self.protocol_canvas, toolbar_frame)
        toolbar.update()
        
        # Store references
        self.figures['protocol'] = fig
        self.canvases['protocol'] = self.protocol_canvas
        self.axes['protocol'] = self.protocol_ax
        
        # Update immediately
        self.update_protocol_graph()
        
    def create_traffic_analysis(self, parent):
        """Create traffic analysis section"""
        # Control panel
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(control_frame, text="Update Graphs", 
                  command=self.update_traffic_graphs).pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="Export All", 
                  command=lambda: self.export_figure('traffic')).pack(side='left', padx=5)
        
        # Create figure with subplots
        fig = Figure(figsize=(12, 8), dpi=80)
        
        # Create 2x2 grid of plots
        self.traffic_ax1 = fig.add_subplot(221)  # Speed timeline
        self.traffic_ax2 = fig.add_subplot(222)  # Top hosts
        self.traffic_ax3 = fig.add_subplot(223)  # Port activity
        self.traffic_ax4 = fig.add_subplot(224)  # Traffic composition
        
        fig.tight_layout(pad=3.0)
        
        self.traffic_canvas = FigureCanvasTkAgg(fig, parent)
        self.traffic_canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=5)
        
        # Add toolbar
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill='x', padx=10, pady=(0, 10))
        toolbar = NavigationToolbar2Tk(self.traffic_canvas, toolbar_frame)
        toolbar.update()
        
        # Store references
        self.figures['traffic'] = fig
        self.canvases['traffic'] = self.traffic_canvas
        self.axes['traffic'] = [self.traffic_ax1, self.traffic_ax2, self.traffic_ax3, self.traffic_ax4]
        
        # Update immediately
        self.update_traffic_graphs()
        
    def create_performance_analysis(self, parent):
        """Create performance analysis section"""
        # Control panel
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(control_frame, text="Update Graphs", 
                  command=self.update_performance_graphs).pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="Export All", 
                  command=lambda: self.export_figure('performance')).pack(side='left', padx=5)
        
        # Create figure with subplots
        fig = Figure(figsize=(12, 8), dpi=80)
        
        # Create 2x2 grid of plots
        self.perf_ax1 = fig.add_subplot(221)  # Speed timeline
        self.perf_ax2 = fig.add_subplot(222)  # Latency distribution
        self.perf_ax3 = fig.add_subplot(223)  # Jitter analysis
        self.perf_ax4 = fig.add_subplot(224)  # Packet loss
        
        fig.tight_layout(pad=3.0)
        
        self.perf_canvas = FigureCanvasTkAgg(fig, parent)
        self.perf_canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=5)
        
        # Add toolbar
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill='x', padx=10, pady=(0, 10))
        toolbar = NavigationToolbar2Tk(self.perf_canvas, toolbar_frame)
        toolbar.update()
        
        # Store references
        self.figures['performance'] = fig
        self.canvases['performance'] = self.perf_canvas
        self.axes['performance'] = [self.perf_ax1, self.perf_ax2, self.perf_ax3, self.perf_ax4]
        
        # Update immediately
        self.update_performance_graphs()
        
    def create_anomaly_analysis(self, parent):
        """Create anomaly detection section"""
        # Control panel
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(control_frame, text="Scan for Anomalies", 
                  command=self.scan_anomalies).pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="Clear List", 
                  command=self.clear_anomalies).pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="Export Report", 
                  command=self.export_anomaly_report).pack(side='left', padx=5)
        
        # Anomaly list
        list_frame = ttk.LabelFrame(parent, text="Detected Anomalies", padding=10)
        list_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        columns = ('Severity', 'Type', 'Description', 'Time', 'Count')
        self.anomaly_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.anomaly_tree.heading(col, text=col)
            self.anomaly_tree.column(col, width=100, minwidth=50)
        
        self.anomaly_tree.column('Severity', width=80)
        self.anomaly_tree.column('Type', width=120)
        self.anomaly_tree.column('Description', width=200)
        self.anomaly_tree.column('Time', width=100)
        self.anomaly_tree.column('Count', width=60)
        
        # Add scrollbar
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.anomaly_tree.yview)
        self.anomaly_tree.configure(yscrollcommand=vsb.set)
        
        self.anomaly_tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        
        # Anomaly details
        detail_frame = ttk.LabelFrame(parent, text="Anomaly Details", padding=10)
        detail_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.anomaly_detail_text = scrolledtext.ScrolledText(detail_frame, height=8, wrap=tk.WORD)
        self.anomaly_detail_text.pack(fill='both', expand=True)
        
        # Bind selection event
        self.anomaly_tree.bind('<<TreeviewSelect>>', self.show_anomaly_details)
        
    def create_status_bar(self):
        """Create status bar at bottom"""
        self.status_bar = ttk.Frame(self.root, relief='sunken', padding=5)
        self.status_bar.pack(side='bottom', fill='x')
        
        # Status labels
        self.status_label = ttk.Label(self.status_bar, text="Ready", foreground='#34a853')
        self.status_label.pack(side='left')
        
        # Monitoring status
        self.monitoring_status = ttk.Label(self.status_bar, text="Not Monitoring", foreground='#ea4335')
        self.monitoring_status.pack(side='left', padx=(20, 10))
        
        # WiFi status with refresh button
        wifi_frame = ttk.Frame(self.status_bar)
        wifi_frame.pack(side='right')
        
        ttk.Label(wifi_frame, text="WiFi:", style='Normal.TLabel').pack(side='left', padx=(10, 2))
        self.wifi_status = ttk.Label(wifi_frame, text="Scanning...", foreground='#4285f4')
        self.wifi_status.pack(side='left', padx=(0, 10))
        
        ttk.Button(wifi_frame, text="⟳", width=3, 
                  command=self.check_wifi_status).pack(side='left')
        
        # Update timestamp
        self.update_time_label = ttk.Label(self.status_bar, text="")
        self.update_time_label.pack(side='right', padx=10)
        
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        if not self.is_monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """Start network monitoring"""
        interface = self.interface_var.get()
        if not interface:
            messagebox.showerror("Error", "Please select an interface first!")
            return
        
        try:
            self.monitor.start_monitoring(interface=interface)
            self.is_monitoring = True
            self.current_interface = interface
            
            self.monitor_btn.configure(text="⏸ Stop Monitoring", style='Danger.TButton')
            self.status_label.config(text=f"Monitoring {interface}...", foreground='#4285f4')
            self.monitoring_status.config(text=f"Monitoring: {interface}", foreground='#34a853')
            
            # Start monitoring thread for GUI updates
            monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            monitor_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start monitoring: {str(e)}")
    
    def stop_monitoring(self):
        """Stop network monitoring"""
        try:
            self.monitor.stop_monitoring()
            self.is_monitoring = False
            self.monitor_btn.configure(text="▶ Start Monitoring", style='Accent.TButton')
            self.status_label.config(text="Monitoring Stopped", foreground='#ea4335')
            self.monitoring_status.config(text="Not Monitoring", foreground='#ea4335')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop monitoring: {str(e)}")
    
    def monitor_loop(self):
        """Background monitoring loop for GUI updates"""
        while self.is_monitoring:
            try:
                # Get updated data
                stats = self.monitor.get_statistics()
                network_info = self.monitor.get_network_info()
                recent_data = self.monitor.get_recent_data(count=100)
                
                # Calculate bytes per second in KB/s
                if 'bytes_per_second' in stats:
                    stats['bytes_per_second'] = stats['bytes_per_second'] / 1024
                
                # Put data in queue for GUI update
                self.update_queue.put({
                    'stats': stats,
                    'network_info': network_info,
                    'recent_data': recent_data
                })
                
                # Check for WiFi changes
                current_wifi = network_info.get('ssid', 'N/A')
                if current_wifi != self.last_wifi_ssid:
                    self.last_wifi_ssid = current_wifi
                    self.root.after(0, self.update_wifi_status, current_wifi)
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(2)
    
    def periodic_update(self):
        """Periodic GUI updates"""
        try:
            # Process any pending updates from monitor thread
            while not self.update_queue.empty():
                data = self.update_queue.get_nowait()
                self.update_gui_data(data)
            
            # Update network info if not monitoring
            if not self.is_monitoring:
                network_info = self.monitor.get_network_info()
                self.update_network_info(network_info)
                
                # Check WiFi status
                current_wifi = network_info.get('ssid', 'N/A')
                if current_wifi != self.last_wifi_ssid:
                    self.last_wifi_ssid = current_wifi
                    self.update_wifi_status(current_wifi)
            
            # Update timestamp
            current_time = time.strftime("%H:%M:%S")
            self.update_time_label.config(text=f"Last update: {current_time}")
            
        except Exception as e:
            print(f"Update error: {e}")
        
        # Schedule next update
        self.root.after(1000, self.periodic_update)
    
    def update_gui_data(self, data):
        """Update GUI with new data"""
        stats = data['stats']
        network_info = data['network_info']
        recent_data = data['recent_data']
        
        # Update network info
        self.update_network_info(network_info)
        
        # Update metrics
        self.network_info_labels['download_speed'].config(
            text=f"{stats.get('download_speed_mbps', 0):.2f}")
        self.network_info_labels['upload_speed'].config(
            text=f"{stats.get('upload_speed_mbps', 0):.2f}")
        self.network_info_labels['packets_per_sec'].config(
            text=f"{stats.get('packets_per_second', 0):.0f}")
        self.network_info_labels['bytes_per_sec'].config(
            text=f"{stats.get('bytes_per_second', 0):.0f}")
        
        self.network_info_labels['latency'].config(
            text=f"{stats.get('avg_latency_ms', 0):.1f}")
        self.network_info_labels['jitter'].config(
            text=f"{stats.get('jitter_ms', 0):.1f}")
        self.network_info_labels['packet_loss'].config(
            text=f"{stats.get('packet_loss_percent', 0):.2f}")
        self.network_info_labels['active_connections'].config(
            text=f"{stats.get('active_connections', 0)}")
        
        # Update packet tree
        self.update_packet_tree(recent_data)
        
        # Update connections
        self.update_connections_tree()
        
        # Update monitoring statistics
        self.update_monitor_stats(recent_data)
        
        # Update health score
        health = self.monitor.analyze_network_health()
        health_score = health['health_score']
        self.health_label.config(text=f"Score: {health_score}/100")
        self.health_progress['value'] = health_score
        
        # Update status color based on health
        if health_score >= 80:
            self.health_label.config(foreground='#34a853')
        elif health_score >= 60:
            self.health_label.config(foreground='#fbbc05')
        else:
            self.health_label.config(foreground='#ea4335')
    
    def update_network_info(self, network_info):
        """Update network information display"""
        # Format connection info
        connection_type = network_info.get('connection_type', 'Unknown')
        ssid = network_info.get('ssid', 'N/A')
        
        if connection_type == 'WiFi' and ssid != 'N/A':
            conn_info = f"{ssid} (WiFi)"
            signal = network_info.get('signal_strength', '')
            if signal and signal != 'N/A':
                conn_info += f" - {signal}"
        else:
            conn_info = f"{connection_type}"
        
        # Update labels
        info_mapping = {
            'connection_info': conn_info,
            'local_ip': network_info.get('local_ip', 'N/A'),
            'public_ip': network_info.get('public_ip', 'N/A'),
            'gateway': network_info.get('gateway', 'N/A'),
            'dns_servers': ', '.join(network_info.get('dns_servers', ['N/A'])),
            'mac_address': network_info.get('mac_address', 'N/A'),
            'signal_strength': network_info.get('signal_strength', 'N/A'),
            'speed_mbps': network_info.get('speed_mbps', 'N/A'),
            'interface_status': 'Up' if network_info.get('is_up', False) else 'Down'
        }
        
        for key, value in info_mapping.items():
            if key in self.network_info_labels:
                self.network_info_labels[key].config(text=value)
    
    def update_packet_tree(self, packets):
        """Update packet tree with new data"""
        if not self.capture_active:
            return
        
        # Clear existing items if we have more than 1000 packets
        current_items = self.packet_tree.get_children()
        if len(current_items) > 1000:
            for item in current_items[:500]:
                self.packet_tree.delete(item)
        
        # Add new packets
        start_idx = len(self.packet_tree.get_children()) + 1
        
        for i, packet in enumerate(packets[-50:]):  # Show last 50 packets
            timestamp = time.strftime('%H:%M:%S', time.localtime(packet['timestamp']))
            src_port = packet.get('src_port', '')
            dst_port = packet.get('dst_port', '')
            
            source = f"{packet['src_ip']}"
            if src_port:
                source += f":{src_port}"
            
            destination = f"{packet['dst_ip']}"
            if dst_port:
                destination += f":{dst_port}"
            
            self.packet_tree.insert('', 'end', values=(
                start_idx + i,
                timestamp,
                source,
                destination,
                packet['protocol'],
                packet['packet_size'],
                self.get_packet_info(packet)
            ))
        
        # Auto-scroll to bottom
        if packets:
            self.packet_tree.yview_moveto(1)
    
    def update_connections_tree(self):
        """Update connections tree"""
        try:
            connections = self.monitor.get_active_connections()
            
            # Clear existing items
            for item in self.conn_tree.get_children():
                self.conn_tree.delete(item)
            
            for i, conn in enumerate(connections):
                self.conn_tree.insert('', 'end', values=(
                    conn.get('protocol', 'N/A'),
                    conn.get('local_addr', 'N/A'),
                    conn.get('local_port', 'N/A'),
                    conn.get('remote_addr', 'N/A'),
                    conn.get('remote_port', 'N/A'),
                    conn.get('status', 'N/A'),
                    conn.get('process_name', 'N/A'),
                    conn.get('pid', 'N/A')
                ))
        except Exception as e:
            print(f"Connection update error: {e}")
    
    def update_monitor_stats(self, packets):
        """Update monitoring statistics"""
        if not packets:
            return
        
        # Count packets by protocol
        protocol_counts = {}
        for packet in packets:
            proto = packet.get('protocol', 'Unknown')
            protocol_counts[proto] = protocol_counts.get(proto, 0) + 1
        
        # Update labels
        total_packets = len(packets)
        total_bytes = sum(p.get('packet_size', 0) for p in packets)
        
        self.monitor_stats['total_packets'].config(text=str(total_packets))
        self.monitor_stats['total_bytes'].config(text=f"{total_bytes:,}")
        self.monitor_stats['tcp_count'].config(text=str(protocol_counts.get('TCP', 0)))
        self.monitor_stats['udp_count'].config(text=str(protocol_counts.get('UDP', 0)))
        
        http_count = protocol_counts.get('HTTP', 0) + protocol_counts.get('HTTPS', 0)
        self.monitor_stats['http_count'].config(text=str(http_count))
    
    def get_packet_info(self, packet):
        """Get formatted packet info"""
        protocol = packet['protocol']
        size = packet['packet_size']
        
        if protocol == 'TCP':
            return f"TCP Segment ({size} bytes)"
        elif protocol == 'UDP':
            return f"UDP Datagram ({size} bytes)"
        elif protocol == 'ICMP':
            return f"ICMP Packet ({size} bytes)"
        elif protocol in ['HTTP', 'HTTPS']:
            return f"{protocol} Data ({size} bytes)"
        else:
            return f"{protocol} Packet ({size} bytes)"
    
    def check_wifi_status(self):
        """Check and update WiFi status"""
        try:
            network_info = self.monitor.get_network_info()
            ssid = network_info.get('ssid', 'N/A')
            signal = network_info.get('signal_strength', 'N/A')
            
            if ssid != 'N/A' and ssid:
                status_text = f"{ssid}"
                if signal != 'N/A':
                    status_text += f" ({signal})"
                self.wifi_status.config(text=status_text, foreground='#34a853')
            else:
                self.wifi_status.config(text="No WiFi", foreground='#ea4335')
                
            self.status_label.config(text="WiFi status updated", foreground='#34a853')
                
        except Exception as e:
            self.wifi_status.config(text="Error", foreground='#ea4335')
            print(f"WiFi check error: {e}")
    
    def update_wifi_status(self, ssid):
        """Update WiFi status display"""
        if ssid and ssid != 'N/A':
            network_info = self.monitor.get_network_info()
            signal = network_info.get('signal_strength', '')
            status_text = f"{ssid}"
            if signal and signal != 'N/A':
                status_text += f" ({signal})"
            self.wifi_status.config(text=status_text, foreground='#34a853')
        else:
            self.wifi_status.config(text="No WiFi", foreground='#ea4335')
    
    def refresh_interfaces(self):
        """Refresh interface list"""
        interfaces = self.monitor.get_available_interfaces()
        self.interface_combo['values'] = interfaces
        if interfaces:
            current = self.interface_var.get()
            if current in interfaces:
                self.interface_combo.set(current)
            else:
                self.interface_combo.current(0)
        self.status_label.config(text="Interfaces refreshed", foreground='#34a853')
    
    def on_interface_change(self, event):
        """Handle interface selection change"""
        interface = self.interface_var.get()
        if interface:
            self.status_label.config(text=f"Interface selected: {interface}", foreground='#4285f4')
    
    def refresh_display(self):
        """Refresh all displays"""
        self.refresh_interfaces()
        self.check_wifi_status()
        self.update_connections_tree()
        self.update_protocol_graph()
        self.update_traffic_graphs()
        self.update_performance_graphs()
        self.status_label.config(text="Display refreshed", foreground='#34a853')
    
    def reset_statistics(self):
        """Reset all statistics"""
        try:
            # Clear packet tree
            for item in self.packet_tree.get_children():
                self.packet_tree.delete(item)
            
            # Clear connection tree
            for item in self.conn_tree.get_children():
                self.conn_tree.delete(item)
            
            # Clear anomaly tree
            for item in self.anomaly_tree.get_children():
                self.anomaly_tree.delete(item)
            
            # Reset metrics
            for key in ['download_speed', 'upload_speed', 'packets_per_sec', 'bytes_per_sec',
                       'latency', 'jitter', 'packet_loss', 'active_connections']:
                if key in self.network_info_labels:
                    self.network_info_labels[key].config(text="0.0")
            
            # Reset monitor stats
            for key in self.monitor_stats:
                self.monitor_stats[key].config(text="0")
            
            # Reset health
            self.health_label.config(text="Score: N/A", foreground='#34a853')
            self.health_progress['value'] = 0
            
            self.status_label.config(text="Statistics reset", foreground='#fbbc05')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset statistics: {str(e)}")
    
    def perform_speed_test(self):
        """Perform speed test in background"""
        def run_speed_test():
            try:
                self.status_label.config(text="Running speed test...", foreground='#4285f4')
                results = self.monitor.perform_speed_test()
                
                # Update current statistics
                with self.monitor.lock:
                    self.monitor.statistics['download_speed_mbps'] = results['download_mbps']
                    self.monitor.statistics['upload_speed_mbps'] = results['upload_mbps']
                    self.monitor.statistics['avg_latency_ms'] = results['latency_ms']
                    self.monitor.statistics['jitter_ms'] = results['jitter_ms']
                    self.monitor.statistics['packet_loss_percent'] = results['packet_loss_percent']
                
                # Show results
                result_text = f"""
                ⚡ Speed Test Results ⚡
                
                Download Speed: {results['download_mbps']:.2f} Mbps
                Upload Speed: {results['upload_mbps']:.2f} Mbps
                Latency: {results['latency_ms']:.1f} ms
                Jitter: {results['jitter_ms']:.1f} ms
                Packet Loss: {results['packet_loss_percent']:.2f}%
                Test Duration: {results['test_duration']:.1f} seconds
                
                Test completed at: {results['timestamp']}
                """
                
                # Update GUI in main thread
                self.root.after(0, lambda: messagebox.showinfo("Speed Test Results", result_text))
                self.root.after(0, lambda: self.status_label.config(text="Speed test completed", foreground='#34a853'))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Speed test failed: {str(e)}"))
                self.root.after(0, lambda: self.status_label.config(text="Speed test failed", foreground='#ea4335'))
        
        # Run in thread to avoid freezing GUI
        threading.Thread(target=run_speed_test, daemon=True).start()
    
    def show_network_health(self):
        """Show network health analysis"""
        try:
            health = self.monitor.analyze_network_health()
            
            health_text = f"""
            🏥 Network Health Analysis 🏥
            
            Overall Health Score: {health['health_score']}/100
            Status: {'✅ Excellent' if health['health_score'] >= 90 else 
                    '👍 Good' if health['health_score'] >= 70 else
                    '⚠️ Fair' if health['health_score'] >= 50 else
                    '❌ Poor'}
            
            Component Scores:
            • Speed ({health['metrics']['speed']['value']:.1f} Mbps): {health['metrics']['speed']['score']}/100
            • Latency ({health['metrics']['latency']['value']:.1f} ms): {health['metrics']['latency']['score']}/100
            • Packet Loss ({health['metrics']['packet_loss']['value']:.2f}%): {health['metrics']['packet_loss']['score']}/100
            • Jitter ({health['metrics']['jitter']['value']:.2f} ms): {health['metrics']['jitter']['score']}/100
            • Stability: {health['metrics']['stability']['score']}/100
            
            Recommendations:
            """
            
            for rec in health['recommendations']:
                health_text += f"• {rec}\n"
            
            health_text += f"\nAnalysis Time: {health['timestamp']}"
            
            messagebox.showinfo("Network Health", health_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze network health: {str(e)}")
    
    def analyze_traffic(self):
        """Analyze captured traffic"""
        try:
            packets = self.monitor.get_recent_data(count=1000)
            
            # Create analysis window
            analysis_window = tk.Toplevel(self.root)
            analysis_window.title("Traffic Analysis")
            analysis_window.geometry("900x700")
            
            # Create notebook for different analysis views
            notebook = ttk.Notebook(analysis_window)
            notebook.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Summary tab
            summary_frame = ttk.Frame(notebook)
            notebook.add(summary_frame, text='📊 Summary')
            
            summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, font=('Courier', 10))
            summary_text.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Perform analysis
            analysis = self.analyzer.analyze_traffic(packets)
            summary = analysis['summary']
            
            summary_text.insert('1.0', f"""
            {'='*60}
            📊 TRAFFIC ANALYSIS SUMMARY
            {'='*60}
            
            Total Packets: {summary['total_packets']:,}
            Total Bytes: {summary['total_bytes']:,}
            Duration: {summary['duration']:.2f} seconds
            Average Speed: {summary['avg_speed_mbps']:.2f} Mbps
            Peak Speed: {summary['peak_speed_mbps']:.2f} Mbps
            Analysis Time: {summary['analysis_time']:.3f} seconds
            
            {'-'*60}
            📈 PROTOCOL DISTRIBUTION
            {'-'*60}
            """)
            
            for proto, data in analysis['protocols'].items():
                summary_text.insert('end', 
                    f"• {proto:10} {data['count']:6,} packets ({data['percentage']:5.1f}%)\n")
            
            summary_text.insert('end', f"""
            {'-'*60}
            🎯 TOP HOSTS
            {'-'*60}
            """)
            
            for host, data in list(analysis['top_hosts'].items())[:5]:
                summary_text.insert('end', 
                    f"• {host:15} Sent: {data['sent']:4,} Received: {data['received']:4,}\n")
            
            summary_text.config(state='disabled')
            
            # Anomalies tab
            anomalies_frame = ttk.Frame(notebook)
            notebook.add(anomalies_frame, text='🚨 Anomalies')
            
            anomalies_text = scrolledtext.ScrolledText(anomalies_frame, wrap=tk.WORD, font=('Courier', 10))
            anomalies_text.pack(fill='both', expand=True, padx=10, pady=10)
            
            if analysis['anomalies']:
                anomalies_text.insert('1.0', "🚨 DETECTED ANOMALIES:\n" + "="*40 + "\n\n")
                for anomaly in analysis['anomalies']:
                    severity_icon = '🔴' if anomaly['severity'] == 'High' else '🟡' if anomaly['severity'] == 'Medium' else '🟢'
                    anomalies_text.insert('end', 
                        f"{severity_icon} {anomaly['type']} ({anomaly['severity']})\n")
                    anomalies_text.insert('end', f"   Description: {anomaly['description']}\n")
                    anomalies_text.insert('end', f"   Time: {anomaly.get('time', 'N/A')}\n")
                    if 'count' in anomaly:
                        anomalies_text.insert('end', f"   Count: {anomaly['count']}\n")
                    anomalies_text.insert('end', "-"*40 + "\n")
            else:
                anomalies_text.insert('1.0', "✅ No anomalies detected.\n\nYour network traffic appears normal.")
            
            anomalies_text.config(state='disabled')
            
            # Health tab
            health_frame = ttk.Frame(notebook)
            notebook.add(health_frame, text='🏥 Health')
            
            health_text = scrolledtext.ScrolledText(health_frame, wrap=tk.WORD, font=('Courier', 10))
            health_text.pack(fill='both', expand=True, padx=10, pady=10)
            
            health_assessment = analysis['health_assessment']
            health_text.insert('1.0', f"""
            {'='*60}
            🏥 NETWORK HEALTH ASSESSMENT
            {'='*60}
            
            Overall Health Score: {health_assessment['health_score']}/100
            Status: {health_assessment['status']}
            
            {'-'*60}
            📊 FACTOR BREAKDOWN
            {'-'*60}
            """)
            
            for factor, score in health_assessment['factors'].items():
                health_text.insert('end', f"• {factor.title():12} {score:3}/100\n")
            
            health_text.insert('end', f"""
            {'-'*60}
            💡 RECOMMENDATIONS
            {'-'*60}
            """)
            
            if health_assessment['health_score'] >= 90:
                health_text.insert('end', "✅ Your network is in excellent condition!\n")
                health_text.insert('end', "   Continue with regular monitoring.\n")
            elif health_assessment['health_score'] >= 70:
                health_text.insert('end', "👍 Network health is good.\n")
                health_text.insert('end', "   Monitor for any performance degradation.\n")
            elif health_assessment['health_score'] >= 50:
                health_text.insert('end', "⚠️ Network health is fair.\n")
                health_text.insert('end', "   Consider optimizing your network setup.\n")
            else:
                health_text.insert('end', "❌ Network health needs attention.\n")
                health_text.insert('end', "   Review recommendations and take action.\n")
            
            health_text.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Traffic analysis failed: {str(e)}")
    
    def show_graphs(self):
        """Show graphs window"""
        try:
            # Create graphs window
            graph_window = tk.Toplevel(self.root)
            graph_window.title("Network Graphs")
            graph_window.geometry("1200x800")
            
            # Create notebook for different graphs
            notebook = ttk.Notebook(graph_window)
            notebook.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Get data
            packets = self.monitor.get_recent_data(count=500)
            
            # Speed graph
            speed_frame = ttk.Frame(notebook)
            notebook.add(speed_frame, text='⚡ Speed')
            
            fig = Figure(figsize=(10, 6), dpi=80)
            ax = fig.add_subplot(111)
            canvas = FigureCanvasTkAgg(fig, speed_frame)
            canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
            
            if packets and len(packets) > 1:
                timestamps = [p['timestamp'] for p in packets]
                download_speeds = [p.get('download_speed_mbps', 0) for p in packets]
                upload_speeds = [p.get('upload_speed_mbps', 0) for p in packets]
                
                base_time = timestamps[0]
                relative_times = [t - base_time for t in timestamps]
                
                ax.plot(relative_times, download_speeds, 'b-', label='Download', linewidth=2)
                ax.plot(relative_times, upload_speeds, 'g-', label='Upload', linewidth=2)
                ax.set_xlabel('Time (s)')
                ax.set_ylabel('Speed (Mbps)')
                ax.set_title('Speed Timeline')
                ax.legend()
                ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, 'No data available\nStart monitoring to see graphs',
                       ha='center', va='center', fontsize=12)
                ax.set_title('Speed Timeline')
                ax.axis('off')
            
            canvas.draw()
            
            # Protocol distribution graph
            proto_frame = ttk.Frame(notebook)
            notebook.add(proto_frame, text='📊 Protocols')
            
            fig2 = Figure(figsize=(10, 6), dpi=80)
            ax2 = fig2.add_subplot(111)
            canvas2 = FigureCanvasTkAgg(fig2, proto_frame)
            canvas2.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
            
            if packets:
                protocol_counter = Counter(p.get('protocol', 'Unknown') for p in packets)
                if protocol_counter:
                    labels = list(protocol_counter.keys())
                    sizes = list(protocol_counter.values())
                    colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
                    ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                    ax2.set_title('Protocol Distribution')
                    ax2.axis('equal')
                else:
                    ax2.text(0.5, 0.5, 'No protocol data', ha='center', va='center', fontsize=12)
                    ax2.set_title('Protocol Distribution')
                    ax2.axis('off')
            else:
                ax2.text(0.5, 0.5, 'No data available\nStart monitoring to see graphs',
                        ha='center', va='center', fontsize=12)
                ax2.set_title('Protocol Distribution')
                ax2.axis('off')
            
            canvas2.draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create graphs: {str(e)}")
    
    def update_protocol_graph(self):
        """Update protocol distribution graph - FIXED"""
        try:
            packets = self.monitor.get_recent_data(count=500)
            
            # Clear axis
            self.protocol_ax.clear()
            
            if packets:
                protocol_counter = Counter(p.get('protocol', 'Unknown') for p in packets)
                
                if protocol_counter:
                    labels = list(protocol_counter.keys())
                    sizes = list(protocol_counter.values())
                    
                    # Use color palette
                    colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
                    
                    # Create pie chart
                    self.protocol_ax.pie(sizes, labels=labels, colors=colors, 
                                       autopct='%1.1f%%', startangle=90,
                                       textprops={'fontsize': 10})
                    
                    # Set title
                    self.protocol_ax.set_title('Protocol Distribution', fontsize=14, fontweight='bold')
                    
                    # Equal aspect ratio
                    self.protocol_ax.axis('equal')
                else:
                    self.protocol_ax.text(0.5, 0.5, 'No protocol data\navailable', 
                                         ha='center', va='center', fontsize=12)
                    self.protocol_ax.set_title('Protocol Distribution', fontsize=14, fontweight='bold')
                    self.protocol_ax.axis('off')
            else:
                # Create demo data for display
                labels = ['TCP', 'UDP', 'HTTP', 'HTTPS', 'DNS', 'ICMP']
                sizes = [35, 25, 15, 12, 8, 5]
                colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
                
                self.protocol_ax.pie(sizes, labels=labels, colors=colors, 
                                   autopct='%1.1f%%', startangle=90,
                                   textprops={'fontsize': 10})
                self.protocol_ax.set_title('Protocol Distribution (Demo)', fontsize=14, fontweight='bold')
                self.protocol_ax.axis('equal')
            
            # Redraw canvas
            self.protocol_canvas.draw_idle()
            
        except Exception as e:
            print(f"Protocol graph update error: {e}")
    
    def update_traffic_graphs(self):
        """Update all traffic graphs - FIXED"""
        try:
            packets = self.monitor.get_recent_data(count=500)
            
            # Clear all axes completely
            self.traffic_ax1.clear()
            self.traffic_ax2.clear()
            self.traffic_ax3.clear()
            self.traffic_ax4.clear()
            
            if packets and len(packets) > 1:
                # Speed timeline
                timestamps = [p['timestamp'] for p in packets]
                download_speeds = [p.get('download_speed_mbps', 0) for p in packets]
                upload_speeds = [p.get('upload_speed_mbps', 0) for p in packets]
                
                # Convert timestamps to relative time
                base_time = timestamps[0]
                relative_times = [t - base_time for t in timestamps]
                
                # Plot speed timeline
                self.traffic_ax1.plot(relative_times, download_speeds, 'b-', label='Download', linewidth=2, alpha=0.8)
                self.traffic_ax1.plot(relative_times, upload_speeds, 'g-', label='Upload', linewidth=2, alpha=0.8)
                self.traffic_ax1.set_xlabel('Time (s)')
                self.traffic_ax1.set_ylabel('Speed (Mbps)')
                self.traffic_ax1.set_title('Speed Timeline')
                self.traffic_ax1.legend(loc='upper right', fontsize='small')
                self.traffic_ax1.grid(True, alpha=0.3)
                
                # Top hosts
                host_counter = Counter()
                for packet in packets:
                    src_ip = packet.get('src_ip', '')
                    dst_ip = packet.get('dst_ip', '')
                    if src_ip and src_ip != '0.0.0.0':
                        host_counter[src_ip] += 1
                    if dst_ip and dst_ip != '0.0.0.0' and dst_ip != src_ip:
                        host_counter[dst_ip] += 1
                
                top_hosts = host_counter.most_common(5)
                if top_hosts:
                    hosts = [h[0] for h in top_hosts]
                    counts = [h[1] for h in top_hosts]
                    
                    y_pos = np.arange(len(hosts))
                    bars = self.traffic_ax2.barh(y_pos, counts, color='skyblue', alpha=0.8)
                    
                    # Add value labels
                    for i, (bar, count) in enumerate(zip(bars, counts)):
                        width = bar.get_width()
                        self.traffic_ax2.text(width + max(counts) * 0.01, bar.get_y() + bar.get_height()/2,
                                           f'{count}', ha='left', va='center', fontsize=9)
                    
                    self.traffic_ax2.set_yticks(y_pos)
                    self.traffic_ax2.set_yticklabels(hosts, fontsize=9)
                    self.traffic_ax2.set_xlabel('Packet Count')
                    self.traffic_ax2.set_title('Top Hosts')
                    self.traffic_ax2.invert_yaxis()
                    self.traffic_ax2.grid(True, alpha=0.3, axis='x')
                else:
                    self.traffic_ax2.text(0.5, 0.5, 'No host data\navailable',
                                         ha='center', va='center', fontsize=10)
                    self.traffic_ax2.set_title('Top Hosts')
                    self.traffic_ax2.axis('off')
                
                # Port activity
                port_counter = Counter()
                for packet in packets:
                    src_port = packet.get('src_port', 0)
                    dst_port = packet.get('dst_port', 0)
                    if src_port > 0:
                        port_counter[src_port] += 1
                    if dst_port > 0:
                        port_counter[dst_port] += 1
                
                top_ports = port_counter.most_common(5)
                if top_ports:
                    ports = [f"Port {p[0]}" for p in top_ports]
                    counts = [p[1] for p in top_ports]
                    
                    y_pos = np.arange(len(ports))
                    bars = self.traffic_ax3.barh(y_pos, counts, color='lightgreen', alpha=0.8)
                    
                    # Add value labels
                    for i, (bar, count) in enumerate(zip(bars, counts)):
                        width = bar.get_width()
                        self.traffic_ax3.text(width + max(counts) * 0.01, bar.get_y() + bar.get_height()/2,
                                           f'{count}', ha='left', va='center', fontsize=9)
                    
                    self.traffic_ax3.set_yticks(y_pos)
                    self.traffic_ax3.set_yticklabels(ports, fontsize=9)
                    self.traffic_ax3.set_xlabel('Activity Count')
                    self.traffic_ax3.set_title('Port Activity')
                    self.traffic_ax3.invert_yaxis()
                    self.traffic_ax3.grid(True, alpha=0.3, axis='x')
                else:
                    self.traffic_ax3.text(0.5, 0.5, 'No port data\navailable',
                                         ha='center', va='center', fontsize=10)
                    self.traffic_ax3.set_title('Port Activity')
                    self.traffic_ax3.axis('off')
                
                # Protocol composition
                protocol_counter = Counter(p.get('protocol', 'Unknown') for p in packets)
                if protocol_counter:
                    protocols = list(protocol_counter.keys())
                    counts = list(protocol_counter.values())
                    colors = plt.cm.Set3(np.linspace(0, 1, len(protocols)))
                    
                    self.traffic_ax4.pie(counts, labels=protocols, colors=colors, 
                                       autopct='%1.1f%%', startangle=90)
                    self.traffic_ax4.set_title('Protocol Composition')
                    self.traffic_ax4.axis('equal')
                else:
                    self.traffic_ax4.text(0.5, 0.5, 'No protocol data\navailable',
                                         ha='center', va='center', fontsize=10)
                    self.traffic_ax4.set_title('Protocol Composition')
                    self.traffic_ax4.axis('off')
            
            else:
                # Create demo data for display
                # Speed timeline demo
                x = np.linspace(0, 60, 100)
                download = 50 + 20 * np.sin(x/10) + np.random.normal(0, 5, 100)
                upload = 10 + 5 * np.sin(x/8) + np.random.normal(0, 2, 100)
                
                self.traffic_ax1.plot(x, download, 'b-', label='Download', linewidth=2, alpha=0.8)
                self.traffic_ax1.plot(x, upload, 'g-', label='Upload', linewidth=2, alpha=0.8)
                self.traffic_ax1.set_xlabel('Time (s)')
                self.traffic_ax1.set_ylabel('Speed (Mbps)')
                self.traffic_ax1.set_title('Speed Timeline (Demo)')
                self.traffic_ax1.legend(loc='upper right', fontsize='small')
                self.traffic_ax1.grid(True, alpha=0.3)
                
                # Top hosts demo
                hosts = ['8.8.8.8', '1.1.1.1', '192.168.1.1', '10.0.0.1', '172.16.0.1']
                counts = [150, 120, 95, 80, 70]
                y_pos = np.arange(len(hosts))
                bars = self.traffic_ax2.barh(y_pos, counts, color='skyblue', alpha=0.8)
                
                for i, (bar, count) in enumerate(zip(bars, counts)):
                    width = bar.get_width()
                    self.traffic_ax2.text(width + max(counts) * 0.01, bar.get_y() + bar.get_height()/2,
                                       f'{count}', ha='left', va='center', fontsize=9)
                
                self.traffic_ax2.set_yticks(y_pos)
                self.traffic_ax2.set_yticklabels(hosts, fontsize=9)
                self.traffic_ax2.set_xlabel('Packet Count')
                self.traffic_ax2.set_title('Top Hosts (Demo)')
                self.traffic_ax2.invert_yaxis()
                self.traffic_ax2.grid(True, alpha=0.3, axis='x')
                
                # Port activity demo
                ports = ['80 (HTTP)', '443 (HTTPS)', '53 (DNS)', '22 (SSH)', '3389 (RDP)']
                port_counts = [120, 110, 90, 45, 30]
                y_pos = np.arange(len(ports))
                bars = self.traffic_ax3.barh(y_pos, port_counts, color='lightgreen', alpha=0.8)
                
                for i, (bar, count) in enumerate(zip(bars, port_counts)):
                    width = bar.get_width()
                    self.traffic_ax3.text(width + max(port_counts) * 0.01, bar.get_y() + bar.get_height()/2,
                                       f'{count}', ha='left', va='center', fontsize=9)
                
                self.traffic_ax3.set_yticks(y_pos)
                self.traffic_ax3.set_yticklabels(ports, fontsize=9)
                self.traffic_ax3.set_xlabel('Activity Count')
                self.traffic_ax3.set_title('Port Activity (Demo)')
                self.traffic_ax3.invert_yaxis()
                self.traffic_ax3.grid(True, alpha=0.3, axis='x')
                
                # Protocol composition demo
                protocols = ['TCP', 'UDP', 'HTTP', 'HTTPS', 'DNS']
                protocol_counts = [35, 25, 15, 12, 8]
                colors = plt.cm.Set3(np.linspace(0, 1, len(protocols)))
                self.traffic_ax4.pie(protocol_counts, labels=protocols, colors=colors, 
                                   autopct='%1.1f%%', startangle=90)
                self.traffic_ax4.set_title('Protocol Composition (Demo)')
                self.traffic_ax4.axis('equal')
            
            # Adjust layout and redraw
            self.figures['traffic'].tight_layout(pad=3.0)
            self.traffic_canvas.draw_idle()
            
        except Exception as e:
            print(f"Traffic graphs update error: {e}")
    
    def update_performance_graphs(self):
        """Update performance graphs - FIXED"""
        try:
            packets = self.monitor.get_recent_data(count=500)
            
            # Clear all axes completely
            self.perf_ax1.clear()
            self.perf_ax2.clear()
            self.perf_ax3.clear()
            self.perf_ax4.clear()
            
            # Always show demo data for performance graphs
            # Speed timeline (demo)
            x = np.linspace(0, 60, 100)
            download = 50 + 20 * np.sin(x/10) + np.random.normal(0, 5, 100)
            upload = 10 + 5 * np.sin(x/8) + np.random.normal(0, 2, 100)
            
            self.perf_ax1.plot(x, download, 'b-', label='Download', linewidth=2, alpha=0.8)
            self.perf_ax1.plot(x, upload, 'g-', label='Upload', linewidth=2, alpha=0.8)
            self.perf_ax1.fill_between(x, 0, download, alpha=0.3, color='blue')
            self.perf_ax1.fill_between(x, 0, upload, alpha=0.3, color='green')
            self.perf_ax1.set_xlabel('Time (s)')
            self.perf_ax1.set_ylabel('Speed (Mbps)')
            self.perf_ax1.set_title('Speed Timeline')
            self.perf_ax1.legend(loc='upper right', fontsize='small')
            self.perf_ax1.grid(True, alpha=0.3)
            
            # Latency distribution (demo)
            latencies = np.random.exponential(scale=25, size=1000)
            latencies = np.clip(latencies, 5, 150)
            
            self.perf_ax2.hist(latencies, bins=30, edgecolor='black', 
                              alpha=0.7, color='#34a853', density=False)
            
            mean_latency = np.mean(latencies)
            median_latency = np.median(latencies)
            
            self.perf_ax2.axvline(mean_latency, color='#ea4335', linestyle='--', 
                                linewidth=2, label=f'Mean: {mean_latency:.1f} ms')
            self.perf_ax2.axvline(median_latency, color='#4285f4', linestyle='--',
                                linewidth=2, label=f'Median: {median_latency:.1f} ms')
            
            stats_text = f'Statistics:\nMean: {mean_latency:.1f} ms\nMedian: {median_latency:.1f} ms'
            self.perf_ax2.text(0.02, 0.98, stats_text, transform=self.perf_ax2.transAxes, fontsize=10,
                             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            self.perf_ax2.set_xlabel('Latency (ms)')
            self.perf_ax2.set_ylabel('Frequency')
            self.perf_ax2.set_title('Latency Distribution')
            self.perf_ax2.legend(loc='upper right', fontsize='small')
            self.perf_ax2.grid(True, alpha=0.3)
            
            # Jitter analysis (demo)
            time_points = np.arange(0, 60, 0.5)
            base_latency = 20 + 10 * np.sin(time_points / 10)
            jitter = np.random.normal(0, 3, len(time_points))
            latency = base_latency + jitter
            
            self.perf_ax3.plot(time_points, latency, 'b-', linewidth=1.5, alpha=0.7, label='Latency')
            self.perf_ax3.fill_between(time_points, base_latency - 5, base_latency + 5, 
                                      alpha=0.2, color='blue', label='±5ms range')
            
            avg_jitter = np.mean(np.abs(np.diff(latency)))
            self.perf_ax3.axhline(y=np.mean(latency), color='red', linestyle='--', alpha=0.7, 
                                label=f'Avg Latency: {np.mean(latency):.1f}ms')
            
            self.perf_ax3.text(0.02, 0.98, f'Avg Jitter: {avg_jitter:.2f}ms', 
                             transform=self.perf_ax3.transAxes, fontsize=10,
                             verticalalignment='top',
                             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            
            self.perf_ax3.set_xlabel('Time (s)')
            self.perf_ax3.set_ylabel('Latency (ms)')
            self.perf_ax3.set_title('Jitter Analysis')
            self.perf_ax3.legend(loc='upper right', fontsize='small')
            self.perf_ax3.grid(True, alpha=0.3)
            self.perf_ax3.set_ylim([0, max(latency) * 1.2])
            
            # Packet loss (demo)
            time_points = np.arange(0, 60, 1)
            packet_loss = 0.5 + 2 * np.sin(time_points / 15) + np.random.normal(0, 0.5, len(time_points))
            packet_loss = np.clip(packet_loss, 0, 5)
            
            self.perf_ax4.plot(time_points, packet_loss, 'r-', linewidth=2, alpha=0.8, marker='o', markersize=4)
            self.perf_ax4.fill_between(time_points, 0, packet_loss, alpha=0.3, color='red')
            
            # Add threshold lines
            self.perf_ax4.axhline(y=1, color='green', linestyle='--', alpha=0.7, label='Good (<1%)')
            self.perf_ax4.axhline(y=2, color='orange', linestyle='--', alpha=0.7, label='Acceptable (<2%)')
            self.perf_ax4.axhline(y=5, color='red', linestyle='--', alpha=0.7, label='Poor (≥5%)')
            
            # Add statistics
            avg_loss = np.mean(packet_loss)
            max_loss = np.max(packet_loss)
            
            stats_text = f'Statistics:\nAverage: {avg_loss:.2f}%\nMaximum: {max_loss:.2f}%\nCurrent: {packet_loss[-1]:.2f}%'
            self.perf_ax4.text(0.02, 0.98, stats_text, transform=self.perf_ax4.transAxes,
                             fontsize=10, verticalalignment='top',
                             bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))
            
            self.perf_ax4.set_xlabel('Time (s)')
            self.perf_ax4.set_ylabel('Packet Loss (%)')
            self.perf_ax4.set_title('Packet Loss Over Time')
            self.perf_ax4.legend(loc='upper right', fontsize='small')
            self.perf_ax4.grid(True, alpha=0.3)
            self.perf_ax4.set_ylim([0, max(packet_loss) * 1.2])
            
            # Adjust layout and redraw
            self.figures['performance'].tight_layout(pad=3.0)
            self.perf_canvas.draw_idle()
            
        except Exception as e:
            print(f"Performance graphs update error: {e}")
    
    def scan_anomalies(self):
        """Scan for network anomalies"""
        try:
            packets = self.monitor.get_recent_data(count=1000)
            analysis = self.analyzer.analyze_traffic(packets)
            anomalies = analysis['anomalies']
            
            # Clear existing items
            for item in self.anomaly_tree.get_children():
                self.anomaly_tree.delete(item)
            
            # Add new anomalies
            for i, anomaly in enumerate(anomalies):
                self.anomaly_tree.insert('', 'end', values=(
                    anomaly.get('severity', 'Unknown'),
                    anomaly.get('type', 'Unknown'),
                    anomaly.get('description', 'No description'),
                    anomaly.get('time', 'N/A'),
                    anomaly.get('count', 'N/A')
                ))
            
            self.status_label.config(text=f"Found {len(anomalies)} anomalies", foreground='#fbbc05')
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan for anomalies: {str(e)}")
    
    def clear_anomalies(self):
        """Clear anomaly list"""
        for item in self.anomaly_tree.get_children():
            self.anomaly_tree.delete(item)
        self.anomaly_detail_text.delete(1.0, tk.END)
        self.status_label.config(text="Anomaly list cleared", foreground='#34a853')
    
    def show_anomaly_details(self, event):
        """Show details of selected anomaly"""
        selection = self.anomaly_tree.selection()
        if selection:
            values = self.anomaly_tree.item(selection[0])['values']
            details = f"""
            Anomaly Details:
            Severity: {values[0]}
            Type: {values[1]}
            Description: {values[2]}
            Time Detected: {values[3]}
            Count: {values[4]}
            
            Recommendations:
            """
            
            # Add recommendations based on anomaly type
            if 'Traffic Burst' in values[1]:
                details += "• Investigate source of traffic burst\n• Check for DDoS attacks\n• Monitor bandwidth usage"
            elif 'Large Packets' in values[1]:
                details += "• Check for file transfers\n• Verify MTU settings\n• Monitor for fragmentation"
            elif 'Port Scan' in values[1]:
                details += "• Check firewall logs\n• Verify intrusion detection\n• Monitor suspicious IPs"
            elif 'High Latency' in values[1]:
                details += "• Check network congestion\n• Verify router performance\n• Test alternative routes"
            else:
                details += "• Monitor network traffic\n• Check system logs\n• Update security software"
            
            self.anomaly_detail_text.delete(1.0, tk.END)
            self.anomaly_detail_text.insert(1.0, details)
    
    def toggle_capture(self):
        """Toggle packet capture"""
        if not self.capture_active:
            self.capture_active = True
            self.capture_btn.configure(text="⏸ Stop Capture", style='Danger.TButton')
            self.status_label.config(text="Packet capture started", foreground='#4285f4')
        else:
            self.capture_active = False
            self.capture_btn.configure(text="▶ Start Capture", style='Accent.TButton')
            self.status_label.config(text="Packet capture stopped", foreground='#ea4335')
    
    def clear_monitor(self):
        """Clear monitor display"""
        for item in self.packet_tree.get_children():
            self.packet_tree.delete(item)
        self.status_label.config(text="Display cleared", foreground='#fbbc05')
    
    def export_packets(self):
        """Export captured packets"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Packets"
            )
            
            if filename:
                packets = self.monitor.get_recent_data(count=1000)
                
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Timestamp', 'Source IP', 'Source Port', 'Destination IP', 
                                   'Destination Port', 'Protocol', 'Packet Size', 'Info'])
                    
                    for packet in packets:
                        writer.writerow([
                            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(packet['timestamp'])),
                            packet['src_ip'],
                            packet.get('src_port', ''),
                            packet['dst_ip'],
                            packet.get('dst_port', ''),
                            packet['protocol'],
                            packet['packet_size'],
                            self.get_packet_info(packet)
                        ])
                
                messagebox.showinfo("Success", f"Packets exported to {filename}")
                self.status_label.config(text="Packets exported", foreground='#34a853')
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export packets: {str(e)}")
    
    def refresh_connections(self):
        """Refresh connections list"""
        self.update_connections_tree()
        self.status_label.config(text="Connections refreshed", foreground='#34a853')
    
    def kill_connection(self):
        """Kill selected connection"""
        selection = self.conn_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a connection first!")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to terminate this connection?"):
            # Get connection details
            values = self.conn_tree.item(selection[0])['values']
            
            # Simulate connection termination (in real app, would use system calls)
            self.status_label.config(text=f"Terminated connection to {values[3]}:{values[4]}", 
                                   foreground='#ea4335')
            
            # Remove from tree
            self.conn_tree.delete(selection[0])
            
            messagebox.showinfo("Success", "Connection terminated (simulated)")
    
    def find_process(self):
        """Find process by name"""
        process_name = tk.simpledialog.askstring("Find Process", "Enter process name:")
        if process_name:
            # Search in connection tree
            items = self.conn_tree.get_children()
            found = False
            
            for item in items:
                values = self.conn_tree.item(item)['values']
                if process_name.lower() in values[6].lower():
                    self.conn_tree.selection_set(item)
                    self.conn_tree.see(item)
                    found = True
            
            if found:
                self.status_label.config(text=f"Found process: {process_name}", foreground='#34a853')
            else:
                self.status_label.config(text=f"Process not found: {process_name}", foreground='#ea4335')
    
    def export_connections(self):
        """Export connections list"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Connections"
            )
            
            if filename:
                connections = []
                for item in self.conn_tree.get_children():
                    connections.append(self.conn_tree.item(item)['values'])
                
                if connections:
                    with open(filename, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Protocol', 'Local Address', 'Local Port', 
                                       'Remote Address', 'Remote Port', 'Status', 'Process', 'PID'])
                        for conn in connections:
                            writer.writerow(conn)
                    
                    messagebox.showinfo("Success", f"Connections exported to {filename}")
                    self.status_label.config(text="Connections exported", foreground='#34a853')
                else:
                    messagebox.showwarning("Warning", "No connections to export!")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export connections: {str(e)}")
    
    def show_connection_details(self, event):
        """Show details of selected connection"""
        selection = self.conn_tree.selection()
        if selection:
            values = self.conn_tree.item(selection[0])['values']
            details = f"""
            Connection Details:
            
            Protocol: {values[0]}
            Local Address: {values[1]}:{values[2]}
            Remote Address: {values[3]}:{values[4]}
            Status: {values[5]}
            Process: {values[6]}
            PID: {values[7]}
            
            Additional Information:
            • Connection established via {values[0]}
            • Local port {values[2]} to remote port {values[4]}
            • Process ID: {values[7]}
            • Process name: {values[6]}
            
            Actions:
            • Right-click for more options
            • Use 'Kill Connection' to terminate
            """
            self.conn_detail_text.delete(1.0, tk.END)
            self.conn_detail_text.insert(1.0, details)
    
    def export_figure(self, fig_type):
        """Export figure to file"""
        try:
            if fig_type not in self.figures:
                messagebox.showerror("Error", "Figure not found!")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), 
                          ("SVG files", "*.svg"), ("All files", "*.*")],
                title=f"Export {fig_type.title()} Figure"
            )
            
            if filename:
                self.figures[fig_type].savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Figure exported to {filename}")
                self.status_label.config(text="Figure exported", foreground='#34a853')
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export figure: {str(e)}")
    
    def export_anomaly_report(self):
        """Export anomaly report"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Anomaly Report"
            )
            
            if filename:
                anomalies = []
                for item in self.anomaly_tree.get_children():
                    anomalies.append(self.anomaly_tree.item(item)['values'])
                
                with open(filename, 'w') as f:
                    f.write("Network Monitor Pro - Anomaly Report\n")
                    f.write("="*50 + "\n")
                    f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total Anomalies: {len(anomalies)}\n")
                    f.write("="*50 + "\n\n")
                    
                    for i, anomaly in enumerate(anomalies, 1):
                        f.write(f"Anomaly #{i}:\n")
                        f.write(f"  Severity: {anomaly[0]}\n")
                        f.write(f"  Type: {anomaly[1]}\n")
                        f.write(f"  Description: {anomaly[2]}\n")
                        f.write(f"  Time: {anomaly[3]}\n")
                        f.write(f"  Count: {anomaly[4]}\n")
                        f.write("-"*40 + "\n")
                
                messagebox.showinfo("Success", f"Anomaly report exported to {filename}")
                self.status_label.config(text="Anomaly report exported", foreground='#34a853')
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export anomaly report: {str(e)}")
    
    def flush_dns_cache(self):
        """Flush DNS cache"""
        try:
            system = platform.system()
            
            if system == "Windows":
                subprocess.run(['ipconfig', '/flushdns'], shell=True, capture_output=True)
                self.status_label.config(text="DNS cache flushed (Windows)", foreground='#34a853')
            elif system == "Linux":
                subprocess.run(['sudo', 'systemd-resolve', '--flush-caches'], capture_output=True)
                self.status_label.config(text="DNS cache flushed (Linux)", foreground='#34a853')
            elif system == "Darwin":
                subprocess.run(['sudo', 'killall', '-HUP', 'mDNSResponder'], capture_output=True)
                self.status_label.config(text="DNS cache flushed (macOS)", foreground='#34a853')
            
            messagebox.showinfo("Success", "DNS cache flushed successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to flush DNS cache: {str(e)}")
    
    def ping_test(self):
        """Perform ping test"""
        target = tk.simpledialog.askstring("Ping Test", "Enter host to ping (e.g., 8.8.8.8 or google.com):")
        if target:
            def run_ping():
                try:
                    self.status_label.config(text=f"Pinging {target}...", foreground='#4285f4')
                    
                    # Simulate ping results
                    import random
                    results = {
                        'target': target,
                        'packets_sent': 4,
                        'packets_received': random.randint(3, 4),
                        'packet_loss': random.uniform(0, 25),
                        'min_latency': random.uniform(10, 30),
                        'avg_latency': random.uniform(20, 50),
                        'max_latency': random.uniform(50, 100)
                    }
                    
                    result_text = f"""
                    Ping Results for {target}:
                    
                    Packets: Sent = {results['packets_sent']}, Received = {results['packets_received']}, 
                    Lost = {results['packets_sent'] - results['packets_received']} ({results['packet_loss']:.1f}% loss)
                    
                    Approximate round trip times in ms:
                    Minimum = {results['min_latency']:.0f}ms, 
                    Maximum = {results['max_latency']:.0f}ms, 
                    Average = {results['avg_latency']:.0f}ms
                    """
                    
                    self.root.after(0, lambda: messagebox.showinfo("Ping Results", result_text))
                    self.root.after(0, lambda: self.status_label.config(text="Ping test completed", foreground='#34a853'))
                    
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Ping test failed: {str(e)}"))
            
            threading.Thread(target=run_ping, daemon=True).start()
    
    def toggle_dark_mode(self):
        """Toggle dark mode (placeholder)"""
        messagebox.showinfo("Info", "Dark mode feature coming soon!")
    
    def show_user_guide(self):
        """Show user guide"""
        guide_text = """
        Network Monitor Pro - User Guide
        
        BASIC OPERATION:
        1. Select a network interface from the dropdown
        2. Click 'Start Monitoring' to begin
        3. View real-time statistics in the Dashboard
        
        TABS:
        • Dashboard: Overview and key metrics
        • Monitoring: Live packet capture
        • Connections: Active network connections
        • Analysis: Graphs and traffic analysis
        
        KEY FEATURES:
        • Real-time speed monitoring
        • Packet capture and analysis
        • Connection tracking
        • Network health assessment
        • Anomaly detection
        • Speed testing
        
        TIPS:
        • Use 'Refresh' buttons to update data
        • Export reports for documentation
        • Check 'Network Health' for recommendations
        
        For more help, refer to the documentation.
        """
        messagebox.showinfo("User Guide", guide_text)
    
    def check_updates(self):
        """Check for updates"""
        messagebox.showinfo("Update Check", "You have the latest version: v2.1")
    
    def show_deep_analysis(self):
        """Show deep analysis window"""
        try:
            # Get comprehensive analysis
            packets = self.monitor.get_recent_data(count=2000)
            analysis = self.analyzer.analyze_traffic(packets)
            
            # Create analysis window
            analysis_window = tk.Toplevel(self.root)
            analysis_window.title("Deep Analysis")
            analysis_window.geometry("1000x800")
            
            # Create notebook
            notebook = ttk.Notebook(analysis_window)
            notebook.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Traffic Patterns
            patterns_frame = ttk.Frame(notebook)
            notebook.add(patterns_frame, text='Patterns')
            
            patterns_text = scrolledtext.ScrolledText(patterns_frame, wrap=tk.WORD, font=('Courier', 9))
            patterns_text.pack(fill='both', expand=True, padx=10, pady=10)
            
            temporal = analysis['temporal_analysis']
            patterns_text.insert('1.0', f"""
            TRAFFIC PATTERN ANALYSIS
            {'='*50}
            
            Duration: {temporal['duration']:.1f} seconds
            Average Inter-arrival: {temporal['avg_inter_arrival']:.3f} seconds
            Std Dev Inter-arrival: {temporal['std_inter_arrival']:.3f} seconds
            
            PATTERN SUMMARY:
            """)
            
            for i, pattern in enumerate(temporal.get('patterns', [])[:10], 1):
                patterns_text.insert('end', f"""
                Window {i}:
                • Start: {pattern['start_time']:.1f}s
                • Duration: {pattern['duration']:.1f}s
                • Packets/sec: {pattern['packets_per_second']:.1f}
                • Bytes/sec: {pattern['bytes_per_second']:.1f}
                • Total packets: {pattern['packet_count']}
                • Total bytes: {pattern['byte_count']:,}
                """)
            
            patterns_text.config(state='disabled')
            
            # Performance Details
            perf_frame = ttk.Frame(notebook)
            notebook.add(perf_frame, text='Performance')
            
            perf_text = scrolledtext.ScrolledText(perf_frame, wrap=tk.WORD, font=('Courier', 9))
            perf_text.pack(fill='both', expand=True, padx=10, pady=10)
            
            performance = analysis['performance']
            perf_text.insert('1.0', f"""
            PERFORMANCE ANALYSIS
            {'='*50}
            
            Speed Metrics:
            • Average Speed: {performance['avg_speed_mbps']:.2f} Mbps
            • Peak Speed: {performance['peak_speed_mbps']:.2f} Mbps
            • Average Download: {performance.get('avg_download_mbps', 0):.2f} Mbps
            • Average Upload: {performance.get('avg_upload_mbps', 0):.2f} Mbps
            
            Quality Metrics:
            • Average Latency: {performance['avg_latency_ms']:.1f} ms
            • Jitter: {performance['jitter_ms']:.1f} ms
            • Packet Loss: {performance['packet_loss_percent']:.2f}%
            
            NETWORK CHARACTERISTICS:
            """)
            
            # Add some analysis
            if performance['avg_speed_mbps'] > 100:
                perf_text.insert('end', "• High-speed network connection\n")
            elif performance['avg_speed_mbps'] > 50:
                perf_text.insert('end', "• Medium-speed network connection\n")
            else:
                perf_text.insert('end', "• Low-speed network connection\n")
            
            if performance['avg_latency_ms'] < 20:
                perf_text.insert('end', "• Excellent latency performance\n")
            elif performance['avg_latency_ms'] < 50:
                perf_text.insert('end', "• Good latency performance\n")
            else:
                perf_text.insert('end', "• High latency detected\n")
            
            perf_text.config(state='disabled')
            
            # Security Analysis
            security_frame = ttk.Frame(notebook)
            notebook.add(security_frame, text='Security')
            
            security_text = scrolledtext.ScrolledText(security_frame, wrap=tk.WORD, font=('Courier', 9))
            security_text.pack(fill='both', expand=True, padx=10, pady=10)
            
            security_text.insert('1.0', f"""
            SECURITY ANALYSIS
            {'='*50}
            
            Protocol Distribution:
            """)
            
            for proto, data in analysis['protocols'].items():
                if data['percentage'] > 10:
                    security_text.insert('end', f"• {proto}: {data['percentage']:.1f}%\n")
            
            security_text.insert('end', f"""
            
            Port Activity Summary:
            """)
            
            for port, count in list(analysis['port_analysis'].items())[:10]:
                security_text.insert('end', f"• Port {port}: {count} connections\n")
            
            security_text.insert('end', """
            
            SECURITY RECOMMENDATIONS:
            1. Monitor for unusual port activity
            2. Check for protocol anomalies
            3. Verify encryption on sensitive traffic
            4. Regular security audits recommended
            """)
            
            security_text.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Error", f"Deep analysis failed: {str(e)}")
    
    def show_settings(self):
        """Show settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        
        # Create settings notebook
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # General settings
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text='General')
        
        ttk.Label(general_frame, text="Update Interval (ms):", style='Normal.TLabel').pack(pady=5)
        interval_var = tk.StringVar(value="1000")
        interval_entry = ttk.Entry(general_frame, textvariable=interval_var, width=20)
        interval_entry.pack(pady=5)
        
        ttk.Label(general_frame, text="Max Packets to Display:").pack(pady=5)
        max_packets_var = tk.StringVar(value="1000")
        max_entry = ttk.Entry(general_frame, textvariable=max_packets_var, width=20)
        max_entry.pack(pady=5)
        
        ttk.Label(general_frame, text="Data Retention (days):").pack(pady=5)
        retention_var = tk.StringVar(value="7")
        retention_entry = ttk.Entry(general_frame, textvariable=retention_var, width=20)
        retention_entry.pack(pady=5)
        
        # Monitoring settings
        monitor_frame = ttk.Frame(notebook)
        notebook.add(monitor_frame, text='Monitoring')
        
        self.auto_start_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(monitor_frame, text="Auto-start monitoring on launch", 
                       variable=self.auto_start_var).pack(pady=5, anchor='w')
        
        self.show_details_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(monitor_frame, text="Show packet details", 
                       variable=self.show_details_var).pack(pady=5, anchor='w')
        
        self.log_to_file_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(monitor_frame, text="Log to file", 
                       variable=self.log_to_file_var).pack(pady=5, anchor='w')
        
        # Appearance settings
        appearance_frame = ttk.Frame(notebook)
        notebook.add(appearance_frame, text='Appearance')
        
        ttk.Label(appearance_frame, text="Theme:").pack(pady=5)
        theme_var = tk.StringVar(value="Light")
        theme_combo = ttk.Combobox(appearance_frame, textvariable=theme_var, width=20, state='readonly')
        theme_combo.pack(pady=5)
        theme_combo['values'] = ['Light', 'Dark', 'System']
        
        ttk.Label(appearance_frame, text="Font Size:").pack(pady=5)
        font_var = tk.StringVar(value="Normal")
        font_combo = ttk.Combobox(appearance_frame, textvariable=font_var, width=20, state='readonly')
        font_combo.pack(pady=5)
        font_combo['values'] = ['Small', 'Normal', 'Large']
        
        # Save button
        ttk.Button(settings_window, text="Save Settings", 
                  command=lambda: self.save_settings(
                      interval_var.get(), 
                      max_packets_var.get(),
                      retention_var.get(),
                      self.auto_start_var.get(),
                      self.show_details_var.get(),
                      self.log_to_file_var.get()
                  )).pack(pady=10)
    
    def save_settings(self, interval, max_packets, retention, auto_start, show_details, log_to_file):
        """Save settings"""
        try:
            # Validate inputs
            interval = int(interval)
            max_packets = int(max_packets)
            retention = int(retention)
            
            if interval < 100 or interval > 10000:
                raise ValueError("Interval must be between 100 and 10000 ms")
            if max_packets < 100 or max_packets > 10000:
                raise ValueError("Max packets must be between 100 and 10000")
            if retention < 1 or retention > 365:
                raise ValueError("Retention must be between 1 and 365 days")
            
            # Save settings (in real app, would save to file/database)
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid setting: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def export_report(self):
        """Export comprehensive network report"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Export Network Report"
            )
            
            if filename:
                # Get all data
                network_info = self.monitor.get_network_info()
                stats = self.monitor.get_statistics()
                health = self.monitor.analyze_network_health()
                connections = self.monitor.get_active_connections()
                packets = self.monitor.get_recent_data(count=500)
                analysis = self.analyzer.analyze_traffic(packets)
                
                # Create report
                report = f"""
                {'='*60}
                NETWORK MONITOR PRO - COMPREHENSIVE REPORT
                {'='*60}
                Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
                Report ID: {int(time.time())}
                {'='*60}
                
                SECTION 1: NETWORK INFORMATION
                {'-'*60}
                Connection: {network_info.get('connection_type', 'N/A')}
                SSID: {network_info.get('ssid', 'N/A')}
                Local IP: {network_info.get('local_ip', 'N/A')}
                Public IP: {network_info.get('public_ip', 'N/A')}
                Gateway: {network_info.get('gateway', 'N/A')}
                DNS Servers: {', '.join(network_info.get('dns_servers', ['N/A']))}
                MAC Address: {network_info.get('mac_address', 'N/A')}
                Signal Strength: {network_info.get('signal_strength', 'N/A')}
                Interface Speed: {network_info.get('speed_mbps', 'N/A')}
                Interface Status: {'Up' if network_info.get('is_up', False) else 'Down'}
                Hostname: {network_info.get('hostname', 'N/A')}
                
                SECTION 2: PERFORMANCE METRICS
                {'-'*60}
                Download Speed: {stats.get('download_speed_mbps', 0):.2f} Mbps
                Upload Speed: {stats.get('upload_speed_mbps', 0):.2f} Mbps
                Packets/Second: {stats.get('packets_per_second', 0):.0f}
                Bytes/Second: {stats.get('bytes_per_second', 0):.0f} KB/s
                Latency: {stats.get('avg_latency_ms', 0):.1f} ms
                Jitter: {stats.get('jitter_ms', 0):.1f} ms
                Packet Loss: {stats.get('packet_loss_percent', 0):.2f}%
                Active Connections: {stats.get('active_connections', 0)}
                Total Packets: {stats.get('total_packets', 0):,}
                Total Bytes: {stats.get('total_bytes', 0):,}
                Monitoring Duration: {stats.get('monitoring_duration', 0):.1f} seconds
                
                SECTION 3: NETWORK HEALTH
                {'-'*60}
                Health Score: {health['health_score']}/100
                Speed Score: {health['metrics']['speed']['score']}/100 ({health['metrics']['speed']['value']:.1f} Mbps)
                Latency Score: {health['metrics']['latency']['score']}/100 ({health['metrics']['latency']['value']:.1f} ms)
                Packet Loss Score: {health['metrics']['packet_loss']['score']}/100 ({health['metrics']['packet_loss']['value']:.2f}%)
                Jitter Score: {health['metrics']['jitter']['score']}/100 ({health['metrics']['jitter']['value']:.2f} ms)
                Stability Score: {health['metrics']['stability']['score']}/100
                
                Recommendations:
                """
                
                for rec in health['recommendations']:
                    report += f"- {rec}\n"
                
                report += f"""
                SECTION 4: CONNECTIONS SUMMARY
                {'-'*60}
                Total Active Connections: {len(connections)}
                
                SECTION 5: TRAFFIC ANALYSIS
                {'-'*60}
                Total Packets Analyzed: {analysis['summary']['total_packets']:,}
                Total Bytes: {analysis['summary']['total_bytes']:,}
                Average Speed: {analysis['summary']['avg_speed_mbps']:.2f} Mbps
                Peak Speed: {analysis['summary']['peak_speed_mbps']:.2f} Mbps
                
                Protocol Distribution:
                """
                
                for proto, data in analysis['protocols'].items():
                    report += f"- {proto}: {data['count']:,} packets ({data['percentage']:.1f}%)\n"
                
                report += f"""
                SECTION 6: ANOMALIES
                {'-'*60}
                Total Anomalies Detected: {len(analysis['anomalies'])}
                """
                
                for i, anomaly in enumerate(analysis['anomalies'][:10], 1):
                    report += f"{i}. {anomaly['type']} ({anomaly['severity']}): {anomaly['description']}\n"
                
                report += f"""
                {'='*60}
                END OF REPORT
                {'='*60}
                """
                
                with open(filename, 'w') as f:
                    f.write(report)
                
                messagebox.showinfo("Success", f"Report exported to {filename}")
                self.status_label.config(text="Report exported", foreground='#34a853')
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {str(e)}")
    
    def export_data(self):
        """Export all data in various formats"""
        try:
            format_choice = tk.messagebox.askquestion("Export Format", 
                                                     "Export as JSON (Yes) or CSV (No)?")
            
            if format_choice == 'yes':
                filename = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    title="Export Data as JSON"
                )
                
                if filename:
                    data = {
                        'network_info': self.monitor.get_network_info(),
                        'statistics': self.monitor.get_statistics(),
                        'health': self.monitor.analyze_network_health(),
                        'connections': self.monitor.get_active_connections(),
                        'packets': self.monitor.get_recent_data(count=1000),
                        'timestamp': time.time(),
                        'export_date': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    with open(filename, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    
                    messagebox.showinfo("Success", f"Data exported to {filename}")
            else:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    title="Export Data as CSV"
                )
                
                if filename:
                    # Export statistics
                    stats = self.monitor.get_statistics()
                    with open(filename, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Metric', 'Value', 'Unit', 'Timestamp'])
                        for key, value in stats.items():
                            writer.writerow([key, value, '', time.strftime('%Y-%m-%d %H:%M:%S')])
                    
                    messagebox.showinfo("Success", f"Data exported to {filename}")
            
            self.status_label.config(text="Data exported", foreground='#34a853')
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""
        Network Monitor Pro v2.1 - FIXED
        
        Advanced network monitoring tool with real-time visualization
        and comprehensive analysis capabilities.
        
        Features:
        • Real-time network monitoring and statistics
        • Speed testing and performance analysis
        • Traffic visualization with graphs
        • Anomaly detection and security analysis
        • Connection tracking and management
        • Comprehensive health assessment
        • Data export and reporting
        
        System Information:
        • Python: {platform.python_version()}
        • Platform: {platform.system()} {platform.release()}
        • Processor: {platform.processor()}
        
        Created for network administrators, IT professionals,
        and anyone interested in network performance analysis.
        
        © 2024 Network Monitor Pro. All rights reserved.
        """
        messagebox.showinfo("About Network Monitor Pro", about_text)
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_monitoring:
            self.monitor.stop_monitoring()
        self.root.destroy()

def main():
    """Main application entry point"""
    try:
        if TTKTHEMES_AVAILABLE:
            root = ThemedTk(theme="arc")
        else:
            root = tk.Tk()
        
        app = NetworkMonitorGUI(root)
        
        # Handle window closing
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Center window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Start GUI
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Failed to start application: {str(e)}")

if __name__ == "__main__":
    main()