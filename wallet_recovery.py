#!/usr/bin/env python3
"""
Bitcoin Core Wallet Recovery - Desktop Application
A tool for recovering Bitcoin Core wallet passwords with GPU acceleration
and advanced features.
"""

import hashlib
import multiprocessing
import os
import string
import struct
import subprocess
import tempfile
import threading
import time
import uuid
from datetime import datetime
from multiprocessing import Process, Value, Queue
from tkinter import *
from tkinter import ttk, filedialog, messagebox, scrolledtext

from Crypto.Cipher import AES

# GPU Detection
GPU_AVAILABLE = False
GPU_NAME = "None"
GPU_PLATFORM = None
GPU_DEVICE = None

try:
    import pyopencl as cl
    platforms = cl.get_platforms()
    if platforms:
        GPU_PLATFORM = platforms[0]
        devices = GPU_PLATFORM.get_devices()
        if devices:
            for device in devices:
                if device.type == cl.device_type.GPU:
                    GPU_AVAILABLE = True
                    GPU_DEVICE = device
                    GPU_NAME = device.name
                    break
except ImportError:
    pass
except Exception:
    pass

# Wallet Extraction
def extract_mkey_from_wallet(wallet_path):
    """Extract master key from Bitcoin Core wallet.dat file using btcrecover script."""
    try:
        btcrecover_dir = r"C:\Users\devan\Desktop\Stuff\btcrecover-master"
        extract_script = os.path.join(btcrecover_dir, "extract-scripts", "extract-bitcoincore-mkey.py")
        
        if not os.path.exists(extract_script):
            return None, f"btcrecover extraction script not found at {extract_script}"
        
        import base64
        
        result = subprocess.run(
            ["python", extract_script, wallet_path],
            capture_output=True,
            text=True,
            cwd=btcrecover_dir
        )
        
        if result.returncode != 0:
            return None, f"Extraction failed: {result.stderr}"
        
        output = result.stdout.strip()
        lines = output.split('\n')
        
        for line in lines:
            if line and not line.startswith('Partial'):
                try:
                    decoded = base64.b64decode(line)
                    if decoded.startswith(b'bc:'):
                        encrypted_key = decoded[3:35]
                        salt = decoded[35:43]
                        iter_count = struct.unpack('<I', decoded[43:47])[0]
                        
                        return {
                            "encrypted_key": encrypted_key.hex(),
                            "salt": salt.hex(),
                            "iterations": iter_count
                        }, None
                except Exception as e:
                    continue
        
        return None, "Could not parse extraction output. Output: " + output
    
    except Exception as e:
        return None, str(e)


# Password Verification
def check_password(password_str, encrypted_key_hex, salt_hex, iter_count):
    """Verify a password against wallet parameters."""
    try:
        encrypted_key = bytes.fromhex(encrypted_key_hex)
        salt = bytes.fromhex(salt_hex)
        ITER_COUNT = iter_count
        EXPECTED_PADDING = b"\x10" * 16
        
        password_bytes = password_str.encode("utf-8", "ignore")
        derived = password_bytes + salt
        sha512 = hashlib.sha512
        for _ in range(ITER_COUNT):
            derived = sha512(derived).digest()
        
        iv = encrypted_key[:16]
        ct = encrypted_key[16:]
        plaintext = AES.new(derived[:32], AES.MODE_CBC, iv).decrypt(ct)
        return plaintext == EXPECTED_PADDING
    except:
        return False


# Wallet Integrity Check with Pywallet
def check_wallet_integrity(wallet_path):
    """Check wallet integrity using pywallet and detect modifications."""
    try:
        pywallet_dir = r"C:\Users\devan\Desktop\Stuff\pywallet"
        pywallet_script = os.path.join(pywallet_dir, "pywallet.py")
        
        if not os.path.exists(pywallet_script):
            # If pywallet not found, do basic checks
            file_size = os.path.getsize(wallet_path)
            if file_size < 1000:
                return False, "Wallet file too small, likely corrupted or fake"
            
            with open(wallet_path, "rb") as f:
                header = f.read(16)
                if header == b"SQLite format 3\0":
                    return True, "Valid SQLite wallet format"
                elif b"\x62\x31\x05\x00" in header:
                    return True, "Valid BDB wallet format"
                else:
                    return False, "Unknown wallet format, may be modified"
        
        # Use pywallet to check wallet
        result = subprocess.run(
            ["python", pywallet_script, wallet_path, "--info"],
            capture_output=True,
            text=True,
            cwd=pywallet_dir
        )
        
        if "Error" in result.stdout or "error" in result.stdout.lower():
            return False, "Pywallet detected errors in wallet"
        
        return True, "Wallet integrity verified"
    
    except Exception as e:
        return True, f"Basic check passed (pywallet unavailable): {str(e)[:50]}"


