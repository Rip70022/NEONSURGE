#!/usr/bin/env python3
# shit
import os
import time
import curses
import subprocess
import random
import sys
import re
from typing import List, Dict, Tuple, Optional
import signal

class NeonSurgeWifiConfigurator:
    def __init__(self) -> None:
        self.interfaces = []
        self.networks = []
        self.selected_interface = None
        self.scanning = False
        self.connected = False
        self.current_network = None
        self.stdscr = None
        self.max_y = 0
        self.max_x = 0
        self.main_win = None
        self.status_win = None
        self.info_win = None
        self.creator = "Rip70022/craxterpy"
        self.github = "https://www.github.com/Rip70022"
        
    def initialize_curses(self) -> None:
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        self.stdscr.keypad(True)
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        
    def create_windows(self) -> None:
        self.main_win = curses.newwin(self.max_y - 4, self.max_x, 0, 0)
        self.status_win = curses.newwin(4, self.max_x, self.max_y - 4, 0)
        self.main_win.box()
        self.status_win.box()
        
    def get_interfaces(self) -> List[str]:
        result = subprocess.run(['ip', 'link', 'show'], capture_output=True, text=True)
        interfaces = []
        for line in result.stdout.split('\n'):
            if ': ' in line and '<' in line and '>' in line:
                interface = line.split(': ')[1].split(':')[0]
                if 'wl' in interface:
                    interfaces.append(interface)
        return interfaces
    
    def scan_networks(self, interface: str) -> List[Dict]:
        self.animate_scanning()
        
        try:
            subprocess.run(['sudo', 'ip', 'link', 'set', interface, 'up'], check=True)
            result = subprocess.run(['sudo', 'iwlist', interface, 'scan'], capture_output=True, text=True)
            
            networks = []
            current_network = {}
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                
                if 'Cell' in line and 'Address' in line:
                    if current_network:
                        networks.append(current_network)
                    current_network = {'interface': interface}
                    mac_match = re.search(r'Address:\s*([0-9A-F:]{17})', line)
                    if mac_match:
                        current_network['mac'] = mac_match.group(1)
                
                elif 'ESSID' in line:
                    essid_match = re.search(r'ESSID:"([^"]*)"', line)
                    if essid_match:
                        current_network['essid'] = essid_match.group(1)
                
                elif 'Quality' in line:
                    quality_match = re.search(r'Quality=(\d+)/(\d+)', line)
                    if quality_match:
                        quality = int(quality_match.group(1)) / int(quality_match.group(2)) * 100
                        current_network['quality'] = int(quality)
                
                elif 'Encryption key' in line:
                    encryption_match = re.search(r'Encryption key:(on|off)', line)
                    if encryption_match:
                        current_network['encrypted'] = encryption_match.group(1) == 'on'
                
                elif 'IE: IEEE' in line and 'WPA' in line:
                    if 'encryption_type' not in current_network:
                        current_network['encryption_type'] = 'WPA'
                
                elif 'IE: WPA2' in line:
                    current_network['encryption_type'] = 'WPA2'
            
            if current_network:
                networks.append(current_network)
                
            return networks
        
        except subprocess.CalledProcessError:
            return []
    
    def animate_scanning(self) -> None:
        self.scanning = True
        for _ in range(10):
            if not self.scanning:
                break
            self.display_animation()
            time.sleep(0.2)
        self.scanning = False
    
    def display_animation(self) -> None:
        self.main_win.clear()
        self.main_win.box()
        height, width = self.main_win.getmaxyx()
        
        for i in range(5):
            y = height // 2 - 3 + i
            x_start = width // 2 - 10
            
            for j in range(20):
                char = "▓" if random.random() > 0.7 else "▒"
                color = random.randint(1, 5)
                self.main_win.addstr(y, x_start + j, char, curses.color_pair(color) | curses.A_BOLD)
        
        self.main_win.addstr(height // 2, width // 2 - 9, "SCANNING NETWORKS", curses.color_pair(2) | curses.A_BOLD)
        self.main_win.refresh()
    
    def display_header(self) -> None:
        self.main_win.clear()
        self.main_win.box()
        height, width = self.main_win.getmaxyx()
        
        title = "NEONSURGE WIFI CONFIGURATOR"
        self.main_win.addstr(1, width // 2 - len(title) // 2, title, curses.color_pair(5) | curses.A_BOLD)
        
        subtitle = "[ QUANTUM NETWORK INTERFACE ]"
        self.main_win.addstr(2, width // 2 - len(subtitle) // 2, subtitle, curses.color_pair(1))
        
        time_str = time.strftime("%H:%M:%S")
        self.main_win.addstr(1, width - len(time_str) - 3, time_str, curses.color_pair(4))
        
        creator_info = f"Created by: {self.creator}"
        self.main_win.addstr(height - 2, width - len(creator_info) - 3, creator_info, curses.color_pair(2))
        
        github_info = f"GitHub: {self.github}"
        self.main_win.addstr(height - 3, width - len(github_info) - 3, github_info, curses.color_pair(1))
        
        separator = "═" * (width - 2)
        self.main_win.addstr(3, 1, separator, curses.color_pair(1))
    
    def display_interfaces(self) -> None:
        self.display_header()
        self.main_win.addstr(5, 3, "SELECT WIRELESS INTERFACE:", curses.color_pair(2) | curses.A_BOLD)
        
        for i, interface in enumerate(self.interfaces):
            prefix = "⬤ " if interface == self.selected_interface else "○ "
            self.main_win.addstr(7 + i, 5, prefix + interface, 
                                curses.color_pair(1) | curses.A_BOLD if interface == self.selected_interface else 0)
        
        self.main_win.addstr(7 + len(self.interfaces) + 2, 3, "↑/↓: Select  |  Enter: Confirm  |  q: Quit", curses.color_pair(4))
        
        self.status_win.clear()
        self.status_win.box()
        self.status_win.addstr(1, 2, "STATUS: Ready to configure", curses.color_pair(2))
        self.status_win.addstr(2, 2, f"SYSTEM: NeonSurge v1.0 by {self.creator}", curses.color_pair(1))
        
        self.main_win.refresh()
        self.status_win.refresh()
    
    def display_networks(self) -> None:
        self.display_header()
        self.main_win.addstr(5, 3, f"NETWORKS DETECTED ON {self.selected_interface}:", curses.color_pair(2) | curses.A_BOLD)
        
        max_display = self.max_y - 15
        start_idx = 0
        
        for i, network in enumerate(self.networks[:max_display]):
            prefix = "⬤ " if network == self.current_network else "○ "
            essid = network.get('essid', 'Unknown')
            quality = network.get('quality', 0)
            encryption = "🔒" if network.get('encrypted', False) else "🔓"
            
            display_str = f"{prefix}{essid} | Signal: {quality}% | {encryption}"
            
            color = curses.color_pair(1) if network == self.current_network else 0
            if network == self.current_network:
                color |= curses.A_BOLD
                
            self.main_win.addstr(7 + i, 5, display_str, color)
            
            if network == self.current_network and 'mac' in network:
                self.main_win.addstr(7 + i, 5 + len(display_str) + 2, f"MAC: {network['mac']}", curses.color_pair(4))
        
        self.main_win.addstr(7 + min(len(self.networks), max_display) + 2, 3, 
                           "↑/↓: Select  |  Enter: Connect  |  r: Rescan  |  b: Back  |  q: Quit", curses.color_pair(4))
        
        self.status_win.clear()
        self.status_win.box()
        self.status_win.addstr(1, 2, f"STATUS: Scanning complete. Found {len(self.networks)} networks.", curses.color_pair(2))
        self.status_win.addstr(2, 2, f"INTERFACE: {self.selected_interface}", curses.color_pair(1))
        
        self.main_win.refresh()
        self.status_win.refresh()
    
    def connect_to_network(self, network: Dict) -> bool:
        if not network.get('essid'):
            return False
            
        self.display_connecting_animation()
        
        if network.get('encrypted', False):
            self.main_win.clear()
            self.main_win.box()
            self.display_header()
            
            self.main_win.addstr(10, 5, f"Enter password for {network.get('essid')}:", curses.color_pair(2))
            self.main_win.addstr(12, 5, "Password: ", curses.color_pair(1))
            
            curses.echo()
            curses.curs_set(1)
            
            password = self.main_win.getstr(12, 15, 63).decode('utf-8')
            
            curses.noecho()
            curses.curs_set(0)
            
            try:
                with open('/tmp/wifi_connect.conf', 'w') as f:
                    f.write(f'''
network={{
    ssid="{network.get('essid')}"
    psk="{password}"
}}
''')
                subprocess.run(['sudo', 'wpa_supplicant', '-B', '-i', self.selected_interface, 
                              '-c', '/tmp/wifi_connect.conf'], check=True)
                time.sleep(1)
                subprocess.run(['sudo', 'dhclient', self.selected_interface], check=True)
                
                os.remove('/tmp/wifi_connect.conf')
                return True
                
            except subprocess.CalledProcessError:
                return False
                
        else:
            try:
                subprocess.run(['sudo', 'iwconfig', self.selected_interface, 'essid', network.get('essid')], check=True)
                subprocess.run(['sudo', 'dhclient', self.selected_interface], check=True)
                return True
            except subprocess.CalledProcessError:
                return False
    
    def display_connecting_animation(self) -> None:
        for i in range(10):
            self.main_win.clear()
            self.main_win.box()
            height, width = self.main_win.getmaxyx()
            
            title = "ESTABLISHING CONNECTION"
            self.main_win.addstr(height // 2 - 5, width // 2 - len(title) // 2, title, curses.color_pair(2) | curses.A_BOLD)
            
            progress = ["[          ]",
                       "[▓         ]",
                       "[▓▓        ]",
                       "[▓▓▓       ]",
                       "[▓▓▓▓      ]",
                       "[▓▓▓▓▓     ]",
                       "[▓▓▓▓▓▓    ]",
                       "[▓▓▓▓▓▓▓   ]",
                       "[▓▓▓▓▓▓▓▓  ]",
                       "[▓▓▓▓▓▓▓▓▓ ]",
                       "[▓▓▓▓▓▓▓▓▓▓]"]
            
            bar = progress[min(i, 10)]
            self.main_win.addstr(height // 2 - 2, width // 2 - len(bar) // 2, bar, curses.color_pair(1) | curses.A_BOLD)
            
            for j in range(height - 10):
                for k in range(5):
                    if random.random() > 0.9:
                        x = random.randint(5, width - 6)
                        y = random.randint(5, height - 6)
                        char = random.choice(["♦", "●", "◆", "▲", "■"])
                        color = random.randint(1, 5)
                        self.main_win.addstr(y, x, char, curses.color_pair(color))
            
            creator_info = f"Created by: {self.creator}"
            self.main_win.addstr(height - 2, width - len(creator_info) - 3, creator_info, curses.color_pair(2))
            
            github_info = f"GitHub: {self.github}"
            self.main_win.addstr(height - 3, width - len(github_info) - 3, github_info, curses.color_pair(1))
            
            self.main_win.refresh()
            time.sleep(0.3)
    
    def display_connection_status(self, success: bool) -> None:
        self.main_win.clear()
        self.main_win.box()
        height, width = self.main_win.getmaxyx()
        
        if success:
            message = "CONNECTION ESTABLISHED"
            color = curses.color_pair(2)
            self.connected = True
        else:
            message = "CONNECTION FAILED"
            color = curses.color_pair(3)
            self.connected = False
            
        self.main_win.addstr(height // 2, width // 2 - len(message) // 2, message, color | curses.A_BOLD)
        
        if success:
            self.display_connection_details()
        
        creator_info = f"Created by: {self.creator}"
        self.main_win.addstr(height - 2, width - len(creator_info) - 3, creator_info, curses.color_pair(2))
        
        github_info = f"GitHub: {self.github}"
        self.main_win.addstr(height - 3, width - len(github_info) - 3, github_info, curses.color_pair(1))
        
        self.main_win.addstr(height - 5, width // 2 - 13, "Press any key to continue", curses.color_pair(4))
        self.main_win.refresh()
        self.main_win.getch()
    
    def display_connection_details(self) -> None:
        try:
            result = subprocess.run(['ip', 'addr', 'show', self.selected_interface], 
                                   capture_output=True, text=True)
            
            ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            ip_address = ip_match.group(1) if ip_match else "Unknown"
            
            self.main_win.addstr(self.max_y // 2 + 2, self.max_x // 2 - 15, f"IP Address: {ip_address}", curses.color_pair(1) | curses.A_BOLD)
            
            if self.current_network and 'essid' in self.current_network:
                self.main_win.addstr(self.max_y // 2 + 3, self.max_x // 2 - 15, f"Network: {self.current_network['essid']}", curses.color_pair(1))
            
            if self.current_network and 'mac' in self.current_network:
                self.main_win.addstr(self.max_y // 2 + 4, self.max_x // 2 - 15, f"Access Point MAC: {self.current_network['mac']}", curses.color_pair(1))
            
        except Exception:
            pass
    
    def run(self) -> None:
        try:
            self.initialize_curses()
            self.create_windows()
            
            self.interfaces = self.get_interfaces()
            if not self.interfaces:
                raise Exception("No wireless interfaces found")
                
            self.selected_interface = self.interfaces[0]
            self.display_interfaces()
            
            while True:
                key = self.stdscr.getch()
                
                if key == ord('q'):
                    break
                    
                if not self.networks:
                    if key == curses.KEY_UP:
                        idx = self.interfaces.index(self.selected_interface)
                        self.selected_interface = self.interfaces[max(0, idx - 1)]
                        self.display_interfaces()
                        
                    elif key == curses.KEY_DOWN:
                        idx = self.interfaces.index(self.selected_interface)
                        self.selected_interface = self.interfaces[min(len(self.interfaces) - 1, idx + 1)]
                        self.display_interfaces()
                        
                    elif key == 10:  # Enter key
                        self.networks = self.scan_networks(self.selected_interface)
                        if self.networks:
                            self.current_network = self.networks[0]
                        self.display_networks()
                        
                else:
                    if key == curses.KEY_UP and self.networks:
                        idx = self.networks.index(self.current_network)
                        self.current_network = self.networks[max(0, idx - 1)]
                        self.display_networks()
                        
                    elif key == curses.KEY_DOWN and self.networks:
                        idx = self.networks.index(self.current_network)
                        self.current_network = self.networks[min(len(self.networks) - 1, idx + 1)]
                        self.display_networks()
                        
                    elif key == ord('r'):
                        self.networks = self.scan_networks(self.selected_interface)
                        if self.networks:
                            self.current_network = self.networks[0]
                        self.display_networks()
                        
                    elif key == ord('b'):
                        self.networks = []
                        self.current_network = None
                        self.display_interfaces()
                        
                    elif key == 10 and self.current_network:  # Enter key
                        success = self.connect_to_network(self.current_network)
                        self.display_connection_status(success)
                        if not success:
                            self.display_networks()
        
        except Exception as e:
            if self.stdscr:
                curses.endwin()
            print(f"Error: {str(e)}")
            sys.exit(1)
            
        finally:
            if self.stdscr:
                curses.endwin()

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must be run as root. Please use sudo.")
        sys.exit(1)
        
    configurator = NeonSurgeWifiConfigurator()
    
    def signal_handler(sig, frame):
        if configurator.stdscr:
            curses.endwin()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    configurator.run()
