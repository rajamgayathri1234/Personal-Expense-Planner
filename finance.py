import pandas as pd
from db import get_connection
def save_monthly_income(user_id, amount, month):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO monthly_income_entries
            (user_id, income_month, amount)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE amount = VALUES(amount)
        """, (user_id, month, amount))
        conn.commit()
    finally:
        conn.close()


def add_bulk_expenses(user_id, expenses, planned_expenses, expense_date):
    conn = get_connection()

    try:
        cur = conn.cursor()

        for category, amount in expenses.items():
            if amount > 0:
                planned_amount = planned_expenses.get(category, 0)

                cur.execute("""
                    INSERT INTO expenses
                    (user_id, amount, category, expense_date,
                     planned_amount, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    amount,
                    category,
                    expense_date,
                    planned_amount,
                    "Monthly expense entry"
                ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

def get_monthly_expense_history(user_id, month):
    conn = get_connection()

    try:
        query = """
            SELECT
                expense_date AS Date,
                category AS Category,
                amount AS `Amount (₹)`,
                description AS Description
            FROM expenses
            WHERE user_id = %s
            AND expense_date >= %s
            AND expense_date < DATE_ADD(%s, INTERVAL 1 MONTH)
            ORDER BY expense_date DESC, expense_id DESC
        """

        return pd.read_sql(
            query, conn,
            params=(user_id, month, month)
        )

    finally:
        conn.close()


    try:
        cur = conn.cursor()

        month_start = expense_date.replace(day=1)

        for category, amount in expenses.items():

            if amount <= 0:
                continue

            cur.execute("""
                SELECT expense_id
                FROM expenses
                WHERE user_id = %s
                AND category = %s
                AND expense_date >= %s
                AND expense_date < DATE_ADD(%s, INTERVAL 1 MONTH)
                AND description = 'Monthly expense entry'
                ORDER BY expense_id
                LIMIT 1
            """, (user_id, category, month_start, month_start))

            existing = cur.fetchone()

            if existing:
                cur.execute("""
                    UPDATE expenses
                    SET amount = amount + %s
                    WHERE expense_id = %s
                """, (amount, existing[0]))

            else:
                cur.execute("""
                    INSERT INTO expenses
                    (user_id, amount, category, expense_date,
                     planned_amount, description)
                    VALUES (%s, %s, %s, %s, 0,
                            'Monthly expense entry')
                """, (
                    user_id,
                    amount,
                    category,
                    month_start
                ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    conn = get_connection()
    try:
        cur = conn.cursor()

        for category, amount in expenses.items():
            if amount > 0:
                cur.execute("""
                    INSERT INTO expenses
                    (user_id, amount, category, expense_date,
                     planned_amount, description)
                    VALUES (%s, %s, %s, %s, 0, %s)
                """, (
                    user_id, amount, category,
                    expense_date, "Monthly expense entry"
                ))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def _query(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        return pd.DataFrame(rows)
    finally:
        conn.close()


def get_month_summary(user_id, month):
    conn = get_connection()

    try:
        cur = conn.cursor(dictionary=True)
        start = month.replace(day=1)

        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM monthly_income_entries
            WHERE user_id = %s
            AND income_month = %s
        """, (user_id, start))

        monthly_income = cur.fetchone()["total"]

        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM income
            WHERE user_id = %s
            AND income_date >= %s
            AND income_date < DATE_ADD(%s, INTERVAL 1 MONTH)
        """, (user_id, start, start))

        additional_income = cur.fetchone()["total"]

        cur.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses
            WHERE user_id = %s
            AND expense_date >= %s
            AND expense_date < DATE_ADD(%s, INTERVAL 1 MONTH)
        """, (user_id, start, start))

        expenses = cur.fetchone()["total"]

        return {
            "income": float(monthly_income or 0)
                       + float(additional_income or 0),
            "expenses": float(expenses or 0)
        }

    finally:
        conn.close()

    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        start = month.replace(day=1)
        cur.execute("SELECT COALESCE(SUM(amount),0) total FROM income WHERE user_id=%s AND income_date >= %s AND income_date < DATE_ADD(%s, INTERVAL 1 MONTH)", (user_id,start,start))
        income = cur.fetchone()["total"]
        cur.execute("SELECT COALESCE(SUM(amount),0) total FROM expenses WHERE user_id=%s AND expense_date >= %s AND expense_date < DATE_ADD(%s, INTERVAL 1 MONTH)", (user_id,start,start))
        expenses = cur.fetchone()["total"]
        return {"income": float(income or 0), "expenses": float(expenses or 0)}
    finally: conn.close()

def get_expense_summary(user_id, month):
    sql = """
    SELECT c.category_name AS category, COALESCE(b.planned_amount, 0) AS planned,
           COALESCE(SUM(e.amount), 0) AS actual
    FROM categories c
    LEFT JOIN monthly_budgets b ON b.user_id=%s AND b.category=c.category_name
    LEFT JOIN expenses e ON e.user_id=%s AND e.category=c.category_name
         AND e.expense_date >= %s AND e.expense_date < DATE_ADD(%s, INTERVAL 1 MONTH)
    GROUP BY c.category_name, b.planned_amount
    ORDER BY FIELD(c.category_name,'Food','Rent','Health','Shopping','Groceries','Transport','Others')
    """
    return _query(sql, (user_id, user_id, month, month))

def get_transactions(user_id, kind):
    if kind == "expense":
        return _query("SELECT expense_date AS Date, category AS Category, amount AS `Amount (₹)`, description AS Description FROM expenses WHERE user_id=%s ORDER BY expense_date DESC LIMIT 100", (user_id,))
    return _query("SELECT income_date AS Date, source AS Source, amount AS `Amount (₹)`, description AS Description FROM income WHERE user_id=%s ORDER BY income_date DESC LIMIT 100", (user_id,))

def add_expense(user_id, amount, category, expense_date, planned, note):
    conn=get_connection()
    try:
        cur=conn.cursor()
        cur.execute("INSERT INTO expenses(user_id,amount,category,expense_date,planned_amount,description) VALUES(%s,%s,%s,%s,%s,%s)",(user_id,amount,category,expense_date,planned,note))
        conn.commit()
    finally: conn.close()

def add_income(user_id, amount, source, income_date, note):
    conn=get_connection()
    try:
        cur=conn.cursor()
        cur.execute("INSERT INTO income(user_id,amount,source,income_date,description) VALUES(%s,%s,%s,%s,%s)",(user_id,amount,source,income_date,note))
        conn.commit()
    finally: conn.close()

def get_monthly_income(user_id, month):
    return get_month_summary(user_id, month)["income"]

def get_user_details(user_id):
    conn=get_connection()
    try:
        cur=conn.cursor(dictionary=True)
        cur.execute("SELECT u.name,u.email,COALESCE(f.monthly_income,0) monthly_income FROM users u LEFT JOIN financial_details f ON f.user_id=u.user_id WHERE u.user_id=%s",(user_id,))
        return cur.fetchone() or {}
    finally: conn.close()

def update_user_details(user_id,name,email,monthly_income):
    conn=get_connection()
    try:
        cur=conn.cursor()
        cur.execute("UPDATE users SET name=%s,email=%s WHERE user_id=%s",(name,email,user_id))
        cur.execute("INSERT INTO financial_details(user_id,monthly_income) VALUES(%s,%s) ON DUPLICATE KEY UPDATE monthly_income=VALUES(monthly_income)",(user_id,monthly_income))
        conn.commit()
    finally: conn.close()

def get_budget_rows(user_id):
    conn=get_connection()
    try:
        cur=conn.cursor()
        cur.execute("SELECT category,planned_amount FROM monthly_budgets WHERE user_id=%s",(user_id,))
        return {r[0]:float(r[1]) for r in cur.fetchall()}
    finally: conn.close()

def save_budget(user_id,category,amount):
    conn=get_connection()
    try:
        cur=conn.cursor()
        cur.execute("INSERT INTO monthly_budgets(user_id,category,planned_amount) VALUES(%s,%s,%s) ON DUPLICATE KEY UPDATE planned_amount=VALUES(planned_amount)",(user_id,category,amount))
        conn.commit()
    finally: conn.close()

def get_monthly_trend(user_id):
    return _query("SELECT DATE_FORMAT(expense_date,'%Y-%m') month, SUM(amount) expenses FROM expenses WHERE user_id=%s GROUP BY DATE_FORMAT(expense_date,'%Y-%m') ORDER BY month",(user_id,))
