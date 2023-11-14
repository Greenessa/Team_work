from pprint import pprint

import requests

from tokens import token_access


class VK_Client:
    API_BASE_URL = 'https://api.vk.com/method'

    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id

    def get_params(self):
        return {'access_token': self.token, 'v': '5.131'}

    def get_friends(self):
        params = self.get_params()
        params.update({'user_id': self.user_id})
        resp = requests.get(f'{self.API_BASE_URL}/friends.get', params=params).json()
        return resp

    def get_photos(self):
        params = self.get_params()
        params.update({'owner_id': self.user_id, "extended": 1})
        resp = requests.get(f'{self.API_BASE_URL}/photos.getAll', params=params).json()
        return resp

    def users_info(self):
        params = self.get_params()
        params.update({'user_ids': self.user_id, 'fields': 'city, sex, bdate'})
        response = requests.get(f'{self.API_BASE_URL}/users.get', params=params)
        return response.json()

    def get_candidates(self, city, gender, age):
        params = self.get_params()
        params.update({'count': 20, 'fields': 'city, sex, bdate, relation', 'city': city, 'sex': gender,
                  'age_from': (age - 8),
                  'age_to': (age + 10)})
        resp = requests.get(f'{self.API_BASE_URL}/users.search', params=params)
        return resp.json()

    def allow_message(self, group_id):
        params = self.get_params()
        url = 'https://api.vk.com/method/messages.allowMessagesFromGroup'
        params.update({'group_id': group_id, 'key': str(self.user_id)})
        resp = requests.get(f'{self.API_BASE_URL}/messages.allowMessagesFromGroup', params=params)
        return resp.json()

# vk_klient = VK_Client(token_access, 180411688)
# res = vk_klient.get_friends()
# pprint(res['response']['items'])
# if 845050 not in res['response']['items']:
#     print("not")
# else:
#     print("yes")