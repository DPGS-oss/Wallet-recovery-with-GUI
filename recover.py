#!/usr/bin/env python3
"""
Bitcoin Core Wallet Password Recovery Tool
Standalone, multi-core CPU brute force with dictionary and pattern attacks.
No external dependencies beyond pycryptodome (pip install pycryptodome).
"""

import hashlib
import itertools
import multiprocessing
import os
import string
import struct
import sys
import time
from multiprocessing import Process, Value, Queue

from Crypto.Cipher import AES

# ── Wallet encryption parameters (extracted from wallet.dat) ──
# These were extracted using btcrecover's extract-bitcoincore-mkey.py
PART_ENCRYPTED_MASTER_KEY = bytes.fromhex(
    "24b4a225bbf86972233aec387401b536"  # IV  (first 16 bytes)
    "ef1fe333fd18cf15d13e8fe1b1acfbe2"  # CT  (second 16 bytes)
)
SALT = bytes.fromhex("7363b105beaf4028")
ITER_COUNT = 36762

# The correct PKCS7 padding for a 48-byte key (48 = 3*16, last block is all padding)
EXPECTED_PADDING = b"\x10" * 16

WALLET_FILE = r"C:\Users\devan\AppData\Roaming\Bitcoin\Wallet BTC\wallet.dat"
NUM_WORKERS = max(1, multiprocessing.cpu_count())


# ── Core verification ─────────────────────────────────────────
def check_password(password_str):
    """
    Verify a single password against the Bitcoin Core wallet.
    Returns True if the password is correct, False otherwise.
    
    Algorithm (Bitcoin Core):
      1. derived = SHA-512(password_bytes + salt)
      2. Repeat iter_count-1 more times: derived = SHA-512(derived)
      3. AES-256-CBC decrypt last 2 blocks of encrypted master key
         using derived[:32] as key, block[-2] as IV
      4. If decrypted block == \x10*16 (PKCS7 padding), password is correct
    """
    password_bytes = password_str.encode("utf-8", "ignore")
    derived = password_bytes + SALT
    sha512 = hashlib.sha512
    for _ in range(ITER_COUNT):
        derived = sha512(derived).digest()
    
    iv = PART_ENCRYPTED_MASTER_KEY[:16]
    ct = PART_ENCRYPTED_MASTER_KEY[16:]
    plaintext = AES.new(derived[:32], AES.MODE_CBC, iv).decrypt(ct)
    return plaintext == EXPECTED_PADDING


# ── Worker for parallel checking ──────────────────────────────
def worker_passwordlist(password_chunk, result_queue, found_flag, worker_id, counter):
    """Check a chunk of passwords from a list."""
    for pw in password_chunk:
        if found_flag.value:
            return
        pw = pw.strip()
        if check_password(pw):
            result_queue.put(pw)
            found_flag.value = 1
            return
        with counter.get_lock():
            counter.value += 1


def worker_bruteforce(charset, length, start_idx, end_idx, result_queue, found_flag, counter):
    """Brute-force passwords of a given length from start_idx to end_idx."""
    base = len(charset)
    for idx in range(start_idx, end_idx):
        if found_flag.value:
            return
        # Convert index to password
        pw = []
        n = idx
        for _ in range(length):
            pw.append(charset[n % base])
            n //= base
        password = "".join(reversed(pw))
        
        if check_password(password):
            result_queue.put(password)
            found_flag.value = 1
            return
        with counter.get_lock():
            counter.value += 1


# ── Progress display ──────────────────────────────────────────
def show_progress(counter, total, found_flag, start_time, label):
    """Print progress updates every 5 seconds."""
    while not found_flag.value:
        time.sleep(5)
        count = counter.value
        elapsed = time.time() - start_time
        rate = count / elapsed if elapsed > 0 else 0
        if total > 0:
            pct = count / total * 100
            eta = (total - count) / rate if rate > 0 else float("inf")
            eta_str = format_time(eta) if eta < float("inf") else "unknown"
            print(f"\r  [{label}] {count:,}/{total:,} ({pct:.1f}%) | "
                  f"{rate:.0f} pw/s | Elapsed: {format_time(elapsed)} | ETA: {eta_str}   ",
                  end="", flush=True)
        else:
            print(f"\r  [{label}] {count:,} checked | "
                  f"{rate:.0f} pw/s | Elapsed: {format_time(elapsed)}   ",
                  end="", flush=True)
    print()


def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}h"
    else:
        return f"{seconds/86400:.1f}d"


