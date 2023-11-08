import subprocess
import json
import requests
import argparse


BASE_URL = "https://dashboard.signalsciences.net/api/v0"

class RateLimitRuleCloner:
    def __init__(self, api_user, api_token, corp):
        self.api_user = api_user
        self.api_token = api_token
        self.corp = corp

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "x-api-user": self.api_user,
            "x-api-token": self.api_token
        }

    def signal_exists(self, destination_site, signal_name):
        url = f"{BASE_URL}/corps/{self.corp}/sites/{destination_site}/signals/{signal_name}"
        response = requests.get(url, headers=self.get_headers())
        return response.status_code == 200

    def create_signal(self, destination_site, signal_name):
        if not self.signal_exists(destination_site, signal_name):
            url = f"{BASE_URL}/corps/{self.corp}/sites/{destination_site}/signals"
            payload = {"tagName": signal_name, "description": "Auto-created signal"}
            response = requests.post(url, headers=self.get_headers(), json=payload)
            if response.status_code == 201:
                print(f"Signal '{signal_name}' successfully created.")
            else:
                print(f"Failed to create signal '{signal_name}': {response.text}")
                response.raise_for_status()

    def fetch_rate_limit_rule(self, source_site, rule_id):
        url = f"{BASE_URL}/corps/{self.corp}/sites/{source_site}/rules/{rule_id}"
        response = requests.get(url, headers=self.get_headers())
        response.raise_for_status()
        return response.json()

    def modify_rate_limit_rule(self, rule_data, destination_site):
        # Modify the rule for the destination site
        rule_data['siteNames'] = [destination_site]
        # Remove non-copyable fields
        for field in ['id', 'createdBy', 'created', 'updated', 'siteNames']:
            rule_data.pop(field, None)
        return rule_data

    def curl_create_rate_limit_rule(self, destination_site, rule_data):
        # Check and create signals or lists if necessary
        if 'signal' in rule_data:
            self.create_signal(destination_site, rule_data['signal'])
        if 'conditions' in rule_data:
            for condition in rule_data['conditions']:
                if condition['type'] == 'multival' and 'conditions' in condition:
                    for sub_condition in condition['conditions']:
                        if sub_condition['type'] == 'single' and 'field' in sub_condition and sub_condition['field'] == 'signalType':
                            self.create_signal(destination_site, sub_condition['value'])

        # Prepare the curl command
        curl_command = [
            'curl', '-X', 'POST',
            f"{BASE_URL}/corps/{self.corp}/sites/{destination_site}/rules",
            '-H', 'Content-Type: application/json',
            '-H', f"x-api-user: {self.api_user}",
            '-H', f"x-api-token: {self.api_token}",
            '-d', json.dumps(rule_data)
        ]
        
        # Execute the curl command
        result = subprocess.run(curl_command, capture_output=True, text=True)
        if result.returncode == 0:  # Success
            print("Rule successfully created:")
            print(result.stdout)
        else:  # Error
            print("Failed to create rule:")
            print(result.stderr)

# The below part is just for direct command-line execution and testing
if __name__ == "__main__":
    # Argument Parsing
    parser = argparse.ArgumentParser(description='Signal Sciences - Clone a rate limit rule from one site to another.')
    parser.add_argument('api_user', help='Email associated with the API user')
    parser.add_argument('api_token', help='API token for Signal Sciences')
    parser.add_argument('corp', help='Corporation ID')
    parser.add_argument('--source_site', required=True, help='Source site ID')
    parser.add_argument('--destination_site', required=True, help='Destination site ID')
    parser.add_argument('rule_id', help='Rate limit rule ID to copy')

    args = parser.parse_args()
    cloner = RateLimitRuleCloner(args.api_user, args.api_token, args.corp)
    rule_data = cloner.fetch_rate_limit_rule(args.source_site, args.rule_id)
    modified_rule_data = cloner.modify_rate_limit_rule(rule_data, args.destination_site)
    cloner.curl_create_rate_limit_rule(args.destination_site, modified_rule_data)
