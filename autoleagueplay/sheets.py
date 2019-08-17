import pickle
from typing import List

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from autoleagueplay.ladder import Ladder
from autoleagueplay.paths import PackageFiles

SHEET_ID = '1XULvW97g46EdrYRuhiHBfARDkviULYjRO5dA8sMmxkY'
SHEET_NAME = 'Off Season 0'
INITIAL_LADDER_COL = 4   # D
RANK_ONE_ROW = 4
LADDER_LENGTH = 45
LADDER_SPACING = 1   # One column between each ladder

# If modifying these scopes, delete the file 'cred/sheets-api-token.pickle'
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def fetch_ladder_from_sheets(week_num: int) -> Ladder:
    values = get_values_from_sheet(get_credentials(), SHEET_ID, get_ladder_range(week_num), SHEET_NAME)
    bots = [row[0] for row in values]
    return Ladder(bots)


def get_ladder_range(week_num: int) -> str:
    col = get_col_name(INITIAL_LADDER_COL + week_num * (1 + LADDER_SPACING))
    return f'{col}{RANK_ONE_ROW}:{col}{RANK_ONE_ROW + LADDER_LENGTH}'


def get_col_name(col_num: int) -> str:
    """
    Transforms a column number to its column name. I.e. 1 => A, 2 => B, 27 => AA, 14558 => UMX
    :param col_num:
    :return: the name of the column
    """
    numeric = (col_num - 1) % 26
    letter = chr(65 + numeric)
    remaining_index = (col_num - 1) // 26
    if remaining_index > 0:
        return get_col_name(remaining_index - 1) + letter
    else:
        return letter


def get_credentials():
    creds = None
    # The file 'cred/sheets-api-token.pickle' stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if PackageFiles.sheets_token.exists():
        with open(PackageFiles.sheets_token, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if PackageFiles.credentials.exists():
                flow = InstalledAppFlow.from_client_secrets_file(PackageFiles.credentials, SHEETS_SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                raise ValueError(f"""ERROR: Cannot use Google Sheet API due to missing credentials.
                    Go to \'https://developers.google.com/sheets/api/quickstart/python\'.
                    Click the \'Enable the Google Sheets API\' button, accept, and download the \'credentials.json\'.
                    Put the \'credentials.json\' in the directory \'{PackageFiles.credentials.parent.absolute()}\' and try again.
                    Next time you run the script a browser will open, where Google asks you if this script can get permission.
                    Afterwards everything should work.
                    """)
        # Save the credentials for the next run
        with open(PackageFiles.sheets_token, 'wb') as token:
            pickle.dump(creds, token)
    return creds


def get_values_from_sheet(creds, spreadsheet_id: str, range: str, sheet_name: str) -> List[List[str]]:
    """
    Uses the Google Sheets API v4 to fetch the values from a spreadsheet.
    :param creds: credentials
    :param spreadsheet_id: the id of the spreadsheet. Can be found in the link. E.g.: '1u7iWUg0LA4wWaTMoDuBbBuA4de_fdL_kSxLyIQruvkg'
    :param range: the range to fetch, e.g.: 'D4:D48'
    :param sheet_name: the sheet name, e.g.: 'Ark1'
    :return: a list of rows that are lists of strings.
    """

    range_name = str(sheet_name) + "!" + str(range)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    return result.get('values', [])


if __name__ == '__main__':
    # As test, fetch and print the initial ladder
    values = get_values_from_sheet(get_credentials(), SHEET_ID, get_ladder_range(0))
    bots = [row[0] for row in values]
    print(bots)
