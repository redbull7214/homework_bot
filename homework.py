import os
from queue import Empty
import time
import requests
import logging
import sys
import telegram
from dotenv import load_dotenv

class ResponseStatusError(Exception):
    pass

class EmptyDictError(Exception):
    pass

logging.basicConfig(
    level=logging.INFO,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)


logger = logging.getLogger(__name__)
# Устанавливаем уровень, с которого логи будут сохраняться в файл
# Указываем обработчик логов
handler = logging.StreamHandler(sys.stdout)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

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
        logging.info(f'Сообщение удачно отправлено в чат:{TELEGRAM_CHAT_ID}.')
    except Exception as error:
        logging.error(f'Сбой при отправке сообщения в Telegram:{error}.')


def get_api_answer(current_timestamp):
    """Функция отправляющая запрос к API."""

    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            return 'Ошибка в ответе API' 
            # raise ResponseStatusError(f'Api возвращает код отличный от 200:{response.status_code}.')
            
        response = response.json()
        return response
    except Exception as error:
        logging.error(f'Эндпоинт недоступен:{error}.')
        # send_message(bot, f'Эндпоинт недоступен:{error}')


def check_response(response):
    """Проверка ответа от API."""
    # if response.status_code != 200:
    #     logging.error(f'Api возвращает код отличный от 200:{response.status_code}.')
    if response == {}:
        raise EmptyDictError('Передан пустой словарь')
        
    try:
        homeworks = response.get('homeworks')

        return homeworks
    except Exception as error:
        logging.error(f'Сбой при обработке сообщения:{error}.')
        # send_message(bot, f'Сбой при обработке сообщения:{error}.')


def parse_status(homework):
    """Получение информации о статусе домашней работы."""

    
    homework_name = homework.get('homework_name')
    if homework_name is None:
        logging.error(f'Ошибка получения названия домашней работы:{homework}.')
        return f'Ошибка в работе {homework}'
        
    
    homework_status = homework.get('status')
    
    if homework_status is None:        
        logging.error(f'Ошибка получения статуса домашней работы:{homework_name}.')
        
        return f'Ошибка определения статуса работы: {homework_name}'
    
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if verdict is None:

        logging.error(f'Ошибка в ключах словаря "HOMEWORK_STATUSES":{homework_name} нет в {HOMEWORK_STATUSES.keys()}.')
        
        return f'Ошибка при определении статуса работы: {homework_name}'
        
    
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Функция проверки доступности всех переменных окружения."""

    if PRACTICUM_TOKEN is None:
        logging.critical(
            'Отсутствует обязательная переменная окружения:'
            ' "PRACTICUM_TOKEN" Программа принудительно остановлена. ')

    if TELEGRAM_TOKEN is None:
        logging.critical(
            'Отсутствует обязательная переменная окружения:'
            ' "TELEGRAM_TOKEN" Программа принудительно остановлена. ')

    if TELEGRAM_CHAT_ID is None:
        logging.critical(
            'Отсутствует обязательная переменная окружения:'
            ' "TELEGRAM_CHAT_ID" Программа принудительно остановлена. ')

    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID is not None:
        return True
    return False


def main():
    """Основная логика работы бота."""
    
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if check_tokens():

        current_timestamp = int(time.time())

        while True:
            try:
                response = get_api_answer(current_timestamp)
                homeworks = check_response(response)

                for homework in homeworks:
                    message = parse_status(homework)
                    send_message(bot, message)

                current_timestamp = int(time.time())
                time.sleep(RETRY_TIME)

            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
                time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