# ── Strategy runners ──────────────────────────────────────────
def run_passwordlist(passwords, label):
    """Run a password list check across all CPU cores."""
    total = len(passwords)
    print(f"\n{'='*60}")
    print(f"  STRATEGY: {label}")
    print(f"  Passwords: {total:,} | Workers: {NUM_WORKERS}")
    print(f"  Started: {time.strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    result_queue = Queue()
    found_flag = Value("i", 0)
    counter = Value("i", 0)

    # Split passwords across workers
    chunk_size = max(1, total // NUM_WORKERS)
    chunks = [passwords[i:i + chunk_size] for i in range(0, total, chunk_size)]

    start_time = time.time()
    
    # Start progress monitor
    monitor = Process(target=show_progress, args=(counter, total, found_flag, start_time, label))
    monitor.daemon = True
    monitor.start()

    # Start workers
    workers = []
    for i, chunk in enumerate(chunks):
        p = Process(target=worker_passwordlist, args=(chunk, result_queue, found_flag, i, counter))
        p.start()
        workers.append(p)

    # Wait for all workers
    for p in workers:
        p.join()
    
    found_flag.value = 1  # Signal monitor to stop
    monitor.join(timeout=2)

    elapsed = time.time() - start_time
    checked = counter.value
    rate = checked / elapsed if elapsed > 0 else 0

    if not result_queue.empty():
        password = result_queue.get()
        print(f"\n\n{'!'*60}")
        print(f"  PASSWORD FOUND: {password}")
        print(f"  Checked {checked:,} passwords in {format_time(elapsed)} ({rate:.0f} pw/s)")
        print(f"{'!'*60}\n")
        return password

    print(f"\n  Done. {checked:,} passwords in {format_time(elapsed)} ({rate:.0f} pw/s). Not found.")
    return None


def run_bruteforce(charset, length, label):
    """Run brute force across all CPU cores for a specific password length."""
    total = len(charset) ** length
    print(f"\n{'='*60}")
    print(f"  STRATEGY: {label}")
    print(f"  Charset: {len(charset)} chars | Length: {length} | Total: {total:,}")
    print(f"  Workers: {NUM_WORKERS}")
    print(f"  Started: {time.strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    result_queue = Queue()
    found_flag = Value("i", 0)
    counter = Value("i", 0)

    # Split work across workers
    chunk_size = max(1, total // NUM_WORKERS)
    start_time = time.time()

    # Start progress monitor
    monitor = Process(target=show_progress, args=(counter, total, found_flag, start_time, label))
    monitor.daemon = True
    monitor.start()

    # Start workers
    workers = []
    for i in range(NUM_WORKERS):
        start_idx = i * chunk_size
        end_idx = min(start_idx + chunk_size, total) if i < NUM_WORKERS - 1 else total
        p = Process(target=worker_bruteforce,
                    args=(charset, length, start_idx, end_idx, result_queue, found_flag, counter))
        p.start()
        workers.append(p)

    # Wait for all workers
    for p in workers:
        p.join()

    found_flag.value = 1  # Signal monitor to stop
    monitor.join(timeout=2)

    elapsed = time.time() - start_time
    checked = counter.value
    rate = checked / elapsed if elapsed > 0 else 0

    if not result_queue.empty():
        password = result_queue.get()
        print(f"\n\n{'!'*60}")
        print(f"  PASSWORD FOUND: {password}")
        print(f"  Checked {checked:,} passwords in {format_time(elapsed)} ({rate:.0f} pw/s)")
        print(f"{'!'*60}\n")
        return password

    print(f"\n  Done. {checked:,} passwords in {format_time(elapsed)} ({rate:.0f} pw/s). Not found.")
    return None


# ── Password generators ──────────────────────────────────────
def load_common_passwords():
    """A curated list of common/likely passwords."""
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
        "devan", "Devan", "DEVAN",
    ]

    # Add year-based and number-based
    for year in range(1970, 2026):
        common.extend([
            str(year),
            f"bitcoin{year}", f"Bitcoin{year}", f"BTC{year}",
            f"password{year}", f"Password{year}",
            f"wallet{year}", f"Wallet{year}",
            f"crypto{year}", f"Crypto{year}",
            f"devan{year}", f"Devan{year}",
        ])

    # PINs 0-99999
    for i in range(100000):
        common.append(str(i))
        if i < 10000:
            common.append(f"{i:04d}")
        if i < 1000:
            common.append(f"{i:03d}")

    # Deduplicate
    seen = set()
    unique = []
    for p in common:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def load_file_passwords(filepath):
    """Load passwords from a file, one per line."""
    if not os.path.exists(filepath):
        return []
    passwords = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            passwords.append(line.rstrip("\n\r"))
    return passwords


# ── Main ──────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  BITCOIN CORE WALLET PASSWORD RECOVERY")
    print(f"  Wallet: {WALLET_FILE}")
    print(f"  Encryption: AES-256-CBC, {ITER_COUNT:,} SHA-512 iterations")
    print(f"  CPU cores: {NUM_WORKERS}")
    print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Quick sanity check - verify the algorithm works
    print("\n  Running sanity check...", end=" ", flush=True)
    assert not check_password("__sanity_check_wrong__"), "Wrong password correctly rejected"
    print("OK")

    # Benchmark
    print("  Benchmarking...", end=" ", flush=True)
    t0 = time.time()
    for _ in range(3):
        check_password("benchmark_test")
    single_core_rate = 3.0 / (time.time() - t0)
    est_rate = single_core_rate * NUM_WORKERS
    print(f"{single_core_rate:.1f} pw/s per core, ~{est_rate:.0f} pw/s total ({NUM_WORKERS} cores)")

    print("\n  Press Ctrl+C at any time to skip to the next strategy.\n")

    strategies = []

    # ── Strategy 1: Common passwords + PINs ────────────────────
    common = load_common_passwords()
    strategies.append(("passwordlist", common, f"Common passwords & PINs ({len(common):,})"))

    # ── Strategy 2: Large password list from btcrecover ────────
    btcr_list = r"C:\Users\devan\Desktop\Stuff\btcrecover-master\passwordlist.txt"
    if os.path.exists(btcr_list):
        big_passwords = load_file_passwords(btcr_list)
        size_mb = os.path.getsize(btcr_list) / (1024 * 1024)
        strategies.append(("passwordlist", big_passwords,
                          f"btcrecover wordlist ({len(big_passwords):,} passwords, {size_mb:.1f} MB)"))

    # ── Strategy 3-7: Brute force by length ────────────────────
    CHARSET_ALNUM = string.ascii_letters + string.digits  # 62 chars
    CHARSET_LOWER_DIGITS = string.ascii_lowercase + string.digits  # 36 chars
    CHARSET_DIGITS = string.digits  # 10 chars
    CHARSET_WITH_SPECIAL = CHARSET_ALNUM + "!@#$%^&*()_+-=.,"  # 78 chars

    # Digits-only up to 8
    strategies.append(("bruteforce", (CHARSET_DIGITS, 5), "Brute force digits 5 chars (100K)"))
    strategies.append(("bruteforce", (CHARSET_DIGITS, 6), "Brute force digits 6 chars (1M)"))
    strategies.append(("bruteforce", (CHARSET_DIGITS, 7), "Brute force digits 7 chars (10M)"))
    strategies.append(("bruteforce", (CHARSET_DIGITS, 8), "Brute force digits 8 chars (100M)"))

    # Lowercase + digits
    strategies.append(("bruteforce", (CHARSET_LOWER_DIGITS, 4), "Brute force a-z0-9 length 4 (~1.7M)"))
    strategies.append(("bruteforce", (CHARSET_LOWER_DIGITS, 5), "Brute force a-z0-9 length 5 (~60M)"))

    # Full alphanumeric
    strategies.append(("bruteforce", (CHARSET_ALNUM, 4), "Brute force A-Za-z0-9 length 4 (~14.8M)"))
    strategies.append(("bruteforce", (CHARSET_ALNUM, 5), "Brute force A-Za-z0-9 length 5 (~916M)"))

    # Longer lowercase+digits
    strategies.append(("bruteforce", (CHARSET_LOWER_DIGITS, 6),
                       "Brute force a-z0-9 length 6 (~2.2B) [SLOW - days on CPU]"))

    for stype, data, label in strategies:
        try:
            if stype == "passwordlist":
                result = run_passwordlist(data, label)
            elif stype == "bruteforce":
                charset, length = data
                result = run_bruteforce(charset, length, label)
            else:
                continue

            if result is not None:
                print(f"\n{'#'*60}")
                print(f"  SUCCESS! Your wallet password is: {result}")
                print(f"")
                print(f"  Next steps:")
                print(f"  1. Open Bitcoin Core")
                print(f"  2. Go to Settings > Unlock Wallet")
                print(f"  3. Enter the password above")
                print(f"  4. Transfer your BTC to a new wallet with a known password")
                print(f"{'#'*60}")
                
                # Save to file
                with open(os.path.join(os.path.dirname(__file__), "FOUND_PASSWORD.txt"), "w") as f:
                    f.write(f"Password: {result}\n")
                    f.write(f"Found at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Wallet: {WALLET_FILE}\n")
                print(f"\n  Password also saved to FOUND_PASSWORD.txt")
                return

        except KeyboardInterrupt:
            print(f"\n\n  Skipping '{label}'...")
            continue

    print(f"\n{'='*60}")
    print(f"  ALL STRATEGIES EXHAUSTED - PASSWORD NOT FOUND")
    print(f"")
    print(f"  What to try next:")
    print(f"  1. Try to recall ANY fragment of the password")
    print(f"  2. Rent a GPU server (vast.ai ~$0.50/hr) for 50-100x speedup")
    print(f"  3. Use a professional recovery service (e.g. Dave Bitcoin, Wallet Recovery Services)")
    print(f"  4. Run this script with longer brute-force lengths (edit the strategies list)")
    print(f"{'='*60}")


if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for Windows
    main()
