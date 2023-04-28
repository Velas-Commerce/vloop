import csv
import subprocess
import os
import json
from dotenv import load_dotenv
import datetime
import logging

# Configure logging
logging.basicConfig(filename='vloop.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Get environment variables for lncli
tls_cert_path = os.environ['TLS_CERT_PATH']
macaroon_path = os.environ['MACAROON_PATH']
invoice_csv_file = os.environ['INVOICE_CSV_FILE']
invoice_csv_file_expanded = os.path.expanduser(invoice_csv_file)

# Get environment variables for litd
rpc_server = os.environ['RPC_SERVER']
network = os.environ['NETWORK']
litd_tls_cert_path = os.environ['LITD_TLS_CERT_PATH']
conf_target = os.environ['CONF_TARGET']
addr = os.environ['ADDR']

# Define a function to run lncli commands


def run_lncli_command(command):
    # Build the command line arguments
    args = [
        'lncli',
        '--macaroonpath', macaroon_path,
        '--tlscertpath', tls_cert_path,
        command
    ]

    # Run the command and capture the output
    command_output = subprocess.check_output(args)

    # Parse the output as JSON
    output_json = json.loads(command_output)

    # Return the output as a JSON object
    return output_json


total_amount = 0
total_lightning = 0

# Run the lncli listchannels command and get the total amount of channel capacity
list_channels_output = run_lncli_command('listchannels')
total_capacity = sum([int(channel['capacity'])
                     for channel in list_channels_output['channels']])

# Get the list of channels and calculate the local_balance_ratio for each channel
list_channels_output = run_lncli_command('listchannels')

for channel in list_channels_output['channels']:
    # Extract the channel ID, capacity, local balance, and active status
    chan_id = channel['chan_id']  # change channel_id to chan_id
    capacity = int(channel['capacity'])
    local_balance = int(channel['local_balance'])
    active = channel['active']

    # Calculate the local_balance_ratio
    local_balance_ratio = local_balance / capacity

loop_amounts = []
with open(invoice_csv_file_expanded, 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        amount_str = row[' amount'].strip()  # strip any extra characters
        lightning_str = row[' lightning'].strip()
        if float(lightning_str) > 0:
            loop_amounts.append(float(lightning_str))
            total_amount += float(amount_str)
            total_lightning += float(lightning_str)

total_satoshis = int(sum(loop_amounts) * 100000000)

# Define an empty list to store the channels that have sufficient local balance
eligible_channels = []

# Sort channels based on local balance ratio
list_channels_output['channels'].sort(key=lambda x: float(
    x['local_balance']) / float(x['capacity']), reverse=True)

# Find eligible channels that have a local balance greater than the loop amounts
if total_satoshis < 250000:
    print("Daily income of {:,} satoshis is too low to loop".format(
        total_satoshis))
    exit()

if total_satoshis <= 5000000:
    total_loop = total_satoshis
    loop_amounts = [total_satoshis]
    loop_count = 1

    # Filter the channels based on local_balance and append to eligible_channels list
    for channel in list_channels_output['channels']:
        capacity = int(channel['capacity'])
        local_balance = int(channel['local_balance'])

        # Calculate the local_balance_ratio
        local_balance_ratio = local_balance / capacity

        if local_balance >= total_satoshis:
            eligible_channels.append({
                'chan_id': channel['chan_id'],
                'capacity': capacity,
                'local_balance': local_balance,
                'local_balance_ratio': local_balance_ratio
            })

else:
    loop_count = total_satoshis // 5000000 + (total_satoshis % 5000000 > 0)
    remainder = total_satoshis % 5000000
    amount_per_loop = total_satoshis // loop_count
    loop_amounts = [amount_per_loop] * loop_count
    for i in range(min(remainder, loop_count)):
        loop_amounts[i] += 1

    # Filter the channels based on local_balance and append to eligible_channels list
    for channel in list_channels_output['channels']:
        active = channel['active']

        # Skip the channel if it's not active
        if not active:
            continue

        capacity = int(channel['capacity'])
        local_balance = int(channel['local_balance'])

        # Calculate the local_balance_ratio
        local_balance_ratio = local_balance / capacity

        if local_balance >= max(loop_amounts):
            eligible_channels.append({
                'chan_id': channel['chan_id'],
                'capacity': capacity,
                'local_balance': local_balance,
                'local_balance_ratio': local_balance_ratio,
                'active': active
            })


# Sort eligible_channels based on local_balance_ratio
eligible_channels.sort(key=lambda x: x['local_balance_ratio'], reverse=True)

print('List of active channels with sufficient local balance (ranked by local_balance_ratio):')
print('Rank, chan_id, capacity, local_balance, local_balance_ratio, active')
for rank, channel in enumerate(eligible_channels, 1):
    chan_id = channel['chan_id']
    capacity = channel['capacity']
    local_balance = channel['local_balance']
    local_balance_ratio = channel['local_balance'] / channel['capacity']
    active = channel['active']  # Extract the active status from the channel
    print(f'{rank}, {chan_id}, {capacity}, {local_balance}, {local_balance_ratio:.6f}, {active}')

# Print an empty line for readability
print()

# Make and print a list of suggested channels for each loop
total_satoshis = sum(loop_amounts)
print(f'Total satoshis to loop out: {total_satoshis:,}')
loop_priority_rank = 1
for i, loop_amount in enumerate(loop_amounts):
    while loop_priority_rank <= len(eligible_channels):
        channel = eligible_channels[loop_priority_rank - 1]
        local_balance = channel['local_balance']
        if local_balance >= loop_amount:
            print(
                f'Loop {i+1}: {loop_amount:,} satoshis, channel {channel["chan_id"]}')
            loop_priority_rank += 1
            break
        else:
            loop_priority_rank += 1
    else:
        print(
            f'Error: no eligible channels for loop {i+1} with amount {loop_amounts[i]:,} satoshis')

# Print an empty line for readability
print()

print(f'Total amount to loop out: $ {total_amount:.2f} USD')
print(f'Total amount in lightning payments: {total_lightning} bitcoin')
print(f'Total amount in satoshis: {total_satoshis:,} satoshis')

# Ask user for verification
verification = input("Do you want to run the suggested loops? (y/n): ")

# If user verifies, run the suggested loops
if verification.lower() == 'y':
    csv_filename = 'vloop-results.csv'

    # Check if the CSV file exists; if not, create it with headers
    if not os.path.exists(csv_filename):
        with open(csv_filename, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Date', 'Time', 'Label', 'Address', 'Amount'])

    num_loops_to_run = min(len(eligible_channels), len(loop_amounts))
    for i in range(num_loops_to_run):
        loop_amount = loop_amounts[i]
        channel = eligible_channels[i]

        # Generate the label with date, time, and loop number
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d-%H%M")
        label = f"{formatted_time}-{i+1}"

        print(
            f'Sending {loop_amount:,} satoshis through channel {channel["chan_id"]}')
        # Run the loop out command with the additional parameters and the --force option
        cmd = [
            'loop', f'--rpcserver={rpc_server}', f'--network={network}', f'--tlscertpath={litd_tls_cert_path}',
            'out', '--channel', str(channel['chan_id']),
            f'--conf_target={conf_target}', '--label', label,
            f'--addr={addr}',
            '--amt', str(loop_amount),
            '--force'  # Add the --force option here
        ]

        # Run the command and capture the output
        try:
            result = subprocess.run(
                cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error while running command: {e}")
            continue

        # Print the output to the terminal
        print("Command output:", result.stdout)
        print("Command error (if any):", result.stderr)

        # Write the additional information and output to the log file
        with open('vloop.log', 'a') as log_file:
            log_file.write(f"Label: {label}\n")
            log_file.write(f"Address: {addr}\n")
            log_file.write(f"Amount: {loop_amount}\n")
            log_file.write("Command output:\n")
            log_file.write(result.stdout)
            log_file.write("Command error (if any):\n")
            log_file.write(result.stderr)

        # Append the result to the CSV file
        with open('vloop-results.csv', 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(
                [current_time.date(), current_time.time(), label, addr, loop_amount])
else:
    print("Exiting program.")
