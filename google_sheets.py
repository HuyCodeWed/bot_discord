import gspread
from oauth2client.service_account import ServiceAccountCredentials
import discord

# Kết nối tới Google Sheet
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/config/credentials.json", scope)
client = gspread.authorize(creds)

# Mở Sheet theo tên
sheet = client.open("acccounts").sheet1

def get_all_accounts():
    rows = sheet.get_all_values()[1:]  # Bỏ dòng tiêu đề
    accounts = []
    options = []

    for row in rows:
        if len(row) >= 5:
            stt, tk, mk, level, time_limit = row
            accounts.append(row)
            options.append(discord.SelectOption(
                label=f"Tài khoản #{stt}",
                description=f"Level: {level} | Hạn cày: {time_limit}",
                value=stt
            ))
    return options, accounts

def delete_account_by_stt(stt):
    rows = sheet.get_all_values()
    for i, row in enumerate(rows[1:], start=2):  # Bắt đầu từ dòng 2
        if row[0] == str(stt):
            sheet.delete_rows(i)
            return row
    return None