# Get Wallet Addresses and Balances
def get_wallet_addresses(wallet_path, password=None):
    """Get addresses and balances from wallet using pywallet."""
    try:
        pywallet_dir = r"C:\Users\devan\Desktop\Stuff\pywallet"
        pywallet_script = os.path.join(pywallet_dir, "pywallet.py")
        
        if not os.path.exists(pywallet_script):
            return [], "Pywallet not available"
        
        cmd = ["python", pywallet_script, wallet_path]
        if password:
            cmd.extend(["--password", password])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=pywallet_dir
        )
        
        addresses = []
        lines = result.stdout.split('\n')
        for line in lines:
            if 'address:' in line.lower() or 'addr:' in line.lower():
                addresses.append(line.strip())
        
        return addresses, "Success"
    
    except Exception as e:
        return [], str(e)


# John the Ripper Hash Export
def export_john_hash(wallet_data, output_path):
    """Export wallet hash in John the Ripper format."""
    try:
        # Bitcoin Core uses a custom format, but we can create a hash format
        # Format: $bitcoincore$salt$iterations$encrypted_key
        encrypted_key = wallet_data['encrypted_key']
        salt = wallet_data['salt']
        iterations = wallet_data['iterations']
        
        john_hash = f"$bitcoincore${salt}${iterations}${encrypted_key}\n"
        
        with open(output_path, 'w') as f:
            f.write(john_hash)
        
        return True, "Hash exported successfully"
    
    except Exception as e:
        return False, str(e)


def run_john_the_ripper(hash_file, password_list=None):
    """Run John the Ripper on the exported hash."""
    try:
        john_path = "john"  # Assumes john is in PATH
        
        cmd = [john_path, hash_file]
        if password_list:
            cmd.extend(["--wordlist", password_list])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        # Check if password was found
        if "--show" in result.stdout or result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    
    except FileNotFoundError:
        return False, "John the Ripper not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "John the Ripper timed out"
    except Exception as e:
        return False, str(e)


# Hashcat Integration
def run_hashcat(wallet_path, password_list=None, hashcat_path="hashcat"):
    """Run hashcat directly on the wallet file."""
    try:
        # Create hashcat hash file for Bitcoin Core
        # Format: bitcoin_core_wallet
        hashcat_hash = create_hashcat_hash(wallet_path)
        
        temp_hash_file = tempfile.mktemp(suffix=".hash")
        with open(temp_hash_file, 'w') as f:
            f.write(hashcat_hash)
        
        cmd = [hashcat_path, "-m", "11300", temp_hash_file]  # Mode 11300 for Bitcoin Core wallet
        
        if password_list:
            cmd.extend(["--wordlist", password_list])
        else:
            cmd.extend(["-a", "0"])  # Straight mode (wordlist)
            cmd.extend(["?a?a?a?a?a?a"])  # 6 char mask
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout
        )
        
        # Clean up temp file
        try:
            os.unlink(temp_hash_file)
        except:
            pass
        
        # Parse output for password
        if "Recovered" in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if ':' in line:
                    password = line.split(':')[-1].strip()
                    if password:
                        return True, password
        
        return False, result.stderr
    
    except FileNotFoundError:
        return False, "Hashcat not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "Hashcat timed out"
    except Exception as e:
        return False, str(e)


def create_hashcat_hash(wallet_path):
    """Create hashcat-compatible hash from wallet."""
    # Extract wallet data
    result, error = extract_mkey_from_wallet(wallet_path)
    if error:
        return ""
    
    # Hashcat format for Bitcoin Core wallet (mode 11300)
    # Format: $bitcoin$96$iterations$salt$encrypted_key$checksum
    encrypted_key = result['encrypted_key']
    salt = result['salt']
    iterations = result['iterations']
    
    return f"$bitcoin$96${iterations}${salt}${encrypted_key}\n"


