import requests
import google.auth
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime


def get_pagespeed_insights(url, api_key):
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "key": api_key,
        "strategy": "mobile"  # Або 'desktop'
    }
    response = requests.get(endpoint, params=params)
    data = response.json()

    # Витягуємо основні показники
    insights = {
        "loading_time": data['lighthouseResult']['audits']['speed-index']['displayValue'],
        "performance_score": data['lighthouseResult']['categories']['performance']['score'] * 100,
        "first_contentful_paint": data['lighthouseResult']['audits']['first-contentful-paint'][
            'displayValue'],
        "largest_contentful_paint": data['lighthouseResult']['audits']['largest-contentful-paint'][
            'displayValue'],
        "time_to_interactive": data['lighthouseResult']['audits']['interactive']['displayValue'],
        "cumulative_layout_shift": data['lighthouseResult']['audits']['cumulative-layout-shift'][
            'displayValue'],
        "first_input_delay": data['lighthouseResult']['audits']['max-potential-fid']['displayValue']
    }

    return insights


def connect_to_google_sheets(sheet_id, creds_json):
    credentials = Credentials.from_service_account_file(creds_json, scopes=[
        "https://www.googleapis.com/auth/spreadsheets"])
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    return sheet


def append_to_google_sheet(sheet, sheet_id, range_name, values):
    body = {
        'values': values
    }
    result = sheet.values().append(
        spreadsheetId=sheet_id, range=range_name,
        valueInputOption="RAW", body=body).execute()
    print(f"{result.get('updates').get('updatedCells')} cells appended.")


def read_urls_from_file(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]


def run_pagespeed_and_update_sheet(urls, api_key, sheet_id, range_name, creds_json):
    sheet = connect_to_google_sheets(sheet_id, creds_json)

    for url in urls:
        result = get_pagespeed_insights(url, api_key)

        values = [[
            str(datetime.now()),
            url,
            result['loading_time'],
            result['performance_score'],
            result['first_contentful_paint'],
            result['largest_contentful_paint'],
            result['time_to_interactive'],
            result['cumulative_layout_shift'],
            result['first_input_delay']
        ]]

        # Виводимо результати в термінал
        print("Results:")
        print(f"Date and Time: {values[0][0]}")
        print(f"URL: {values[0][1]}")
        print(f"Loading Time: {values[0][2]}")
        print(f"Performance Score: {values[0][3]}")
        print(f"First Contentful Paint: {values[0][4]}")
        print(f"Largest Contentful Paint: {values[0][5]}")
        print(f"Time to Interactive: {values[0][6]}")
        print(f"Cumulative Layout Shift: {values[0][7]}")
        print(f"First Input Delay: {values[0][8]}")

        # Додаємо результати в Google Sheets
        append_to_google_sheet(sheet, sheet_id, range_name, values)


# Введіть ваші дані
api_key = "AIzaSyDRX9vQxzcTtZVVcNtYFG5f98nNBF7sXJM"
urls_file = "urls.txt"  # Вкажіть шлях до файлу з URL-адресами
sheet_id = "1m0jLAm0521GMY7L1mBiAdZSUSoiCxHdbdWO0N7NBOIA"
range_name = "Sheet1!A1:D1"
creds_json = "./credentials.json"

urls_to_test = read_urls_from_file(urls_file)
run_pagespeed_and_update_sheet(urls_to_test, api_key, sheet_id, range_name, creds_json)

