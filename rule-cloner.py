import requests
import argparse
import json


BASE_URL = "https://dashboard.signalsciences.net/api/v0"


def get_headers(api_user, api_token):
    return {
        "Content-Type": "application/json",
        "x-api-user": api_user,
        "x-api-token": api_token
    }

def fetch_resource(api_user, api_token, corp, site, resource_type, resource_name=None):
    url = f"{BASE_URL}/corps/{corp}/sites/{site}/{resource_type}"
    if resource_name:
        url += f"/{resource_name}"
    response = requests.get(url, headers=get_headers(api_user, api_token))
    response.raise_for_status()
    return response.json()

def create_resource(api_user, api_token, corp, site, resource_type, payload):
    url = f"{BASE_URL}/corps/{corp}/sites/{site}/{resource_type}"
    response = requests.post(url, headers=get_headers(api_user, api_token), json=payload)
    response.raise_for_status()
    return response.json()

def list_rules(api_user, api_token, corp, site):
    rules_data = fetch_resource(api_user, api_token, corp, site, 'rules')
    return rules_data["data"]

def copy_rule(api_user, api_token, corp, source_site, destination_site, rule_id):
    rule_data = next((r for r in list_rules(api_user, api_token, corp, source_site) if r['id'] == rule_id), None)
    if not rule_data:
        return {'error': 'Rule not found in source site.'}

    rule_data.pop('id', None)
    rule_data.pop('createdBy', None)
    rule_data.pop('created', None)
    rule_data.pop('updated', None)

    return create_resource(api_user, api_token, corp, destination_site, 'rules', rule_data)

# Argument Parsing
parser = argparse.ArgumentParser(description='Signal Sciences - Copy rule from one site to another.')
parser.add_argument('api_user', help='Email associated with the API user')
parser.add_argument('api_token', help='API token for Signal Sciences')
parser.add_argument('corp', help='Corporation ID')
parser.add_argument('--source_site', help='Source site ID')
parser.add_argument('--destination_site', help='Destination site ID')
parser.add_argument('--rule_id', help='Rule ID to copy')
parser.add_argument('--show_rules', action='store_true', help='Show all rules for the specified site')


if __name__ == "__main__":
    args = parser.parse_args()

    if args.show_rules and args.source_site:
        try:
            rules = list_rules(args.api_user, args.api_token, args.corp, args.source_site)
            for rule in rules:
                print(f"ID: {rule['id']}, Description: {rule.get('reason', 'No description available')}")
        except requests.HTTPError as e:
            print(f"Failed to list rules: {e}")

    elif args.source_site and args.destination_site and args.rule_id:
        try:
            result = copy_rule(args.api_user, args.api_token, args.corp, args.source_site, args.destination_site, args.rule_id)
            print(json.dumps(result, indent=4))
        except requests.HTTPError as e:
            print(f"Failed to copy rule: {e}")
    else:
        print("Error: Please provide the source site, destination site, and rule ID to copy a rule.")
