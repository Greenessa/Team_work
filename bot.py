from random import randrange
import sqlalchemy
import vk_api
import requests
import json
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from db_search import get_info, add_to_favorites, add_to_file, dell_table
from main import get_cand_list, get_info_user
from models import create_tables
from tokens import token_bot, dsn

vk_session = vk_api.VkApi(token=token_bot)
"""это комментарий"""
"""Модуль работы бота"""


def send_message(user_id, message, keyboard=None):
    """Отправляет сообщение в чат пользователя."""
    args = {
        "user_id": user_id,
        "message": message,
        "random_id": randrange(10 ** 7)
    }
    if keyboard is not None:
        args['keyboard'] = keyboard.get_keyboard()
    else:
        keyboard = VkKeyboard()
        args['keyboard'] = keyboard.get_empty_keyboard()
    vk_session.method("messages.send", args)


def send_photo(user_id, photo_id):
    """Отправляет фотографии в чат пользователя."""
    for photo in range(0, len(photo_id)):
        vk_session.method("messages.send",
                          {"user_id": user_id, "attachment": photo_id[photo][0],
                           "random_id": randrange(10 ** 7)})


def send_docs(user_id, file):
    """Отправляет файл с избранными кандидатами в чат пользователя."""
    vk_session = vk_api.VkApi(token=token_bot)
    vk = vk_session.get_api()
    url = vk.docs.getMessagesUploadServer(type='doc', peer_id=user_id)['upload_url']
    res = json.loads(requests.post(url, files={'file': open(file, encoding='cp1251', newline='')}).text)
    jsonAnswer = vk.docs.save(file=res['file'], tag=[])
    vk.messages.send(peer_id=user_id, random_id=0,
                     attachment=f"doc{jsonAnswer['doc']['owner_id']}_{jsonAnswer['doc']['id']}")


while True:
    try:
        count_vip = 0
        list_vk_id = []
        count = 0
        vip_menu = True
        vip_cand = False
        first_user = 1
        first_user_id = 0
        engine = sqlalchemy.create_engine(dsn)
        create_tables(engine)
        for event in VkLongPoll(vk_session).listen():  # прослушка чата
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:  # ждем события (нового сообщения)
                request = event.text.lower()  # записываем текст из чата
                user_id = event.user_id  # записываем id  пользователя
                if request == 'найти пару' and not first_user:
                    send_message(user_id,
                                 "Мы не можем пока подобрать Вам кандидатов, поскольку бот занят сбором данных для предыдущего клиента. Повторите Ваше обращение через 5 минут.")
                if first_user:
                    first_user_id = user_id
                if first_user_id == user_id:
                    if request == 'найти пару' and first_user:
                        count_vip = 0
                        list_vk_id = []
                        count = 0
                        vip_menu = True
                        vip_cand = False
                        first_user = 0
                        first_user_id = user_id
                        send_message(user_id, 'Выполняю запрос. Пожалуйста, подождите')
                        get_info_date = get_info_user(user_id)
                        if get_info_date['city'] is None:
                            send_message(user_id,
                                         "Мы не можем подобрать кандидата, в Вашем профиле отсутствует город")
                        else:
                            list_vk_id = get_cand_list(get_info_date)
                            keyboard = VkKeyboard()
                            keyboard.add_button("Вперед", color=VkKeyboardColor.POSITIVE)
                            send_message(user_id, 'Для просмотра нажмите кнопку "Вперед"', keyboard)
                            count = 0
                    elif request == 'вперед' and not first_user:
                        try:
                            result = get_info(count, list_vk_id, vip_cand)
                            count += 1
                        except:
                            send_message(user_id,
                                         'Сначала произведите поиск кандидатов.\n Отправте в чат команду "Найти пару"')
                            continue
                        if result['message'] != 'Вы просмотрели все варианты.':
                            send_photo(user_id, result['photo'])
                            keyboard = VkKeyboard()
                            keyboard.add_button("Вперед", color=VkKeyboardColor.POSITIVE)
                            if vip_menu:
                                keyboard.add_button("В избранное", color=VkKeyboardColor.PRIMARY)
                                keyboard.add_button("Завершить просмотр", color=VkKeyboardColor.NEGATIVE)
                            else:
                                keyboard.add_button("Выйти", color=VkKeyboardColor.NEGATIVE)
                            send_message(user_id, result['message'], keyboard)
                        else:
                            if vip_menu:
                                keyboard = VkKeyboard(one_time=True)
                                keyboard.add_button(f"Перейти в избранное ({count_vip})", color=VkKeyboardColor.POSITIVE)
                                send_message(user_id, 'Вы просмотрели всех кандидатов', keyboard)
                                vip_menu = True
                                vip_cand = False
                            else:
                                send_message(user_id,
                                             'Вы просмотрели всех избранных.\n Надеюсь, что мне удалось Вам помочь. \nОтправил Вам файл с выбранным.')
                                add_to_file(user_id)
                                dell_table()
                                send_docs(user_id, 'vip.csv')
                    elif request == 'в избранное' and not first_user:
                        try:
                            result = add_to_favorites(result['vk_id'], user_id)
                            count_vip += 1
                            #hprint(count_vip)
                        except:
                            pass
                        if not result:
                            keyboard = VkKeyboard()
                            keyboard.add_button("Вперед", color=VkKeyboardColor.POSITIVE)
                            keyboard.add_button('В избранное', color=VkKeyboardColor.PRIMARY)
                            keyboard.add_button("Завершить просмотр", color=VkKeyboardColor.NEGATIVE)
                            send_message(user_id, 'Запись добавлена в избранные', keyboard)

                    elif request == f'перейти в избранное ({count_vip})' and not first_user:
                        if count_vip > 0:
                            vip_menu = False
                            vip_cand = True
                            keyboard = VkKeyboard()
                            keyboard.add_button("Вперед", color=VkKeyboardColor.POSITIVE)
                            keyboard.add_button("Выйти", color=VkKeyboardColor.NEGATIVE)
                            send_message(user_id, 'Вы находитесь в избранных. \nДля просмотра нажмите "Вперед"', keyboard)
                            count = 0
                        else:
                            send_message(user_id, 'В избранном нет кандидатов.')
                            keyboard = VkKeyboard()
                            keyboard.add_button("Вперед", color=VkKeyboardColor.POSITIVE)
                            send_message(user_id, 'Для просмотра нажмите кнопку "Вперед"\n и добавте в избраноое', keyboard)

                    elif request == 'завершить просмотр' and not first_user:
                        if count == 0:
                            send_message(user_id, 'Вы не просматрели список кандидатов, попробуем еще раз?')
                            keyboard = VkKeyboard()
                            keyboard.add_button("Вперед", color=VkKeyboardColor.POSITIVE)
                            send_message(user_id, 'Для просмотра нажмите кнопку "Вперед"', keyboard)
                        keyboard = VkKeyboard(one_time=True)
                        keyboard.add_button(f'Перейти в избранное ({count_vip})', color=VkKeyboardColor.POSITIVE)
                        send_message(user_id, 'Завершить просмотр', keyboard)
                    elif request == 'выйти':
                        first_user = 1
                        add_to_file(user_id)
                        dell_table()
                        send_docs(user_id, 'vip.csv')
                        send_message(user_id, 'Отправил Вам файл с выбранным.')
                    else:
                        keyboard = VkKeyboard(one_time=True)
                        keyboard.add_button("Найти пару", color=VkKeyboardColor.POSITIVE)
                        send_message(user_id,
                                     'Вас приветствует бот Клуба знакомств. Для начала поиска пары нажмите кнопку "Найти пару"',
                                     keyboard)
    except:
        pass
