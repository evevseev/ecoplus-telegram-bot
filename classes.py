from dataclasses import dataclass

from aiogram.utils.callback_data import CallbackData


@dataclass
class UnitAction:
    short_name: str
    long_name: str
    confirmation: bool


actions = {
    "tech_mode_on": UnitAction("[ВКЛ] Тех. режим", "Включить технический режим", True),
    "tech_mode_off": UnitAction("[ВЫКЛ] Тех. режим", "Выключить технический режим", False),
    "open_lock": UnitAction("Открыть замок", "Открыть замок", True),
    "open_battery": UnitAction("(PRO) Открыть АКБ", "Открыть крышку АКБ", True),
    "rgb_blue": UnitAction("🔵", "Включить 🔵 цвет", False),
    "rgb_green": UnitAction("🟢️", "Включить 🟢️ цвет", False),
    "rgb_pink": UnitAction("🟣", "Включить 🟣 цвет", False),
    "rgb_off": UnitAction("🔘", "Выключить подсветку", False),
    "open_akb": UnitAction("(PRO) Открыть АКБ", "Открыть замок АКБ", True),
    "beep": UnitAction("Подать сигнал", "Подать сигнал", False)
}

action_cb = CallbackData('unit_action', 'unitid', 'action', 'unit_name')
days_offsetting_cb = CallbackData('days_offsetting', 'action', 'days')
