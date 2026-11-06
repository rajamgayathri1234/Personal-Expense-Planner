# Personal Expense Planner

A Streamlit personal-finance application using Python, MySQL, Pandas and Plotly.

## Features
- Login and registration with PBKDF2 password hashing
- Home dashboard with income, expenses, savings and recommended savings
- Planned vs actual expense summary and chart
- Expense and additional-income entry forms
- Rule-based AI-style budget and savings insights
- Monthly reports with CSV download
- User details and monthly category budgets
- Indian Rupee (₹) display

## 1. Requirements
- Python 3.10 or newer
- MySQL Server and MySQL Workbench (or MySQL command line)

## 2. Create the database
Open MySQL Workbench, open `sql/schema.sql`, and execute the script.
It creates the `personal_expense_planner` database and all required tables.

Optional demo account:
- Email: `demo@example.com`
- Password: `Demo@12345`

You can also register a new account from the app.

## 3. Configure MySQL
Copy `.env.example` to `.env` in the project root.
Update `DB_USER` and `DB_PASSWORD` to match your local MySQL account.

Example:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=personal_expense_planner
```

## 4. Install packages (Windows PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

## 5. Run the application
From the project folder:
```powershell
streamlit run app.py
```
The browser will open at `http://localhost:8501`.

## Notes
- Every transaction is linked to the signed-in user.
- The recommendations are rule-based Python logic, not a connected generative AI model.
- Do not share your `.env` file or database password.
