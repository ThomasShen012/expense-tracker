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
    TRANSPORTATION = "Transportation"
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
    payment: PaymentMethod
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
#add column header to worksheet
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
#add_column_with_header(worksheet, "L")

#insert id col for db
def add_column(worksheet, header):

    row_num = len(worksheet.col_values(3))

    #get the data's row num instead of the sheet's row num
    print(row_num)

    new_col = [[header]]

    original_header = worksheet.row_values(1)
    if header not in original_header:
        worksheet.insert_cols(new_col, 1)
    else:
        print(f"Already a column called '{header}'")

    id_list = []
    id_list = [[str(index + 1)] for index in range(row_num-1)]
    print(id_list)

    #print(worksheet.col_values(1))

    id_range = f"A2:A{row_num}"
    
    worksheet.batch_update(
        [{
            'range': id_range,
            'values': id_list
        }])
    

def delete_column(worksheet):
    header = worksheet.row_values(1)
    print(header)
    print(len(header))

    for index in range(len(header)):
        print("index: ", index)
        print("header[index]: ", header[index])

        if header[index] not in ['ID', 'Date', 'Category', 'Payment', 'Amount', 'Description', 'L']:
            worksheet.delete_columns(index+1)

    #worksheet.delete_columns(1)

#worksheet = get_worksheet()
#add_column(worksheet, "ID")
#delete_column(worksheet)
'''




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
    payment: PaymentMethod = Form(...),
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
        payment.value, 
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
    payment: PaymentMethod = Form(...),
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

    # sort the data but also store its original row w/ enumerate
    ####  IMPORTANT  ####
    expense_data = sorted(
        enumerate(expense_data, start=2),
        key=lambda x: datetime.strptime(x[1]["Date"], "%Y-%m-%d")
    )

    # get the original row number of the data
    original_row = expense_data[index][0]
    print(original_row)

    updated_data = {
        "Date": date.strftime("%Y-%m-%d"),
        "Category": category.value, 
        "Payment": payment.value, 
        "Amount": amount, 
        "Description": description,
        "L": l
    }

    # update data in the worksheet
    worksheet.update(f"A{original_row}:F{original_row}", [[
        updated_data["Date"],
        updated_data["Category"],
        updated_data["Payment"],
        updated_data["Amount"],
        updated_data["Description"],
        updated_data["L"]
    ]])

    # update data in the fetched list
    expense_data[index][1].update(updated_data)

    # remove original row num to return the data
    ####  IMPORTANT  ####
    expense_data = [entry[1] for entry in expense_data]


    return templates.TemplateResponse(
        "get_all.html",
        {
            "request": request, 
            "message": "Date updated successfully",
            "all_expense": expense_data
        }
    )



@app.get("/test")
async def test_func():
    return {"data": "testing gateway"}


