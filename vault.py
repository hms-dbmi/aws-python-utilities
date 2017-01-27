from string import Template
import hvac

def create_vault_policy(template_name, dictionary, policy_name, vault_url, vault_token):
    secret_template = open(template_name)
    substitution_result = Template(secret_template.read()).safe_substitute(dictionary)
    secret_template.close()

    # After files are created we need to run some vault commands.
    vault_client = hvac.Client(url=vault_url, token=vault_token)
    vault_client.set_policy(policy_name, substitution_result)
