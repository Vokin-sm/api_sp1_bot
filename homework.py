import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
WAITING_TIME = 300
WAITING_TIME_ERROR = 5
API_HOMEWORKS_URL = (
    'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
)

verdicts = {
    'reviewing': 'Ваша работа взята в ревью',
    'approved': ('Ревьюеру всё понравилось, '
                 'можно приступать к следующему уроку.'),
    'rejected': 'К сожалению в работе нашлись ошибки.'
}

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'my_logger.log',
    maxBytes=50000000,
    backupCount=5
)
logger.addHandler(handler)


class HomeworkError(Exception):
    pass


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logger.error(
            'Ошибка переменной с именнем домашней работы'
        )
        raise HomeworkError(
            'Ошибка переменной с именнем домашней работы'
        )
    homework_status = homework.get('status')
    if homework_status is None:
        logger.error(
            'Ошибка переменной со статусом домашней работы'
        )
        raise HomeworkError(
            'Ошибка переменной со статусом домашней работы'
        )
    return (
        f'У вас проверили работу "{homework_name}":\n\n'
        f'{verdicts[homework_status]}'
    )


def get_homework_statuses(current_timestamp):
    data = {'from_date': current_timestamp}
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    try:
        homework_statuses = requests.get(
            API_HOMEWORKS_URL,
            params=data,
            headers=headers
        )
        return homework_statuses.json()
    except Exception as e:
        logger.exception(e)
        return {}


def send_message(message, bot_client):
    logger.info('Отправка сообщения')
    try:
        return bot_client.send_message(CHAT_ID, message)
    except Exception:
        logger.exception('Ошибка отправки сообщения')
        raise HomeworkError(
            'Ошибка отправки сообщения'
        )


def main():
    logger.debug('Запуск бота')
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logger.debug('Бот создался')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]),
                    bot_client
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(WAITING_TIME)

        except Exception as e:
            error = f'Бот столкнулся с ошибкой: {e}'
            logger.exception(error)
            send_message(error, bot_client)
            time.sleep(WAITING_TIME_ERROR)


if __name__ == '__main__':
    main()
