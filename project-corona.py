# -"- coding:utf-8 -"-

import requests
import json
import os

from flask import Flask, request
import logging
import sqlite3

'''
# 0.009 - широта, 0.15625 - долгота
con = sqlite3.connect('data_covid.db')
cur = con.cursor()

# Выполнение запроса и получение всех результатов
result = cur.execute("SELECT title FROM Films WHERE (year >= 1997)" +
                     " AND ((genre=(SELECT id FROM genres WHERE title = " + 
                     "'анимация')) OR (genre=(SELECT id FROM genres WHERE title = 'музыка')))").fetchall()

# Вывод результатов на экран
for elem in result:
    print(*elem)
    '''
def search(cords, rad=1):
    con = sqlite3.connect('data_covid.db')
    cur = con.cursor()
    result = cur.execute(
        "SELECT * FROM adresses WHERE (width >= " + str(int(cords[0].replace('.', '').ljust(10, '0')) -
                                                         900000 * rad) + ") AND (width <= " + str(int(cords[0].replace('.', '').ljust(10, '0')) + 900000 * rad) +
        ") AND (height >= " + str(int(cords[1].replace('.', '').ljust(10, '0')) -
                                 1562500 * rad) + ") AND (height <= " + str(int(cords[1].replace('.', '').ljust(10, '0')) + 1562500 * rad) + ")").fetchall()
    con.close()
    return str(len(result))


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
    # logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }
    handle_dialog(request.json, response)
    # logging.info(f'Response:  {response!r}')
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
        if req['request']['nlu']['tokens'] == ['закончить', 'диалог']:
            res['response']['text'] = 'Пока! Возвращайся за новой информацией завтра!'
            res['response']['end_session'] = True
            return
    except Exception:
        pass
    if parts[user_id] == 0:
        try:
            for i, dat in enumerate(req['request']['nlu']['entities']):
                if dat['type'] == "YANDEX.GEO":
                    parts[user_id] = 1
                    geocoder_request = "http://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b&geocode=" + \
                        req['request']['nlu']['entities'][i]['value']['street'] + \
                        ",+" + req['request']['nlu']['entities'][i]['value']['house_number'] + "&format=json"
                    response = requests.get(geocoder_request)
                    if response:
                        json_response = response.json()
                        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                        toponym_coordinates = toponym["Point"]["pos"]
                        res['response']['text'] = search(
                            toponym_coordinates.split())
                    else:
                        res['response']['text'] = 'Мне очень жаль, но такого адреса нет, скажите еще раз'
                    return
            res['response']['text'] = 'Кажется, это не адрес. Назовите адрес еще раз'
            res['response']['buttons'] = [{
                "title": "Красная площадь, 1",
                "payload": {},
                "hide": True
            }, {
                "title": "Закончить диалог",
                "payload": {},
                "hide": True
            }]
        except Exception as e:
            res['response']['text'] = "Ошибка: " + str(e) + "  " + str(e.__class__.__name__) + ". Назовите адрес еще раз"
            res['response']['buttons'] = [{
                "title": "Красная площадь, 1",
                "payload": {},
                "hide": True
            }, {
                "title": "Закончить диалог",
                "payload": {},
                "hide": True
            }]
    elif parts[user_id] == 1:
        res['response']['text'] = 'Хочешь узнать еще о каком-нибудь месте?'
        parts[user_id] = 2
        res['response']['buttons'] = [{
            "title": "Да",
            "payload": {},
            "hide": True
        }, {
            "title": "Нет",
            "payload": {},
            "hide": True
        }]
    else:
        if 'нет' in req['request']['nlu']['tokens'] or 'не хочу' in req['request']['nlu']['tokens']:
            res['response']['text'] = 'Пока! Возвращайся за новой информацией завтра!'
            res['response']['end_session'] = True
            return
        else:
            parts[user_id] = 0
            res['response']['text'] = 'Назови адрес'
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
