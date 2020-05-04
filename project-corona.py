# -"- coding:utf-8 -"-

import requests
import json
import os

from flask import Flask, request
import logging
import sqlite3


def search(cords, rad=1):
    dis = []
    con = sqlite3.connect('data_covid.db')
    cur = con.cursor()
    result = cur.execute(
        "SELECT * FROM adresses WHERE (width >= " + str(int(cords[0].replace('.', '').ljust(10, '0')) -
                                                         900000 * rad) + ") AND (width <= " + str(int(cords[0].replace('.', '').ljust(10, '0')) + 900000 * rad) +
        ") AND (height >= " + str(int(cords[1].replace('.', '').ljust(10, '0')) -
                                 1562500 * rad) + ") AND (height <= " + str(int(cords[1].replace('.', '').ljust(10, '0')) + 1562500 * rad) + ")").fetchall()
    con.close()
    for i in result:
        distance = ((
            (i[2] - int(cords[1].replace('.', '').ljust(10, '0'))) / 900) ** 2 + (
            (i[3] - int(cords[0].replace('.', '').ljust(10, '0'))) / 1562.5) ** 2) ** 0.5
        dis.append(distance)
    text = "В радиусе 1 километра от этого дома " + str(len(result))
    if str(len(result))[-1] == '1' and str(len(result))[-2] != '1':
      text += ' зараженный'
    else:
      text += ' зараженных'
    if int(round(min(dis), 0)) > 10:
        text += ', при этом ближайший дом находится по адресу: '
        text += result[dis.index(min(dis))][1].replace('Москва, ', '')
        text += ' на расстоянии в '
        text += str(int(round(min(dis), 0)))
        if str(int(round(min(dis), 0)))[-1] == '1' and str(int(round(min(dis), 0)))[-2] != '1':      
            text += ' метр от этого дома.'
        elif str(int(round(min(dis), 0)))[-1] == '2' and str(int(round(min(dis), 0)))[-2] != '1':
            text += ' метра от этого дома.'
        elif str(int(round(min(dis), 0)))[-1] == '3' and str(int(round(min(dis), 0)))[-2] != '1':
            text += ' метра от этого дома.'
        elif str(int(round(min(dis), 0)))[-1] == '4' and str(int(round(min(dis), 0)))[-2] != '1':
            text += ' метра от этого дома.'
        else:
            text += ' метров от этого дома.'
    else:
      text += ' и ближайший зараженный находится в этом доме!'
    text += ' Хочешь узнать еще о каком-нибудь месте?'
    return text


app = Flask(__name__)


logging.basicConfig(level=logging.DEBUG)


sessionStorage = {}

parts = {}  # 0 - узнаем адрес, 1 - говорим количество
#                  и ближайший адрес, 2 - спрашиваем хочет ли узнать еще

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

  
def handle_dialog(req, res):
    user_id = req['session']['user_id']
    if req['session']['new']:
        parts[user_id] = 0
        res['response'][
            'text'] = 'Привет! Узнай сколько заболевших коронавирусом есть около тебя! Назови адрес, про который хочешь узнать'
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
            res['response']['text'] = 'Пока! Возвращайся за новой информацией завтра и старайся поменьше выходить из дома!'
            res['response']['end_session'] = True
            return
    except Exception:
        pass
    try:
        if req['request']['nlu']['tokens'] == ['что', 'ты', 'умеешь'] or req['request']['nlu']['tokens'] == ['помощь']:
            res['response']['text'] = 'Я умею определять сколько зараженных коронавирусом людей находятся в радиусе 1 километра от тебя, для этого мне достаточно сказать адрес любого дома. Скажи мне адрес'
            parts[user_id] = 0
            return
    except Exception:
        pass
    if parts[user_id] == 0:
        try:
            for i, dat in enumerate(req['request']['nlu']['entities']):
                if dat['type'] == "YANDEX.GEO":
                    
                    geocoder_request = "http://geocode-maps.yandex.ru/1.x/?apikey=40d1649f-0493-4b70-98ba-98533de7710b&geocode=Москва,+" + \
                        req['request']['nlu']['entities'][i]['value']['street'] + \
                        ",+" + req['request']['nlu']['entities'][i]['value']['house_number'] + "&format=json"
                    response = requests.get(geocoder_request)
                    if response:
                        json_response = response.json()
                        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                        toponym_coordinates = toponym["Point"]["pos"]
                        res['response']['text'] = search(
                            toponym_coordinates.split())
                        parts[user_id] = 1
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
            res['response']['text'] = "Не совсем тебя поняла. Назови адрес еще раз"
            res['response']['buttons'] = [{
                "title": "Красная площадь, 1",
                "payload": {},
                "hide": True
            }, {
                "title": "Закончить диалог",
                "payload": {},
                "hide": True
            }]

    else:
        if 'нет' in req['request']['nlu']['tokens'] or 'не хочу' in req['request']['nlu']['tokens']:
            res['response']['text'] = 'Пока! Возвращайся за новой информацией завтра и старайся поменьше выходить из дома!'
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
