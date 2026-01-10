# LCR - Legacy Code Reviver

> **"Resurrecting broken research code with absolute Data Integrity."**

LCR (Legacy Code Reviver) is a specialized execution engine designed to safely run "abandoned" research code (e.g., Python 2.7 + OpenCV 2.4 scripts) on modern systems without modification.

## Key Features

- **Supply Chain Recovery**: Restore abandoned libraries (like OpenCV 2.4) using APT-based archive mapping.
- **Containerized Safety**: Execute legacy scripts in isolated Docker environments.
- **DI-First Architecture**: Strict separation of Read-Only inputs and Timestamped outputs, ensuring Data Integrity.

## Quick Start

### Prerequisites
- Docker Desktop (Running)
- Python 3.10+

### Installation
```bash
# Clone the repository
git clone https://github.com/Start-LCR/lcr-portfolio.git
cd lcr-portfolio

# Setup environment
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### Running the Application
```bash
python run_gui.py
```
This will launch the LCR Interface. Select your legacy script and execute.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Yusoku Advisor Godo Kaisha (ゆうそくアドバイザー合同会社)
