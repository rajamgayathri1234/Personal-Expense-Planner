CREATE DATABASE IF NOT EXISTS personal_expense_planner
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE personal_expense_planner;

CREATE TABLE IF NOT EXISTS users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(190) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_details (
  financial_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  monthly_income DECIMAL(12,2) DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_financial_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS categories (
  category_id INT AUTO_INCREMENT PRIMARY KEY,
  category_name VARCHAR(60) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS expenses (
  expense_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  category VARCHAR(60) NOT NULL,
  expense_date DATE NOT NULL,
  planned_amount DECIMAL(12,2) DEFAULT 0,
  description VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_expense_user_date(user_id, expense_date),
  CONSTRAINT fk_expense_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS income (
  income_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  source VARCHAR(60) NOT NULL,
  income_date DATE NOT NULL,
  description VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_income_user_date(user_id, income_date),
  CONSTRAINT fk_income_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS monthly_budgets (
  budget_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  category VARCHAR(60) NOT NULL,
  planned_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
  UNIQUE KEY uq_user_category(user_id, category),
  CONSTRAINT fk_budget_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

INSERT IGNORE INTO categories(category_name) VALUES
('Food'),('Rent'),('Health'),('Shopping'),('Groceries'),('Transport'),('Others');

-- Optional starter/demo data. Demo login: demo@example.com / Demo@12345
-- Password hash uses PBKDF2-HMAC-SHA256, 200,000 iterations.
INSERT IGNORE INTO users(user_id,name,email,password_hash)
VALUES (1,'Demo User','demo@example.com','a1b2c3d4e5f60718293a4b5c6d7e8f90$1426976fa462f4cb019ef4d30f2148393771e91a5dcc5fd2cf1e8c1361366bbd');

-- Demo transaction inserts are safe to run once on a fresh database.
INSERT INTO financial_details(user_id,monthly_income)
SELECT 1,60000 WHERE EXISTS(SELECT 1 FROM users WHERE user_id=1)
ON DUPLICATE KEY UPDATE monthly_income=VALUES(monthly_income);

INSERT INTO monthly_budgets(user_id,category,planned_amount)
SELECT 1,'Food',8000 WHERE EXISTS(SELECT 1 FROM users WHERE user_id=1)
ON DUPLICATE KEY UPDATE planned_amount=VALUES(planned_amount);
