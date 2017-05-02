import string
import random
import hvac


def populate_vault_django_secret(settings, environment, task):
    vault_path = settings["VAULT_PROJECT_NAME"]

    secret_to_vault(settings, vault_path + "/" + task + "/" + environment + "/django_secret", ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(25)))


def populate_vault_auth0(settings, environment, task):

    vault_path = settings["VAULT_PROJECT_NAME"] + "/" + task + "/" + environment

    secret_to_vault(settings, vault_path + "/auth0_domain", settings["AUTH0_DOMAIN"])
    secret_to_vault(settings, vault_path + "/auth0_client_id", settings["AUTH0_CLIENT_ID"])
    secret_to_vault(settings, vault_path + "/auth0_secret", settings["AUTH0_SECRET"])


def populate_vault_auth0_full(settings, environment, task):

    populate_vault_auth0(settings, environment, task)

    vault_path = settings["VAULT_PROJECT_NAME"] + "/" + task + "/" + environment

    secret_to_vault(settings, vault_path + "/account_server_url", settings["ACCOUNT_SERVER_URL"])
    secret_to_vault(settings, vault_path + "/auth0_success_url", settings[task.upper() + "_AUTH0_SUCCESS_URL"])
    secret_to_vault(settings, vault_path + "/auth0_logout_url", settings["AUTH0_LOGOUT_URL"])
    secret_to_vault(settings, vault_path + "/auth0_callback_url", settings["AUTH0_CALLBACK_URL"])


def populate_vault_registration_services(settings, environment, task):

    vault_path = settings["VAULT_PROJECT_NAME"] + "/" + environment

    secret_to_vault(settings, vault_path + "/auth0_success_url", settings["AUTH0_SUCCESS_URL_" + task])
    secret_to_vault(settings, vault_path + "/permission_server_url", settings["PERMISSION_SERVER_URL"])


def secret_to_vault(settings, path, value):

    print("-----")
    print(path)
    print(value)
    print("-----")

    if settings["VAULT_DRY_RUN"] == "True":
        print("Skipped.")
    else:
        vault_client = hvac.Client(url=settings["VAULT_URL"], token=settings["VAULT_TOKEN"], verify=False)
        vault_client.write(path, value=value)
        print("Written.")


def id_generator(size=18, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def id_generator_char(size=1, chars=string.ascii_uppercase):
    return ''.join(random.choice(chars) for _ in range(size))


def populate_vault(vault_project_name, vault_url, vault_token, environment):

    REQUIRED_PASSWORDS = [
        "BIOMART_USER",
        "BIOMART",
        "I2B2PM",
        "I2B2HIVE",
        "I2B2METADATA",
        "I2B2WORKDATA",
        "I2B2SAMPLEDATA",
        "I2B2DEMODATA",
        "SEARCHAPP",
        "DEAPP",
        "TM_LZ",
        "TM_CZ",
        "TM_WZ",
        "I2B2IM"
    ]

    vault_client = hvac.Client(url=vault_url, token=vault_token)

    for required_password in REQUIRED_PASSWORDS:

        current_password = id_generator_char() + id_generator()
        current_key_name = "/secret/" + vault_project_name + '/' + environment + "/" + required_password

        vault_client.write(current_key_name, value=current_password)

