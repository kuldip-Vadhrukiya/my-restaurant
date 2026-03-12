from django.contrib import admin
from .models import (
    Category, MenuItem, Table, Order, OrderItem,
    Staff, Role, RestaurantSetting, TaxSetting,
    ItemVariant, ItemAddOn  # <--- 1. YE JODIYE
)

# ===============================
# CATEGORY ADMIN
# ===============================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    ordering = ('sort_order',)

# ===============================
# VARIANTS & ADDONS (INLINES) - 2. YE NAYE CLASSES HAI
# ===============================
class VariantInline(admin.TabularInline):
    model = ItemVariant
    extra = 1 # कितने खाली डिब्बे पहले से दिखाने हैं

class AddOnInline(admin.TabularInline):
    model = ItemAddOn
    extra = 1

# ===============================
# MENU ITEM ADMIN
# ===============================
@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    # 3. YE LINE ZAROOR JODIYE
    inlines = [VariantInline, AddOnInline] 
    
    list_display = ('name', 'category', 'price', 'is_veg', 'is_available')
    list_editable = ('price', 'is_available')
    list_filter = ('category', 'is_veg')
    search_fields = ('name',)

# ===============================
# SIMPLE REGISTRATIONS
# ===============================
admin.site.register(Table)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Staff)
admin.site.register(Role)
admin.site.register(RestaurantSetting)
admin.site.register(TaxSetting)