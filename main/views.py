from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, F
from decimal import Decimal
from datetime import timedelta
import json
from .models import (
    Order, OrderItem, Category, MenuItem, Table, Staff, Role, 
    RestaurantSetting, TaxSetting, InventoryItem, Expense,
    Attendance, OverrideLog, ZReport, WaiterAlert,
    ItemVariant, ItemAddOn )

# ==========================================
# 1. CUSTOMER PORTAL
# ==========================================
def home(request):
    if request.GET.get('table'):
        request.session['customer_table'] = request.GET.get('table')
    context = {
        'table_number': request.session.get('customer_table', 'Unknown'),
        'setting': RestaurantSetting.objects.first(),
        'features': [
            {'icon': 'fa-fire-burner', 'label': 'Live Kitchen', 'color': 'bg-red-50 text-red-500'},
            {'icon': 'fa-bolt', 'label': 'Superfast', 'color': 'bg-blue-50 text-blue-500'},
            {'icon': 'fa-leaf', 'label': '100% Fresh', 'color': 'bg-emerald-50 text-emerald-500'},
            {'icon': 'fa-spray-can-sparkles', 'label': 'Hygienic', 'color': 'bg-cyan-50 text-cyan-500'},
        ]
    }
    return render(request, "main/home.html", context)

def menu(request):
    if request.GET.get('table'): request.session['customer_table'] = request.GET.get('table')
    context = {
        'categories': Category.objects.filter(is_active=True).prefetch_related('items').order_by('sort_order'),
        'table_number': request.session.get('customer_table', 'Unknown')
    }
    return render(request, "main/menu.html", context)

# ==========================================
# 2. CART API
# ==========================================
def get_cart(request):
    if "cart" not in request.session: request.session["cart"] = {}
    return request.session["cart"]

def cart_add(request, item_id):
    cart, item_id = get_cart(request), str(item_id)
    product = get_object_or_404(MenuItem, id=int(item_id))
    if item_id in cart: cart[item_id]["qty"] += 1
    else:
        cart[item_id] = {
            "name": product.name, "price": float(product.price),
            "image": product.image.url if product.image else "",
            "qty": 1, "spice": request.GET.get("spice", "Regular"), "instruction": request.GET.get("instruction", "")
        }
    request.session.modified = True
    return JsonResponse({"success": True, "qty": cart[item_id]["qty"]})

def cart_inc(request, item_id):
    cart, item_id = get_cart(request), str(item_id)
    if item_id in cart: cart[item_id]["qty"] += 1; request.session.modified = True
    return JsonResponse({"success": True})

def cart_dec(request, item_id):
    cart, item_id = get_cart(request), str(item_id)
    if item_id in cart:
        cart[item_id]["qty"] -= 1
        if cart[item_id]["qty"] <= 0: del cart[item_id]
        request.session.modified = True
    return JsonResponse({"success": True})

def cart_count(request): return JsonResponse({"count": sum(i["qty"] for i in request.session.get("cart", {}).values())})
def cart_data(request): return JsonResponse({"items": [{"id": int(k), **v, "total": v["price"] * v["qty"]} for k, v in request.session.get("cart", {}).items()]})
def cart_update_spice(request, item_id, level): cart, item_id = get_cart(request), str(item_id); cart[item_id]["spice"] = level; request.session.modified = True; return JsonResponse({"success": True})
def cart_update_instruction(request, item_id): cart, item_id = get_cart(request), str(item_id); cart[item_id]["instruction"] = request.GET.get("text", ""); request.session.modified = True; return JsonResponse({"success": True})

@csrf_exempt
def place_order(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            cart_items = data.get('cart', {})
            table_name = request.session.get('customer_table', 'Takeaway')
            
            if not cart_items:
                return JsonResponse({"success": False, "message": "Cart is empty"})

            table_obj = Table.objects.filter(name=table_name).first()
            if not table_obj:
                return JsonResponse({"success": False, "message": "Invalid Table"})

            # --- 🌟 CRITICAL LOCK CHECK START ---
            # अगर बिल मांगा जा चुका है (status='Completed'), तो नया आर्डर नहीं लेने देंगे
            is_locked = Order.objects.filter(table=table_obj, status='Completed', payment_status='Pending').exists()
            if is_locked:
                return JsonResponse({"success": False, "message": "Bill is being generated. Menu is locked!"})
            # --- 🌟 CRITICAL LOCK CHECK END ---

            new_items_total = sum(float(i["price"]) * int(i["qty"]) for i in cart_items.values())

            # एक्टिव आर्डर ढूंढो
            active_order = Order.objects.filter(table=table_obj, payment_status='Pending').exclude(status='Cancelled').first()
            
            if active_order:
                # पुराने आर्डर में ही पैसे जोड़ो
                active_order.total_amount += Decimal(str(new_items_total))
                active_order.status = 'Pending' # आर्डर को वापस एक्टिव मोड में डालो
                active_order.save()
            else:
                # फ्रेश आर्डर बनाओ
                active_order = Order.objects.create(table=table_obj, total_amount=new_items_total, status='Pending', payment_status='Pending')

            # आइटम्स को सेव करो
            for i in cart_items.values():
                OrderItem.objects.create(
                    order=active_order, 
                    item_name=i["name"], 
                    qty=i["qty"], 
                    price=Decimal(str(i["price"])), 
                    spice=i.get("spice", "Regular"), 
                    instruction=i.get("note", ""), 
                    item_status='Pending',
                    variant_name=i.get("variant", "Regular")
                )

            request.session["cart"] = {}
            request.session["active_order_id"] = active_order.order_id
            return JsonResponse({"success": True, "order_id": active_order.order_id})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})
    return JsonResponse({"success": False})

def orders_page(request):
    # 1. सत्र (Session) या URL से ऑर्डर आईडी प्राप्त करें
    order_id = request.GET.get('order_id') or request.session.get('active_order_id')
    
    if not order_id: 
        return render(request, "main/orders.html", {"order": None})
    
    try:
        # 2. ऑर्डर और उसके आइटम्स को एक बार में उठाएं (Performance Optimized)
        order = Order.objects.prefetch_related('items').get(order_id=order_id)
        
        # 🌟 लॉजिक: नया आइटम सबसे ऊपर और पुराना नीचे (-id)
        all_items = order.items.all().order_by('-id') 
        
        # 🌟 टाइमर लॉजिक: हर आइटम के लिए 'Order Age' निकालना
        for item in all_items:
            # यह पता लगाता है कि ऑर्डर बने हुए कितने सेकंड बीत गए
            diff = timezone.now() - order.created_at
            item.seconds_passed = int(diff.total_seconds())

        # 3. लाइव बिल कैलकुलेशन (Real-time Breakdown)
        subtotal = float(order.total_amount)
        cgst = round(subtotal * 0.025, 2) # 2.5% CGST
        sgst = round(subtotal * 0.025, 2) # 2.5% SGST
        grand_total = round(subtotal + cgst + sgst, 2)

        # 4. स्मार्ट स्टेटस लॉजिक (Zomato Style)
        served_count = sum(1 for i in all_items if i.item_status == 'Served')
        total_items = all_items.count()
        
        if served_count == total_items and total_items > 0: 
            overall_status = "All items served! 🍽️"
            progress_width = "100%"
        elif any(i.item_status == 'Ready' for i in all_items): 
            overall_status = "Items are on the way! 🏃‍♂️"
            progress_width = "75%"
        elif any(i.item_status == 'Cooking' for i in all_items):
            overall_status = "Chef is cooking your meal 👨‍🍳"
            progress_width = "50%"
        else: 
            overall_status = "Order confirmed & received ✅"
            progress_width = "25%"
            
        # 5. डेटा को HTML के लिए तैयार करना (Context)
        context = {
            "order": order, 
            "items": all_items,
            "subtotal": subtotal,
            "cgst": cgst, 
            "sgst": sgst, 
            "grand_total": grand_total, 
            "overall_status": overall_status, 
            "progress_width": progress_width,
            "served_count": served_count,
            "total_items": total_items
        }
        return render(request, "main/orders.html", context)

    except Order.DoesNotExist: 
        return render(request, "main/orders.html", {"order": None})

