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

class GoogleSheetsApi:
  def __init__(self, api_call_params, creds_path, token_path, output_path, save=False):
    # If modifying these scopes, delete the file token.json.
    self.SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    self.api_call_params = api_call_params
    self.CREDS_PATH = creds_path
    self.TOKEN_PATH = token_path
    self.OUTPUT_JSON_PATH = output_path
    self.save = save

    self.creds = self.authorize()

    self.service = build("sheets", "v4", credentials=self.creds)

    self.main()

  def authorize(self):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(self.TOKEN_PATH):
      creds = Credentials.from_authorized_user_file(self.TOKEN_PATH, self.SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
      else:
        flow = InstalledAppFlow.from_client_secrets_file(
            self.CREDS_PATH, self.SCOPES
        )
        creds = flow.run_local_server(port=0)
      # Save the credentials for the next run
      with open(self.TOKEN_PATH, "w") as token:
        token.write(creds.to_json())

    return creds

  def main(self):
    try:
      # Call the Sheets API
      sheet = self.service.spreadsheets()

      r = sheet.get(**self.api_call_params)

      response = r.execute()

      if self.save:
        with open(self.OUTPUT_JSON_PATH, "w+") as f:
          json.dump(response, f, indent=4)

    except HttpError as err:
      print(err)


if __name__ == "__main__":
  GoogleSheetsApi()
# [END sheets_quickstart]
