from pprint import pprint

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from models import create_tables, Candidates, Photos, Flag, VK, VK_Client
from tokens import dsn, token_access


# Получение токена
# from urllib.parse import urlencode
# Oauth_Base_url = 'https://oauth.vk.com/authorize'
# params = {'client_id': '51722110', 'redirect_uri': 'https://oauth.vk.com/blank.html', 'display': 'page', 'scope': 'photos, offline', 'response_type': 'access_token', 'v':'5.131', 'state': '123456'}
# auth_url = f'{Oauth_Base_url}?{urlencode(params)}'
# print(auth_url)


# получение информации о пользователе, для определения города, пола, возраста
def get_info_user(user_id):
    #access_token = open("access_token").read()  # access_token нужен один из файла access_token
    access_token = token_access
    user_id = user_id  # id пользователя передаем с чата, через dot.py
    vk = VK(access_token, user_id)  # создаем экземпляр класса VK
    cl_info = vk.users_info()  # получаем информацию о пользователе, который общается с ботом
    # print(cl_info)

    city = cl_info['response'][0].setdefault('city', {'id': None, 'title': ''})  # устанавливаем значения по умолчанию town заменил на sity (путаюсь) -->
    cl_info['response'][0].setdefault('bdate', '')  # --> на случай отсутствия данных

    sex = cl_info['response'][0]['sex']  # для определения пола, инвертируем и ищем по этому значени.
    if sex == 2:
        gender = 1
    else:
        gender = 2
    sp = cl_info['response'][0]['bdate'].split('.')  # подготовка даты для функции get_candidates
    age = 2023 - int(sp[2])
    result = {  # формируем словарь для -->
        'city': city['id'],
        'gender': gender,
        'bdate': age,
        'vk': vk,
        'is_closed': cl_info['response'][0]['is_closed'],
        'user_id': user_id}  # --> оброботки его в боте и если данные валидны -->
    return result  # --> вызываем get_cand_list с параметрами result


# функция для поиска кандидатов и заполнения базы данных
def get_cand_list(data):
    #DSN = open("dsn").read()
    engine = sqlalchemy.create_engine(dsn)
    create_tables(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    #access_token = open('access_token').read()  # тот же access_token, что и в get_info_user
    access_token = token_access
    data_for = data['vk'].get_candidates(data['city'], data['gender'], data['bdate'])['response'][
        'items']  # поиск кандидатов
    # print(data_for[0])
    # if data_for[0]['relation'] in [1,6,0]:
    #     print('Отлично')
    for el in data_for:
        el.setdefault('city', {'id': None, 'title': ''})
        el.setdefault('bdate', '')
        el.setdefault('relation', 0)
    for el in data_for:
        vk_klient = VK_Client(access_token, el['id'])
        try:
            dict = vk_klient.get_photos()['response']['items']  # получаем фото кандидата
            # pprint(dict)
        except Exception:
            #print("Ошибка заполнения словаря с фотографиями")
            # pprint(dict)
            continue
        # pprint(dict)
        dict2 = {}
        if el['is_closed'] == False:  # проверяем приватность страници, если False, то страница публичная и можно получить доступ к информации
            if el['city']['id'] == data['city'] and el['relation'] in [1, 6, 0] and el['bdate'] != '':# --> по-этому сравниваем город пользователя с городом кандидата
                #pprint(el)
                cand = Candidates(name=el['first_name'],
                                  fam_name=el['last_name'],
                                  city=el['city']['title'],
                                  age=(2023 - int(el['bdate'].split('.')[2])),
                                  gender=el['sex'],
                                  vk_id=el['id'],
                                  vk_url=f"https://vk.com/id{el['id']}",
                                  user_id=data['user_id'])
                session.add(cand)  # добавляем данные в базу
                for elem in dict:
                    a = elem['likes']['count']  # записываем количество лайков
                    dict2[a] = f'photo{elem["owner_id"]}_{elem["id"]}'  # формируем не обходимый формат для фото
                sp_photos = sorted(dict2.items(), reverse=True)  # сортируем по убыванию
                # получаем три фотографии с наибольшим количеством лайков
                if len(sp_photos) >= 3:
                    photo = Photos(candidate_id=el['id'], photo_url=sp_photos[0][1])
                    session.add(photo)
                    photo = Photos(candidate_id=el['id'], photo_url=sp_photos[1][1])
                    session.add(photo)
                    photo = Photos(candidate_id=el['id'], photo_url=sp_photos[2][1])
                    session.add(photo)
                elif len(sp_photos) == 2:
                    photo = Photos(candidate_id=el['id'], photo_url=sp_photos[0][1])
                    session.add(photo)
                    photo = Photos(candidate_id=el['id'], photo_url=sp_photos[1][1])
                    session.add(photo)
                elif len(sp_photos) == 1:
                    photo = Photos(candidate_id=el['id'], photo_url=sp_photos[0][1])
                    session.add(photo)  # записываем данные о фото в базу
    list_cand_vk_id = session.query(Candidates.vk_id).all()  # id всех найденых кандидатов
    session.commit()  # записываем данные в базу данных
    session.close()  # закрываем сессию
    return list_cand_vk_id  # возвращаем id всех найденых кандидатов


# get_cand_list(get_info_user(815147892))
#get_cand_list(get_info_user(707708596))
