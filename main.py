from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import json
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Load service account info from environment variable
SERVICE_ACCOUNT_INFO = os.environ.get("GOOGLE_SERVICE_ACCOUNT_INFO")
if not SERVICE_ACCOUNT_INFO:
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_INFO environment variable not set.")

service_account_info = json.loads(SERVICE_ACCOUNT_INFO)
creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

# Hardcoded spreadsheet ID and ranges
SHEET_ID = "1jlwROtexTkyqorAo0HIR1nct1iMgmj2fpv89mdlvZ1U"
GROUPS_RANGE = "Groups!A1:Z51"  # Adjust as needed
INDIVIDUAL_SHEET_ID = "1jlwROtexTkyqorAo0HIR1nct1iMgmj2fpv89mdlvZ1U"
INDIVIDUAL_RANGE = "فردي!A1:Z51"  # Adjust as needed

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_INFO, scopes=SCOPES
)
service = build("sheets", "v4", credentials=creds)
sheet_api = service.spreadsheets()

def safe_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0

@app.get("/api/groups")
def get_groups():
    result = (
        sheet_api.values()
        .get(spreadsheetId=SHEET_ID, range=GROUPS_RANGE, )
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return []
    headers = values[0]
    rows = [
        {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
        for row in values[1:]
    ]
    # Only keep the specified keys
    keys_of_interest = [
        "مجموعة",
        "مجموع الحضور",
        "مجموع المشاركة",
        "مشروع جماعي",
        "كتاب 1",
        "كتاب 2",
        "مجموع الدرجات"
    ]
    filtered_rows = [
        {k: row.get(k, "") for k in keys_of_interest}
        for row in rows
    ]
    # Remove the first object (header row or empty row)
    if filtered_rows:
        filtered_rows = filtered_rows[1:]
    # Sort by 'مجموع الدرجات' (as integer, descending)
    filtered_rows.sort(key=lambda x: safe_int(x.get("مجموع الدرجات", 0)), reverse=True)
    return filtered_rows

@app.get("/api/individual")
def get_individual():
    result = (
        sheet_api.values()
        .get(spreadsheetId=SHEET_ID, range=INDIVIDUAL_RANGE)
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return []
    headers = values[0]
    rows = [
        {headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
        for row in values[1:]
    ]
    # Only keep the specified keys
    keys_of_interest = [
        "الأسم",
        "مجموع الحضور",
        "مجموع المشاركة",
        "مشروع فردي",
        "الإبداع في المشروع",
        "كتاب 1",
        "كتاب 2",
        "مجموع الدرجات",
        "المجموعة"
    ]
    filtered_rows = [
        {k: row.get(k, "") for k in keys_of_interest}
        for row in rows
    ]
    # Remove the first object (header row or empty row)
    if filtered_rows:
        filtered_rows = filtered_rows[1:]
    # Sort by 'مجموع الدرجات' (as integer, descending), then by 'الأسم' (ascending)
    filtered_rows.sort(key=lambda x: (-safe_int(x.get("مجموع الدرجات", 0)), x.get("الأسم", "")))
    return filtered_rows

# Mount static files after API routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Optionally, serve index.html for all non-API routes (for React Router)
@app.get("/{full_path:path}")
async def serve_react_app():
    return FileResponse("static/index.html")
