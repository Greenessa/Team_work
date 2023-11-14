import requests

class VK_Client:
    API_BASE_URL = 'https://api.vk.com/method'

    def __init__(self, token, user_id):
        self.token = token
        self.user_id = user_id

    def get_params(self):
        return {'access_token': self.token, 'v': '5.131'}

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

