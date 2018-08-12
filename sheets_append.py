from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from datetime import datetime
import functools

SCOPES = 'https://www.googleapis.com/auth/spreadsheets'

def read_file(filename):
    with open(filename) as f:
        return f.read().strip().split()

def __append(service, spreadsheet, range, data_row):
    
    service.spreadsheets().values().append(spreadsheetId=spreadsheet,
            range=range,
            body={'values':[data_row]},
            valueInputOption="USER_ENTERED").execute()
    

def __setup():
    global append
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    spreadsheet_id, range_name = read_file('spreadsheet.txt')

    append = functools.partial(__append, service, spreadsheet_id, range_name)


__setup()

if __name__ == '__main__':
    append([str(datetime.now()), 45])
