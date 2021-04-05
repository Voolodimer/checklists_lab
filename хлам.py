from pprint import PrettyPrinter, pprint
# Добавить столбец
# sht = gc.open_by_key(DOCUMENT_ID)
#
# requests = []
#
# requests.append({
#       "insertDimension": {
#         "range": {
#           "sheetId": 0,
#           "dimension": "COLUMNS",
#           "startIndex": 2,
#           "endIndex": 4
#         },
#         "inheritFromBefore": True
#       }
#     })
#
# body = {
#     'requests': requests
# }
# sht.batch_update(body)

# res_str = ''
# a = ord('A')
# for i in range(a, a + 26):
#     res_str += chr(i) + ' '
#     #print(chr(i), end=' ')
#
# print()
# for i in range(a, a + 26):
#     for j in range(a, a + 26):
#         max = a
#         count = 0
#         res_str += chr(i) + chr(j + count) + ' '
#         #print(chr(i) + chr(j + count), end=' ')
#         a += 1
#         count += 1
#     # print()
#     a = ord('A')
#
# # print(res_str)
# res_list = res_str.rstrip(' ').split(' ')
# pp = PrettyPrinter(width=140, compact=True)
# pp.pprint(res_list)
#
# i = 0
# for i in range(1, len(res_list)):
#     print(res_list[i - 1], end=' ')
#     if i == 0:
#         i += 1
#         continue
#     if i % 26 == 0:
#         print()
#     i += 1

# test_list = ['r-8', '55', 'chev', '2021.04.01 21:24', 'Да', 'Нет', 'Да', 'Нет', 'Да', 'Нет', 'Да', 'Нет', 'Да', 'Нет', 'Да', 'Нет']
# str1 = 'fdg'
# str2 = 'fes'
# str3 = 'bge'
# tst_nw_lst = ['fdg', 'fes', 'fdb']
# new_list = []
# buff_list = []
#
#
# for i in range(0, 3):
#     buff_list.append(tst_nw_lst[i])
#     new_list.append(buff_list)
#     buff_list = []
#
# print(new_list)

from pprint import pprint
# import httplib2
# import apiclient
# from oauth2client.service_account import ServiceAccountCredentials
#
# CREDENTIALS_FILE = 'credentials.json'
# DOCUMENT_ID = '1agrCBLZTYY1NRRQk4wWkoD4iC4bbQ4StqCGOqmt9TgU'
#
# # Авторизуемся и получаем service — экземпляр доступа к API
# credentials = ServiceAccountCredentials.from_json_keyfile_name(
#     CREDENTIALS_FILE,
#     ['https://www.googleapis.com/auth/spreadsheets',
#      'https://www.googleapis.com/auth/drive'])
# # объект который работает с аутентификацией, через него будут проходить запросы
# httpAuth = credentials.authorize(httplib2.Http())
# # экземпляр обёртки API к которой мы будем обращаться
# service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)
#
# # Пример чтения файла
# values = service.spreadsheets().values().get(
#     spreadsheetId=DOCUMENT_ID,
#     range='A1:E10',
#     majorDimension='COLUMNS'
# ).execute()
# pprint(values)
# #shId = service.sheetId()
#
# spreadsheet = service.spreadsheets().get(spreadsheetId=DOCUMENT_ID).execute()
# sheetList = spreadsheet.get('sheets')
# for sheet in sheetList:
#     pass
#     # print(sheet['properties']['sheetId'], sheet['properties']['title'])
#
# sheetId = sheetList[0]['properties']['sheetId']
#
# #print('Мы будем использовать лист с Id = ', sheetId)
#
# #print(sheetId)
#
# # exit()
# # Пример записи в файл
#
# values = service.spreadsheets().values().batchUpdate(
#     spreadsheetId=DOCUMENT_ID,
#     body={
#         "valueInputOption": "USER_ENTERED",
#         "data": [
#             {"range": {
#                     "sheetId": sheetId,  # ID листа
#                     "startRowIndex": 1,  # Со строки номер startRowIndex
#                     "endRowIndex": 5,  # по endRowIndex - 1 (endRowIndex не входит!)
#                     "startColumnIndex": 0,  # Со столбца номер startColumnIndex
#                     "endColumnIndex": 1  # по endColumnIndex - 1
#                 },
#             "majorDimension": "ROWS",
#             "values": [
#                 ['1', '2', '4', '4', '5']
#             ]
#             }
# 	    ]
#     }
# ).execute()


