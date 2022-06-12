import os
import time
import requests
import logging
import sys
import telegram
from dotenv import load_dotenv
from http import HTTPStatus
from exceptions import (
    SendMessageError, HTTPStatusError, TokensError
)


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения в телеграмм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение удачно отправлено в чат:{TELEGRAM_CHAT_ID}.')
    except telegram.TelegramError as error:

        raise SendMessageError(
            logging.error(f'Сбой при отправке сообщения в Telegram:{error}.'))


def get_api_answer(current_timestamp):
    """Функция отправляющая запрос к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    data = {'url': ENDPOINT, 'headers': HEADERS, 'params': params}
    try:
        logger.info('Выполнение запроса к API')
        response = requests.get(**data)
    except Exception as error:
        raise ConnectionError(
            logging.error(f'Ошибка при запросе к API {error}'))
    if response.status_code == HTTPStatus.OK:
        response = response.json()
        logger.info('Запрос успешно выполнен')
        return response
    else:
        raise HTTPStatusError(
            logging.error(
                f'Эндпоинт недоступен, статус ответа:{response.status_code}.'))


def check_response(response):
    """Проверка ответа от API."""
    if type(response) != dict:
        raise TypeError(
            logging.error(f'Передан неверный тип данных {type(response)}'))
    try:
        homeworks = response['homeworks']
    except KeyError as ex:
        raise KeyError(
            logging.error(f'Сбой при обращении к словарю {ex}'))
    if type(homeworks) != list:
        raise TypeError(
            logging.error(f'Передан неверный тип данных {type(homeworks)}'))
    return homeworks


def parse_status(homework):
    """Получение информации о статусе домашней работы."""
    try:
        homework_name = homework['homework_name']
    except KeyError as ex:
        raise KeyError(
            logging.error(
                f'Сбой при обращении к ключам словаря "homework_name" {ex}'))
    try:
        homework_status = homework['status']
    except KeyError as ex:
        raise KeyError(
            logging.error(
                f'Сбой при обращении к ключам словаря "status" {ex}'))
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError as ex:
        raise KeyError(
            logging.error(
                f'Сбой при обращении к ключам словаря "homework_status" {ex}'))

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функция проверки доступности всех переменных окружения."""
    if all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN]):
        return True
    return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if not check_tokens():
        raise TokensError(logging.critical(
            'Отсутствует одна из обязательных переменных окружения'
            'Программа принудительно остановлена. '))
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:

                message = parse_status(homework)

                send_message(bot, message)
            current_timestamp = int(time.time())

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':

    logging.basicConfig(
        level=logging.INFO,
        filename='program.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    main()
