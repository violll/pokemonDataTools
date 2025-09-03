# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START sheets_quickstart]
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import json

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = "16VckpktZW7qaUzu0Mvz2tLvCh9eS97y-BBmQB6R_JME"
SAMPLE_RANGE_NAME = "Team & Encounters!I5:J"

CREDS_PATH = r"C:\Users\Gil\OneDrive\Documents\Programming\pokemonDataTools\src\utils\google_sheets_api\credentials.json"
TOKEN_PATH = r"C:\Users\Gil\OneDrive\Documents\Programming\pokemonDataTools\src\utils\google_sheets_api\token.json"
OUTPUT_JSON_PATH = r"C:\Users\Gil\OneDrive\Documents\Programming\pokemonDataTools\src\utils\google_sheets_api\output.json"

def main():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists(TOKEN_PATH):
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          CREDS_PATH, SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open(TOKEN_PATH, "w") as token:
      token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()

    r = sheet.get(spreadsheetId=SAMPLE_SPREADSHEET_ID, 
                                   ranges =SAMPLE_RANGE_NAME, 
                                   fields = "sheets.data.rowData.values.dataValidation,sheets.data.rowData.values.userEnteredValue.stringValue")

    response = r.execute()
    print(response)

    with open(OUTPUT_JSON_PATH, "w+") as f:
      json.dump(response, f, indent=4)

  except HttpError as err:
    print(err)


if __name__ == "__main__":
  main()
# [END sheets_quickstart]
