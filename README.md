# Kirana Store Management System

A beginner-friendly web project built with **Python Flask + SQLite + HTML/CSS**.

## Features
- Dashboard with product count, low-stock count, today's sales and estimated inventory value
- Add, edit and delete products
- Search products by name/category
- Record sales and automatically reduce stock
- View recent sales
- Low-stock warning
- SQLite database is created automatically and seeded with sample products on first run

## Requirements
- Python 3.9+
- Flask

## Run on Windows
1. Extract the ZIP file.
2. Open the extracted `Kirana_Store_Management_System` folder.
3. In the address bar of File Explorer, type `cmd` and press Enter.
4. Run:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
5. Open http://127.0.0.1:5000 in your browser.

If `python` is not recognized, install Python from https://www.python.org/downloads/ and tick **Add Python to PATH** during installation.

## Demo data
The app inserts a few sample products the first time it runs. You can delete or edit them and add your own.

## Note
This is an educational/demo project. Before real commercial use, add authentication, backups, stronger validation and deployment security.
