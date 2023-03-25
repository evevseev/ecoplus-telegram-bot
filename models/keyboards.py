from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from models.classes import actions, action_cb, days_offsetting_cb
from models.unit import get_unit_model


def get_days_keyboard(days: int):
    if days > 0:
        return InlineKeyboardMarkup().row(
            InlineKeyboardButton('⬅️', callback_data=days_offsetting_cb.new(action='before', days=days)),
            InlineKeyboardButton('➡️', callback_data=days_offsetting_cb.new(action='after', days=days))).row(
            InlineKeyboardButton('🔘', callback_data=days_offsetting_cb.new(action='today', days=days))
        )
    else:
        return InlineKeyboardMarkup().row(
            InlineKeyboardButton('⬅️', callback_data=days_offsetting_cb.new(action='before', days=days)))


def get_unit_keyboard(unit):
    admin_link = f"https://my.busy-fly.com/unit/scooter-list/{unit['id']}/view"

    unblock = InlineKeyboardButton(actions["tech_mode_on"].short_name,
                                   callback_data=action_cb.new(unitid=unit['id'], action='tech_mode_on',
                                                               unit_name=unit['name']))
    block = InlineKeyboardButton(actions["tech_mode_off"].short_name,
                                 callback_data=action_cb.new(unitid=unit['id'], action='tech_mode_off',
                                                             unit_name=unit['name']))

    beep = InlineKeyboardButton(actions["beep"].short_name,
                                callback_data=action_cb.new(unitid=unit['id'], action='beep',
                                                            unit_name=unit['name']))
    blue = InlineKeyboardButton(actions["rgb_blue"].short_name,
                                callback_data=action_cb.new(unitid=unit['id'], action='rgb_blue',
                                                            unit_name=unit['name']))

    off = InlineKeyboardButton(actions["rgb_off"].short_name,
                               callback_data=action_cb.new(unitid=unit['id'], action='rgb_off',
                                                           unit_name=unit['name']))

    akb = InlineKeyboardButton(actions["open_akb"].short_name,
                               callback_data=action_cb.new(unitid=unit['id'], action='open_akb',
                                                           unit_name=unit['name']))

    showinadmin = InlineKeyboardButton('Показать в админке', url=admin_link)

    photos = InlineKeyboardButton('Показать фото 📷',
                                  callback_data=action_cb.new(unitid=unit['id'], action='photos',
                                                              unit_name=unit['name']))

    last_commands = InlineKeyboardButton('Показать последние команды',
                                  callback_data=action_cb.new(unitid=unit['id'], action='last_commands',
                                                              unit_name=unit['name']))
    model = get_unit_model(unit['name']).name

    buttons = InlineKeyboardMarkup()
    buttons.row(beep)
    buttons.row(unblock, block)

    # if model == 'PLUS':
    #    buttons.row(blue, off)

    if model == 'PLUS' or model == 'PRO':
        buttons.row(akb)
    buttons.row(photos, last_commands)
    buttons.row(showinadmin)
    return buttons


def get_main_menu():
    return ReplyKeyboardMarkup(resize_keyboard=True).add("🟢 Активных заказов").add("💵 Выручка за день")
