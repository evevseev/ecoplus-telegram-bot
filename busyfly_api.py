import base64
import logging
import os
from collections import Counter, defaultdict
from io import BytesIO
import requests
from datetime import datetime

server = 'https://api.busy-fly.com/api/v1'

headers = {
    'authorization': 'Bearer ' + os.environ['ADMIN_API'],
    'accept-language': 'ru'}


def get(link: str):
    r = requests.get(server + link, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        raise Exception


def patch(link: str, payload: dict):
    r = requests.patch(server + link, payload, headers=headers)
    if r.status_code == 200:
        return True
    else:
        raise Exception


def post(link: str, payload: dict):
    r = requests.post(server + link, json=payload, headers=headers)
    if r.status_code == 200 or r.status_code == 201:
        return r
    else:
        raise Exception


def getUnitInfo(unit_name: str):
    r = get(f"/unit?per-page=25&page=1&UnitSearch%5Bname%5D={unit_name}&expand=unitModel,unitType,lastMsgUnit,endUser,"
            f"activeOrder,endUserPricePlans,"
            f"activeOrder.endUserOrderIntervals,unitModel.project,address,speed,sats,gsm,unitIsInService,"
            f"activeOrder.currency_code,height,availabilityStatus,lbsLac,lbsCountryCode,lbsOperatorId,lbsCellId,"
            f"hwModel")
    if len(r) != 0:
        return r[0]
    else:
        return "err"


# TODO: UNIT NAME or UNIT ID CHECK
def getLastUnitImages(unit_name: str, orders_count: int):  # unitid real system
    l = []
    r = \
        get(f"/end-user-order?per-page={orders_count}&page=1&EndUserOrderSearch%5Bunit_name%5D={unit_name}&EndUserOrderSearch%5Bstatus%5D=finished&EndUserOrderSearch[finish_by_source]=client&sort=&fields=id&expand=unitImagesShort")
    if len(r) > 0:
        for i in r:
            for j in i["unitImagesShort"]:
                o = get(f'/order/{i["id"]}/image/{j["id"]}')["image"]
                l.append(BytesIO(base64.b64decode(o)))
        return l
    return


def getEarnings(days_offset: int):
    curr_date = datetime.today()
    if curr_date.day - days_offset > 0:  # TODO: fix this line
        start_time = datetime(curr_date.year, curr_date.month, curr_date.day - days_offset, 0, 0, 0, 0)
        end_time = datetime(curr_date.year, curr_date.month, curr_date.day - days_offset, 23, 59, 59, 0)

        start_time.timestamp()
        end_time.timestamp()

        r = get(
            f"/end-user-order?per-page=5000&page=1&EndUserOrderSearch%5Bstatus%5D=finished&EndUserOrderSearch%5Bstart_time_from%5D={int(start_time.timestamp())}&EndUserOrderSearch%5Bstart_time_to%5D={int(end_time.timestamp())}")
        sum_t = 0
        for i in r:
            sum_t += i["total_price"]
        result = {"total": sum_t,
                  "orders": len(r),
                  "date": end_time}
        return result
    return


# TODO: fixcolhoz
def get_active_rides():
    link = f"/unit?per-page=999999&page=1&UnitSearch%5Bunit_type%5D=electric-scooter&UnitSearch%5Bunit_status_id%5D=1&fields=name,status_order,calculated_region_name,unit_status_id"
    response = requests.get(server + link, headers=headers).json()
    active_rides_by_region = defaultdict(int)
    for i in response:
        if i["status_order"] == "active":
            if i['calculated_region_name'] in active_rides_by_region:
                active_rides_by_region[i['calculated_region_name']] += 1
            else:
                active_rides_by_region[i['calculated_region_name']] = 0

    total_units_by_city = Counter(unit['calculated_region_name'] for unit in response)
    return active_rides_by_region, total_units_by_city


def get_last_unit_commands(unit_id: int) -> list[dict]:
    url = f"/unit-log?per-page=10&page=1&UnitLogSearch%5Bsource_type%5D=user&UnitLogSearch%5Bunit_id%5D={unit_id}&sort="
    commands = []
    response = requests.get(server + url, headers=headers).json()
    for i in response:
        commands.append({'time': i["time"], 'description': i["description"], 'user': i["user_login"]})
    return commands


def sendUnitCommand(unit_id: int, action: str):
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
        raise NotImplementedError;

    ok = patch(url, payload)
    if ok:
        logging.info(f"Смена статуса самоката: \n {url} {payload}")



def send_user_notification(user_id: int, message: str):
    url = f"/end-user-send-push-batch"
    payload = {"end_user_ids": [user_id], "push_notification_text": message}
    ok = post(url, payload)


def give_user_money(user_id: int, amount: int):
    if amount > 1000 or amount < 0:
        logging.error("give_user_money || amount is out of range")
        raise ValueError
    url = f"/end-user-change-balance"
    payload = {"id": None, "change_balance_action": "plus-balance", "currency_code": "RUB",
               "amount_in_currency": amount, "end_user_id": user_id}
    post(url, payload)

