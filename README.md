# Bitcoin Core Wallet Recovery Tool

![Bitcoin Core Wallet Recovery](https://img.shields.io/badge/Bitcoin-Core-orange)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

A comprehensive desktop application for recovering Bitcoin Core wallet passwords with GPU acceleration, custom password lists, and advanced wallet analysis features.

## Screenshots

### Main Application Window
![Main Window](docs/screenshots/main_window.png)
*The main application interface showing the 4-step recovery process*

### Step 1: Extract & Verify
![Step 1](docs/screenshots/step1_extract.png)
*Upload your wallet.dat file and verify its integrity*

### Step 2: Strategy Selection
![Step 2](docs/screenshots/step2_strategy.png)
*Choose from multiple recovery strategies including custom password lists*

### Step 3: Recovery Progress
![Step 3](docs/screenshots/step3_progress.png)
*Real-time progress tracking with password checking rate*

### Step 4: Wallet Information
![Step 4](docs/screenshots/step4_wallet_info.png)
*View all addresses and balances in your wallet*

## Features

### Core Recovery
- **Multiple Recovery Strategies**: Common passwords, brute force, custom lists
- **GPU Acceleration**: OpenCL support for 50-500x faster recovery
- **Multi-Core CPU**: Utilizes all available CPU cores
- **Real-Time Progress**: Live updates with password checking rate
- **Stop/Resume**: Cancel recovery at any time

### Wallet Analysis
- **Integrity Verification**: Detect modified or fake wallet files
- **Address Extraction**: View all addresses in the wallet
- **Pywallet Integration**: Advanced wallet information (optional)

### Advanced Features
- **Custom Password Lists**: Upload your own password dictionaries
- **John the Ripper Export**: Export hashes for external cracking tools
- **Manual Entry**: Enter extracted data manually
- **Dark Theme**: Modern, easy-on-the-eyes interface

## Applications

### Personal Use
- Recover forgotten wallet passwords
- Access old Bitcoin Core wallets
- Verify wallet integrity
- Check wallet contents before recovery

### Professional Use
- Forensic analysis of Bitcoin wallets
- Wallet recovery services
- Security auditing
- Educational purposes

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows, Linux, or macOS

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/btc-wallet-recovery.git
cd btc-wallet-recovery

# Install dependencies
pip install -r requirements.txt

# Run the application
python wallet_recovery.py
```

### Optional GPU Support

```bash
# Install OpenCL for GPU acceleration
pip install pyopencl
```

### Optional Pywallet Integration

```bash
# Clone pywallet for advanced wallet features
git clone https://github.com/spesmilo/pywallet.git pywallet
```

### Optional John the Ripper

Download from [Openwall](https://www.openwall.com/john/) and add to PATH.

## Usage Guide

### Step 1: Extract & Verify

1. Click "Browse" to select your `wallet.dat` file
2. Click "Extract & Verify" to:
   - Extract the encrypted master key
   - Verify wallet integrity
   - Check for modifications
3. The extracted data will be displayed

**Manual Entry**: If you already have the key, salt, and iterations, enter them manually.

### Step 2: Choose Strategy

#### Built-in Strategies
- **Hashcat (GPU Accelerated)**: Native hashcat integration for GPU-accelerated cracking
- **BTCRecover (Advanced)**: Native btcrecover integration for advanced recovery options
- **Custom Password List**: Upload your own password dictionary
- **Common Passwords**: ~100K common passwords and PINs
- **Brute Force Digits**: 5-6 digit numbers
- **Brute Force a-z0-9**: 4-5 character alphanumeric

#### GPU-Accelerated Strategies (if GPU available)
- **A-Za-z0-9 (4 chars)**: 14.8M combinations
- **A-Za-z0-9 (5 chars)**: 916M combinations
- **a-z0-9 (6 chars)**: 2.2B combinations

#### Custom Password List
1. Click "Upload Password List"
2. Select a `.txt` file with passwords (one per line)
3. Click "Use Custom List"
4. Select the custom strategy and start recovery

### Step 3: Recovery Progress

- **Progress Bar**: Shows completion percentage
- **Password Count**: Number of passwords checked
- **Rate**: Passwords per second
- **Elapsed Time**: Time since recovery started
- **Stop Button**: Cancel recovery at any time

If the password is found:
- It will be displayed in green
- Copy to clipboard with one click
- Save immediately!

### Step 4: Wallet Information

1. Click "Refresh Wallet Info"
2. View all addresses in the wallet
3. Note: Requires pywallet installation

## Hashcat Integration

Hashcat is natively integrated into the application for GPU-accelerated password recovery.

### Using Hashcat

1. Extract wallet data (Step 1)
2. Select "Hashcat (GPU Accelerated)" strategy in Step 2
3. Optionally upload a custom password list
4. Start recovery

Hashcat will run directly with GPU acceleration if available, providing much faster recovery speeds compared to CPU-based methods.

### Installing Hashcat

**Windows:**
Download from [hashcat.net](https://hashcat.net/hashcat/) and add to PATH

**Linux:**
```bash
sudo apt install hashcat
```

**macOS:**
```bash
brew install hashcat
```

## BTCRecover Integration

BTCRecover is natively integrated for advanced wallet recovery options.

### Using BTCRecover

1. Extract wallet data (Step 1)
2. Select "BTCRecover (Advanced)" strategy in Step 2
3. Optionally upload a custom password list
4. Start recovery

BTCRecover provides advanced features like token-based recovery, mask attacks, and more sophisticated password patterns.

### Installing BTCRecover

```bash
git clone https://github.com/gurnec/btcrecover.git
cd btcrecover
pip install -r requirements.txt
```

## John the Ripper Integration

### Export Hash

1. Extract wallet data (Step 1)
2. Go to Step 2
3. Click "Export for John the Ripper"
4. Save the `.hash` file

### Use with John the Ripper

```bash
# Basic usage
john wallet.hash

# With custom wordlist
john --wordlist=passwords.txt wallet.hash

# Show found password
john --show wallet.hash
```

## Performance Benchmarks

| Hardware | Strategy | Rate | Time (100K) |
|----------|----------|------|-------------|
| Intel i7 (8 cores) | Common Passwords | ~150 pw/s | ~11 min |
| RTX 3090 | Common Passwords | ~8,000 pw/s | ~12 sec |
| A100 | Common Passwords | ~30,000 pw/s | ~3 sec |

## Recovery Strategies Explained

### Dictionary Attacks
Best for:
- Common passwords
- PIN codes
- Years and patterns
- Previously used passwords

### Brute Force
Best for:
- Short passwords (4-6 chars)
- Simple character sets
- When you know the length

### Custom Lists
Best for:
- Personal password history
- Leaked password databases
- Targeted wordlists
- Pattern-based passwords

## Security Considerations

### Local Use
- Your wallet never leaves your computer
- No network transmission
- Full privacy and security

### GPU Cloud Use
- Ensure trusted cloud provider
- Use encrypted storage
- Delete wallet after recovery
- Transfer BTC to new wallet immediately

## Troubleshooting

### "Encrypted master key not found"
- Ensure the wallet is encrypted
- Check if it's a Bitcoin Core wallet
- Try opening in Bitcoin Core first

### Recovery is too slow
- Use GPU acceleration (50-500x faster)
- Reduce search space
- Use custom password lists
- Try cloud GPU instances

### Pywallet not available
- Install pywallet: `git clone https://github.com/spesmilo/pywallet.git`
- Update pywallet path in code
- Use wallet.dat directly in Bitcoin Core

## File Structure

```
btc-wallet-recovery/
├── wallet_recovery.py       # Main desktop application
├── recover.py              # Command-line recovery tool
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── LICENSE                 # MIT License
├── CONTRIBUTING.md         # Contribution guidelines
├── .gitignore             # Git ignore file
└── docs/
    └── screenshots/        # Application screenshots
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for legitimate wallet recovery only. Do not use to access wallets you don't own. The developers are not responsible for any loss of funds. Always backup your wallets.

## Acknowledgments

- [btcrecover](https://github.com/gurnec/btcrecover) - Wallet extraction algorithm
- [pywallet](https://github.com/spesmilo/pywallet) - Wallet analysis tool
- [John the Ripper](https://www.openwall.com/john/) - Password cracking tool
- [pycryptodome](https://www.pycryptodome.org/) - Cryptographic library

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/btc-wallet-recovery/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/btc-wallet-recovery/discussions)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/btc-wallet-recovery&type=Date)](https://star-history.com/#yourusername/btc-wallet-recovery&Date)
