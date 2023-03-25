from services import busyfly_api, payment_gateways_api
import os

from models.keyboards import get_days_keyboard, get_unit_keyboard, get_main_menu

from utils.utils import is_admin, get_admins

from models.classes import actions, action_cb, days_offsetting_cb
from datetime import datetime

import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

admins = get_admins()
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

bot = Bot(token=os.environ['BOT_API'], parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())


# dp.middleware.setup(LoggingMiddleware())

class actionStatus(StatesGroup):
    wait_confirmation = State()


async def send_unit_action_confirmation(data: dict, message: types.Message):
    msg = f"Вы действительно хотите {actions[data['action']].long_name}? || #{data['unit_name']}?"
    await actionStatus.wait_confirmation.set()

    state = dp.current_state()
    await state.update_data(
        {"unitid": data['unitid'],
         "action": data['action']}
    )

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).row("✅ Да!", "❌ Отмена")
    await message.answer(msg, reply_markup=keyboard)

    logging.info(
        f"{message.chat.id} ({message.chat.full_name}) - отправлен запрос на подтверждение // {actions[data['action']].long_name} #{data['unit_name']}")


# TODO: change to chat id
async def send_unit_images(message: types.Message, unit_name: str, orders_count: int):
    photo_bytes = busyfly_api.get_last_unit_images(unit_name, orders_count)

    if photo_bytes:
        photos = types.MediaGroup()
        for i in photo_bytes:
            photos.attach_photo(InputFile(i, 'Самокат!'))
        await message.answer_media_group(photos)


# TODO: change to chat id and add func unit info
async def send_unit_details(message: types.Message, unit_name: str):
    unit = busyfly_api.get_unit(unit_name)
    if unit != "err":

        msg = f'🛴  <b>{unit["registration_number"]}</b> ({unit["status_connection"]})\n' \
              f'==   {unit["status_order_grid"]}'

        if unit["statusCombined"] == "on_charge":
            msg += " | На зарядке ⚡️ (тех. режим)"
        elif unit["statusCombined"] == "at_warehouse":
            msg += " | На складе 🏠"
        elif unit["statusCombined"] == "available":
            msg += " | Доступен 🆓"
        elif unit["statusCombined"] == "statusCombined":
            msg += " | Снят с доступа ⚠️"
        elif unit["statusCombined"] == "stolen":
            msg += " | Украден 👺👺👺👺👺️"

        msg += f'\n\n🔋  {unit["charge"]}%\n' \
               f'📡  {unit["sats"]} спутников\n\n' \
               f'<b>Последнее сообщение:</b> {int((datetime.now() - datetime.fromtimestamp(unit["last_msg_time"])).total_seconds())} сек\n'

        if unit["activeOrder"]:
            msg += f'\n{unit["activeOrder"]["end_user_price_plan_name"]}\n' \
                   f'{unit["activeOrder"]["end_user_login"]}\n' \
                   f'{unit["activeOrder"]["status"]}\n\n'

        if unit["last_order_finish_time"]:
            msg += f'<b>Последний заказ завершен:</b> {datetime.fromtimestamp(unit["last_order_finish_time"]).strftime("%Y-%m-%d %H:%M:%S")}'
        else:
            msg += f'<b>Еще не было ни одного заказа! 😴</b>'

        await message.answer_location(unit["lat"], unit["lon"])
        await message.answer(msg, reply_markup=get_unit_keyboard(unit))

    else:
        await message.answer('<b>Самокат не найден!</b>')


