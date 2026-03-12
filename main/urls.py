from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 1. CUSTOMER SIDE & API
    # ==========================================
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('orders/', views.orders_page, name='orders_page'), 
    path('bill/', views.bill_page, name='bill_page'),
    path('process_payment/', views.process_payment, name='process_payment'),

    # --- Cart API ---
    path('cart/add/<int:item_id>/', views.cart_add, name='cart_add'),
    path('cart/inc/<int:item_id>/', views.cart_inc, name='cart_inc'),
    path('cart/dec/<int:item_id>/', views.cart_dec, name='cart_dec'),
    path('cart/count/', views.cart_count, name='cart_count'),
    path('cart/data/', views.cart_data, name='cart_data'),
    path('cart/update_spice/<int:item_id>/<str:level>/', views.cart_update_spice, name='cart_update_spice'),
    path('cart/update_instruction/<int:item_id>/', views.cart_update_instruction, name='cart_update_instruction'),
    path('cart/place_order/', views.place_order, name='place_order'),

    # ==========================================
    # 2. AUTHENTICATION (RBAC LOGIN)
    # ==========================================
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),

    # ==========================================
    # 3. ADMIN PANEL (CORE & OPERATIONS)
    # ==========================================
    path('dashboard/', views.dashboard_overview, name='dashboard_overview'),
    path('live-orders/', views.live_orders, name='live_orders'),
    path('kitchen-status/', views.kitchen_status, name='kitchen_status'),
    path('billing/', views.billing, name='billing'), # All Invoices / Bill History

    # ==========================================
    # 4. MANAGEMENT (Menu, Tables, Staff, Inventory)
    # ==========================================
    path('management/menu/', views.menu_management, name='menu_management'),
    path('management/category/', views.category_management, name='category_management'),
    path('management/category/delete/<int:id>/', views.delete_category, name='delete_category'),
    
    path('manage/tables/', views.table_management, name='table_management'),
    path('manage/tables/delete/<int:id>/', views.delete_table, name='delete_table'),
    
    path('manage/staff/', views.staff_management, name='staff_management'),
    path('manage/staff/delete/<int:id>/', views.delete_staff, name='delete_staff'),
    path('manage/role/add/', views.add_role, name='add_role'),
    path('manage/role/delete/<int:id>/', views.delete_role, name='delete_role'),
    
    path('management/inventory/', views.inventory_management, name='inventory'),
    path('management/inventory/update/', views.update_inventory_stock, name='update_inventory_stock'),
    path('management/inventory/delete/<int:id>/', views.delete_inventory_item, name='delete_inventory_item'),

    # ==========================================
    # 5. BUSINESS, REPORTS & SETTINGS
    # ==========================================
    path('business/accounts/', views.accounts_expense, name='accounts_expense'),
    path('panel/reports/sales/', views.sales_report, name='sales_report'),
    path('settings/restaurant/', views.restaurant_settings, name='restaurant_settings'),

    # ==========================================
    # 6. KDS SCREEN (Kitchen Display)
    # ==========================================
    path('kds/', views.kds_screen, name='kds_screen'),

    # ==========================================
    # 7. MANAGER PANEL ROUTES (Stubs)
    # ==========================================
    path('manager/dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager/pos/', views.manager_pos, name='manager_pos'),
    path('manager/live-orders/', views.manager_live_orders, name='manager_live_orders'),
    path('manager/tables/', views.manager_tables, name='manager_tables'),
    path('manager/kitchen/', views.manager_kitchen, name='manager_kitchen'),
    path('manager/menu-control/', views.manager_menu_control, name='manager_menu_control'),
    path('manager/overrides/', views.manager_overrides, name='manager_overrides'),
    path('manager/expenses/', views.manager_expenses, name='manager_expenses'),
    path('manager/attendance/', views.manager_attendance, name='manager_attendance'),
    path('manager/day-close/', views.manager_day_close, name='manager_day_close'),

    # ==========================================
    # 8. WAITER APP ROUTES (Stubs)
    # ==========================================
    path('waiter/floor/', views.waiter_floor, name='waiter_floor'),
    path('waiter/punch/', views.waiter_punch_order, name='waiter_punch_order'),
    path('waiter/running/', views.waiter_running_orders, name='waiter_running_orders'),
    path('waiter/alerts/', views.waiter_alerts, name='waiter_alerts'),

    # ==========================================
    # 9. CASHIER PANEL ROUTES (Stubs)
    # ==========================================
    path('cashier/pos/', views.cashier_pos, name='cashier_pos'),
    path('cashier/history/', views.cashier_history, name='cashier_history'),
    path('cashier/settlements/', views.cashier_settlements, name='cashier_settlements'),
    path('cashier/day-close/', views.cashier_day_close, name='cashier_day_close'),
    path('cashier/print/<str:order_id>/', views.print_bill, name='print_bill'),
    path('cashier/get-bill/<int:table_id>/', views.get_bill_details, name='get_bill_details'),
    path('cashier/settle-order/', views.complete_settlement, name='complete_settlement'),

    path('api/repeat-item/', views.api_repeat_item, name='api_repeat_item'),
    path('api/customer-call/', views.customer_call_action, name='customer_call_action'),
    path('api/get-item-customization/<int:item_id>/', views.api_get_item_customization, name='get_item_customization'),
    path('api/kds-updates/', views.api_kds_updates, name='api_kds_updates'),
    path('api/waiter-updates/', views.api_waiter_updates, name='api_waiter_updates'),
path('api/resolve-alert/', views.api_resolve_alert, name='api_resolve_alert'),
path('api/get-order-status/', views.get_current_order_status, name='get_order_status'),
]