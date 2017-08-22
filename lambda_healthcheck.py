import urllib.request


def lambda_handler(event, context):
    url_to_ping = event['url']

    r = urllib.request.urlopen(url_to_ping)

    if r.getcode() != 200:
        raise Exception('I failed!')

    return {
        'message': "No failures found."
    }