@dp.callback_query_handler(action_cb.filter(), state='*')
async def process_callback_btn(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    if is_admin(query.message.chat.id):
        await state.reset_state()
        data = callback_data

        if data['action'] == "beep":
            await bot.answer_callback_query(query.id, text='Звуковой сигнал включен!', show_alert=True)
            busyfly_api.send_unit_command(data['unitid'], 'beep')
            return
        elif data['action'] == 'photos':
            await query.message.answer("Загружаю фотографии...")
            await send_unit_images(query.message, data['unit_name'], 5)
        elif data['action'] == 'last_commands':
            commands = busyfly_api.get_last_unit_commands(data['unitid'])
            commands_text = ""
            for command in commands:
                commands_text += f"{command['time']} <b>{command['description']}</b> ({command['user']})\n"
            await query.message.answer(commands_text)

        elif actions[data['action']].unit_action_confirmation_callback:
            await send_unit_action_confirmation(data, query.message)
        # TODO: Добавить проверку на сущестовавание команды
        else:
            busyfly_api.send_unit_command(data['unitid'], data['action'])
            await query.message.answer(f"\n({actions[data['action']].long_name} // {data['unit_name']})",
                                       reply_markup=get_main_menu())

        await bot.answer_callback_query(query.id)


@dp.message_handler(state=actionStatus.wait_confirmation)
async def unit_action_confirmation_callback(message: types.Message, state: FSMContext):
    if is_admin(message.chat.id):
        if message.text == "✅ Да!":
            data = await state.get_data()
            busyfly_api.send_unit_command(data['unitid'], data['action'])
            await message.answer(f"\n({actions[data['action']].long_name} // {data['unitid']})",
                                 reply_markup=get_main_menu())
            await state.reset_state()

        elif message.text == "❌ Отмена":
            await message.answer("Отменил!", reply_markup=get_main_menu())
            await state.reset_state()

        else:
            await message.answer("Выберите действие!")


@dp.message_handler(commands=['send_all'])
async def send_all_users(message: types.Message):
    if is_admin(message.chat.id):
        for i in admins:
            try:
                await bot.forward_message(i, message.chat.id, message.message_id)
            except Exception as e:
                await message.reply(f"Не получилось отправиь сообщение пользователю {i}\nОшибка: {e}")


@dp.message_handler(text=['Активных заказов'])
async def get_active_orders(message: types.Message):
    if is_admin(message.chat.id):
        rides, available_by_city = busyfly_api.get_active_rides()
        available = sum(available_by_city[i] for i in available_by_city)
        msg = ""
        for key, count in available_by_city.items():
            msg += f"<b>{key}:</b> {rides[key]}/{count}\n"
        await message.answer(
            f"🔸 <b>Активных заказов</b>\n(активных/доступных)\n\n{msg}\n<i><b>Выставлено самокатов:</b> {available}</i>")
        logging.info(f"{message.chat.id} ({message.chat.username}) - смотрит активные заказы")


@dp.message_handler(text=['Выручка за день'])
async def get_earnings(message: types.Message):
    if is_admin(message.chat.id) and not (message.chat.id == 827277891):
        r = busyfly_api.get_project_earnings(0)
        await message.answer(f"{r['date'].date()}\n\n"
                             f"Выручка: {r['total']}\n"
                             f"Заказов: {r['orders']}", reply_markup=get_days_keyboard(0))


@dp.callback_query_handler(days_offsetting_cb.filter())
async def get_earnings_calendar(query: types.CallbackQuery, callback_data: dict):
    if is_admin(query.message.chat.id):
        days = int(callback_data['days'])
        action = callback_data['action']
        # TODO: if below
        if action == "before":
            days += 1
        elif action == "after":
            days -= 1
        elif action == "today":
            days = 0
        r = busyfly_api.get_project_earnings(days)
        if r:
            await bot.edit_message_text(f"{r['date'].date()}\n\n"
                                        f"Выручка: {r['total']}\n"
                                        f"Заказов: {r['orders']}",
                                        query.from_user.id,
                                        query.message.message_id,
                                        reply_markup=get_days_keyboard(days))
        else:
            await query.message.answer("Вы может просматривать статистику только за этот месяц!")


@dp.message_handler(commands=['help'])
async def get_help(message: types.Message):
    if is_admin(message.chat.id):
        await message.answer(
            "Доступные команды:\n"
            "/transaction_info - получить информацию о транзакции\n")


@dp.message_handler(commands=['transaction_info'])
async def get_transaction_info(message: types.Message):
    if is_admin(message.chat.id):
        split = message.text.split()
        if len(split) == 2:
            try:
                await message.answer(payment_gateways_api.get_transaction_info(int(split[1])))
            except payment_gateways_api.TransactionNotFound as e:
                await message.answer(f"Транзакция не найдена!")
        else:
            await message.answer("Использование: /transaction_info (id)")


@dp.message_handler(commands=['give_money'])
async def give_money(message: types.Message):
    if message.chat.id in [62863141, 317914529]:
        split = message.text.split()
        if len(split) < 3 or not split[1].isdigit() or not split[2].isdigit():
            await message.answer("Использование: /give_money (id) (amount) (reason)")
        else:
            try:
                busyfly_api.give_user_money(int(split[1]), int(split[2]))
                busyfly_api.send_user_notification(int(split[1]), f"Ваш баланс был пополнен на {split[2]} руб.")
                await message.answer(f"Баланс пользователя #{split[1]} пополнен на {split[2]} руб.")
                logging.info(
                    f"{message.chat.id} ({message.chat.username}) - пополнил баланс пользователя #{split[1]} пополнен на {split[2]} руб.")
            except ValueError as e:
                await message.answer("Проверьте введенное кол-во бонусов.")


@dp.message_handler(text=['Повторить попытку'])
@dp.message_handler(commands=['start', 'id'])
async def send_welcome(message: types.Message):
    if not is_admin(message.chat.id):
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton('Повторить попытку'))
        await message.reply(f"Отсутствует доступ к системе!\n\n"
                            f"Ваш ChatID: {message.chat.id}\n"
                            f"Сообщите его администратору!", reply_markup=kb)
    else:
        await message.reply(f"Вход выполнен успешно!\nID: {message.chat.id}", reply_markup=get_main_menu())


@dp.message_handler()
async def select_unit(message: types.Message):
    if is_admin(message.chat.id):
        if message.text.isdigit():
            if 6 > len(message.text) >= 3:
                unit_name = "0" * (6 - len(message.text)) + message.text
            elif 10 > len(message.text) >= 6:
                unit_name = message.text
            else:
                await message.reply("Неверный номер самоката!")
                return
        elif "FAKE" in message.text:
            unit_name = message.text
        else:
            await message.reply("Номер самоката может содержать только цифры!")
            return

        await send_unit_details(message, unit_name)
        logging.info(f"{message.chat.id} ({message.chat.username}) - выбрал самокат {message.text}")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
