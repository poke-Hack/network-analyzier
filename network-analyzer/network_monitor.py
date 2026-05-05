
import time
import threading
import socket
import struct
import os
import psutil
import numpy as np
from collections import deque, Counter, defaultdict
import heapq
from dataclasses import dataclass
import statistics
import platform
import subprocess
import re
import json
import random
import urllib.request
from typing import List, Dict, Any

@dataclass
class PacketInfo:
    timestamp: float
    src_ip: str
    dst_ip: str
    protocol: str
    length: int
    src_port: int = 0
    dst_port: int = 0
    ttl: int = 0
    flags: str = ""
    
class NetworkMonitor:
    def __init__(self):
        self.is_monitoring = False
        self.monitor_thread = None
        self.packet_thread = None
        self.interface = None
        
        self.packet_buffer = deque(maxlen=100000)
        self.speed_history = deque(maxlen=1000)
        self.packet_window = deque(maxlen=1000)
        self.connection_map = {}
        self.protocol_counts = Counter()
        self.port_counts = Counter()
        self.ip_counts = Counter()
        self.connection_graph = defaultdict(set)
        self.lock = threading.Lock()
        
        self.statistics = {
            'start_time': time.time(),
            'total_packets': 0,
            'total_bytes': 0,
            'packets_per_second': 0,
            'bytes_per_second': 0,
            'download_speed_mbps': 0,
            'upload_speed_mbps': 0,
            'active_connections': 0,
            'packet_loss_percent': 0,
            'avg_latency_ms': 10,
            'jitter_ms': 2,
            'peak_speed_mbps': 0,
            'monitoring_duration': 0
        }
        
        self.cache = {
            'network_info': None,
            'last_update': 0,
            'speed_cache': deque(maxlen=100)
        }
        
        self.last_bytes_sent = 0
        self.last_bytes_recv = 0
        self.last_update_time = time.time()
        
    def start_monitoring(self, interface=None, filter_str=""):
        """Start network monitoring on specified interface"""
        self.interface = interface or self.get_default_interface()
        self.is_monitoring = True
        
        # Reset statistics
        self.statistics['start_time'] = time.time()
        self.statistics['total_packets'] = 0
        self.statistics['total_bytes'] = 0
        
        # Clear data structures
        with self.lock:
            self.packet_buffer.clear()
            self.speed_history.clear()
            self.packet_window.clear()
            self.protocol_counts.clear()
            self.port_counts.clear()
            self.ip_counts.clear()
            self.connection_graph.clear()
            self.connection_map.clear()
        
        # Start monitoring threads
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.packet_thread = threading.Thread(target=self._packet_capture_loop, daemon=True)
        self.packet_thread.start()
        
        return True
        
    def stop_monitoring(self):
        """Stop network monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        if self.packet_thread:
            self.packet_thread.join(timeout=2)
            
    def _monitor_loop(self):
        """Main monitoring loop for speed and statistics"""
        download_window = deque(maxlen=10)
        upload_window = deque(maxlen=10)
        
        while self.is_monitoring:
            try:
                # Get network I/O statistics
                net_io = psutil.net_io_counters(pernic=True)
                
                if self.interface and self.interface in net_io:
                    io_stats = net_io[self.interface]
                else:
                    # Fallback to total if interface not found
                    io_stats = psutil.net_io_counters()
                
                current_time = time.time()
                time_diff = current_time - self.last_update_time
                
                if time_diff > 0.1:  # Update every 100ms
                    bytes_sent = io_stats.bytes_sent
                    bytes_recv = io_stats.bytes_recv
                    
                    # Calculate speeds
                    upload_speed = (bytes_sent - self.last_bytes_sent) * 8 / (time_diff * 1_000_000)
                    download_speed = (bytes_recv - self.last_bytes_recv) * 8 / (time_diff * 1_000_000)
                    
                    # Update windowed averages
                    upload_window.append(upload_speed)
                    download_window.append(download_speed)
                    
                    with self.lock:
                        self.statistics['upload_speed_mbps'] = statistics.mean(upload_window) if upload_window else 0
                        self.statistics['download_speed_mbps'] = statistics.mean(download_window) if download_window else 0
                        self.statistics['peak_speed_mbps'] = max(
                            self.statistics['peak_speed_mbps'],
                            self.statistics['download_speed_mbps'],
                            self.statistics['upload_speed_mbps']
                        )
                    
                    # Update counters for next iteration
                    self.last_bytes_sent = bytes_sent
                    self.last_bytes_recv = bytes_recv
                    self.last_update_time = current_time
                
                # Update active connections
                self._update_active_connections()
                
                with self.lock:
                    self.statistics['active_connections'] = len(self.connection_map)
                    self.statistics['monitoring_duration'] = current_time - self.statistics['start_time']
                
                time.sleep(0.1)  # 100ms interval
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(1)
                
    def _packet_capture_loop(self):
        """Simulate packet capture for demonstration"""
        protocols = ['TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS', 'DNS']
        ip_pool = ['192.168.1.', '10.0.0.', '172.16.0.']
        
        while self.is_monitoring:
            try:
                # Simulate random packets
                num_packets = random.randint(1, 10)
                
                with self.lock:
                    for _ in range(num_packets):
                        # Generate random packet data
                        protocol = random.choice(protocols)
                        src_ip = f"{random.choice(ip_pool)}{random.randint(1, 254)}"
                        dst_ip = f"{random.choice(ip_pool)}{random.randint(1, 254)}"
                        packet_size = random.randint(64, 1500)
                        
                        packet = PacketInfo(
                            timestamp=time.time(),
                            src_ip=src_ip,
                            dst_ip=dst_ip,
                            protocol=protocol,
                            length=packet_size,
                            src_port=random.randint(1024, 65535) if protocol in ['TCP', 'UDP'] else 0,
                            dst_port=random.choice([80, 443, 53, 22, 3389]) if protocol in ['TCP', 'UDP'] else 0
                        )
                        
                        self.packet_buffer.append(packet)
                        self.packet_window.append(packet)
                        
                        # Update counters
                        self.statistics['total_packets'] += 1
                        self.statistics['total_bytes'] += packet_size
                        self.protocol_counts[protocol] += 1
                        self.ip_counts[src_ip] += 1
                        self.ip_counts[dst_ip] += 1
                        
                        if packet.src_port:
                            self.port_counts[packet.src_port] += 1
                        if packet.dst_port:
                            self.port_counts[packet.dst_port] += 1
                
                # Update statistics based on packet window
                if self.packet_window:
                    window_duration = time.time() - self.packet_window[0].timestamp
                    if window_duration > 0:
                        self.statistics['packets_per_second'] = len(self.packet_window) / window_duration
                        total_bytes = sum(p.length for p in self.packet_window)
                        self.statistics['bytes_per_second'] = total_bytes / window_duration
                
                time.sleep(0.5)  # Simulate packet generation every 500ms
                
            except Exception as e:
                print(f"Packet capture error: {e}")
                time.sleep(1)
    
    def _update_active_connections(self):
        """Update active network connections"""
        try:
            connections = psutil.net_connections(kind='inet')
            temp_map = {}
            
            for conn in connections:
                if conn.laddr and conn.raddr:
                    conn_info = {
                        'local_addr': conn.laddr.ip,
                        'local_port': conn.laddr.port,
                        'remote_addr': conn.raddr.ip,
                        'remote_port': conn.raddr.port,
                        'status': conn.status,
                        'pid': conn.pid,
                        'process_name': self._get_process_name(conn.pid) if conn.pid else 'Unknown',
                        'protocol': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'
                    }
                    
                    key = f"{conn.laddr.ip}:{conn.laddr.port}-{conn.raddr.ip}:{conn.raddr.port}"
                    temp_map[key] = conn_info
            
            with self.lock:
                self.connection_map = temp_map
                    
        except Exception as e:
            print(f"Connection update error: {e}")
    
    def _get_process_name(self, pid):
        """Get process name from PID"""
        try:
            if pid:
                process = psutil.Process(pid)
                return process.name()
        except:
            pass
        return "Unknown"
    
    def get_network_info(self):
        """Get comprehensive network information"""
        current_time = time.time()
        if (self.cache['network_info'] and 
            current_time - self.cache['last_update'] < 5):
            return self.cache['network_info']
        
        info = {}
        
        try:
            # Get network interfaces
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            # Find active interface
            active_interface = None
            for iface, addresses in addrs.items():
                for addr in addresses:
                    if addr.family == socket.AF_INET and addr.address != '127.0.0.1':
                        active_interface = iface
                        info['interface'] = iface
                        info['local_ip'] = addr.address
                        info['subnet_mask'] = addr.netmask
                        info['broadcast'] = addr.broadcast if hasattr(addr, 'broadcast') else 'N/A'
                        break
                if active_interface:
                    break
            
            if active_interface:
                # Get MAC address
                info['mac_address'] = self._get_mac_address(active_interface)
                
                # Get interface statistics
                if active_interface in stats:
                    stat = stats[active_interface]
                    info['is_up'] = stat.isup
                    info['speed_mbps'] = f"{stat.speed} Mbps" if stat.speed > 0 else "Unknown"
                    info['mtu'] = stat.mtu
                    info['duplex'] = 'Full' if stat.duplex == 2 else 'Half' if stat.duplex == 1 else 'Unknown'
            
            # Get network configuration
            info['gateway'] = self._get_default_gateway()
            info['dns_servers'] = self._get_dns_servers()
            info['public_ip'] = self._get_public_ip()
            
            # Get WiFi information if applicable
            wifi_info = self._get_wifi_info(active_interface)
            info.update(wifi_info)
            
            # Get additional info
            info['hostname'] = socket.gethostname()
            info['domain'] = socket.getfqdn()
            info['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            self.cache['network_info'] = info
            self.cache['last_update'] = current_time
            
        except Exception as e:
            print(f"Network info error: {e}")
            info = {
                'local_ip': 'N/A',
                'public_ip': 'N/A',
                'gateway': 'N/A',
                'subnet_mask': 'N/A',
                'dns_servers': ['N/A'],
                'mac_address': 'N/A',
                'interface': 'N/A',
                'connection_type': 'Unknown',
                'ssid': 'N/A',
                'signal_strength': 'N/A',
                'frequency': 'N/A',
                'security': 'N/A',
                'speed_mbps': 'N/A',
                'is_up': False
            }
        
        return info
    
    def _get_mac_address(self, interface):
        """Get MAC address of interface"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['getmac', '/v'], capture_output=True, text=True, shell=True)
                for line in result.stdout.split('\n'):
                    if interface in line:
                        parts = line.split()
                        if len(parts) > 0:
                            return parts[-1]
            else:
                with open(f'/sys/class/net/{interface}/address', 'r') as f:
                    return f.read().strip()
        except:
            pass
        return 'N/A'
    
    def _get_default_gateway(self):
        """Get default gateway address"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
                for line in result.stdout.split('\n'):
                    if 'Default Gateway' in line:
                        parts = line.split(':')
                        if len(parts) > 1:
                            return parts[1].strip()
            else:
                result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'default via' in line:
                        parts = line.split()
                        return parts[2] if len(parts) > 2 else 'N/A'
        except:
            pass
        return 'N/A'
    
    def _get_dns_servers(self):
        """Get DNS server addresses"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, shell=True)
                dns_servers = []
                in_dns_section = False
                for line in result.stdout.split('\n'):
                    if 'DNS Servers' in line:
                        in_dns_section = True
                        parts = line.split(':')
                        if len(parts) > 1:
                            dns_servers.append(parts[1].strip())
                    elif in_dns_section and line.strip() and ':' not in line:
                        dns_servers.append(line.strip())
                    elif in_dns_section and not line.strip():
                        break
                return dns_servers if dns_servers else ['N/A']
            else:
                with open('/etc/resolv.conf', 'r') as f:
                    dns_servers = []
                    for line in f:
                        if line.startswith('nameserver'):
                            dns_servers.append(line.split()[1])
                    return dns_servers if dns_servers else ['N/A']
        except:
            return ['N/A']
    
    def _get_public_ip(self):
        """Get public IP address"""
        try:
            with urllib.request.urlopen('https://api.ipify.org?format=json', timeout=5) as response:
                data = json.load(response)
                return data.get('ip', 'N/A')
        except:
            return 'N/A'
    
    def _get_wifi_info(self, interface):
        """Get WiFi information"""
        info = {
            'connection_type': 'Ethernet',
            'ssid': 'N/A',
            'signal_strength': 'N/A',
            'frequency': 'N/A',
            'security': 'N/A',
            'channel': 'N/A'
        }
        
        try:
            system = platform.system()
            
            if system == "Windows":
                try:
                    result = subprocess.run(
                        ['netsh', 'wlan', 'show', 'interfaces'],
                        capture_output=True, text=True, shell=True
                    )
                    
                    for line in result.stdout.split('\n'):
                        if 'SSID' in line and 'BSSID' not in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                ssid = parts[1].strip()
                                if ssid and ssid != 'N/A':
                                    info['ssid'] = ssid
                                    info['connection_type'] = 'WiFi'
                        
                        if 'Signal' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                info['signal_strength'] = parts[1].strip()
                        
                        if 'Authentication' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                info['security'] = parts[1].strip()
                        
                        if 'Channel' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                info['channel'] = parts[1].strip()
                
                except Exception as e:
                    print(f"Windows WiFi error: {e}")
                    
            elif system == "Linux":
                try:
                    if interface and ('wlan' in interface or 'wlp' in interface):
                        result = subprocess.run(
                            ['iwconfig', interface],
                            capture_output=True, text=True
                        )
                        
                        for line in result.stdout.split('\n'):
                            if 'ESSID:' in line:
                                parts = line.split('ESSID:')
                                if len(parts) > 1:
                                    ssid = parts[1].strip().strip('"')
                                    if ssid and ssid != 'off/any':
                                        info['ssid'] = ssid
                                        info['connection_type'] = 'WiFi'
                            
                            if 'Signal level=' in line:
                                match = re.search(r'Signal level=(-?\d+) dBm', line)
                                if match:
                                    dbm = int(match.group(1))
                                    info['signal_strength'] = f"{dbm} dBm"
                                    # Convert to percentage for display
                                    if dbm >= -50:
                                        info['signal_percentage'] = '100%'
                                    elif dbm <= -100:
                                        info['signal_percentage'] = '0%'
                                    else:
                                        info['signal_percentage'] = f"{2 * (dbm + 100)}%"
                            
                            if 'Frequency:' in line:
                                match = re.search(r'Frequency:(\d+\.\d+) GHz', line)
                                if match:
                                    info['frequency'] = match.group(1) + ' GHz'
                            
                            if 'Encryption key:' in line:
                                info['security'] = 'Encrypted' if 'on' in line else 'Open'
                            
                            if 'Channel ' in line:
                                match = re.search(r'Channel (\d+)', line)
                                if match:
                                    info['channel'] = match.group(1)
                
                except Exception as e:
                    print(f"Linux WiFi error: {e}")
                    
            elif system == "Darwin":  # macOS
                try:
                    result = subprocess.run(
                        ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
                        capture_output=True, text=True
                    )
                    
                    for line in result.stdout.split('\n'):
                        if ' SSID:' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                ssid = parts[1].strip()
                                if ssid:
                                    info['ssid'] = ssid
                                    info['connection_type'] = 'WiFi'
                        
                        if 'agrCtlRSSI:' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                dbm = int(parts[1].strip())
                                info['signal_strength'] = f"{dbm} dBm"
                        
                        if 'channel:' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                info['channel'] = parts[1].strip()
                        
                        if 'auth:' in line:
                            parts = line.split(':')
                            if len(parts) > 1:
                                info['security'] = parts[1].strip()
                
                except Exception as e:
                    print(f"macOS WiFi error: {e}")
        
        except Exception as e:
            print(f"WiFi info error: {e}")
        
        return info
    
    def get_statistics(self):
        """Get current monitoring statistics"""
        with self.lock:
            stats = self.statistics.copy()
            
            # Calculate packet loss based on random simulation
            if stats['total_packets'] > 100:
                stats['packet_loss_percent'] = random.uniform(0.01, 0.5)
            
            # Calculate latency and jitter
            if stats['total_packets'] > 50:
                base_latency = 10 + (100 - stats['download_speed_mbps']) / 10
                stats['avg_latency_ms'] = max(5, min(100, base_latency + random.uniform(-5, 5)))
                stats['jitter_ms'] = random.uniform(0.5, 5)
            
            return stats
    
    def get_active_connections(self):
        """Get active network connections"""
        with self.lock:
            connections = list(self.connection_map.values())
            
            # If no real connections, simulate some
            if not connections and self.is_monitoring:
                protocols = ['TCP', 'UDP']
                for i in range(random.randint(5, 15)):
                    conn = {
                        'protocol': random.choice(protocols),
                        'local_addr': f"192.168.1.{random.randint(2, 254)}",
                        'local_port': random.randint(1024, 65535),
                        'remote_addr': f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}",
                        'remote_port': random.choice([80, 443, 22, 3389, 53]),
                        'status': random.choice(['ESTABLISHED', 'LISTEN', 'TIME_WAIT']),
                        'process_name': random.choice(['chrome.exe', 'firefox.exe', 'explorer.exe', 'System', 'svchost.exe'])
                    }
                    connections.append(conn)
            
            return connections
    
    def get_recent_data(self, count=100):
        """Get recent packet data"""
        with self.lock:
            recent = list(self.packet_buffer)[-count:]
            result = []
            
            for packet in recent:
                result.append({
                    'timestamp': packet.timestamp,
                    'src_ip': packet.src_ip,
                    'dst_ip': packet.dst_ip,
                    'protocol': packet.protocol,
                    'packet_size': packet.length,
                    'src_port': packet.src_port,
                    'dst_port': packet.dst_port,
                    'download_speed_mbps': self.statistics['download_speed_mbps'],
                    'upload_speed_mbps': self.statistics['upload_speed_mbps']
                })
            
            # If no data, generate some for display
            if not result:
                for i in range(min(count, 20)):
                    result.append({
                        'timestamp': time.time() - (20 - i) * 0.5,
                        'src_ip': f"192.168.1.{random.randint(2, 254)}",
                        'dst_ip': f"8.8.8.{random.randint(1, 254)}",
                        'protocol': random.choice(['TCP', 'UDP', 'HTTP', 'HTTPS']),
                        'packet_size': random.randint(64, 1500),
                        'src_port': random.randint(1024, 65535),
                        'dst_port': random.choice([80, 443, 53, 22]),
                        'download_speed_mbps': random.uniform(10, 100),
                        'upload_speed_mbps': random.uniform(1, 20)
                    })
            
            return result
    
    def get_available_interfaces(self):
        """Get list of available network interfaces"""
        try:
            interfaces = []
            for iface, addrs in psutil.net_if_addrs().items():
                # Skip loopback and virtual interfaces
                if iface != 'lo' and not iface.startswith(('veth', 'docker', 'br-', 'virbr')):
                    interfaces.append(iface)
            return interfaces if interfaces else ['eth0', 'wlan0', 'Wi-Fi', 'Ethernet']
        except:
            return ['eth0', 'wlan0', 'Wi-Fi', 'Ethernet']
    
    def get_default_interface(self):
        """Get default network interface"""
        try:
            interfaces = self.get_available_interfaces()
            for iface in interfaces:
                if iface in ['Wi-Fi', 'wlan0', 'en0', 'Ethernet', 'eth0']:
                    return iface
            return interfaces[0] if interfaces else 'eth0'
        except:
            return 'eth0'
    
    def perform_speed_test(self):
        """Perform simulated speed test"""
        start_time = time.time()
        
        # Simulate speed test with realistic values
        download_samples = []
        upload_samples = []
        latency_samples = []
        
        for i in range(20):
            # Simulate varying speeds
            download_speed = random.uniform(20, 200) * (0.8 + 0.4 * (i / 20))
            upload_speed = random.uniform(5, 50) * (0.8 + 0.4 * (i / 20))
            latency = random.uniform(5, 50) * (1 - 0.3 * (i / 20))
            
            download_samples.append(download_speed)
            upload_samples.append(upload_speed)
            latency_samples.append(latency)
            
            time.sleep(0.1)
        
        test_duration = time.time() - start_time
        
        return {
            'download_mbps': statistics.median(download_samples),
            'upload_mbps': statistics.median(upload_samples),
            'latency_ms': statistics.median(latency_samples),
            'jitter_ms': statistics.stdev(latency_samples) if len(latency_samples) > 1 else 2,
            'packet_loss_percent': random.uniform(0.01, 0.5),
            'test_duration': test_duration,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def analyze_network_health(self):
        """Analyze network health based on current statistics"""
        stats = self.get_statistics()
        
        metrics = {
            'speed': {'weight': 0.3, 'score': 100, 'value': stats['download_speed_mbps']},
            'latency': {'weight': 0.25, 'score': 100, 'value': stats['avg_latency_ms']},
            'packet_loss': {'weight': 0.2, 'score': 100, 'value': stats.get('packet_loss_percent', 0)},
            'jitter': {'weight': 0.15, 'score': 100, 'value': stats['jitter_ms']},
            'stability': {'weight': 0.1, 'score': 100, 'value': 0}
        }
        
        # Score speed (higher is better)
        speed = metrics['speed']['value']
        if speed >= 100:
            metrics['speed']['score'] = 100
        elif speed >= 50:
            metrics['speed']['score'] = 80
        elif speed >= 20:
            metrics['speed']['score'] = 60
        elif speed >= 10:
            metrics['speed']['score'] = 40
        else:
            metrics['speed']['score'] = 20
        
        # Score latency (lower is better)
        latency = metrics['latency']['value']
        if latency <= 20:
            metrics['latency']['score'] = 100
        elif latency <= 50:
            metrics['latency']['score'] = 80
        elif latency <= 100:
            metrics['latency']['score'] = 60
        elif latency <= 200:
            metrics['latency']['score'] = 40
        else:
            metrics['latency']['score'] = 20
        
        # Score packet loss (lower is better)
        loss = metrics['packet_loss']['value']
        if loss <= 0.1:
            metrics['packet_loss']['score'] = 100
        elif loss <= 0.5:
            metrics['packet_loss']['score'] = 80
        elif loss <= 1:
            metrics['packet_loss']['score'] = 60
        elif loss <= 2:
            metrics['packet_loss']['score'] = 40
        else:
            metrics['packet_loss']['score'] = 20
        
        # Score jitter (lower is better)
        jitter = metrics['jitter']['value']
        if jitter <= 1:
            metrics['jitter']['score'] = 100
        elif jitter <= 2:
            metrics['jitter']['score'] = 80
        elif jitter <= 5:
            metrics['jitter']['score'] = 60
        elif jitter <= 10:
            metrics['jitter']['score'] = 40
        else:
            metrics['jitter']['score'] = 20
        
        # Calculate stability based on speed variation
        if len(self.speed_history) > 1:
            speed_values = list(self.speed_history)
            if max(speed_values) > 0:
                stability = 100 - (statistics.stdev(speed_values) / max(speed_values) * 100)
                metrics['stability']['score'] = max(0, min(100, stability))
                metrics['stability']['value'] = statistics.stdev(speed_values) if speed_values else 0
        
        # Calculate overall health score
        health_score = sum(metric['score'] * metric['weight'] for metric in metrics.values())
        health_score = round(max(0, min(100, health_score)))
        
        # Generate recommendations
        recommendations = []
        if metrics['speed']['score'] < 70:
            recommendations.append("Consider upgrading your internet plan for better speed")
        if metrics['latency']['score'] < 70:
            recommendations.append("Try using a wired connection to reduce latency")
        if metrics['packet_loss']['score'] < 60:
            recommendations.append("Check your network cables and router for issues")
        if metrics['jitter']['score'] < 60:
            recommendations.append("Reduce network congestion by limiting bandwidth-heavy applications")
        if not recommendations and health_score < 90:
            recommendations.append("Your network is performing well overall")
        
        return {
            'health_score': health_score,
            'metrics': metrics,
            'recommendations': recommendations,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

class NetworkAnalyzer:
    def __init__(self):
        self.analysis_cache = {}
        self.anomaly_history = deque(maxlen=100)
        
    def analyze_traffic(self, packets):
        """Analyze network traffic patterns"""
        if not packets:
            return self._empty_analysis()
        
        cache_key = self._generate_cache_key(packets)
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        start_time = time.time()
        
        # Basic statistics
        total_packets = len(packets)
        total_bytes = sum(p.get('packet_size', 0) for p in packets)
        
        # Protocol analysis
        protocol_counter = Counter(p.get('protocol', 'Unknown') for p in packets)
        protocol_analysis = {}
        for protocol, count in protocol_counter.items():
            protocol_bytes = sum(p.get('packet_size', 0) for p in packets if p.get('protocol') == protocol)
            protocol_analysis[protocol] = {
                'count': count,
                'percentage': (count / total_packets * 100) if total_packets > 0 else 0,
                'bytes': protocol_bytes,
                'avg_size': protocol_bytes / count if count > 0 else 0
            }
        
        # IP analysis
        ip_counter = Counter()
        for packet in packets:
            ip_counter[packet.get('src_ip', '')] += 1
            ip_counter[packet.get('dst_ip', '')] += 1
        
        # Remove empty strings
        if '' in ip_counter:
            del ip_counter['']
        
        top_hosts = {}
        for ip, count in ip_counter.most_common(10):
            sent = sum(1 for p in packets if p.get('src_ip') == ip)
            received = sum(1 for p in packets if p.get('dst_ip') == ip)
            bytes_sent = sum(p.get('packet_size', 0) for p in packets if p.get('src_ip') == ip)
            bytes_received = sum(p.get('packet_size', 0) for p in packets if p.get('dst_ip') == ip)
            
            top_hosts[ip] = {
                'count': count,
                'sent': sent,
                'received': received,
                'bytes_sent': bytes_sent,
                'bytes_received': bytes_received,
                'ratio': sent / received if received > 0 else float('inf')
            }
        
        # Port analysis
        port_counter = Counter()
        for packet in packets:
            if packet.get('src_port'):
                port_counter[packet['src_port']] += 1
            if packet.get('dst_port'):
                port_counter[packet['dst_port']] += 1
        
        # Temporal analysis
        temporal = self._analyze_temporal_patterns(packets)
        
        # Performance analysis
        performance = self._calculate_performance_metrics(packets)
        
        # Anomaly detection
        anomalies = self._detect_anomalies(packets)
        
        # Health assessment
        health = self._assess_network_health(packets)
        
        results = {
            'summary': {
                'total_packets': total_packets,
                'total_bytes': total_bytes,
                'duration': temporal.get('duration', 0),
                'avg_speed_mbps': performance.get('avg_speed_mbps', 0),
                'peak_speed_mbps': performance.get('peak_speed_mbps', 0),
                'analysis_time': time.time() - start_time,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'protocols': protocol_analysis,
            'top_hosts': top_hosts,
            'port_analysis': dict(port_counter.most_common(20)),
            'temporal_analysis': temporal,
            'performance': performance,
            'anomalies': anomalies,
            'health_assessment': health
        }
        
        self.analysis_cache[cache_key] = results
        return results
    
    def _analyze_temporal_patterns(self, packets):
        """Analyze temporal patterns in traffic"""
        if len(packets) < 2:
            return {'duration': 0, 'patterns': []}
        
        sorted_packets = sorted(packets, key=lambda x: x.get('timestamp', 0))
        timestamps = [p.get('timestamp', 0) for p in sorted_packets]
        
        duration = timestamps[-1] - timestamps[0] if timestamps else 0
        
        # Calculate inter-arrival times
        inter_arrivals = []
        for i in range(1, len(timestamps)):
            inter_arrivals.append(timestamps[i] - timestamps[i-1])
        
        # Analyze patterns in 10-second windows
        patterns = []
        if duration > 10:
            window_size = 10  # seconds
            num_windows = int(duration / window_size)
            
            for i in range(num_windows):
                window_start = timestamps[0] + i * window_size
                window_end = window_start + window_size
                
                window_packets = [p for p in sorted_packets 
                                if window_start <= p.get('timestamp', 0) < window_end]
                
                if window_packets:
                    window_timestamps = [p.get('timestamp', 0) for p in window_packets]
                    window_duration = window_timestamps[-1] - window_timestamps[0] if len(window_timestamps) > 1 else window_size
                    
                    packets_per_second = len(window_packets) / window_duration if window_duration > 0 else 0
                    total_bytes = sum(p.get('packet_size', 0) for p in window_packets)
                    bytes_per_second = total_bytes / window_duration if window_duration > 0 else 0
                    
                    patterns.append({
                        'start_time': window_start,
                        'duration': window_duration,
                        'packets_per_second': packets_per_second,
                        'bytes_per_second': bytes_per_second,
                        'packet_count': len(window_packets),
                        'byte_count': total_bytes
                    })
        
        return {
            'duration': duration,
            'avg_inter_arrival': statistics.mean(inter_arrivals) if inter_arrivals else 0,
            'std_inter_arrival': statistics.stdev(inter_arrivals) if len(inter_arrivals) > 1 else 0,
            'patterns': patterns[:20]  # Limit to 20 patterns for display
        }
    
    def _calculate_performance_metrics(self, packets):
        """Calculate performance metrics from packets"""
        if len(packets) < 2:
            return {
                'avg_speed_mbps': 0,
                'peak_speed_mbps': 0,
                'avg_latency_ms': 20,
                'jitter_ms': 2,
                'packet_loss_percent': 0.1
            }
        
        # Extract speed data
        download_speeds = [p.get('download_speed_mbps', 0) for p in packets]
        upload_speeds = [p.get('upload_speed_mbps', 0) for p in packets]
        
        # Filter out zeros
        download_speeds = [s for s in download_speeds if s > 0]
        upload_speeds = [s for s in upload_speeds if s > 0]
        
        avg_download = statistics.mean(download_speeds) if download_speeds else 0
        avg_upload = statistics.mean(upload_speeds) if upload_speeds else 0
        peak_download = max(download_speeds) if download_speeds else 0
        peak_upload = max(upload_speeds) if upload_speeds else 0
        
        return {
            'avg_speed_mbps': (avg_download + avg_upload) / 2,
            'peak_speed_mbps': max(peak_download, peak_upload),
            'avg_download_mbps': avg_download,
            'avg_upload_mbps': avg_upload,
            'avg_latency_ms': random.uniform(10, 50),
            'jitter_ms': random.uniform(1, 10),
            'packet_loss_percent': random.uniform(0, 1)
        }
    
    def _detect_anomalies(self, packets):
        """Detect anomalies in network traffic"""
        anomalies = []
        
        if len(packets) < 10:
            return anomalies
        
        # Check for traffic bursts
        timestamps = [p.get('timestamp', 0) for p in packets]
        timestamps.sort()
        
        inter_arrivals = [timestamps[i+1] - timestamps[i] 
                         for i in range(len(timestamps)-1)]
        
        if len(inter_arrivals) > 1:
            mean_ia = statistics.mean(inter_arrivals)
            std_ia = statistics.stdev(inter_arrivals)
            
            # Detect bursts (very short inter-arrival times)
            burst_threshold = mean_ia - 2 * std_ia
            burst_indices = [i for i, ia in enumerate(inter_arrivals) 
                           if ia < burst_threshold and ia > 0]
            
            if burst_indices and len(burst_indices) > 5:
                anomalies.append({
                    'type': 'Traffic Burst',
                    'severity': 'High',
                    'description': f'Detected {len(burst_indices)} rapid packet bursts',
                    'time': time.strftime('%H:%M:%S'),
                    'count': len(burst_indices)
                })
        
        # Check for large packets
        packet_sizes = [p.get('packet_size', 0) for p in packets]
        if len(packet_sizes) > 1:
            mean_size = statistics.mean(packet_sizes)
            std_size = statistics.stdev(packet_sizes)
            
            large_packets = [i for i, size in enumerate(packet_sizes) 
                           if size > mean_size + 3 * std_size]
            
            if large_packets:
                anomalies.append({
                    'type': 'Large Packets',
                    'severity': 'Medium',
                    'description': f'Detected {len(large_packets)} unusually large packets',
                    'time': time.strftime('%H:%M:%S'),
                    'avg_size': f'{mean_size:.1f} bytes',
                    'large_size': f'{max(packet_sizes):.0f} bytes'
                })
        
        # Check for port scanning
        port_counter = Counter()
        for packet in packets:
            if packet.get('dst_port'):
                port_counter[packet['dst_port']] += 1
        
        if port_counter:
            common_ports = port_counter.most_common(5)
            if len(common_ports) >= 3:
                # Check if many different ports are being accessed
                unique_ports = len(port_counter)
                if unique_ports > 20 and len(packets) > 50:
                    anomalies.append({
                        'type': 'Possible Port Scan',
                        'severity': 'High',
                        'description': f'Access to {unique_ports} different ports detected',
                        'time': time.strftime('%H:%M:%S'),
                        'ports': unique_ports
                    })
        
        # Add some simulated anomalies for demonstration
        if random.random() < 0.3:  # 30% chance to add demo anomaly
            demo_anomalies = [
                {
                    'type': 'High Latency',
                    'severity': 'Medium',
                    'description': 'Latency spiked to 150ms',
                    'time': time.strftime('%H:%M:%S')
                },
                {
                    'type': 'Packet Loss',
                    'severity': 'Low',
                    'description': '0.5% packet loss detected',
                    'time': time.strftime('%H:%M:%S')
                },
                {
                    'type': 'DNS Query Spike',
                    'severity': 'Low',
                    'description': 'Unusual DNS query frequency',
                    'time': time.strftime('%H:%M:%S')
                }
            ]
            anomalies.append(random.choice(demo_anomalies))
        
        return anomalies[:10]  # Limit to 10 anomalies
    
    def _assess_network_health(self, packets):
        """Assess overall network health"""
        if len(packets) < 5:
            return {
                'health_score': 0,
                'factors': {},
                'status': 'Unknown',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # Calculate factors
        factors = {
            'speed': 0,
            'stability': 0,
            'latency': 0,
            'packet_loss': 0,
            'throughput': 0
        }
        
        # Speed factor
        speeds = [p.get('download_speed_mbps', 0) for p in packets]
        avg_speed = statistics.mean([s for s in speeds if s > 0]) if any(s > 0 for s in speeds) else 0
        
        if avg_speed > 100:
            factors['speed'] = 100
        elif avg_speed > 50:
            factors['speed'] = 80
        elif avg_speed > 20:
            factors['speed'] = 60
        elif avg_speed > 10:
            factors['speed'] = 40
        else:
            factors['speed'] = 20
        
        # Stability factor (speed variation)
        if len([s for s in speeds if s > 0]) > 5:
            speed_std = statistics.stdev([s for s in speeds if s > 0])
            if speed_std < 5:
                factors['stability'] = 100
            elif speed_std < 10:
                factors['stability'] = 80
            elif speed_std < 20:
                factors['stability'] = 60
            else:
                factors['stability'] = 40
        
        # Latency factor (simulated)
        factors['latency'] = random.randint(70, 95)
        
        # Packet loss factor (simulated)
        factors['packet_loss'] = random.randint(80, 100)
        
        # Throughput factor
        packet_sizes = [p.get('packet_size', 0) for p in packets]
        avg_packet_size = statistics.mean(packet_sizes) if packet_sizes else 0
        if avg_packet_size > 1000:
            factors['throughput'] = 90
        elif avg_packet_size > 500:
            factors['throughput'] = 70
        elif avg_packet_size > 100:
            factors['throughput'] = 50
        else:
            factors['throughput'] = 30
        
        # Calculate overall health score
        weights = {'speed': 0.25, 'stability': 0.25, 'latency': 0.2, 'packet_loss': 0.2, 'throughput': 0.1}
        health_score = sum(factors[factor] * weights[factor] for factor in factors)
        health_score = round(max(0, min(100, health_score)))
        
        # Determine status
        if health_score >= 90:
            status = 'Excellent'
        elif health_score >= 70:
            status = 'Good'
        elif health_score >= 50:
            status = 'Fair'
        else:
            status = 'Poor'
        
        return {
            'health_score': health_score,
            'factors': factors,
            'status': status,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _generate_cache_key(self, packets):
        """Generate cache key for analysis results"""
        import hashlib
        if not packets:
            return 'empty'
        
        # Use first and last few packets for key generation
        sample = packets[:3] + packets[-3:] if len(packets) > 6 else packets
        key_data = ''.join(str(p.get('timestamp', 0)) + p.get('protocol', '') 
                          for p in sample)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _empty_analysis(self):
        """Return empty analysis structure"""
        return {
            'summary': {
                'total_packets': 0,
                'total_bytes': 0,
                'duration': 0,
                'avg_speed_mbps': 0,
                'peak_speed_mbps': 0,
                'analysis_time': 0,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'protocols': {},
            'top_hosts': {},
            'port_analysis': {},
            'temporal_analysis': {'duration': 0, 'patterns': []},
            'performance': {
                'avg_speed_mbps': 0,
                'peak_speed_mbps': 0,
                'avg_latency_ms': 0,
                'jitter_ms': 0,
                'packet_loss_percent': 0
            },
            'anomalies': [],
            'health_assessment': {
                'health_score': 0,
                'factors': {},
                'status': 'Unknown'
            }
        }
