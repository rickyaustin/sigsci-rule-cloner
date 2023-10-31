# Signal Sciences Rule Cloner

## Overview
The `rule-cloner.py` script is designed to interact with the Signal Sciences API to facilitate the copying of firewall rules from one site to another within the same corporation. This tool is particularly useful for managing and synchronizing WAF rules across different environments or applications.

## Features
- **List Rules**: Retrieve and display a list of all existing rules from the source site.
- **Copy Single Rule**: Copy a specified rule from the source site to the destination site by providing the rule's unique identifier.
- **Copy All Rules**: Automate the process of copying all rules from the source site to the destination site with a single command.

## Prerequisites
- Python 3
- `requests` library (install with `pip install requests`)
- Signal Sciences API credentials (API user and API token)

## Usage

### Listing Rules
To list all rules for a specified site, run the script with the `--show_rules` flag:

```sh
python3 rule-cloner.py <api_user> <api_token> <corp> --source_site <source_site_name> --show_rules

### Copying A rule
python rule-cloner.py <api_user> <api_token> <corp> --source_site <source_site_name> --destination_site <destination_site_name> --rule_id <rule_id_to_copy>


