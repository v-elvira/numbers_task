from pprint import pprint
from time import sleep
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from decimal import Decimal
import requests

import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials

import psycopg2
from psycopg2 import sql

import bot_reminder


def goodle_api_auth():

    # File from Google Developer Console
    CREDENTIALS_FILE = 'sales-test-353800-036108c631c7.json'

    # Get service for API access
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE,
        ['https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive'])
    httpAuth = credentials.authorize(httplib2.Http())
    service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)
    return service


def read_spreadsheet_values(service):

    # Google Sheets document ID (from URL)
    spreadsheet_id = '1gxZkyPBxCLwsfKzkpVySeOWaqQBnQYicMjVlZgkyS8U'

    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='A2:D',
        majorDimension='ROWS'
    ).execute()
    return values['values']


def get_valute_rate(code='USD'):

    result = requests.get("https://www.cbr.ru/scripts/XML_daily.asp")  # last value
    soup = BeautifulSoup(result.content, features='xml')
    rates = {i.CharCode.string: (
        Decimal(i.Value.string.replace(',', '.')),
        int(i.Nominal.string)
    ) for i in soup('Valute')
    }
    return rates[code][0] / rates[code][1]


def get_db_connection():
    conn = psycopg2.connect(dbname='postgres', user='postgres',
                     password='pwd', host='localhost')
    return conn


def notify(cursor):
    cursor.execute('''
    SELECT id, contract, TO_CHAR(delivery_date, 'yyyy-mm-dd') FROM sales
                   WHERE delivery_date <= NOW() + INTERVAL '1 DAY' 
                   ORDER BY id;''')
    records = cursor.fetchall()
    if records:
        bot_reminder.notify(tuple(records))
        print('Уведомление отправлено в телеграм')
    return


if __name__ == '__main__':

    SLEEP_TIME = 10  # seconds between loops for Google spreadsheets checking
    CURRENCY_CHECK_LOOPS = 60  # loops between usd rate updating
    NOTIFICATION_TIME = "5:14"  # Telegram bot alarm time
    NOTIFY_ON_START = True  # Telegram bot alarm on start

    notif_time = datetime.strptime(NOTIFICATION_TIME, "%H:%M").time()

    usd = get_valute_rate(code='USD')
    print('Курс usd:', usd)

    try:
        service = goodle_api_auth()
    except Exception as ex:
        print("Google authentication failed", ex)
        exit(1)

    old_values = set()
    new_values = set()

    conn = get_db_connection()

    loop_counter = 0
    first_loop = True

    with conn.cursor() as cursor:
        conn.autocommit = True

        set_drop_create_table = sql.SQL('''
        SET DATESTYLE TO German;
        DROP TABLE IF EXISTS sales;
        CREATE TABLE sales(id INT PRIMARY KEY, 
                            contract INT NOT NULL,
                            price NUMERIC NOT NULL, 
                            delivery_date DATE NOT NULL, 
                            rub_price NUMERIC NOT NULL);''')
        cursor.execute(set_drop_create_table)

        while True:
            #  if it's time to notify
            now_time = datetime.now()
            min_time = (now_time - timedelta(seconds=SLEEP_TIME//2)).time()
            max_time = (now_time + timedelta(seconds=SLEEP_TIME//2 + SLEEP_TIME%2)).time()
            #  should be exactly 1 notification per day
            if notif_time > min_time and notif_time <= max_time:
                notify(cursor)


            loop_counter += 1
            if not loop_counter % CURRENCY_CHECK_LOOPS:
                usd = get_valute_rate(code='USD')

            values = read_spreadsheet_values(service)
            new_values = set(tuple(i) for i in values if len(i) >= 4)  # if row is complete

            values_to_delete = old_values - new_values
            values_to_add = new_values - old_values

            if values_to_delete:
                delete = sql.SQL('DELETE FROM sales WHERE id in ({})').format(
                    sql.SQL(',').join(map(sql.Literal, {x[0] for x in values_to_delete}))
                )
                cursor.execute(delete)

            if values_to_add:
                values_to_add_with_rub = {(*x, usd * Decimal(x[2])) for x in values_to_add}

                insert = sql.SQL('INSERT INTO sales ('
                                 'id, contract, price, delivery_date, rub_price) VALUES {}').format(
                    sql.SQL(',').join(map(sql.Literal, values_to_add_with_rub)))
                cursor.execute(insert)

            # cursor.execute('SELECT * FROM sales ORDER BY id')
            # records = cursor.fetchall()
            # pprint(records)

            if NOTIFY_ON_START and first_loop:
                notify(cursor)
                first_loop = False

            cursor.execute('SELECT COUNT(*) FROM sales')
            records = cursor.fetchall()
            print('{}. Записей в базе: {}'.format(loop_counter, records[0][0]))
            old_values = new_values
            sleep(SLEEP_TIME)
    conn.close()
