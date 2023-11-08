import requests
import argparse
from rate_limit_cloner import RateLimitRuleCloner 


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


parser = argparse.ArgumentParser(description='Signal Sciences - Copy rule from one site to another.')
parser.add_argument('api_user', help='Email associated with the API user')
parser.add_argument('api_token', help='API token for Signal Sciences')
parser.add_argument('corp', help='Corporation ID')
parser.add_argument('--source_site', required=True, help='Source site ID')
parser.add_argument('--destination_site', required=True, help='Destination site ID')
parser.add_argument('--rule_id', nargs='?', help='Rule ID to copy')  # Rule ID is now optional
parser.add_argument('--show_rules', action='store_true', help='Show all rules for the specified site')


if __name__ == "__main__":
    args = parser.parse_args()

    # Instantiate the RateLimitRuleCloner class
    rate_limit_cloner = RateLimitRuleCloner(args.api_user, args.api_token, args.corp)

    if args.show_rules and args.source_site:
        try:
            rules = list_rules(args.api_user, args.api_token, args.corp, args.source_site)
            for rule in rules:
                print(f"ID: {rule['id']}, Description: {rule.get('reason', 'No description available')}")
        except requests.HTTPError as e:
            print(f"Failed to list rules: {e}")

    elif args.source_site and args.destination_site:
        rules_to_copy = []
        if args.rule_id:
            # Copy a specific rule
            rules_to_copy.append(args.rule_id)
        else:
            # Fetch all rules if no rule_id is specified
            all_rules = list_rules(args.api_user, args.api_token, args.corp, args.source_site)
            rules_to_copy = [rule['id'] for rule in all_rules]

        for rule_id in rules_to_copy:
            try:
                result = copy_rule(args.api_user, args.api_token, args.corp, args.source_site, args.destination_site, rule_id)
                print(f"Rule ID: {rule_id}, Copy Status: Success")
            except requests.HTTPError as http_error:
                if http_error.response.status_code == 400 and 'rate limit' in http_error.response.text.lower():
                    # If the rule is a rate limit rule, try copying with the RateLimitRuleCloner
                    try:
                        rule_data = rate_limit_cloner.fetch_rate_limit_rule(args.source_site, rule_id)
                        modified_rule_data = rate_limit_cloner.modify_rate_limit_rule(rule_data, args.destination_site)
                        rate_limit_cloner.curl_create_rate_limit_rule(args.destination_site, modified_rule_data)
                        print(f"Rule ID: {rule_id}, Copy Status: Success - Copied with RateLimitRuleCloner")
                    except Exception as e:
                        print(f"Rule ID: {rule_id}, Copy Status: Failed: {e}")
                else:
                    print(f"Rule ID: {rule_id}, Copy Status: Failed: {http_error}")