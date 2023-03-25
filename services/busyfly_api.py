import base64
import logging
import os
from collections import Counter, defaultdict
from io import BytesIO
import requests
from datetime import datetime

__admin_auth_token = os.environ['ADMIN_API']
__api_url = 'https://api.busy-fly.com/api/v1'
__basic_headers = {
    'authorization': 'Bearer ' + __admin_auth_token,
    'accept-language': 'ru'}


def get(path: str) -> requests.Response:
    return requests.get(__api_url + path, headers=__basic_headers)


def patch(path: str, payload: dict) -> requests.Response:
    return requests.patch(__api_url + path, payload, headers=__basic_headers)


def post(path: str, payload: dict) -> requests.Response:
    return requests.post(__api_url + path, json=payload, headers=__basic_headers)


def get_unit(unit_name: str) -> dict:
    r = get(f"/unit?per-page=25&page=1&UnitSearch%5Bname%5D={unit_name}&expand=unitModel,unitType,lastMsgUnit,endUser,"
            f"activeOrder,endUserPricePlans,"
            f"activeOrder.endUserOrderIntervals,unitModel.project,address,speed,sats,gsm,unitIsInService,"
            f"activeOrder.currency_code,height,availabilityStatus,lbsLac,lbsCountryCode,lbsOperatorId,lbsCellId,"
            f"hwModel")
    data = r.json()
    if len(data) != 0:
        return data[0]
    else:
        raise Exception("At least one unit was expected")


# TODO: UNIT NAME or UNIT ID CHECK
def get_last_unit_images(unit_name: str, orders_count: int) -> list:  # unitid real system
    images = []
    r = get(f"/end-user-order?per-page={orders_count}&page=1&EndUserOrderSearch"
            f"%5Bunit_name%5D={unit_name}&EndUserOrderSearch%5Bstatus%5D=finished"
            f"&EndUserOrderSearch[finish_by_source]=client&sort=&fields=id&expand=unitImagesShort")
    data = r.json()
    if len(data) > 0:
        for entry in data:
            for j in entry["unitImagesShort"]:
                o = get(f'/order/{entry["id"]}/image/{j["id"]}').json()["image"]
                images.append(BytesIO(base64.b64decode(o)))
        return images
    else:
        raise Exception("No entries are found")


def get_project_earnings(days_offset: int) -> dict:
    curr_date = datetime.today()

    if curr_date.day - days_offset > 0:
        start_time = datetime(curr_date.year, curr_date.month, curr_date.day - days_offset, 0, 0, 0, 0)
        end_time = datetime(curr_date.year, curr_date.month, curr_date.day - days_offset, 23, 59, 59, 0)

        r = get(
            f"/end-user-order?per-page=5000&page=1"
            f"&EndUserOrderSearch%5Bstatus%5D=finished"
            f"&EndUserOrderSearch%5Bstart_time_from%5D={int(start_time.timestamp())}"
            f"&EndUserOrderSearch%5Bstart_time_to%5D={int(end_time.timestamp())}")

        data = r.json()
        earnings_sum = sum((entry["total_price"] for entry in data))

        result = {"total": earnings_sum,
                  "orders": len(data),
                  "date": end_time}

        return result
    else:
        raise Exception("days_offset should be positive")


# TODO: fixcolhoz
def get_active_rides():
    r = get(f"/unit?per-page=999999&page=1&UnitSearch%5Bunit_type%5D=electric-scooter"
            f"&UnitSearch%5Bunit_status_id%5D=1"
            f"&fields=name,status_order,calculated_region_name,unit_status_id")

    data = r.json()
    active_rides_by_region = defaultdict(int)

    for entry in data:
        if entry["status_order"] == "active":
            active_rides_by_region[entry['calculated_region_name']] += 1

    total_units_by_city = Counter(unit['calculated_region_name'] for unit in data)
    return active_rides_by_region, total_units_by_city


def get_last_unit_commands(unit_id: int) -> list[dict]:
    commands = []
    r = get(f"/unit-log?per-page=10&page=1&UnitLogSearch%5Bsource_type%5D=user&UnitLogSearch%5Bunit_id%5D={unit_id})")
    data = r.json()

    for entry in data:
        commands.append({'time': entry["time"],
                         'description': entry["description"],
                         'user': entry["user_login"]})
    return commands


def send_unit_command(unit_id: int, action: str):
    url = f'/unit/{unit_id}'

    if action == 'tech_mode_on':
        payload = {"unit_status_id": 3}
    elif action == 'tech_mode_off':
        payload = {"unit_status_id": 1}
    elif action == 'beep':
        url += "/command/horn_on"
        payload = {"send": True}
    elif action == "rgb_blue":
        url += "/command/custom_command_95"
        payload = {"send": True}
    elif action == "rgb_off":
        url += "/command/custom_command_91"
        payload = {"send": True}
    elif action == "open_akb":
        url += "/command/custom_command_27"
        payload = {"send": True}
    else:
        logging.error("changeStatus || Action not found")
        raise NotImplementedError

    r = patch(url, payload)
    if r.status_code == 200:
        logging.info(f"Смена статуса самоката: \n {url} {payload}")


def send_user_notification(user_id: int, message: str):
    url = f"/end-user-send-push-batch"
    payload = {"end_user_ids": [user_id], "push_notification_text": message}
    post(url, payload)


def give_user_money(user_id: int, amount: int):
    if amount > 1000 or amount < 0:
        logging.error("give_user_money || amount is out of range")
        raise ValueError

    url = f"/end-user-change-balance"
    payload = {"id": None,
               "change_balance_action": "plus-balance",
               "currency_code": "RUB",
               "amount_in_currency": amount,
               "end_user_id": user_id}
    post(url, payload)
