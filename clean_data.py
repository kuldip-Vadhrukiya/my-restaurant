import os
import django

# Django Environment Setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant.settings')
django.setup()

from main.models import Order, Expense, InventoryItem, Table

print("\n🧹 Cleaning up dummy business data...")

# 1. Delete All Orders (OrderItems automatically delete ho jayenge)
Order.objects.all().delete()
print("✅ All Orders, KDS Tickets, and Invoices deleted.")

# 2. Delete All Expenses
Expense.objects.all().delete()
print("✅ All Expenses deleted.")

# 3. Delete All Inventory (Optional: agar inventory bhi zero karni hai)
InventoryItem.objects.all().delete()
print("✅ All Inventory data deleted.")

# 4. Delete Dummy Tables (Jo seed_business ne banaye the)
Table.objects.all().delete()
print("✅ All Tables reset.")

print("\n🎉 Cleanup Complete! Your Menu and Staff Accounts are 100% safe.")
print("Now your Dashboard is back to 0-0 for real live testing! 🚀")