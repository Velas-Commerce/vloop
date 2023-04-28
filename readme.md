# vloop.py - Automated Channel Liquidity Optimization for LND Loop Out

## Introduction

vloop.py is a Python script designed to automate channel liquidity optimization for payment processors using the Lightning Network Daemon (LND) loop out functions.

It uses a user or automatically generated csv file to determine desired loop out amounts. Note that the csv file should contain a column called " lightning" with invoice amounts in decimal bitcoin, rather than satoshis.

The script ranks available channels for loop out based on their local balance ratio, which helps to keep channels balanced and maintain optimal network routing efficiency.

This documentation is intended for not only for Bitcoin Lightning Network developers but also for enthusiasts with minimal knowledge of Python scripting.

## Installation

1. Ensure you have Python 3.6+ installed on your system. You can check your Python version by running `python --version` in your command prompt or terminal.
2. Clone or download the `vloop.py` script from the repository.
3. Install the required Python packages by running the following command in your terminal:

   ```bash
   pip install -r requirements.txt
   ```

4. Install the required Python packages by running the following command in your terminal:

```bash
    TLS_CERT_PATH=<path_to_tls_cert>
    MACAROON_PATH=<path_to_macaroon>
    INVOICE_CSV_FILE=<path_to_invoice_csv>
    RPC_SERVER=<rpc_server_address>
    NETWORK=<mainnet_or_testnet>
    LITD_TLS_CERT_PATH=<path_to_litd_tls_cert>
    CONF_TARGET=<confirmation_target>
    ADDR=<destination_address>
```

Replace the placeholder values with the appropriate information for your LND node and loop server.

## Installation

1. Clone the repository to your local machine or download the script `vloop.py`.

2. Make sure you have Python 3.6 or later installed on your system. You can check your Python version by running `python --version` or `python3 --version` in your command prompt or terminal.

3. The script uses the `venv` virtual environment. To install `venv`, run the following command:

   - For Ubuntu or Debian:
     ```bash
     sudo apt-get install python3-venv
     ```
   - For macOS:
     ```bash
     python3 -m pip install --user virtualenv
     ```
   - For Windows:
     ```powershell
     python3 -m pip install --user virtualenv
     ```

   Then, create a new virtual environment in the same directory as the script by running:

   ```bash
   python3 -m venv venv
   ```

   Activate the virtual environment by running:

- For Linux or macOS:
  ```bash
  source venv/bin/activate
  ```
- For Windows:
  ```powershell
  venv\Scripts\activate
  ```

4. Install the required Python packages in the virtual environment using the following command: `pip install -r requirements.txt` or `pip3 install -r requirements.txt`. The `requirements.txt` file should be in the same folder as `vloop.py`.

5. Set up the required environment variables in a `.env` file in the same directory as the script. Refer to the `.env.example` file provided in the repository for an example of the required variables.

## Usage

To use the `vloop.py` script, navigate to the directory containing the script and run the following command:

```bash
python3 vloop.py
```

The script will prompt you to confirm if you want to run the suggested loops. Enter y to proceed or n to exit.
