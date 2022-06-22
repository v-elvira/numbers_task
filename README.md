# Тестовое задание (developer)

Необходимо разработать скрипт на языке Python 3, 

который будет выполнять следующие функции:

1. Получать данные с документа при помощи Google API, сделанного в [Google Sheets](https://docs.google.com/spreadsheets/d/1LTejK-Oo7L1bFreBIIcEZnF1W1RCC1s_jos3EuIP0jI/edit?usp=sharing) (необходимо копировать в свой Google аккаунт и выдать самому себе права).
2. Данные должны добавляться в БД, в том же виде, что и в файле –источнике, с добавлением колонки «стоимость в руб.»
    
    a. Необходимо создать DB самостоятельно, СУБД на основе PostgreSQL.
    
    b. Данные для перевода $ в рубли необходимо получать по курсу [ЦБ РФ](https://www.cbr.ru/development/SXML/).
    
3. Скрипт работает постоянно для обеспечения обновления данных в онлайн режиме (необходимо учитывать, что строки в Google Sheets таблицу могут удаляться, добавляться и изменяться).

Дополнения, которые дадут дополнительные баллы и поднимут потенциальный уровень оплаты труда:

4. a. Упаковка решения в docker контейнер
    
    b. Разработка функционала проверки соблюдения «срока поставки» из таблицы. В случае, если срок прошел, скрипт отправляет уведомление в Telegram.
    
    c. Разработка одностраничного web-приложения на основе Django или Flask. Front-end React.
    

5. Решение на проверку передается в виде ссылки на проект на Github.
В описании необходимо указать ссылку на ваш Google Sheets документ (открыть права чтения и записи для пользователя sales@numbersss.com ), а также инструкцию по запуску разработанных скриптов.

# Решение
После установки в виртуальное окружение pip install -r requirements.txt пункты 1-3 выполняются через запуск test_task.py. 

Скрипт подключается к базе данных postgres с пользователем postgres и паролем pwd, порт 5432.

Ссыка на Google Sheets: https://docs.google.com/spreadsheets/d/1gxZkyPBxCLwsfKzkpVySeOWaqQBnQYicMjVlZgkyS8U/edit#gid=0

4 а. Контейнер не получился. В docker-compose.yml только PostgreSQL (не знаю, нужен ли)

4 b. Работает. Если запустить отдельно bot_reminder.py, в Telegram можно подписаться на бота @sales_reminder_bot. Из test_task.py приходят оповещения по уже подписанным адресам.

4 c. Нет
