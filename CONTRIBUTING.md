# Contributing to Bitcoin Core Wallet Recovery

Thank you for your interest in contributing to the Bitcoin Core Wallet Recovery project! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- **Clear description** of the problem
- **Steps to reproduce** the issue
- **Expected behavior**
- **Actual behavior**
- **Screenshots** if applicable
- **System information** (OS, Python version, GPU if applicable)
- **Wallet information** (Bitcoin Core version, wallet.dat version)

### Suggesting Enhancements

We appreciate suggestions for new features and improvements. When suggesting an enhancement:

- Use a clear and descriptive title
- Provide a detailed description of the enhancement
- Explain why this enhancement would be useful
- If applicable, provide examples or mockups

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and single-purpose
- Write docstrings for all functions and classes

### Testing

- Test your changes thoroughly before submitting
- Ensure the application runs without errors
- Test on different operating systems if possible
- Test with both CPU and GPU (if applicable)

## Development Setup

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/btc-wallet-recovery.git
cd btc-wallet-recovery

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_recovery.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Formatting

```bash
# Format code with black
black .

# Check for linting errors
flake8 .
```

## Project Structure

```
btc-wallet-recovery/
├── desktop_app_v2.py       # Main desktop application
├── recover.py              # Command-line recovery tool
├── app.py                  # Web application
├── templates/              # Web application templates
├── requirements.txt        # Python dependencies
├── tests/                  # Test files
├── docs/                   # Documentation
└── examples/               # Example scripts
```

## Areas for Contribution

### High Priority
- Additional recovery strategies
- More GPU acceleration kernels
- Support for other wallet types
- Performance optimizations

### Medium Priority
- Better error handling
- More comprehensive tests
- Additional documentation
- Internationalization

### Low Priority
- UI improvements
- Additional themes
- Plugin system
- Cloud deployment scripts

## Security Considerations

This project deals with cryptocurrency wallets. When contributing:

- Never commit wallet.dat files or private keys
- Never commit passwords or sensitive data
- Review all code for security vulnerabilities
- Follow responsible disclosure for security issues

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: For security-related issues only

## Code of Conduct

Be respectful and inclusive:
- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in the CONTRIBUTORS file and in release notes.

Thank you for contributing to Bitcoin Core Wallet Recovery!
