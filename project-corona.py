# -"- coding:utf-8 -"-

import requests
import json
import os

from flask import Flask, request
import logging


app = Flask(__name__)


logging.basicConfig(level=logging.DEBUG)



sessionStorage = {}

parts = {}  # 0 - узнаем адрес, 1 - говорим количество
#                  и ближайший адрес, 2 - спрашиваем хочет ли узнать еще

'''
geocoder_request = "http://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b&geocode=Красная площадь,+1&format=json"

response = requests.get(geocoder_request)
if response:
    json_response = response.json()
    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
    toponym_coodrinates = toponym["Point"]["pos"]
    print(toponym_coodrinates)
else:
    print("Ошибка выполнения запроса:")
    print(geocoder_request)
    print("Http статус:", response.status_code, "(", response.reason, ")")
'''


@app.route('/', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(request.json, response)
    #logging.info(f'Response:  {response!r}')
    return json.dumps(response)




'''
req = requests.post('https://coronavirus.mash.ru/search.php',
                    data={'referal': 'Улица'})
streets = req.text.split('</tr>')[1:]
streets.pop()
for i in streets:
    print(''.join(i.split('</td>')).split('<td>')[1:3])
'''

def handle_dialog(req, res):
    user_id = req['session']['user_id']
    if req['session']['new']:
        parts[user_id] = 0
        res['response'][
            'text'] = 'Привет! Узнай сколько заболевших коронавирусом есть около тебя! Назови адрес, про который хочешь узнать (работает только для Москвы)'
        res['response']['buttons'] = [{
            "title": "Красная площадь, 1",
            "payload": {},
            "hide": True
        }, {
            "title": "Закончить диалог",
            "payload": {},
            "hide": True
        }]
        return

    try:
        if req['request']['original_utterance'].lower() == 'закончить диалог':
            res['response']['text'] = 'Пока! Возвращайся за новой информацией завтра!'
            res['response']['end_session'] = True
        return
    except Exception:
        pass
    if parts[user_id] == 0:
        try:
            err = True
            for i, dat in enumerate(req['request']['nlu']['entities']):
                if dat['type'] == "YANDEX.GEO":
                    parts[user_id] = 1
                    err = False
                    res['response']['text'] = req['request']['nlu']['entities'][i]['value']['street'] + ', ' + \
                        req['request']['nlu']['entities'][i]['value']['house_number']
            if err:
                res['response']['text'] = 'Кажется, такого адреса нет. Назовите адрес еще раз'
                res['response']['buttons'] = [{
                    "title": "Красная площадь, 1",
                    "payload": {},
                    "hide": True
                }, {
                    "title": "Закончить диалог",
                    "payload": {},
                    "hide": True
                }]
        except:
            res['response']['text'] = 'Кажется, такого адреса нет. Назовите адрес еще раз'
            res['response']['buttons'] = [{
                "title": "Красная площадь, 1",
                "payload": {},
                "hide": True
            }, {
                "title": "Закончить диалог",
                "payload": {},
                "hide": True
            }]
        

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
