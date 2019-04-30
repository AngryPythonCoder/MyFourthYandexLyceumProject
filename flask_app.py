from flask import Flask, request
import logging
import json
import random


app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}
letters = ['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я', '-']
with open('mysite/words.txt') as input_file:
    words = set(input_file.read().split())
with open('mysite/image.txt') as input_file:
    lines = input_file.read().split('\n')
gallows = []
for i in range(7):
    gallows.append('\n'.join(lines[11 * i: 11 * (i + 1)]))

@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(request.json, response)

    logging.info('Response: %r', request.json)

    return json.dumps(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:

        word = random.choice(list(words))
        sessionStorage[user_id] = {'attempts': 6, 'word': word, 'used_letters': [], 'used_words': [], 'stat': [0, 0]}

        res['response']['text'] = 'Слово: ' + generate_response(sessionStorage[user_id]['word'], sessionStorage[user_id]['used_letters'])
        res['response']['buttons'] = [{'title': 'Хочу другое слово', 'hide': True}, {'title': 'Хватит', 'hide': True}]
        return

    request = req['request']['original_utterance'].lower()
    attempts = sessionStorage[user_id]['attempts']
    word = sessionStorage[user_id]['word']
    used_letters = sessionStorage[user_id]['used_letters']
    used_words = sessionStorage[user_id]['used_words']
    response = []

    if request in letters:
        if request not in used_letters:
            if request not in word[1:-1]:
                attempts -= 1
                response.append('Нет такой буквы')

            used_letters.append(request)
            response.insert(0, gallows[6 - attempts])

            if set(word[1:-1]).issubset(set(used_letters)):
                sessionStorage[user_id]['stat'][0] += 1
                response.append('Вы выиграли. Было загадано слово {}'.format(word))
                word, attempts, used_words, used_letters, text = new_game(res, attempts, used_words, used_letters)
                response.append('Слово: ' + text)

            elif attempts != 0:
                response.append('\n\n'.join((generate_response(word, used_letters), 'Использованные буквы: ' + ' '.join(used_letters), 'Осталось {} попыток'.format(attempts))))

            else:
                sessionStorage[user_id]['stat'][1] += 1
                response.append('Вы проиграли. Было загадано слово {}'.format(word))
                word, attempts, used_words, used_letters, text = new_game(res, attempts, used_words, used_letters)
                response.append('Слово: ' + text)


        else:
            response.insert(0, gallows[6 - attempts])
            response.append('Эта буква уже была использована')
            response.append('\n\n'.join((generate_response(word, used_letters), 'Использованные буквы: ' + ' '.join(used_letters), 'Осталось {} попыток'.format(attempts))))

    elif request == 'хочу другое слово':
        word, attempts, used_words, used_letters, text = new_game(res, attempts, used_words, used_letters)
        response.append('Слово: ' + text)

    elif request == 'хватит':
        res['response']['text'] = 'Было приятно играть\n\nКоличество выигрышей: {}\n\nКоличество проигрышей: {}'.format(*sessionStorage[user_id]['stat'])
        res['response']['end_session'] = True
        return

    else:
        response.append('Похоже, что введёный текст является некорректным')
        response.insert(0, gallows[6 - attempts])
        response.append('\n\n'.join((generate_response(word, used_letters), 'Использованные буквы: ' + ' '.join(used_letters), 'Осталось {} попыток'.format(attempts))))

    res['response']['text'] = '\n\n'.join(response)

    sessionStorage[user_id]['attempts'] = attempts
    sessionStorage[user_id]['word'] = word
    sessionStorage[user_id]['used_letters'] = used_letters
    sessionStorage[user_id]['used_words'] = used_words

    res['response']['buttons'] = [{'title': 'Хочу другое слово', 'hide': True}, {'title': 'Хватит', 'hide': True}]


def new_game(res, attempts, used_words, used_letters):
    attempts = 6
    used_letters = []
    word = random.choice(list(words - set(used_words)))
    used_words.append(word)

    text = generate_response(word, used_letters)

    return word, attempts, used_words, used_letters, text


def generate_response(word, used_letters):
    response = []

    for index, letter in enumerate(word):
        if (index == 0 or index == len(word) - 1) or letter in used_letters:
            response.append(letter)

        else:
            response.append('_')

    response = ' '.join(response)

    return response


if __name__ == '__main__':
    app.run()