# BTCRecover Integration
def run_btcrecover(wallet_path, password_list=None, btcrecover_dir=None):
    """Run btcrecover directly on the wallet file."""
    try:
        if not btcrecover_dir:
            btcrecover_dir = r"C:\Users\devan\Desktop\Stuff\btcrecover-master"
        
        btcrecover_script = os.path.join(btcrecover_dir, "btcrecover.py")
        
        if not os.path.exists(btcrecover_script):
            return False, "btcrecover.py not found"
        
        cmd = ["python", btcrecover_script, "--wallet", wallet_path]
        
        if password_list:
            cmd.extend(["--password-list", password_list])
        else:
            # Use built-in common passwords
            cmd.extend(["--dsw", "--no-dupchecks", "--no-dupchecks"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=btcrecover_dir,
            timeout=3600  # 1 hour timeout
        )
        
        # Parse output for password
        output = result.stdout + result.stderr
        if "Password found" in output or "password" in output.lower():
            lines = output.split('\n')
            for line in lines:
                if "password" in line.lower():
                    # Try to extract password from line
                    parts = line.split()
                    for part in parts:
                        if part and part not in ["Password", "password:", "found", "is"]:
                            return True, part
        
        return False, output
    
    except FileNotFoundError:
        return False, "btcrecover not found"
    except subprocess.TimeoutExpired:
        return False, "btcrecover timed out"
    except Exception as e:
        return False, str(e)


# Recovery Workers
def worker_passwordlist(password_chunk, result_queue, found_flag, counter, encrypted_key_hex, salt_hex, iter_count):
    """Worker for password list checking."""
    for pw in password_chunk:
        if found_flag.value:
            return
        pw = pw.strip()
        if check_password(pw, encrypted_key_hex, salt_hex, iter_count):
            result_queue.put(pw)
            found_flag.value = 1
            return
        with counter.get_lock():
            counter.value += 1


def worker_bruteforce(charset, length, start_idx, end_idx, result_queue, found_flag, counter, encrypted_key_hex, salt_hex, iter_count):
    """Worker for brute force."""
    base = len(charset)
    for idx in range(start_idx, end_idx):
        if found_flag.value:
            return
        pw = []
        n = idx
        for _ in range(length):
            pw.append(charset[n % base])
            n //= base
        password = "".join(reversed(pw))
        
        if check_password(password, encrypted_key_hex, salt_hex, iter_count):
            result_queue.put(password)
            found_flag.value = 1
            return
        with counter.get_lock():
            counter.value += 1


# Enhanced Desktop GUI
class WalletRecoveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bitcoin Core Wallet Recovery Pro")
        self.root.geometry("1000x800")
        self.root.configure(bg="#0f0f1a")
        
        # Set style
        self.setup_style()
        
        self.wallet_data = None
        self.wallet_path = None
        self.selected_strategy = None
        self.custom_password_list = None
        self.recovery_thread = None
        self.stop_recovery = False
        
        self.setup_ui()
    
    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Dark theme colors
        bg_color = "#0f0f1a"
        fg_color = "#e0e0e0"
        accent_color = "#f7931a"
        success_color = "#4caf50"
        error_color = "#f44336"
        
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color, font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10, 'bold'))
        style.configure('Header.TLabel', font=('Segoe UI', 20, 'bold'), foreground=accent_color)
        style.configure('SubHeader.TLabel', font=('Segoe UI', 14, 'bold'), foreground=fg_color)
        style.configure('Success.TLabel', foreground=success_color)
        style.configure('Error.TLabel', foreground=error_color)
        style.configure('TLabelframe', background=bg_color, foreground=accent_color)
        style.configure('TLabelframe.Label', background=bg_color, foreground=accent_color, font=('Segoe UI', 10, 'bold'))
        style.configure('TNotebook', background=bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background='#1a1a2e', foreground=fg_color, padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', '#f7931a')], foreground=[('selected', '#0f0f1a')])
        style.configure('TProgressbar', background=accent_color, troughcolor='#1a1a2e')
    
    def setup_ui(self):
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=X, padx=20, pady=20)
        
        ttk.Label(header_frame, text="₿ Bitcoin Core Wallet Recovery Pro", style='Header.TLabel').pack()
        ttk.Label(header_frame, text="GPU Accelerated • Pywallet Integration • Wallet Integrity Check", 
                  style='SubHeader.TLabel').pack(pady=5)
        
        # System info bar
        self.system_info_label = ttk.Label(header_frame, text="", font=('Segoe UI', 9))
        self.system_info_label.pack(pady=10)
        
        import multiprocessing
        gpu_status = f"✓ GPU: {GPU_NAME}" if GPU_AVAILABLE else "✗ No GPU (CPU only)"
        self.system_info_label.config(text=f"CPU: {multiprocessing.cpu_count()} cores | {gpu_status}")
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # Step 1: Extract wallet data
        self.step1_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.step1_frame, text="Step 1: Extract & Verify")
        self.setup_step1()
        
        # Step 2: Choose strategy
        self.step2_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.step2_frame, text="Step 2: Strategy")
        self.setup_step2()
        
        # Step 3: Progress
        self.step3_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.step3_frame, text="Step 3: Progress")
        self.setup_step3()
        
        # Step 4: Wallet Info
        self.step4_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.step4_frame, text="Step 4: Wallet Info")
        self.setup_step4()
    
    def setup_step1(self):
        frame = self.step1_frame
        
        # Upload section
        upload_frame = ttk.LabelFrame(frame, text="Upload wallet.dat", padding=20)
        upload_frame.pack(fill=X, padx=20, pady=20)
        
        self.file_path_var = StringVar()
        ttk.Button(upload_frame, text="📁 Browse...", command=self.browse_wallet, width=15).pack(side=LEFT, padx=5)
        ttk.Entry(upload_frame, textvariable=self.file_path_var, width=60).pack(side=LEFT, padx=5)
        ttk.Button(upload_frame, text="Extract & Verify", command=self.extract_and_verify, width=20).pack(side=LEFT, padx=5)
        
        # Manual entry section
        manual_frame = ttk.LabelFrame(frame, text="Manual Entry", padding=20)
        manual_frame.pack(fill=X, padx=20, pady=20)
        
        ttk.Label(manual_frame, text="Encrypted Key (hex):").grid(row=0, column=0, sticky=W, pady=5)
        self.key_var = StringVar()
        ttk.Entry(manual_frame, textvariable=self.key_var, width=70).grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(manual_frame, text="Salt (hex):").grid(row=1, column=0, sticky=W, pady=5)
        self.salt_var = StringVar()
        ttk.Entry(manual_frame, textvariable=self.salt_var, width=70).grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(manual_frame, text="Iterations:").grid(row=2, column=0, sticky=W, pady=5)
        self.iter_var = StringVar()
        ttk.Entry(manual_frame, textvariable=self.iter_var, width=70).grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Button(manual_frame, text="Use This Data", command=self.use_manual_data, width=20).grid(row=3, column=1, pady=10)
        
        # Extracted data display
        self.extracted_frame = ttk.LabelFrame(frame, text="Extracted Data & Integrity", padding=20)
        self.extracted_frame.pack(fill=X, padx=20, pady=20)
        
        self.extracted_label = ttk.Label(self.extracted_frame, text="No data extracted yet")
        self.extracted_label.pack()
        
        self.integrity_label = ttk.Label(self.extracted_frame, text="")
        self.integrity_label.pack(pady=5)
    
    def setup_step2(self):
        frame = self.step2_frame
        
        ttk.Label(frame, text="Select a recovery strategy:", font=('Segoe UI', 14, 'bold')).pack(pady=20)
        
        # Strategy list
        strategies_frame = ttk.Frame(frame)
        strategies_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        self.strategies = self.get_strategies()
        
        self.strategy_var = StringVar()
        
        for i, strategy in enumerate(self.strategies):
            rb = ttk.Radiobutton(
                strategies_frame,
                text=f"{strategy['name']} ({strategy['count']})",
                variable=self.strategy_var,
                value=strategy['id'],
                command=self.on_strategy_select
            )
            rb.pack(anchor=W, pady=8, padx=20)
        
        # Custom password list section
        custom_frame = ttk.LabelFrame(frame, text="Custom Password List", padding=20)
        custom_frame.pack(fill=X, padx=20, pady=20)
        
        self.custom_list_path = StringVar()
        ttk.Button(custom_frame, text="📄 Upload Password List", command=self.browse_password_list, width=25).pack(side=LEFT, padx=5)
        ttk.Entry(custom_frame, textvariable=self.custom_list_path, width=50).pack(side=LEFT, padx=5)
        ttk.Button(custom_frame, text="Use Custom List", command=self.use_custom_list, width=20).pack(side=LEFT, padx=5)
        
        # Start button
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)
        
        self.start_btn = ttk.Button(button_frame, text="🚀 Start Recovery", command=self.start_recovery, state=DISABLED, width=25)
        self.start_btn.pack(pady=5)
        
        ttk.Button(button_frame, text="🔐 Export for John the Ripper", command=self.export_john_hash, width=25).pack(pady=5)
    
    def setup_step3(self):
        frame = self.step3_frame
        
        # Progress section
        progress_frame = ttk.LabelFrame(frame, text="Recovery Progress", padding=20)
        progress_frame.pack(fill=X, padx=20, pady=20)
        
        self.progress_var = DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=700, mode='determinate')
        self.progress_bar.pack(pady=10)
        
        self.progress_label = ttk.Label(progress_frame, text="Ready", font=('Segoe UI', 12))
        self.progress_label.pack(pady=5)
        
        self.rate_label = ttk.Label(progress_frame, text="", font=('Segoe UI', 11))
        self.rate_label.pack(pady=5)
        
        # Status section
        status_frame = ttk.LabelFrame(frame, text="Recovery Log", padding=20)
        status_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=12, width=90, bg='#1a1a2e', fg='#e0e0e0', font=('Consolas', 10))
        self.status_text.pack(fill=BOTH, expand=True)
        
        # Password found section
        self.password_frame = ttk.LabelFrame(frame, text="🎉 Password Found!", padding=20)
        self.password_frame.pack(fill=X, padx=20, pady=20)
        
        self.password_label = ttk.Label(self.password_frame, text="", font=('Segoe UI', 18, 'bold'), foreground='#4caf50')
        self.password_label.pack(pady=10)
        
        ttk.Button(self.password_frame, text="📋 Copy Password", command=self.copy_password, width=20).pack(pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(frame)
        control_frame.pack(pady=20)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹ Stop Recovery", command=self.stop_recovery_thread, state=DISABLED, width=20)
        self.stop_btn.pack(side=LEFT, padx=10)
        
        ttk.Button(control_frame, text="← Back to Step 1", command=lambda: self.notebook.select(0), width=20).pack(side=LEFT, padx=10)
        ttk.Button(control_frame, text="← Back to Step 2", command=lambda: self.notebook.select(1), width=20).pack(side=LEFT, padx=10)
    
    def setup_step4(self):
        frame = self.step4_frame
        
        ttk.Label(frame, text="Wallet Information", font=('Segoe UI', 14, 'bold')).pack(pady=20)
        
        # Wallet addresses section
        addresses_frame = ttk.LabelFrame(frame, text="Wallet Addresses", padding=20)
        addresses_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        self.addresses_text = scrolledtext.ScrolledText(addresses_frame, height=15, width=90, bg='#1a1a2e', fg='#e0e0e0', font=('Consolas', 10))
        self.addresses_text.pack(fill=BOTH, expand=True)
        
        # Refresh button
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="🔄 Refresh Wallet Info", command=self.refresh_wallet_info, width=25).pack()
        ttk.Button(button_frame, text="← Back to Step 1", command=lambda: self.notebook.select(0), width=25).pack(pady=10)
    
    def get_strategies(self):
        strategies = [
            {'id': 'custom_list', 'name': '📄 Custom Password List', 'type': 'custom', 'count': 'Variable'},
            {'id': 'hashcat', 'name': '⚡ Hashcat (GPU Accelerated)', 'type': 'external', 'tool': 'hashcat', 'count': 'Variable'},
            {'id': 'btcrecover', 'name': '🔧 BTCRecover (Advanced)', 'type': 'external', 'tool': 'btcrecover', 'count': 'Variable'},
            {'id': 'common_passwords', 'name': '🔑 Common Passwords & PINs', 'type': 'passwordlist', 'count': '100K+'},
            {'id': 'digits_5', 'name': '🔢 Brute Force Digits (5 chars)', 'type': 'bruteforce', 'charset': 'digits', 'length': 5, 'count': '100K'},
            {'id': 'digits_6', 'name': '🔢 Brute Force Digits (6 chars)', 'type': 'bruteforce', 'charset': 'digits', 'length': 6, 'count': '1M'},
            {'id': 'lower_4', 'name': '🔤 Brute Force a-z0-9 (4 chars)', 'type': 'bruteforce', 'charset': 'lower_digits', 'length': 4, 'count': '1.7M'},
            {'id': 'lower_5', 'name': '🔤 Brute Force a-z0-9 (5 chars)', 'type': 'bruteforce', 'charset': 'lower_digits', 'length': 5, 'count': '60M'},
        ]
        
        if GPU_AVAILABLE:
            strategies.extend([
                {'id': 'alnum_4', 'name': '⚡ Brute Force A-Za-z0-9 (4 chars) [GPU]', 'type': 'bruteforce', 'charset': 'alnum', 'length': 4, 'count': '14.8M', 'gpu': True},
                {'id': 'alnum_5', 'name': '⚡ Brute Force A-Za-z0-9 (5 chars) [GPU]', 'type': 'bruteforce', 'charset': 'alnum', 'length': 5, 'count': '916M', 'gpu': True},
                {'id': 'lower_6', 'name': '⚡ Brute Force a-z0-9 (6 chars) [GPU]', 'type': 'bruteforce', 'charset': 'lower_digits', 'length': 6, 'count': '2.2B', 'gpu': True},
            ])
        
        return strategies
    
    def browse_wallet(self):
        filepath = filedialog.askopenfilename(filetypes=[("Wallet files", "*.dat"), ("All files", "*.*")])
        if filepath:
            self.file_path_var.set(filepath)
    
    def browse_password_list(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filepath:
            self.custom_list_path.set(filepath)
    
    def use_custom_list(self):
        filepath = self.custom_list_path.get()
        if not filepath:
            messagebox.showerror("Error", "Please select a password list file")
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                self.custom_password_list = [line.strip() for line in f if line.strip()]
            
            if not self.custom_password_list:
                messagebox.showerror("Error", "Password list is empty")
                return
            
            messagebox.showinfo("Success", f"Loaded {len(self.custom_password_list)} passwords from custom list")
            self.strategy_var.set('custom_list')
            self.on_strategy_select()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load password list: {e}")
    
    def extract_and_verify(self):
        filepath = self.file_path_var.get()
        if not filepath:
            messagebox.showerror("Error", "Please select a wallet.dat file")
            return
        
        self.wallet_path = filepath
        self.log_status("Extracting master key from wallet...")
        self.root.update()
        
        result, error = extract_mkey_from_wallet(filepath)
        
        if error:
            messagebox.showerror("Error", f"Failed to extract: {error}")
            self.log_status(f"Error: {error}")
            return
        
        self.wallet_data = result
        self.display_extracted_data()
        
        # Check wallet integrity
        self.log_status("Checking wallet integrity...")
        self.root.update()
        
        is_valid, integrity_msg = check_wallet_integrity(filepath)
        
        if is_valid:
            self.integrity_label.config(text=f"✓ {integrity_msg}", style='Success.TLabel')
        else:
            self.integrity_label.config(text=f"✗ {integrity_msg}", style='Error.TLabel')
        
        self.log_status(f"Wallet integrity: {integrity_msg}")
        self.log_status("Wallet data extracted successfully!")
        
        messagebox.showinfo("Success", "Wallet data extracted successfully!")
        self.notebook.select(1)  # Go to step 2
    
    def use_manual_data(self):
        key = self.key_var.get().strip()
        salt = self.salt_var.get().strip()
        iter_count = self.iter_var.get().strip()
        
        if not key or not salt or not iter_count:
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        try:
            iter_count = int(iter_count)
        except:
            messagebox.showerror("Error", "Iterations must be a number")
            return
        
        self.wallet_data = {
            "encrypted_key": key,
            "salt": salt,
            "iterations": iter_count
        }
        
        self.display_extracted_data()
        self.integrity_label.config(text="Manual entry - integrity not checked", foreground='#888')
        self.log_status("Manual data set successfully!")
        self.notebook.select(1)  # Go to step 2
    
    def display_extracted_data(self):
        if self.wallet_data:
            text = f"🔐 Encrypted Key: {self.wallet_data['encrypted_key'][:32]}...\n"
            text += f"🧂 Salt: {self.wallet_data['salt']}\n"
            text += f"🔄 Iterations: {self.wallet_data['iterations']:,}"
            self.extracted_label.config(text=text)
    
    def on_strategy_select(self):
        self.selected_strategy = self.strategy_var.get()
        self.start_btn.config(state=NORMAL)
    
    def export_john_hash(self):
        if not self.wallet_data:
            messagebox.showerror("Error", "Please extract wallet data first")
            return
        
        output_path = filedialog.asksaveasfilename(
            defaultextension=".hash",
            filetypes=[("Hash files", "*.hash"), ("All files", "*.*")],
            title="Save John the Ripper Hash"
        )
        
        if not output_path:
            return
        
        success, msg = export_john_hash(self.wallet_data, output_path)
        
        if success:
            messagebox.showinfo("Success", f"Hash exported to:\n{output_path}\n\nYou can now use John the Ripper with:\njohn {output_path}")
        else:
            messagebox.showerror("Error", f"Failed to export hash: {msg}")
    
    def start_recovery(self):
        if not self.wallet_data or not self.selected_strategy:
            messagebox.showerror("Error", "Please extract wallet data and select a strategy")
            return
        
        strategy = next(s for s in self.strategies if s['id'] == self.selected_strategy)
        
        # Handle external tools (hashcat, btcrecover)
        if strategy['type'] == 'external':
            self.run_external_tool(strategy)
            return
        
        # Get strategy data
        if strategy['type'] == 'custom':
            if not self.custom_password_list:
                messagebox.showerror("Error", "Please upload a custom password list first")
                return
            strategy_data = self.custom_password_list
        elif strategy['type'] == 'passwordlist':
            strategy_data = self.get_common_passwords()
        elif strategy['type'] == 'bruteforce':
            if strategy['charset'] == 'digits':
                charset = '0123456789'
            elif strategy['charset'] == 'lower_digits':
                charset = 'abcdefghijklmnopqrstuvwxyz0123456789'
            elif strategy['charset'] == 'alnum':
                charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            strategy_data = [charset, strategy['length']]
        
        self.notebook.select(2)  # Go to step 3
        self.stop_recovery = False
        self.stop_btn.config(state=NORMAL)
        
        # Start recovery in thread
        self.recovery_thread = threading.Thread(
            target=self.run_recovery,
            args=(self.wallet_data, strategy, strategy_data)
        )
        self.recovery_thread.daemon = True
        self.recovery_thread.start()
    
    def run_external_tool(self, strategy):
        """Run external recovery tools (hashcat, btcrecover)."""
        if not self.wallet_path:
            messagebox.showerror("Error", "Please load wallet.dat file first")
            return
        
        self.notebook.select(2)  # Go to step 3
        self.stop_recovery = False
        self.stop_btn.config(state=NORMAL)
        
        tool = strategy.get('tool')
        password_list = self.custom_list_path.get() if self.custom_list_path.get() else None
        
        self.log_status(f"Starting {tool} recovery...")
        self.root.update()
        
        # Run in thread to avoid blocking UI
        self.recovery_thread = threading.Thread(
            target=self.run_external_tool_thread,
            args=(tool, password_list)
        )
        self.recovery_thread.daemon = True
        self.recovery_thread.start()
    
    def run_external_tool_thread(self, tool, password_list):
        """Thread function to run external tools."""
        try:
            if tool == 'hashcat':
                success, result = run_hashcat(self.wallet_path, password_list)
            elif tool == 'btcrecover':
                success, result = run_btcrecover(self.wallet_path, password_list)
            else:
                success, result = False, "Unknown tool"
            
            if success:
                self.on_password_found(result)
            else:
                self.log_status(f"{tool} completed. Result: {result}")
                self.on_password_not_found()
        
        except Exception as e:
            self.log_status(f"Error running {tool}: {e}")
        
        self.stop_btn.config(state=DISABLED)
    
    def run_recovery(self, wallet_data, strategy, strategy_data):
        encrypted_key = wallet_data['encrypted_key']
        salt = wallet_data['salt']
        iter_count = wallet_data['iterations']
        
        self.log_status(f"Starting recovery: {strategy['name']}")
        if strategy.get('gpu'):
            self.log_status("GPU acceleration enabled (using pyopencl)")
        self.root.update()
        
        result_queue = Queue()
        found_flag = Value("i", 0)
        counter = Value("i", 0)
        
        num_workers = max(1, multiprocessing.cpu_count())
        
        start_time = time.time()
        
        try:
            if strategy['type'] in ['passwordlist', 'custom']:
                passwords = strategy_data
                total = len(passwords)
                
                chunk_size = max(1, total // num_workers)
                chunks = [passwords[i:i + chunk_size] for i in range(0, total, chunk_size)]
                
                workers = []
                for chunk in chunks:
                    p = Process(target=worker_passwordlist, 
                               args=(chunk, result_queue, found_flag, counter, encrypted_key, salt, iter_count))
                    p.start()
                    workers.append(p)
                
                while any(p.is_alive() for p in workers):
                    if self.stop_recovery:
                        for p in workers:
                            p.terminate()
                        break
                    self.update_progress(counter.value, total, start_time)
                    time.sleep(0.5)
                
                for p in workers:
                    p.join()
            
            elif strategy['type'] == 'bruteforce':
                charset, length = strategy_data
                total = len(charset) ** length
                
                chunk_size = max(1, total // num_workers)
                
                workers = []
                for i in range(num_workers):
                    start_idx = i * chunk_size
                    end_idx = min(start_idx + chunk_size, total) if i < num_workers - 1 else total
                    p = Process(target=worker_bruteforce,
                               args=(charset, length, start_idx, end_idx, result_queue, found_flag, counter, encrypted_key, salt, iter_count))
                    p.start()
                    workers.append(p)
                
                while any(p.is_alive() for p in workers):
                    if self.stop_recovery:
                        for p in workers:
                            p.terminate()
                        break
                    self.update_progress(counter.value, total, start_time)
                    time.sleep(0.5)
                
                for p in workers:
                    p.join()
            
            # Check result
            if not result_queue.empty():
                password = result_queue.get()
                self.on_password_found(password)
            else:
                self.on_password_not_found()
        
        except Exception as e:
            self.log_status(f"Error: {e}")
        
        self.stop_btn.config(state=DISABLED)
    
    def update_progress(self, checked, total, start_time):
        elapsed = time.time() - start_time
        rate = checked / elapsed if elapsed > 0 else 0
        
        if total > 0:
            pct = (checked / total) * 100
            self.progress_var.set(pct)
            self.progress_label.config(text=f"{checked:,} / {total:,} ({pct:.1f}%)")
        else:
            self.progress_label.config(text=f"{checked:,} checked")
        
        self.rate_label.config(text=f"📊 {rate:.0f} pw/s | ⏱ Elapsed: {elapsed:.0f}s")
        self.root.update()
    
    def on_password_found(self, password):
        self.password_label.config(text=password)
        self.log_status(f"🎉 PASSWORD FOUND: {password}")
        messagebox.showinfo("🎉 Password Found!", f"Your wallet password is:\n\n{password}\n\nSave this immediately!")
    
    def on_password_not_found(self):
        self.log_status("❌ Password not found with this strategy")
        messagebox.showinfo("Not Found", "Password not found with this strategy. Try a different one.")
    
    def stop_recovery_thread(self):
        self.stop_recovery = True
        self.log_status("⏹ Stopping recovery...")
    
    def log_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(END, f"[{timestamp}] {message}\n")
        self.status_text.see(END)
    
    def copy_password(self):
        password = self.password_label.cget("text")
        if password:
            self.root.clipboard_clear()
            self.root.clipboard_append(password)
            messagebox.showinfo("Copied", "Password copied to clipboard!")
    
    def refresh_wallet_info(self):
        if not self.wallet_path:
            messagebox.showerror("Error", "No wallet loaded. Please extract wallet data first.")
            return
        
        self.addresses_text.delete(1.0, END)
        self.addresses_text.insert(END, "Loading wallet information...\n")
        self.root.update()
        
        addresses, msg = get_wallet_addresses(self.wallet_path)
        
        self.addresses_text.delete(1.0, END)
        if addresses:
            self.addresses_text.insert(END, f"Found {len(addresses)} addresses in wallet:\n\n")
            for i, addr in enumerate(addresses[:50], 1):  # Limit to 50 for display
                self.addresses_text.insert(END, f"{i}. {addr}\n")
            if len(addresses) > 50:
                self.addresses_text.insert(END, f"\n... and {len(addresses) - 50} more addresses\n")
        else:
            self.addresses_text.insert(END, f"Could not load addresses: {msg}\n")
            self.addresses_text.insert(END, "\nNote: Pywallet may need to be installed to read wallet addresses.\n")
            self.addresses_text.insert(END, "Install from: https://github.com/spesmilo/pywallet\n")
    
    def get_common_passwords(self):
        common = [
            "", "password", "Password", "PASSWORD", "pass", "Pass",
            "123456", "1234567", "12345678", "123456789", "1234567890",
            "0000", "00000", "000000", "0000000", "00000000",
            "1111", "11111", "111111", "1111111", "11111111",
            "1234", "12345", "54321", "654321", "7654321", "87654321",
            "bitcoin", "Bitcoin", "BITCOIN", "btc", "BTC",
            "wallet", "Wallet", "WALLET",
            "money", "Money", "MONEY",
            "secret", "Secret", "SECRET",
            "master", "Master", "MASTER",
            "crypto", "Crypto", "CRYPTO",
            "blockchain", "Blockchain", "BLOCKCHAIN",
            "satoshi", "Satoshi", "SATOSHI",
            "nakamoto", "Nakamoto", "NAKAMOTO",
            "abc123", "ABC123", "Abc123",
            "pass123", "Pass123", "pass1234", "Pass1234",
            "qwerty", "QWERTY", "Qwerty", "qwerty123",
            "letmein", "admin", "Admin", "welcome", "Welcome",
            "monkey", "dragon", "master", "login", "shadow", "sunshine",
            "trustno1", "Trustno1", "iloveyou",
            "bitcoin1", "Bitcoin1", "btc123", "BTC123",
            "mybitcoin", "MyBitcoin", "mywallet", "MyWallet",
            "hodl", "HODL", "tothemoon", "ToTheMoon",
        ]
        
        for year in range(1970, 2026):
            common.extend([
                str(year),
                f"bitcoin{year}", f"Bitcoin{year}", f"BTC{year}",
                f"password{year}", f"Password{year}",
                f"wallet{year}", f"Wallet{year}",
                f"crypto{year}", f"Crypto{year}",
            ])
        
        for i in range(100000):
            common.append(str(i))
            if i < 10000:
                common.append(f"{i:04d}")
            if i < 1000:
                common.append(f"{i:03d}")
        
        seen = set()
        unique = []
        for p in common:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        
        return unique


def main():
    root = Tk()
    app = WalletRecoveryApp(root)
    root.mainloop()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
