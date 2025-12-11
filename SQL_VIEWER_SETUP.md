# 🗄️ FREE SQL VIEWER - SETUP GUIDE

## Quick Installation Options

### Option 1: VS Code SQLite Extension (Fastest - 2 minutes)
1. Open VS Code
2. Press `Ctrl + Shift + X` to open Extensions
3. Search for **"SQLite"** by alexcvzz
4. Click **Install**
5. Press `Ctrl + Shift + P`
6. Type **"SQLite: Open Database"**
7. Select `db.sqlite3` from project folder
8. Done! Database explorer appears in sidebar

### Option 2: DBeaver Community Edition (Most Powerful)
- Download: https://dbeaver.io/download/
- Windows Installer, Free version
- Install and connect to `db.sqlite3`
- Full database management interface

### Option 3: Django Shell (No Installation)
```powershell
cd C:\Users\PRABIN\Desktop\resell_prj-main
.\venv\Scripts\python manage.py shell
```

Then use Python commands:
```python
from proj.models import Product, Customer, BikePaymentTransaction

# View all products
Product.objects.all()

# Count bikes
Product.objects.count()

# Filter by status
Product.objects.filter(status='available')

# View transactions
BikePaymentTransaction.objects.all()
```

## Database File Location
```
C:\Users\PRABIN\Desktop\resell_prj-main\db.sqlite3
```

## Recommended: Start with VS Code SQLite Extension!
- No separate download needed
- Works directly in VS Code
- Perfect for development
- Free and lightweight

**All options are completely FREE!**
