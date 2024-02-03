import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


if __name__ == "__main__":

    creds, _ = google.auth.default()
    # create drive api client
    service = build("drive", "v3", credentials=creds)
    files = []
    page_token = None
    folder_id = '1vwGYHk9LLz6kcstquKfduZX-x3F8rEFQ'
    folder_id = '1AZVg4YPLD5Ffj5MAudFovUFiTtyQf0qc'
    # query = f"mimeType='application/vnd.google-apps.document'"
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document'"
    query = f"'{folder_id}' in parents"

    while True:
        response = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
            )
            .execute()
        )
        for file in response.get("files", []):
            # Process change
            print(f'Found file: {file.get("name")}, {file.get("id")}')
        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken", None)
        if page_token is None:
            break


