import os
import django
import random
from datetime import timedelta
from decimal import Decimal

# 1. Django Environment Setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant.settings')
django.setup()

from django.utils import timezone
from main.models import Order, OrderItem, Table, MenuItem, Expense
from django.contrib.auth.models import User

print("\n🧹 Cleaning old dummy orders and expenses...")
Order.objects.all().delete()
Expense.objects.all().delete()

# 2. Setup Tables
print("🪑 Setting up Restaurant Tables...")
tables = []
for i in range(1, 11):
    t, _ = Table.objects.get_or_create(name=f"T-{i}", defaults={'capacity': random.choice([2, 4, 6])})
    tables.append(t)

# 3. Get Menu Items
menu_items = list(MenuItem.objects.all())
if not menu_items:
    print("❌ No menu items found! Please run 'python seed_menu.py' first.")
    exit()

admin_user = User.objects.filter(is_superuser=True).first()
today = timezone.now()

print("📈 Simulating 30 Days of Business Data (Orders, Sales, Expenses)...")
total_orders = 0
total_expenses = 0

# 4. Generate Past 30 Days Data
for i in range(30, -1, -1):
    current_date = today - timedelta(days=i)
    is_weekend = current_date.weekday() >= 5
    
    # 🌟 WEEKEND PE JYADA RUSH HOTA HAI (15-35 orders), WEEKDAYS PE KAM (5-20 orders)
    num_orders = random.randint(15, 35) if is_weekend else random.randint(5, 20)
    
    for _ in range(num_orders):
        is_takeaway = random.choice([True, False, False]) # 33% takeaway
        table = None if is_takeaway else random.choice(tables)
        
        # Determine Status (Aaj ke kuch order live rakhenge)
        if i == 0 and random.random() < 0.3:
            status = random.choice(['Pending', 'Cooking', 'Ready'])
            pay_status = 'Pending'
        else:
            status = random.choice(['Completed', 'Completed', 'Completed', 'Cancelled'])
            pay_status = 'Completed' if status == 'Completed' else 'Pending'

        payment_mode = random.choice(['UPI', 'UPI', 'Cash', 'Card']) if pay_status == 'Completed' else None

        # Create Order
        order = Order.objects.create(
            table=table,
            status=status,
            payment_status=pay_status,
            payment_mode=payment_mode,
        )

        # Backdate the order to 'current_date' (Django auto_now_add override hack)
        fake_time = current_date - timedelta(hours=random.randint(0, 10), minutes=random.randint(0, 59))
        Order.objects.filter(order_id=order.order_id).update(created_at=fake_time, updated_at=fake_time + timedelta(minutes=30))

        # Add Random Items to Order
        order_total = 0
        num_items = random.randint(2, 6)
        selected_items = random.sample(menu_items, num_items)
        
        for item in selected_items:
            qty = random.randint(1, 3)
            price = item.price
            order_total += price * qty
            
            OrderItem.objects.create(
                order=order,
                item_name=item.name,
                qty=qty,
                price=price,
                item_status='Served' if status == 'Completed' else 'Pending'
            )
        
        # Update Total
        Order.objects.filter(order_id=order.order_id).update(total_amount=order_total)
        total_orders += 1

    # 🌟 GENERATE EXPENSES FOR THE DAY
    for _ in range(random.randint(1, 3)):
        cat = random.choice(["Raw Material", "Utility", "Staff Advance", "Maintenance", "Misc"])
        
        if cat == "Raw Material": desc, amt = "Dairy, Veggies & Meat", random.randint(800, 2500)
        elif cat == "Utility": desc, amt = "Gas & Electricity", random.randint(300, 900)
        elif cat == "Staff Advance": desc, amt = "Waiter Advance", random.randint(500, 1000)
        else: desc, amt = f"Daily {cat}", random.randint(100, 500)

        Expense.objects.create(
            title=desc,
            amount=amt,
            category=cat,
            payment_mode=random.choice(["Cash Drawer", "Owner UPI"]),
            date=current_date.date(),
            added_by=admin_user
        )
        total_expenses += 1

print(f"\n🎉 BOOM! Generated {total_orders} Orders and {total_expenses} Expenses.")
print("Go check your Dashboard, Deep Reports, and All Invoices! It looks ALIVE! 🚀")