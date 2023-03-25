import requests
import json
import pprint

from requests.auth import HTTPBasicAuth

API_URL = 'https://api.cloudpayments.ru/'


def get_gateways():
    try:
        with open('payment_gateways.json') as f:
            return json.load(f)
    except:
        return {}


gateways = get_gateways()


# create exception
class TransactionNotFound(Exception):
    pass


def _get_transaction(invoice_id: int) -> dict:
    json = {"InvoiceId": invoice_id}
    for city in gateways["GATEWAYS"]:
        r = requests.post(API_URL + 'payments/get', json=json,
                          auth=HTTPBasicAuth(gateways["GATEWAYS"][city]["public_id"],
                                             gateways["GATEWAYS"][city]["password"]))
        if r.status_code == 200 and r.json()["Message"] != "Not found":
            return r.json()
    raise TransactionNotFound


def get_transaction_info(invoice_id: int) -> str:
    return pprint.pformat(_get_transaction(invoice_id))
