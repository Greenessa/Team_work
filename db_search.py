import csv
import datetime
from pprint import pprint
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from models import create_tables, Candidates, Photos, Flag
from vk_cl import VK_Client
from tokens import dsn, token_access

# Получение токена
# from urllib.parse import urlencode
# Oauth_Base_url = 'https://oauth.vk.com/authorize'
# params = {'client_id': '51722110', 'redirect_uri': 'https://oauth.vk.com/blank.html', 'display': 'page', 'scope': 'photos, offline', 'response_type': 'access_token', 'v':'5.131', 'state': '123456'}
# auth_url = f'{Oauth_Base_url}?{urlencode(params)}'
# print(auth_url)

# подключаемся к базе данных
def get_connection():
    engine = sqlalchemy.create_engine(dsn)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
def get_info_user(user_id):
    """Получает информацию о пользователе для определения критериев отбора: города, пола, возраста кандидатов."""
    #access_token = open("access_token").read()  # access_token нужен один из файла access_token
    #user_id = user_id  # id пользователя передаем с чата, через main.py
    vk = VK_Client(token_access, user_id)  # создаем экземпляр класса VK
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
    today = datetime.date.today()
    year = today.year
    #print(year)
    age = year - int(sp[2])
    result = {  # формируем словарь для -->
        'city': city['id'],
        'gender': gender,
        'bdate': age,
        'vk': vk,
        'is_closed': cl_info['response'][0]['is_closed'],
        'user_id': user_id}  # --> обработки его в боте и если данные валидны -->
    return result  # --> вызываем get_cand_list с параметрами result

def get_info_friend(user_id):
    vk = VK_Client(token_access, user_id)
    res = vk.get_friends()
    fr_list = res['response']['items']
    return fr_list

def get_cand_list(data, fr_list):
    """Получает информацию о кандидатах и заполняет базу данных."""
    session = get_connection()
    #access_token = open('access_token').read()  # тот же access_token, что и в get_info_user
    data_for = data['vk'].get_candidates(data['city'], data['gender'], data['bdate'])['response'][
        'items']  # поиск кандидатов
    # print(data_for[0])
    # if data_for[0]['relation'] in [1,6,0]:
    #     print('Отлично')
    today = datetime.date.today()
    year = today.year
    for el in data_for:
        el.setdefault('city', {'id': None, 'title': ''})
        el.setdefault('bdate', '')
        el.setdefault('relation', 0)
    for el in data_for:
        vk_klient = VK_Client(token_access, el['id'])
        try:
            dict = vk_klient.get_photos()['response']['items']  # получаем фото кандидата
            # pprint(dict)
        except Exception:
            #print("Ошибка заполнения словаря с фотографиями")
            # pprint(dict)
            continue
        # pprint(dict)
        dict2 = {}
        if el['is_closed'] == False and el['id'] not in fr_list:  # проверяем приватность страницы, если False, то страница публичная и можно получить доступ к информации
            if el['city']['id'] == data['city'] and el['relation'] in [1, 6, 0] and el['bdate'] != '':# --> поэтому сравниваем город пользователя с городом кандидата
                #pprint(el)
                cand = Candidates(name=el['first_name'],
                                  fam_name=el['last_name'],
                                  city=el['city']['title'],
                                  age=(year - int(el['bdate'].split('.')[2])),
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
                for photo in sp_photos[:3]:
                    photo1 = Photos(candidate_id=el['id'], photo_url=photo[1])
                    session.add(photo1)  # записываем данные о фото в базу
    list_cand_vk_id = session.query(Candidates.vk_id).all()  # id всех найденых кандидатов
    session.commit()  # записываем данные в базу данных
    session.close()  # закрываем сессию
    return list_cand_vk_id  # возвращаем id всех найденых кандидатов

"""Получает список всех кандидатов либо избранных, запись избранных в файл для отправки пользователю."""

def get_info(count, list_vk_id, vip_cand=False):
    """Получает информацию о кандидате, на вход count - текущий кандидат, list_vk_id - список кандидатов."""
    session = get_connection()
    if vip_cand:  # --> list_vk_id - id всех найденых кандидатов и vip_cand для определения с каким списком кандидатов мы работаем весь или vip
        list_vk_id = session.query(Candidates.vk_id).join(Flag.candidate).all()
    dict_cand_info = {}  # list_vk_id- id всех найденых кандидатов
    list_cand_info = []
    if count < len(list_vk_id):  # если кандидаты еще есть то продолжаем вывод данных
        photos = session.query(Photos.photo_url).filter(
            Photos.candidate_id == list_vk_id[count][0])  # получаем фото кандидата
        for photo_id in photos:  # итерируемся по фотографиям
            list_cand_info.append(photo_id)  # добавляем фото в список
        dict_cand_info['photo'] = list_cand_info  # формируем данные по фотографиям для бота
        date_cand = session.query(Candidates).join(Photos).filter(
            Candidates.vk_id == list_vk_id[count][0]).one()  # получаем данные кондидата
        dict_cand_info['vk_id'] = date_cand.vk_id
        message = f'{date_cand.name} {date_cand.fam_name}\nВозраст: {date_cand.age}\nСтраница в ВК: {date_cand.vk_url}'  # формируем данные кондилата для бота
        dict_cand_info['message'] = message  # добавление в словарь сообщения данные кондилата для бота
        return dict_cand_info  # возвращаем данные кандидата
    message = 'Вы просмотрели все варианты.'  # если были просмотрены все кандидаты
    dict_cand_info['message'] = message
    session.close()
    return dict_cand_info


def add_to_favorites(cand_vk_id, user_id):
    """Записывает избранных кандидатов в файл."""
    session = get_connection()
    cand = session.query(Candidates).filter(Candidates.vk_id == cand_vk_id).one()
    cand_vip = Flag(candidate=cand, flag=True)
    session.add(cand_vip)
    try:
        session.commit()
        session.close()
    except:
        session.close()
        return False


def add_to_file(user_id):
    """Функция формирует файл с избранными, на вход принимает идентификатор пользователя."""
    session = get_connection()
    subq = session.query(Candidates).filter(Candidates.user_id == user_id).subquery()
    vip_cand_info = session.query(Flag).join(subq, Flag.cand_id == subq.c.id).all()
    # vip_cand_info = session.query(Flag).join(Candidates, Candidates.id == Flag.cand_id).all()
    with open('vip.csv', 'w', encoding='cp1251') as f:
        header = ['Имя', ' Фамилия', 'Страница в ВК']
        vip_list_vk_id = []
        for i in vip_cand_info:
            vip_list_vk_id.append([i.candidate.name, i.candidate.fam_name, i.candidate.vk_url])
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(vip_list_vk_id)
    session.close()


def dell_table():
    session = get_connection()
    session.query(Flag).delete()
    session.query(Photos).delete()
    session.query(Candidates).delete()
    session.commit()
    session.close()