def bill_page(request):
    order_id = request.GET.get('order_id') or request.session.get('active_order_id')
    if not order_id: return render(request, "main/bill.html", {"order": None})
    try:
        order = Order.objects.prefetch_related('items').get(order_id=order_id)
        subtotal = float(order.total_amount)
        cgst = sgst = subtotal * 0.025
        return render(request, "main/bill.html", {'order': order, 'items': order.items.all(), 'subtotal': round(subtotal, 2), 'cgst': round(cgst, 2), 'sgst': round(sgst, 2), 'grand_total': round(subtotal + cgst + sgst)})
    except Order.DoesNotExist: return render(request, "main/bill.html", {"order": None})

@csrf_exempt
def process_payment(request):
    if request.method == "POST":
        try:
            order_id = request.session.get('active_order_id')
            if order_id:
                order = Order.objects.get(order_id=order_id); order.payment_status = 'Completed'; order.payment_mode = json.loads(request.body).get('payment_mode', 'Cash'); order.status = 'Completed'; order.save()
                if "active_order_id" in request.session: del request.session["active_order_id"]
                if "cart" in request.session: del request.session["cart"]
                return JsonResponse({"success": True})
        except: return JsonResponse({"success": False})
    return JsonResponse({"success": False})

# ==========================================
# CUSTOMER ACTIONS API (Call Waiter, Bill Req)
# ==========================================
@csrf_exempt
def customer_call_action(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Session se table number nikalenge (Strict Validation)
            table_name = request.session.get('customer_table')
            action = data.get('action') # values: 'water', 'bill', 'clean', 'waiter'

            if not table_name or table_name == 'Unknown':
                return JsonResponse({'success': False, 'message': 'Table session not found. Please scan QR again.'})

            table_obj = Table.objects.filter(name=table_name).first()
            if not table_obj:
                return JsonResponse({'success': False, 'message': 'Invalid Table.'})

            # Check if there is an active order (Bill bina order ke nahi mang sakte)
            active_order = Order.objects.filter(table=table_obj, payment_status='Pending').exclude(status='Cancelled').first()
            
            if action == 'bill' and not active_order:
                return JsonResponse({'success': False, 'message': 'No active order found to generate bill.'})

            # Message formatting
            msg_dict = {
                'water': 'Please serve regular water.',
                'clean': 'Table cleanup requested.',
                'waiter': 'Customer needs assistance.',
                'bill': 'Customer has requested the final bill.'
            }
            message = msg_dict.get(action, 'Assistance required.')

            # Create Alert in Database for Waiter to see
            WaiterAlert.objects.create(
                table=table_obj,
                alert_type=action,
                message=message,
                is_resolved=False
            )

            # Strict Logic: Agar Bill manga hai, toh order status update karo
            if action == 'bill' and active_order:
                # Hum status ko 'Completed' (khana ban gaya) karte hain taaki cashier ko dikhe
                if active_order.status != 'Completed':
                    active_order.status = 'Completed' 
                    active_order.save()

            return JsonResponse({'success': True, 'message': 'Request sent to staff!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
            
    return JsonResponse({'success': False, 'message': 'Invalid Request'})

# ==========================================
# 3. AUTHENTICATION
# ==========================================
def redirect_based_on_role(user):
    if user.is_superuser: return redirect('dashboard_overview')
    if hasattr(user, 'staff') and user.staff.role:
        role_name = user.staff.role.name.lower()
        if 'manager' in role_name: return redirect('manager_dashboard')
        elif 'cashier' in role_name: return redirect('cashier_pos')
        elif 'waiter' in role_name: return redirect('waiter_floor')
    return redirect('dashboard_overview')

def admin_login(request):
    if request.user.is_authenticated: return redirect_based_on_role(request.user)
    if request.method == "POST":
        user = authenticate(username=request.POST.get("username"), password=request.POST.get("password")) 
        if user: login(request, user); return redirect_based_on_role(user)
        return render(request, 'panel/auth/login.html', {'error': 'Invalid credentials'})
    return render(request, 'panel/auth/login.html')

def admin_logout(request): logout(request); return redirect('admin_login')

# ==========================================
# 4. ADMIN OPERATIONS
# ==========================================
@login_required(login_url='admin_login')
def dashboard_overview(request):
    today = timezone.now().date()
    todays_orders = Order.objects.filter(created_at__date=today)
    return render(request, 'panel/dashboard/overview.html', {
        'total_revenue': sum(o.total_amount for o in todays_orders if o.payment_status == 'Completed'),
        'total_orders_count': todays_orders.count(),
        'active_tables': Order.objects.filter(payment_status='Pending').exclude(status='Cancelled').values('table').distinct().count(),
        'total_tables': Table.objects.count(),
        'recent_orders': Order.objects.select_related('table').all().order_by('-created_at')[:5],
        'total_items': MenuItem.objects.count(),
        'out_of_stock': MenuItem.objects.filter(is_available=False).count()
    })

@login_required(login_url='admin_login')
def live_orders(request):
    if request.method == "POST":
        action, order_id = request.POST.get('action'), request.POST.get('order_id')
        try:
            order = Order.objects.get(order_id=order_id)
            if action == 'accept': order.items.filter(item_status='Pending').update(item_status='Cooking'); order.status = 'Cooking'
            elif action == 'force_ready': order.items.exclude(item_status='Served').update(item_status='Ready'); order.status = 'Ready'
            elif action == 'settle': order.items.all().update(item_status='Served'); order.status, order.payment_status, order.payment_mode = 'Completed', 'Completed', 'Cash'
            elif action == 'cancel': order.status = 'Cancelled'
            order.save()
        except Order.DoesNotExist: pass
        return redirect('live_orders')

    active_orders = Order.objects.prefetch_related('items', 'table').filter(status__in=['Pending', 'Cooking', 'Ready']).exclude(status='Cancelled').order_by('-created_at')
    pending = [o for o in active_orders if o.status == 'Pending']
    kitchen = [o for o in active_orders if o.status == 'Cooking']
    ready = [o for o in active_orders if o.status == 'Ready']

    return render(request, 'panel/operations/live_orders.html', {
        'pending_orders': pending, 'kitchen_orders': kitchen, 'ready_orders': ready,
        'count_pending': len(pending), 'count_kitchen': len(kitchen), 'count_ready': len(ready),
        'unpaid_value': round(sum(float(o.total_amount) for o in active_orders if o.payment_status == 'Pending'), 2),
        'active_tables_count': len(set(o.table.name for o in active_orders if o.table))
    })

@login_required(login_url='admin_login')
def kitchen_status(request):
    if request.method == "POST":
        try:
            order = Order.objects.get(order_id=request.POST.get('order_id'))
            order.items.filter(item_status__in=['Pending', 'Cooking']).update(item_status='Ready')
            order.status = 'Ready'; order.save()
        except Order.DoesNotExist: pass
        return redirect('kitchen_status')

    active_orders = []
    current_time = timezone.now()
    for order in Order.objects.prefetch_related('items', 'table').filter(status__in=['Pending', 'Cooking']).order_by('created_at'):
        order.elapsed_mins = int((current_time - order.created_at).total_seconds() // 60)
        active_orders.append(order)

    return render(request, 'panel/operations/kitchen_status.html', {'active_orders': active_orders})

@csrf_exempt
def kds_screen(request):
    if request.method == "POST":
        try:
            item = OrderItem.objects.get(id=request.POST.get('item_id'))
            item.item_status = request.POST.get('new_status'); item.save()
        except OrderItem.DoesNotExist: pass
        return redirect('kds_screen')
    active_items = OrderItem.objects.filter(item_status__in=['Pending', 'Cooking']).select_related('order', 'order__table').order_by('order__created_at')
    for item in active_items: item.kitchen_route = "Main"
    return render(request, 'main/kds.html', {'active_items': active_items})

# ==========================================
# 5. STAFF, INVENTORY, TABLES, MENU
# ==========================================
@login_required(login_url='admin_login')
def staff_management(request):
    if request.method == "POST":
        try:
            staff_id, name = request.POST.get('staff_id'), request.POST.get('name')
            role_id, phone = request.POST.get('role'), request.POST.get('phone') 
            salary = request.POST.get('salary', 0)
            pos_access = request.POST.get('pos_access') == 'on'
            password = request.POST.get('password') 
            role = get_object_or_404(Role, id=role_id) if role_id else None

            if staff_id:
                staff = get_object_or_404(Staff, id=staff_id)
                staff.name, staff.role, staff.phone, staff.salary = name, role, phone, salary
                if pos_access and password:
                    if not staff.user: staff.user = User.objects.create_user(username=phone, password=password)
                    else: staff.user.username = phone; staff.user.set_password(password); staff.user.save()
                    staff.pin_code = password
                elif not pos_access and staff.user:
                    staff.user.delete(); staff.user = None; staff.pin_code = ''
                staff.save(); messages.success(request, "Staff updated successfully!")
            else:
                if pos_access and User.objects.filter(username=phone).exists():
                    messages.error(request, "Phone number already registered."); return redirect('staff_management')
                user = User.objects.create_user(username=phone, password=password) if (pos_access and password) else None
                Staff.objects.create(user=user, name=name, role=role, phone=phone, salary=salary, pin_code=password if pos_access else '', is_active=True)
                messages.success(request, "Staff added successfully!")
        except Exception as e: messages.error(request, f"Error: {e}")
        return redirect('staff_management')

    if not Role.objects.exists():
        for r in ['Manager', 'Cashier', 'Chef', 'Waiter']: Role.objects.get_or_create(name=r)

    return render(request, 'panel/management/staff_list.html', {'staff_list': Staff.objects.all().order_by('-is_active', 'name'), 'roles': Role.objects.all().order_by('name')})

@login_required(login_url='admin_login')
def delete_staff(request, id): Staff.objects.filter(id=id).delete(); return redirect('staff_management')
@login_required(login_url='admin_login')
def add_role(request):
    if request.method == "POST":
        name = request.POST.get('role_name')
        if name and not Role.objects.filter(name__iexact=name).exists(): Role.objects.create(name=name)
    return redirect('staff_management')
@login_required(login_url='admin_login')
def delete_role(request, id): Role.objects.filter(id=id).delete(); return redirect('staff_management')

@login_required(login_url='admin_login')
def inventory_management(request):
    if request.method == "POST":
        try: InventoryItem.objects.create(name=request.POST.get('name'), category=request.POST.get('category'), stock=float(request.POST.get('stock')), unit=request.POST.get('unit'), min_level=float(request.POST.get('min_level')), price_per_unit=float(request.POST.get('price_per_unit')))
        except: pass
        return redirect('inventory')
    items = InventoryItem.objects.all().order_by('name')
    return render(request, 'panel/management/inventory.html', {'items': items, 'total_items': items.count(), 'low_stock_count': sum(1 for i in items if i.stock <= i.min_level), 'inventory_value': round(sum(i.stock * i.price_per_unit for i in items), 2)})

@login_required(login_url='admin_login')
def update_inventory_stock(request):
    if request.method == "POST":
        try: item = InventoryItem.objects.get(id=request.POST.get('item_id')); item.stock += float(request.POST.get('added_stock')); item.save()
        except: pass
    return redirect('inventory')
@login_required(login_url='admin_login')
def delete_inventory_item(request, id): InventoryItem.objects.filter(id=id).delete(); return redirect('inventory')

@login_required(login_url='admin_login')
def accounts_expense(request):
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'add':
            try: Expense.objects.create(title=request.POST.get('desc'), amount=float(request.POST.get('amount')), category=request.POST.get('category'), payment_mode=request.POST.get('mode'), date=request.POST.get('date'), added_by=request.user)
            except: pass
        elif action == 'delete':
            try: Expense.objects.get(id=request.POST.get('expense_id')).delete()
            except: pass
        return redirect('accounts_expense')
    todays_sales = sum(o.total_amount for o in Order.objects.filter(created_at__date=timezone.now().date(), payment_status='Completed'))
    return render(request, 'panel/reports/expenses.html', {'todays_sales': float(todays_sales), 'expenses': Expense.objects.all().order_by('-date', '-id')})

@login_required(login_url='admin_login')
def table_management(request):
    if request.method == "POST":
        try:
            tid, name, cap = request.POST.get('table_id'), request.POST.get('name').strip(), request.POST.get('capacity', 4)
            if tid:
                if Table.objects.filter(name__iexact=name).exclude(id=tid).exists(): messages.error(request, f"Table '{name}' already exists!")
                else: t = Table.objects.get(id=tid); t.name, t.capacity = name, cap; t.save(); messages.success(request, f"Table '{name}' updated!")
            else:
                if Table.objects.filter(name__iexact=name).exists(): messages.error(request, f"Table '{name}' already exists!")
                else: Table.objects.create(name=name, capacity=cap); messages.success(request, f"New Table '{name}' added successfully!")
        except Exception as e: messages.error(request, f"Error: {e}")
        return redirect('table_management')
    
    tables = []
    for t in Table.objects.all().order_by('name'):
        is_occupied = Order.objects.filter(table=t, payment_status='Pending').exclude(status='Cancelled').exists()
        tables.append({'id': t.id, 'name': t.name, 'capacity': t.capacity, 'zone': 'AC Hall', 'status': 'Occupied' if is_occupied else 'Vacant'})
    stats = {'total': len(tables), 'occupied': sum(1 for t in tables if t['status']=='Occupied'), 'vacant': sum(1 for t in tables if t['status']=='Vacant'), 'capacity': sum(t['capacity'] for t in tables)}
    return render(request, 'panel/management/table_list.html', {'tables': tables, 'stats': stats})

@login_required(login_url='admin_login')
def delete_table(request, id): Table.objects.filter(id=id).delete(); return redirect('table_management')

@login_required(login_url='admin_login')
def menu_management(request):
    if request.method == "POST":
        action = request.POST.get('action')
        # --- DELETE LOGIC ---
        if action == 'delete':
            item_id = request.POST.get('item_id')
            if item_id:
                MenuItem.objects.filter(id=item_id).delete()
            return redirect('menu_management')
            
        # --- ADD / UPDATE LOGIC ---
        else:
            try:
                item_id = request.POST.get('item_id')
                data = {
                    'name': request.POST.get('name'), 
                    'price': request.POST.get('price'), 
                    'category': Category.objects.get(id=request.POST.get('category')),
                    'description': request.POST.get('description', ''), 
                    'is_veg': request.POST.get('dietType') == 'veg',
                    'is_available': request.POST.get('is_available') == 'on', 
                    'is_bestseller': request.POST.get('is_bestseller') == 'on'
                }

                if item_id:
                    MenuItem.objects.filter(id=item_id).update(**data)
                    item_obj = MenuItem.objects.get(id=item_id)
                    # पुराने वेरिएंट्स साफ़ करें ताकि डुप्लीकेट न हों
                    item_obj.variants.all().delete()
                else:
                    item_obj = MenuItem.objects.create(image=request.FILES.get('image'), **data)

                # वेरिएंट्स (Variants) सेव करें
                v_names = request.POST.getlist('v_names[]')
                v_prices = request.POST.getlist('v_prices[]')
                for n, p in zip(v_names, v_prices):
                    if n and p:
                        ItemVariant.objects.create(item=item_obj, variant_name=n, price=p)

            except Exception as e:
                messages.error(request, f"Error saving item: {e}")
                
        return redirect('menu_management')

    # GET Request: लिस्ट दिखाएँ
    cat_filter = request.GET.get('category')
    items = MenuItem.objects.filter(category_id=cat_filter) if cat_filter and cat_filter != 'all' else MenuItem.objects.all()
    return render(request, 'panel/management/menu_list.html', {
        'categories': Category.objects.all().order_by('sort_order'), 
        'items': items
    })

@login_required(login_url='admin_login')
def category_management(request):
    if request.method == "POST":
        cat_id, sort_raw = request.POST.get('cat_id'), request.POST.get('sort_order')
        data = {'name': request.POST.get('name'), 'sort_order': int(sort_raw) if sort_raw and sort_raw.isdigit() else 0, 'is_active': request.POST.get('is_active') == 'on'}
        if cat_id: Category.objects.filter(id=cat_id).update(**data)
        else: Category.objects.create(**data)
        return redirect('category_management')
    return render(request, 'panel/management/category_list.html', {'categories': Category.objects.all().order_by('sort_order')})

@login_required(login_url='admin_login')
def delete_category(request, id): Category.objects.filter(id=id).delete(); return redirect('category_management')

@login_required(login_url='admin_login')
def sales_report(request):
    completed = Order.objects.filter(payment_status='Completed').exclude(status='Cancelled')
    today = timezone.now().date()
    def kpis(days):
        qs = completed.filter(created_at__date__gte=today - timedelta(days=days))
        rev, cnt = sum(o.total_amount for o in qs), qs.count()
        return {'revenue': float(rev), 'orders': cnt, 'aov': round(float(rev/cnt if cnt > 0 else 0), 2)}
    trend_lbl, trend_data = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        trend_lbl.append(d.strftime('%a')); trend_data.append(float(sum(o.total_amount for o in completed.filter(created_at__date=d))))
    total_rev, total_exp = sum(o.total_amount for o in completed), sum(e.amount for e in Expense.objects.all())
    return render(request, 'panel/reports/sales_report.html', {
        'stats_today': json.dumps(kpis(0)), 'stats_7days': json.dumps(kpis(7)), 'stats_30days': json.dumps(kpis(30)),
        'net_margin': round(((total_rev - total_exp) / total_rev * 100) if total_rev > 0 else 0, 1),
        'sales_trend_labels': json.dumps(trend_lbl), 'sales_trend_data': json.dumps(trend_data),
        'upi_rev': float(sum(o.total_amount for o in completed if 'UPI' in str(o.payment_mode))),
        'cash_rev': float(sum(o.total_amount for o in completed if 'Cash' in str(o.payment_mode)))
    })

@login_required(login_url='admin_login')
def restaurant_settings(request):
    setting, _ = RestaurantSetting.objects.get_or_create(id=1)
    tax, _ = TaxSetting.objects.get_or_create(id=1)
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'basic_info':
            setting.name = request.POST.get('name', setting.name); setting.tagline = request.POST.get('tagline', setting.tagline); setting.phone = request.POST.get('phone', setting.phone); setting.email = request.POST.get('email', setting.email); setting.address = request.POST.get('address', setting.address)
            if request.FILES.get('logo'): setting.logo = request.FILES.get('logo')
            setting.save(); messages.success(request, "Restaurant basic details updated successfully!")
        elif action == 'tax_rules':
            tax.gst_number = request.POST.get('gst_number', tax.gst_number); tax.cgst_percentage = float(request.POST.get('cgst', tax.cgst_percentage)); tax.sgst_percentage = float(request.POST.get('sgst', tax.sgst_percentage)); tax.is_gst_inclusive = request.POST.get('is_gst_inclusive') == 'on'; tax.save()
            setting.service_charge_percentage = float(request.POST.get('service_charge', setting.service_charge_percentage)); setting.packaging_charge = int(request.POST.get('packaging_charge', setting.packaging_charge)); setting.save()
            messages.success(request, "Tax and Billing rules updated successfully!")
        return redirect('restaurant_settings')
    return render(request, 'panel/settings/restaurant.html', {'setting': setting, 'tax': tax})

@login_required(login_url='admin_login')
def billing(request):
    if request.method == "POST":
        action, order_id = request.POST.get('action'), request.POST.get('order_id')
        try:
            order = Order.objects.get(order_id=order_id)
            if action == 'void': order.status = 'Cancelled'; order.save(); messages.success(request, f"Invoice #{order_id} voided.")
            elif action == 'change_mode': order.payment_mode = request.POST.get('payment_mode'); order.save(); messages.success(request, f"Mode updated.")
        except Order.DoesNotExist: messages.error(request, "Invoice not found.")
        return redirect('billing')
    invoices = Order.objects.prefetch_related('items', 'table').filter(status__in=['Completed', 'Cancelled']).order_by('-updated_at')
    today = timezone.now().date()
    todays_invoices = invoices.filter(updated_at__date=today, status='Completed')
    return render(request, 'panel/operations/billing.html', {'invoices': invoices, 'todays_invoices_count': todays_invoices.count(), 'total_collection_today': float(sum(o.total_amount for o in todays_invoices)), 'total_void_today': invoices.filter(updated_at__date=today, status='Cancelled').count()})

def api_invoice_details(request, order_id):
    try:
        order = Order.objects.prefetch_related('items').get(order_id=order_id)
        items = [{"name": i.item_name, "qty": i.qty, "price": float(i.price), "total": float(i.get_total())} for i in order.items.all()]
        subtotal = float(order.total_amount)
        tax = subtotal * 0.05 # 5% GST
        return JsonResponse({"success": True, "order_id": order.order_id, "date": order.updated_at.strftime("%d %b %Y, %I:%M %p"), "table": order.table.name if order.table else "Takeaway", "mode": order.payment_mode or "Unpaid", "items": items, "subtotal": subtotal, "tax": tax, "grand_total": subtotal + tax})
    except Order.DoesNotExist: return JsonResponse({"success": False})

# ==========================================
# 6. MANAGER FULL PANEL ROUTES
# ==========================================
@login_required(login_url='admin_login')
def manager_dashboard(request):
    today = timezone.now().date()
    current_time = timezone.now()
    todays_completed = Order.objects.filter(created_at__date=today, payment_status='Completed')
    shift_revenue = sum(o.total_amount for o in todays_completed)
    cash_rev = sum(o.total_amount for o in todays_completed if 'Cash' in str(o.payment_mode))
    upi_rev = sum(o.total_amount for o in todays_completed if 'UPI' in str(o.payment_mode))
    card_rev = sum(o.total_amount for o in todays_completed if 'Card' in str(o.payment_mode))
    total_modes = cash_rev + upi_rev + card_rev
    
    total_tables = Table.objects.count()
    active_tables = Order.objects.filter(payment_status='Pending').exclude(status='Cancelled').values('table').distinct().count()
    
    active_orders_qs = Order.objects.prefetch_related('items', 'table').filter(status__in=['Pending', 'Cooking', 'Ready']).order_by('created_at')
    delayed_count = sum(1 for o in active_orders_qs if int((current_time - o.created_at).total_seconds() // 60) > 20)
    
    feed = []
    for o in active_orders_qs[:6]:
        feed.append({
            'table': o.table.name if o.table else 'Takeaway',
            'summary': ", ".join([i.item_name for i in o.items.all()[:2]]),
            'elapsed_mins': int((current_time - o.created_at).total_seconds() // 60),
            'is_delayed': int((current_time - o.created_at).total_seconds() // 60) > 20,
            'status': o.status
        })

    return render(request, 'manager/dashboard.html', {
        'shift_revenue': float(shift_revenue), 'cash_in_drawer': float(cash_rev),
        'upi_rev': float(upi_rev), 'card_rev': float(card_rev),
        'upi_pct': int((upi_rev/total_modes*100)) if total_modes else 0, 'cash_pct': int((cash_rev/total_modes*100)) if total_modes else 0, 'card_pct': 100 - (int((upi_rev/total_modes*100)) if total_modes else 0) - (int((cash_rev/total_modes*100)) if total_modes else 0) if total_modes else 0,
        'active_tables': active_tables, 'total_tables': total_tables, 'occupancy_percent': int((active_tables/total_tables*100)) if total_tables else 0,
        'live_orders_count': active_orders_qs.count(), 'delayed_count': delayed_count, 'active_orders_feed': feed,
        'low_stock_items': InventoryItem.objects.filter(stock__lte=F('min_level')).order_by('stock')[:5], 'low_stock_count': InventoryItem.objects.filter(stock__lte=F('min_level')).count()
    })

@login_required(login_url='admin_login')
def manager_pos(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action_type, table_id, cart_items = data.get('type'), data.get('table'), data.get('cart', [])
            if not cart_items: return JsonResponse({"success": False, "message": "Cart is empty!"})

            subtotal = sum(float(item['price']) * int(item['qty']) for item in cart_items)
            tax, total_amount = subtotal * 0.05, subtotal + (subtotal * 0.05)
            table_obj = Table.objects.filter(id=table_id).first() if table_id and table_id != 'Takeaway' else None

            if table_obj and action_type == 'KOT':
                order = Order.objects.filter(table=table_obj, payment_status='Pending').exclude(status='Cancelled').first()
                if not order: order = Order.objects.create(table=table_obj, total_amount=0, status='Cooking', payment_status='Pending')
            else:
                order = Order.objects.create(table=table_obj, total_amount=0, status='Completed' if action_type == 'PAY' else 'Cooking', payment_status='Completed' if action_type == 'PAY' else 'Pending', payment_mode='Cash' if action_type == 'PAY' else None)

            for item in cart_items: OrderItem.objects.create(order=order, item_name=item['name'], qty=item['qty'], price=item['price'], item_status='Pending' if action_type == 'KOT' else 'Served')
            order.total_amount += Decimal(str(total_amount)); order.save()
            return JsonResponse({"success": True, "message": "KOT Sent!" if action_type == 'KOT' else "Bill Settled!", "order_id": order.order_id})
        except Exception as e: return JsonResponse({"success": False, "message": str(e)})

    return render(request, 'manager/pos_billing.html', {
        'categories': Category.objects.filter(is_active=True).order_by('sort_order'),
        'tables': Table.objects.all().order_by('name'), 'menu_items': MenuItem.objects.filter(is_available=True)
    })

@login_required(login_url='admin_login')
def manager_live_orders(request):
    if request.method == "POST":
        try:
            order = Order.objects.get(order_id=request.POST.get('order_id'))
            action = request.POST.get('action')
            if action == 'accept': order.items.filter(item_status='Pending').update(item_status='Cooking'); order.status = 'Cooking'
            elif action == 'force_ready': order.items.exclude(item_status='Served').update(item_status='Ready'); order.status = 'Ready'
            order.save()
        except Order.DoesNotExist: pass
        return redirect('manager_live_orders')

    orders = Order.objects.prefetch_related('items', 'table').filter(status__in=['Pending', 'Cooking', 'Ready']).exclude(status='Cancelled').order_by('created_at')
    current_time = timezone.now()
    orders_data = [{'order': o, 'elapsed_mins': int((current_time - o.created_at).total_seconds() // 60), 'is_delayed': int((current_time - o.created_at).total_seconds() // 60) > 20 and o.status != 'Ready', 'items': o.items.all()} for o in orders]
    return render(request, 'manager/live_orders.html', {'orders_data': orders_data, 'active_tables_count': len(set(o.table for o in orders if o.table))})

@login_required(login_url='admin_login')
def manager_tables(request):
    current_time = timezone.now()
    tables_data = []
    max_dur, longest_table, occ_count = 0, "None", 0

    for t in Table.objects.all().order_by('name'):
        active_order = Order.objects.filter(table=t, payment_status='Pending').exclude(status='Cancelled').first()
        status, bill, elapsed = 'Vacant', 0, 0
        if active_order:
            occ_count += 1; bill = float(active_order.total_amount)
            elapsed = int((current_time - active_order.created_at).total_seconds() // 60)
            if elapsed > max_dur: max_dur = elapsed; longest_table = t.name
            status = 'Billed' if active_order.status == 'Completed' else 'Running'
        tables_data.append({'id': t.id, 'name': t.name, 'capacity': t.capacity, 'status': status, 'bill': bill, 'elapsed_mins': elapsed})

    return render(request, 'manager/tables.html', {
        'tables': tables_data, 'total_tables': len(tables_data), 'occupied_count': occ_count, 'vacant_count': len(tables_data) - occ_count,
        'avg_occupancy': int(max_dur / 2) if max_dur > 0 else 0, 'longest_table': longest_table, 'max_duration': max_dur
    })

@login_required(login_url='admin_login')
def manager_kitchen(request):
    if request.method == "POST":
        try:
            order = Order.objects.get(order_id=request.POST.get('order_id'))
            order.items.filter(item_status__in=['Pending', 'Cooking']).update(item_status='Ready')
            order.status = 'Ready'; order.save()
        except Order.DoesNotExist: pass
        return redirect('manager_kitchen')

    active_orders = Order.objects.prefetch_related('items', 'table').filter(status__in=['Pending', 'Cooking']).order_by('created_at')
    current_time = timezone.now()
    for o in active_orders: o.elapsed_mins = int((current_time - o.created_at).total_seconds() // 60)
    return render(request, 'manager/kitchen_monitor.html', {'active_orders': active_orders, 'active_count': active_orders.count()})

@login_required(login_url='admin_login')
def manager_menu_control(request):
    if request.method == "POST":
        try:
            item = MenuItem.objects.get(id=request.POST.get('item_id'))
            item.is_available = not item.is_available
            item.save()
        except MenuItem.DoesNotExist: pass
        return redirect('manager_menu_control')
    return render(request, 'manager/menu_control.html', {'menu_items': MenuItem.objects.all().order_by('category__sort_order', 'name')})

@login_required(login_url='admin_login')
def manager_expenses(request):
    if request.method == "POST":
        try: Expense.objects.create(title=request.POST.get('desc'), amount=float(request.POST.get('amount')), category=request.POST.get('category'), date=timezone.now().date(), added_by=request.user)
        except: pass
        return redirect('manager_expenses')
    todays_expenses = Expense.objects.filter(date=timezone.now().date()).order_by('-id')
    return render(request, 'manager/expenses.html', {'expenses': todays_expenses, 'todays_expense_total': sum(e.amount for e in todays_expenses)})

@login_required(login_url='admin_login')
def manager_attendance(request):
    today = timezone.now().date()
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'punch':
            pin = request.POST.get('pin')
            staff = Staff.objects.filter(pin_code=pin).first()
            if staff:
                att, created = Attendance.objects.get_or_create(staff=staff, date=today)
                if created: 
                    att.check_in = timezone.now().time()
                    att.status = 'Present' if att.check_in.hour < 10 else 'Late'
                elif not att.check_out: 
                    att.check_out = timezone.now().time()
                att.save()
        return redirect('manager_attendance')

    roster = []
    for staff in Staff.objects.filter(is_active=True):
        att = Attendance.objects.filter(staff=staff, date=today).first()
        if att: roster.append(att)
        else: roster.append({'staff': staff, 'status': 'Absent', 'check_in': None, 'check_out': None})

    stats = {
        'total': Staff.objects.filter(is_active=True).count(),
        'present': Attendance.objects.filter(date=today, status='Present').count(),
        'late': Attendance.objects.filter(date=today, status='Late').count(),
    }
    stats['absent'] = stats['total'] - (stats['present'] + stats['late'])

    return render(request, 'manager/attendance.html', {'roster': roster, 'stats': stats})

@login_required(login_url='admin_login')
def manager_overrides(request):
    if request.method == "POST":
        pin = request.POST.get('pin')
        if pin == '1234': # Verify Manager PIN
            OverrideLog.objects.create(
                action_type=request.POST.get('action_type'),
                target=request.POST.get('target'),
                impact=float(request.POST.get('impact', 0)),
                reason=request.POST.get('reason'),
                authorized_by=request.user.username
            )
        return redirect('manager_overrides')
    
    logs = OverrideLog.objects.all().order_by('-created_at')
    return render(request, 'manager/overrides.html', {'logs': logs})

@login_required(login_url='admin_login')
def manager_day_close(request):
    today = timezone.now().date()
    is_closed = ZReport.objects.filter(date=today).exists()
    
    todays_orders = Order.objects.filter(created_at__date=today, payment_status='Completed')
    total_sales = sum(o.total_amount for o in todays_orders)
    total_expenses = sum(e.amount for e in Expense.objects.filter(date=today))
    expected_cash = sum(o.total_amount for o in todays_orders if 'Cash' in str(o.payment_mode)) - total_expenses

    if request.method == "POST" and not is_closed:
        pin = request.POST.get('pin')
        if pin == '1234':
            ZReport.objects.create(
                date=today,
                total_sales=total_sales,
                cash_expected=expected_cash,
                cash_actual=float(request.POST.get('actual_cash', 0)),
                mismatch_reason=request.POST.get('reason', ''),
                closed_by=request.user
            )
        return redirect('manager_day_close')

    return render(request, 'manager/day_close.html', {
        'is_closed': is_closed,
        'total_sales': float(total_sales),
        'total_expenses': float(total_expenses),
        'expected_cash': float(expected_cash)
    })

# ==========================================
# 7. WAITER PANEL (MOBILE UI)
# ==========================================
@login_required(login_url='admin_login')
def waiter_floor(request):
    tables_data = []
    # Real-time Table Status Calculation
    for t in Table.objects.all().order_by('name'):
        active_order = Order.objects.filter(table=t, payment_status='Pending').exclude(status='Cancelled').first()
        status, time_str = 'Vacant', ''
        alerts = []
        
        if active_order:
            elapsed = int((timezone.now() - active_order.created_at).total_seconds() // 60)
            time_str = f"{elapsed}m"
            
            # Sub-status calculation
            if active_order.items.filter(item_status='Ready').exists():
                status = 'Food Ready'
                alerts.append('food')
            elif active_order.status == 'Completed':
                status = 'Bill Req'
                alerts.append('bill')
            else:
                status = 'Running'
                
        # Handle manual waiter alerts from DB
        db_alerts = WaiterAlert.objects.filter(table=t, is_resolved=False)
        for a in db_alerts:
            if a.alert_type not in alerts: alerts.append(a.alert_type)

        tables_data.append({
            'id': t.name, 'seats': t.capacity, 
            'status': status, 'time': time_str, 'alerts': alerts
        })

    return render(request, 'waiter/floor.html', {'tables_json': json.dumps(tables_data)})


@login_required(login_url='admin_login')
@csrf_exempt
def waiter_punch_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            table_name = data.get('table')
            cart_items = data.get('cart', [])
            
            if not cart_items or not table_name:
                return JsonResponse({"success": False, "message": "Cart is empty"})

            table_obj = Table.objects.filter(name=table_name).first()
            if not table_obj:
                return JsonResponse({"success": False, "message": "Invalid Table"})

            subtotal = sum(float(item['price']) * int(item['qty']) for item in cart_items)
            
            order = Order.objects.filter(table=table_obj, payment_status='Pending').exclude(status='Cancelled').first()
            if not order: 
                order = Order.objects.create(table=table_obj, total_amount=0, status='Cooking', payment_status='Pending')
            
            for item in cart_items: 
                # Add Notes/Instructions if waiter added them
                notes = item.get('notes', [])
                instruction = ", ".join(notes) if isinstance(notes, list) else str(notes)
                
                OrderItem.objects.create(
                    order=order, 
                    item_name=item['name'], 
                    qty=item['qty'], 
                    price=item['price'], 
                    instruction=instruction,
                    item_status='Pending'
                )
            
            order.total_amount += Decimal(str(subtotal + (subtotal * 0.05)))
            order.status = 'Cooking'
            order.save()
            return JsonResponse({"success": True})
        except Exception as e: 
            return JsonResponse({"success": False, "message": str(e)})

    selected_table = request.GET.get('table', '')
    categories = Category.objects.filter(is_active=True).order_by('sort_order')
    items = MenuItem.objects.filter(is_available=True)
    
    # Yahan hum Image aur Bestseller Tags bhi bhej rahe hain!
    items_json = []
    for i in items:
        items_json.append({
            "id": i.id, 
            "name": i.name, 
            "cat": i.category.name, 
            "price": float(i.price), 
            "veg": getattr(i, 'is_veg', True),
            "image": i.image.url if i.image else "",
            "bestseller": getattr(i, 'is_bestseller', False),
            "spicy": getattr(i, 'is_spicy', False)
        })
    
    return render(request, 'waiter/punch_order.html', {
        'selected_table': selected_table, 
        'categories': categories, 
        'menu_items_json': json.dumps(items_json)
    })


@login_required(login_url='admin_login')
def waiter_running_orders(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        table_name = request.POST.get('table')
        try:
            item = OrderItem.objects.get(id=item_id)
            item.item_status = 'Served'
            item.save()
        except: pass
        return redirect(f'/waiter/running/?table={table_name}')

    active_tables = Order.objects.filter(status__in=['Pending', 'Cooking', 'Ready']).values_list('table__name', flat=True).distinct()
    selected_table = request.GET.get('table', active_tables[0] if active_tables else None)
    
    kots = []
    if selected_table:
        orders = Order.objects.filter(table__name=selected_table, status__in=['Pending', 'Cooking', 'Ready']).order_by('-created_at')
        for o in orders:
            items_list = []
            for i in o.items.exclude(item_status='Served'):
                items_list.append({
                    'id': i.id, 'name': i.item_name, 'qty': i.qty, 
                    'status': i.item_status, 
                    'status_class': 'text-slate-400 line-through' if i.item_status == 'Served' else 'text-slate-800'
                })
            if items_list:
                kots.append({'order_id': o.order_id, 'items': items_list})

    return render(request, 'waiter/running_orders.html', {
        'active_tables': active_tables, 
        'selected_table': selected_table, 
        'kots': kots
    })


@login_required(login_url='admin_login')
def waiter_alerts(request):
    alerts = []
    # 1. Fetch tables where Food is Ready
    ready_orders = Order.objects.filter(items__item_status='Ready').distinct()
    for o in ready_orders:
        if o.table: alerts.append({'table': o.table.name, 'msg': "Food is ready for pickup in Kitchen!"})
    
    # 2. Fetch manual alerts (e.g. Water/Bill requested by customer scan)
    manual_alerts = WaiterAlert.objects.filter(is_resolved=False)
    for a in manual_alerts:
        alerts.append({'table': a.table.name, 'msg': a.message})

    return render(request, 'waiter/alerts.html', {'alerts': alerts})


# ==========================================
# 8. CASHIER PANEL (BILLING & POS)
# ==========================================
@login_required(login_url='admin_login')
def cashier_pos(request):
    tables = Table.objects.all().order_by('name')
    table_data = []
    occupied = 0
    billed = 0
    
    for t in tables:
        order = Order.objects.filter(table=t, payment_status='Pending').exclude(status='Cancelled').first()
        status = 'Available'
        bill_amount = 0
        order_id = ''
        
        if order:
            # Agar KOT ready ho chuka hai ya manager ne bill generate kar diya hai
            if order.status == 'Completed' or order.status == 'Ready':
                status = 'Billed'
                billed += 1
            else:
                status = 'Occupied'
                occupied += 1
            bill_amount = order.total_amount
            order_id = order.order_id
            
        table_data.append({
            'id': t.id, 'name': t.name, 'status': status,
            'bill_amount': float(bill_amount), 'order_id': order_id
        })
        
    context = {
        'tables': table_data,
        'total_tables': tables.count(),
        'occupied_count': occupied,
        'billed_count': billed,
        'available_count': tables.count() - occupied - billed
    }
    return render(request, 'cashier/pos_screen.html', context)

def get_bill_details(request, table_id):
    order = Order.objects.filter(table_id=table_id, payment_status='Pending').exclude(status='Cancelled').first()
    if not order:
        return JsonResponse({'success': False, 'message': 'No active orders on this table.'})
    
    items = [{'item_name': i.item_name, 'qty': i.qty, 'price': float(i.price)} for i in order.items.all()]
    return JsonResponse({
        'success': True,
        'order_id': order.order_id,
        'total': float(order.total_amount),
        'items': items
    })

@login_required(login_url='admin_login')
def complete_settlement(request):
    if request.method == "POST":
        order_id = request.POST.get('order_id')
        payment_mode = request.POST.get('payment_mode')
        
        if order_id and payment_mode:
            order = Order.objects.filter(order_id=order_id).first()
            if order:
                # 1. आर्डर स्टेटस अपडेट करें
                order.payment_status = 'Completed'
                order.payment_mode = payment_mode
                order.status = 'Completed'
                order.save()
                
                # 🌟 2. INVENTORY AUTO-DEDUCT LOGIC START 🌟
                # आर्डर के हर आइटम को चेक करें और स्टॉक कम करें
                for item in order.items.all():
                    # हम 'InventoryItem' में आइटम का नाम मैच कर रहे हैं
                    inventory_obj = InventoryItem.objects.filter(name__icontains=item.item_name).first()
                    if inventory_obj:
                        # मान लीजिये एक डिश में 1 यूनिट माल लगता है
                        inventory_obj.stock -= float(item.qty)
                        inventory_obj.save()
                # 🌟 INVENTORY AUTO-DEDUCT LOGIC END 🌟

                messages.success(request, f"Bill #{order_id} settled! Stock updated.")
                return redirect('print_bill', order_id=order.order_id)
                
    return redirect('cashier_pos')
    
@login_required(login_url='admin_login')
def print_bill(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    subtotal = float(order.total_amount) / 1.05 # Reverse calculating 5% GST for bill
    gst = float(order.total_amount) - subtotal
    return render(request, 'cashier/thermal_bill.html', {
        'order': order, 'items': order.items.all(), 
        'subtotal': round(subtotal, 2), 'gst': round(gst, 2)
    })

@login_required(login_url='admin_login')
def cashier_settlements(request):
    # Orders jahan khana ban gaya hai par payment pending hai
    orders = Order.objects.filter(payment_status='Pending').exclude(status='Cancelled').order_by('-created_at')
    pending_amount = sum(o.total_amount for o in orders)
    avg_bill = (pending_amount / orders.count()) if orders.count() > 0 else 0
    
    return render(request, 'cashier/settlements.html', {
        'orders': orders, 'unpaid_count': orders.count(),
        'pending_amount': pending_amount, 'avg_bill': round(avg_bill, 2)
    })

@login_required(login_url='admin_login')
def cashier_history(request):
    today = timezone.now().date()
    orders = Order.objects.filter(payment_status='Completed', updated_at__date=today).order_by('-updated_at')
    
    cash_sales = sum(o.total_amount for o in orders if o.payment_mode == 'Cash')
    upi_sales = sum(o.total_amount for o in orders if o.payment_mode == 'UPI')
    card_sales = sum(o.total_amount for o in orders if o.payment_mode == 'Card')
    
    return render(request, 'cashier/history.html', {
        'orders': orders, 'total_sales_count': orders.count(),
        'cash_sales': float(cash_sales), 'upi_sales': float(upi_sales),
        'net_revenue': float(cash_sales + upi_sales + card_sales)
    })

@login_required(login_url='admin_login')
def cashier_day_close(request):
    today = timezone.now().date()
    orders = Order.objects.filter(payment_status='Completed', updated_at__date=today)
    
    cash_sales = float(sum(o.total_amount for o in orders if o.payment_mode == 'Cash'))
    upi_sales = float(sum(o.total_amount for o in orders if o.payment_mode == 'UPI'))
    card_sales = float(sum(o.total_amount for o in orders if o.payment_mode == 'Card'))
    expenses = float(sum(e.amount for e in Expense.objects.filter(date=today)))
    
    expected_cash = cash_sales - expenses

    if request.method == "POST":
        ZReport.objects.create(
            date=today, total_sales=(cash_sales + upi_sales + card_sales),
            cash_expected=expected_cash, cash_actual=float(request.POST.get('actual_cash', 0)),
            mismatch_reason=request.POST.get('reason', ''), closed_by=request.user
        )
        return redirect('admin_logout') # Din band hone par logout kar do

    return render(request, 'cashier/day_close.html', {
        'cash_sales': cash_sales, 'upi_sales': upi_sales, 'card_sales': card_sales,
        'expenses': expenses, 'expected_cash': expected_cash,
        'is_closed': ZReport.objects.filter(date=today).exists()
    })

@csrf_exempt
def api_repeat_item(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_name = data.get('item_name')
            price = data.get('price')
            table_name = request.session.get('customer_table')

            table_obj = Table.objects.filter(name=table_name).first()
            order = Order.objects.filter(table=table_obj, payment_status='Pending').exclude(status='Cancelled').first()
            
            if not order:
                return JsonResponse({'success': False, 'message': 'No active order found.'})

            # Naya item add karo (Qty 1)
            OrderItem.objects.create(
                order=order, item_name=item_name, qty=1, price=Decimal(str(price)), item_status='Pending'
            )

            # Bill Update (Price + 5% GST)
            order.total_amount += Decimal(str(float(price) * 1.05))
            order.save()

            return JsonResponse({'success': True, 'message': f'Added 1 more {item_name}!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

@csrf_exempt
def api_cancel_item(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            # Item ko dhundo
            item = OrderItem.objects.get(id=item_id)
            order = item.order
            
            # Strict Logic: Sirf 'Pending' items hi cancel ho sakte hain
            if item.item_status != 'Pending':
                return JsonResponse({'success': False, 'message': 'Chef has already started cooking this!'})
            
            # Bill Update (Price - 5% GST)
            item_price_with_tax = float(item.price) * 1.05
            order.total_amount -= Decimal(str(item_price_with_tax))
            
            item.delete() # Item delete kar do
            order.save()
            
            return JsonResponse({'success': True, 'message': 'Item removed from order.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

def api_get_item_customization(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    variants = item.variants.all()
    addons = item.addons.all()
    
    return JsonResponse({
        'has_variants': variants.exists(),
        'has_addons': addons.exists(),
        'variants': [{'name': v.variant_name, 'price': float(v.price)} for v in variants],
        'addons': [{'name': a.addon_name, 'price': float(a.price)} for a in addons]
    })

def api_kds_updates(request):
    # 'Pending' और 'Cooking' वाले आइटम्स, कैटेगरी के साथ
    active_items = OrderItem.objects.filter(
        item_status__in=['Pending', 'Cooking']
    ).select_related('order', 'order__table').order_by('order__created_at')

    data = []
    for item in active_items:
        diff = timezone.now() - item.order.created_at
        elapsed_minutes = int(diff.total_seconds() // 60)
        
        # आइटम की कैटेगरी के आधार पर स्टेशन तय करना
        # मान लो कैटेगरी का नाम 'Punjabi' है तो स्टेशन 'Punjabi' होगा
        station_name = item.order.items.filter(item_name=item.item_name).first().item_name # यहाँ आप category logic लगा सकते हैं
        
        data.append({
            'id': item.id,
            'table': item.order.table.name if item.order.table else "Takeaway",
            'name': item.item_name,
            'qty': item.qty,
            'spice': item.spice or 'Regular',
            'note': item.instruction or '',
            'status': item.item_status,
            'elapsed': elapsed_minutes,
            'variant': item.variant_name or '',
            # 🌟 यह ज़रूरी है: कैटेगरी को स्टेशन के रूप में भेजना
            'station': item.item_status # यहाँ हम कैटेगरी पास करेंगे
        })
    
    return JsonResponse({'items': data})

def api_waiter_updates(request):
    # 1. वो टेबल्स जहाँ खाना 'Ready' है पर सर्व नहीं हुआ
    ready_items = OrderItem.objects.filter(item_status='Ready').values_list('order__table__name', flat=True).distinct()
    
    # 2. वो टेबल्स जिन्होंने 'Water', 'Bill' आदि माँगा है (WaiterAlert Model से)
    active_alerts = WaiterAlert.objects.filter(is_resolved=False).select_related('table')
    
    table_alerts = {}
    
    # Ready Food की लिस्ट तैयार करें
    for t_name in ready_items:
        table_alerts[t_name] = ['food']
        
    # Customer Requests की लिस्ट तैयार करें
    for alert in active_alerts:
        t_name = alert.table.name
        if t_name not in table_alerts:
            table_alerts[t_name] = []
        table_alerts[t_name].append(alert.alert_type)
        
    return JsonResponse({'table_alerts': table_alerts})

@csrf_exempt
def api_resolve_alert(request):
    # जब वेटर सर्विस दे दे, तो अलर्ट खत्म करने के लिए
    if request.method == "POST":
        table_name = request.POST.get('table_name')
        alert_type = request.POST.get('alert_type')
        table_obj = Table.objects.filter(name=table_name).first()
        if table_obj:
            WaiterAlert.objects.filter(table=table_obj, alert_type=alert_type, is_resolved=False).update(is_resolved=True)
            return JsonResponse({'success': True})
    return JsonResponse({'success': False})

def get_current_order_status(request):
    table_name = request.session.get('customer_table')
    table_obj = Table.objects.filter(name=table_name).first()
    # पेंडिंग पेमेंट वाले आर्डर का स्टेटस देखो
    order = Order.objects.filter(table=table_obj, payment_status='Pending').first()
    if order:
        return JsonResponse({'status': order.status})
    return JsonResponse({'status': 'none'})