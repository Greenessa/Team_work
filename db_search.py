import csv
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from models import Photos, Candidates, Flag
from tokens import dsn

# подключаемся к базе данных

"""Получает список всех кандидатов либо избранных, запись избранных в файл для отправки пользователю."""


def get_info(count, list_vk_id, vip_cand=False):
    """Получает информацию о кандидате, на вход count - текущий кандидат, list_vk_id - список кандидатов."""
    engine = sqlalchemy.create_engine(dsn)
    Session = sessionmaker(bind=engine)
    session = Session()
    if vip_cand:  # --> list_vk_id - id всех найденых кандидатов и vip_cand для определения с каким списком кандидатов мы работаем весь или vip
        list_vk_id = session.query(Candidates.vk_id).join(Flag.candidate).all()
    dict_cand_info = {}  # list_vk_id- id всех найденых кандидатов
    list_cand_info = []
    if count < len(list_vk_id):  # если сондидаты еще есть то продолжаем вывод данных
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
    engine = sqlalchemy.create_engine(dsn)
    Session = sessionmaker(bind=engine)
    session = Session()
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
    engine = sqlalchemy.create_engine(dsn)
    Session = sessionmaker(bind=engine)
    session = Session()
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
    engine = sqlalchemy.create_engine(dsn)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.query(Flag).delete()
    session.query(Photos).delete()
    session.query(Candidates).delete()
    session.commit()
    session.close()
