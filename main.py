from fastapi import FastAPI, Body, Request, Form
from pydantic import BaseModel
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
from datetime import datetime
from enum import Enum
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"))

# Google Sheets setup
Json = "rare-habitat-442607-u2-524a233c38ab.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_file(Json, scopes=SCOPES)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key("1edSXPXLFtcT7DYKZc4A6XFEiZGbWG_5MYHrhc0GIg2M")
worksheet_title = "Expenses"
headers = ["Date", "Category", "Payment", "Amount" , "Description", "L"]

class Category(str, Enum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    UTILITIES = "Utilities"
    ENTERTAINMENT = "Entertainment"
    HEALTH = "Health"
    OTHER = "Other"

class PaymentMethod(str, Enum):
    CASH = "Cash"
    CARD = "Card"
    APPLE_PAY = "Apple Pay"
    LINE_PAY = "Line Pay"
    EASY_CARD = "Easy Card"


# Pydantic model for an expense
class Expense(BaseModel):
    date: date
    category: Category 
    method: PaymentMethod
    amount: int  
    description: str
    l: float

@app.on_event("startup")
async def check_worksheet_exists():
    try:
        worksheet = sheet.worksheet(worksheet_title)
        # print(f"Worksheet '{worksheet_title}' already exists.")

    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{worksheet_title}' not found. Creating a new one...")
        worksheet = sheet.add_worksheet(title=worksheet_title, rows=100, cols=len(headers))
        worksheet.append_row(headers)
        print(f"Worksheet '{worksheet_title}' created.")

def get_worksheet():
    try:
        return sheet.worksheet(worksheet_title)
    except gspread.exceptions.WorksheetNotFound:
        raise HTTPException(status_code=404, detail=f"Worksheet '{worksheet_title}' not found")

######
'''
def add_column_with_header(worksheet, new_header):
    current_cols = worksheet.col_count
    current_rows = worksheet.row_count

    if len(worksheet.row_values(1)) < current_cols:
        current_cols = len(worksheet.row_values(1))

    new_column_index = current_cols + 1
    worksheet.resize(rows=current_rows, cols=new_column_index)
    worksheet.update_cell(1, new_column_index, new_header)

    for row in range(2, worksheet.row_count + 1):
        worksheet.update_cell(row, new_column_index, "")

worksheet = get_worksheet()
add_column_with_header(worksheet, "L")
'''
#####


### routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/add", response_class=HTMLResponse)
async def new_expense(request: Request):
    return templates.TemplateResponse("add.html", {"request": request})

@app.post("/add", response_class=HTMLResponse)
async def add_expense(
    request: Request,
    date: date = Form(...),
    category: Category = Form(...),
    method: PaymentMethod = Form(...),
    amount: float = Form(...),
    description: str = Form(...),
    l: str = Form(...)
):
    worksheet = get_worksheet()

    if l == "":
        l == None
    else:
        l == float(l)
    
    new_data = [
        date.strftime("%Y-%m-%d"), 
        category.value, 
        method.value, 
        amount, 
        description,
        l
    ]
    worksheet.append_row(new_data)

    return templates.TemplateResponse(
        "add.html", 
        {"request": request, "message": "Expense added successfully!", "data": new_data}
    )


@app.get("/expenses")
async def getall(request: Request):
    worksheet = get_worksheet()
    expense_data = worksheet.get_all_records()

    ### to sort data with date(reverse=True: descending order)
    expense_data.sort(key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%d"), reverse=False)

    return templates.TemplateResponse("get_all.html", {"request": request, "all_expense": expense_data})

@app.post("/expenses", response_class=HTMLResponse)
async def update_expense(
    request: Request,
    index: int = Form(...),
    date: date = Form(...),
    category: Category = Form(...),
    method: PaymentMethod = Form(...),
    amount: float = Form(...),
    description: str = Form(...),
    l: str = Form(...)
):
    if l == "":
        l == None
    else:
        l == float(l)

    worksheet = get_worksheet()
    expense_data = worksheet.get_all_records()

    expense_data.sort(key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%d"), reverse=False)

    updated_data = {
        "Date": date.strftime("%Y-%m-%d"), 
        "Category": category.value, 
        "Method": method.value, 
        "Amount": amount, 
        "Description": description,
        "L": l
    }
    print(updated_data)

    expense_data[index].update(updated_data)
    print(f"A{index + 2}:F{index + 2}")

    '''
    worksheet.update(f"A{index + 2}:F{index + 2}", [[
        updated_data["Date"],
        updated_data["Category"],
        updated_data["Method"],
        updated_data["Amount"],
        updated_data["Description"],
        updated_data["L"],
    ]])
    '''

    return templates.TemplateResponse(
        "get_all.html",
        {
            "request": request, 
            "message": "Date updated successfully", 
            "data": updated_data,
            "all_expense": expense_data
        }
    )

@app.get("/test")
async def test_func():
    return {"data": "testing gateway"}


