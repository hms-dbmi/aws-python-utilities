import string
import random
from parameter_store import secret_to_ps


def populate_ps_django_secret(settings, ssm_client, environment, task, key_name, dry_run):
    vault_path = settings["VAULT_PROJECT_NAME"]

    secret_to_ps(ssm_client, vault_path + "/" + task + "/" + environment + "/django_secret", ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(25)), key_name, dry_run)


def populate_ps_auth0(settings, ssm_client, environment, task, key_name, dry_run):

    vault_path = settings["VAULT_PROJECT_NAME"] + "/" + task + "/" + environment

    secret_to_ps(ssm_client, vault_path + "/auth0_domain", settings["AUTH0_DOMAIN"], key_name, dry_run)
    secret_to_ps(ssm_client, vault_path + "/auth0_client_id", settings["AUTH0_CLIENT_ID"], key_name, dry_run)
    secret_to_ps(ssm_client, vault_path + "/auth0_secret", settings["AUTH0_SECRET"], key_name, dry_run)


def populate_ps_auth0_full(settings, ssm_client, environment, task, key_name, dry_run):

    populate_ps_auth0(settings, ssm_client, environment, task, key_name, dry_run)

    vault_path = settings["VAULT_PROJECT_NAME"] + "/" + task + "/" + environment

    secret_to_ps(ssm_client, vault_path + "/account_server_url", settings["ACCOUNT_SERVER_URL"], key_name, dry_run)
    secret_to_ps(ssm_client, vault_path + "/auth0_success_url", settings[task.upper() + "_AUTH0_SUCCESS_URL"], key_name, dry_run)
    secret_to_ps(ssm_client, vault_path + "/auth0_logout_url", settings["AUTH0_LOGOUT_URL"], key_name, dry_run)
    secret_to_ps(ssm_client, vault_path + "/auth0_callback_url", settings["AUTH0_CALLBACK_URL"], key_name, dry_run)


def populate_ps_registration_services(settings, environment, task):

    vault_path = settings["VAULT_PROJECT_NAME"] + "/" + environment

    secret_to_ps(settings, vault_path + "/auth0_success_url", settings["AUTH0_SUCCESS_URL_" + task])
    secret_to_ps(settings, vault_path + "/permission_server_url", settings["PERMISSION_SERVER_URL"])


def id_generator(size=18, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def id_generator_char(size=1, chars=string.ascii_uppercase):
    return ''.join(random.choice(chars) for _ in range(size))

