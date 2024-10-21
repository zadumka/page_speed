import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Функція для отримання результатів PageSpeed Insights
def get_pagespeed_insights(url, api_key, strategy):
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "key": api_key,
        "strategy": strategy  # 'mobile' або 'desktop'
    }
    response = requests.get(endpoint, params=params)
    data = response.json()

    # Витягуємо основні показники
    insights = {
        "loading_time": data['lighthouseResult']['audits']['speed-index']['displayValue'],
        "performance_score": data['lighthouseResult']['categories']['performance']['score'] * 100,
        "first_contentful_paint": data['lighthouseResult']['audits']['first-contentful-paint']['displayValue'],
        "largest_contentful_paint": data['lighthouseResult']['audits']['largest-contentful-paint']['displayValue'],
        "time_to_interactive": data['lighthouseResult']['audits']['interactive']['displayValue'],
        "cumulative_layout_shift": data['lighthouseResult']['audits']['cumulative-layout-shift']['displayValue'],
        "first_input_delay": data['lighthouseResult']['audits']['max-potential-fid']['displayValue']
    }

    return insights

# Функція для підключення до Google Sheets
def connect_to_google_sheets(creds_json):
    credentials = Credentials.from_service_account_info(creds_json, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    service = build('sheets', 'v4', credentials=credentials)
    return service.spreadsheets()

# Функція для додавання даних до Google Sheets
def append_to_google_sheet(sheet, sheet_id, range_name, values):
    body = {
        'values': values
    }
    result = sheet.values().append(
        spreadsheetId=sheet_id, range=range_name,
        valueInputOption="RAW", body=body).execute()
    print(f"{result.get('updates').get('updatedCells')} cells appended.")

# Функція для зчитування URL із Google Sheets
def read_urls_from_google_sheet(sheet, sheet_id, range_name):
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = result.get('values', [])
    return [row[0] for row in values if row]  # Повертаємо лише перший стовпець

# Функція для запуску PageSpeed Insights і оновлення Google Sheets
def run_pagespeed_and_update_sheet(sheet, sheet_id, api_key):
    urls_sheet_range = "URLList!A2:A"  # Вказуємо назву листа та діапазон, де зберігаються URL
    urls_to_test = read_urls_from_google_sheet(sheet, sheet_id, urls_sheet_range)

    # Сторінки для кожного хосту
    range_name_neo = "Results_NEO!A1:I"  # Для хосту neo
    range_name_goit = "Results_Goit!A1:I"  # Для хосту goit.global

    for url in urls_to_test:
        # Викликаємо функцію двічі: для мобільної та десктопної версії
        mobile_result = get_pagespeed_insights(url, api_key, "mobile")
        desktop_result = get_pagespeed_insights(url, api_key, "desktop")

        # Результати для мобільної версії
        mobile_values = [[
            str(datetime.now()),
            url,
            "mobile",  # Додаємо інформацію, що це мобільна версія
            mobile_result['loading_time'],
            mobile_result['performance_score'],
            mobile_result['first_contentful_paint'],
            mobile_result['largest_contentful_paint'],
            mobile_result['time_to_interactive'],
            mobile_result['cumulative_layout_shift'],
            mobile_result['first_input_delay']
        ]]

        # Результати для десктопної версії
        desktop_values = [[
            str(datetime.now()),
            url,
            "desktop",  # Додаємо інформацію, що це десктопна версія
            desktop_result['loading_time'],
            desktop_result['performance_score'],
            desktop_result['first_contentful_paint'],
            desktop_result['largest_contentful_paint'],
            desktop_result['time_to_interactive'],
            desktop_result['cumulative_layout_shift'],
            desktop_result['first_input_delay']
        ]]

        # Виводимо результати в термінал
        print(f"Mobile Results for {url}: {mobile_values}")
        print(f"Desktop Results for {url}: {desktop_values}")

        # Визначаємо, на яку сторінку відправляти результати
        if "i-travel.com.ua" in url:
            append_to_google_sheet(sheet, sheet_id, range_name_neo, mobile_values)
            append_to_google_sheet(sheet, sheet_id, range_name_neo, desktop_values)
        elif "goit.global" in url:
            append_to_google_sheet(sheet, sheet_id, range_name_goit, mobile_values)
            append_to_google_sheet(sheet, sheet_id, range_name_goit, desktop_values)

# Введіть ваші дані
load_dotenv()  # Завантажуємо змінні середовища з .env файлу
api_key = os.getenv("PAGE_SPEED_SERVICE_API_KEY")  # Правильний спосіб отримання API ключа з .env
sheet_id = os.getenv("GOOGLE_SHEET_ID")

# Дані для підключення до Google Sheets
creds_json = {
    "type": os.getenv("GOOGLE_SERVICE_ACCOUNT_TYPE"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),  # Заміна для форматування
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_CERT_URL"),
    "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN")
}

# Підключення до Google Sheets
sheet = connect_to_google_sheets(creds_json)

# Запуск аналізу та оновлення Google Sheets
run_pagespeed_and_update_sheet(sheet, sheet_id, api_key)



