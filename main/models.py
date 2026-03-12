from django.db import models
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw
from django.contrib.auth.models import User
from django.utils import timezone

# ==========================================
# 1. MENU & CATEGORY MODELS
# ==========================================

class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, null=True, default="fa-solid fa-utensils") 
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['sort_order']


class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    
    # --- Pehle wale fields ---
    is_veg = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    is_bestseller = models.BooleanField(default=False)
    
    # --- Naye Filter Fields (Inhe Add Karo) ---
    is_jain = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_spicy = models.BooleanField(default=False)
    is_kids_friendly = models.BooleanField(default=True)
    is_chef_special = models.BooleanField(default=False)
    prep_time = models.IntegerField(default=15, help_text="In minutes") # Isse Quick Serve filter chalega
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# --- ADDED FOR OPTION 2: VARIANTS & ADD-ONS ---

class ItemVariant(models.Model):
    """E.g. Half, Full, 500ml, 1kg"""
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='variants')
    variant_name = models.CharField(max_length=50) # 'Half' or 'Full'
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.item.name} - {self.variant_name} (₹{self.price})"

class ItemAddOn(models.Model):
    """E.g. Extra Cheese, Extra Mayo"""
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='addons')
    addon_name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.addon_name} (+₹{self.price})"


# ==========================================
# 2. TABLE MANAGEMENT (QR Code)
# ==========================================

class Table(models.Model):
    name = models.CharField(max_length=50, unique=True) # e.g. T1, T2
    capacity = models.IntegerField(default=4)
    is_occupied = models.BooleanField(default=False)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

# 2. TABLE & LIVE QR
class Table(models.Model):
    name = models.CharField(max_length=50, unique=True)
    capacity = models.IntegerField(default=4)
    is_occupied = models.BooleanField(default=False)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.qr_code:
            from django.conf import settings
            # 🌟 LIVE URL: settings.py से SITE_URL उठाएगा
            base_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')
            qr_data = f"{base_url}/menu/?table={self.name}"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            self.qr_code.save(f'qr_table_{self.name}.png', File(buffer), save=False)
        super().save(*args, **kwargs)

    def __str__(self): return self.name
    
# ==========================================
# 3. STAFF & ROLES (UPDATED PROFESSIONAL)
# ==========================================

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    permissions = models.TextField(blank=True, help_text="Comma separated permissions")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Staff(models.Model):
    # --- 1. Identity & Login ---
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True) # Link to Role model
    phone = models.CharField(max_length=15, unique=True) # Ye Username banega
    email = models.EmailField(blank=True, null=True)
    
    # --- 2. Personal Info ---
    address = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True, null=True)
    
    # --- 3. Financials ---
    salary_type = models.CharField(max_length=20, choices=[('Monthly', 'Monthly'), ('Daily', 'Daily')], default='Monthly')
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    
    # --- 4. Security & Docs ---
    pin_code = models.CharField(max_length=6, help_text="Login Password") 
    photo = models.ImageField(upload_to='staff_photos/', blank=True, null=True)
    id_proof = models.ImageField(upload_to='staff_docs/', blank=True, null=True) # Aadhaar/VoterID
    is_verified = models.BooleanField(default=False)
    
    # --- 5. Status ---
    joining_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.role.name if self.role else 'No Role'}"

# ==========================================
# 4. ORDER MODELS
# ==========================================

STATUS_CHOICES = (
    ('Pending', 'Pending'),
    ('Cooking', 'Cooking'),
    ('Ready', 'Ready'),
    ('Completed', 'Completed'),
    ('Cancelled', 'Cancelled'),
)

class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    # Table ko Foreign Key banaya hai taaki 'no such column' error na aaye
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, default="Pending")
    payment_mode = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.order_id}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    qty = models.IntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    spice = models.CharField(max_length=50, blank=True, null=True)
    instruction = models.CharField(max_length=255, blank=True, null=True)
    item_status = models.CharField(max_length=20, default='Pending') 
    
    # --- Option 2 Fields ---
    variant_name = models.CharField(max_length=50, blank=True, null=True) # Saves 'Half' or 'Full'
    addons_list = models.TextField(blank=True, null=True) # Saves 'Extra Cheese, Extra Mayo' as text

    def get_total(self):
        return self.qty * self.price
     # ==========================================
# ==========================================
# 5. ADVANCED SETTINGS MODELS
# ==========================================

class RestaurantSetting(models.Model):
    # --- 1. Branding & Identity ---
    name = models.CharField(max_length=100, default="My Restaurant")
    tagline = models.CharField(max_length=200, blank=True, null=True, help_text="e.g. Taste of Gujarat")
    logo = models.ImageField(upload_to='branding/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='branding/', blank=True, null=True, help_text="Banner for Customer Menu")
    
    # --- 2. Contact & Social ---
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)
    maps_link = models.URLField(blank=True, null=True, help_text="Google Maps Location Link")

    # --- 3. Operational Settings (Dukaan kab khulegi?) ---
    is_open = models.BooleanField(default=True, help_text="Master Switch to Open/Close Restaurant")
    opening_time = models.TimeField(blank=True, null=True)
    closing_time = models.TimeField(blank=True, null=True)
    
    # --- 4. Order & Billing Rules ---
    currency_symbol = models.CharField(max_length=5, default="₹")
    service_charge_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Extra Service Charge %")
    packaging_charge = models.IntegerField(default=0, help_text="Fixed charge for Takeaway orders")
    min_order_value = models.IntegerField(default=0, help_text="Minimum bill amount required")
    allow_takeaway = models.BooleanField(default=True)

    def __str__(self):
        return "Restaurant Master Config"

# (TaxSetting model waisa hi rahega, usme change nahi hai)
class TaxSetting(models.Model):
    gst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    cgst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=2.50)
    sgst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=2.50)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    is_gst_inclusive = models.BooleanField(default=True)

    def __str__(self):
        return "Tax Config"

# ==========================================
# 6. MANAGER SPECIFIC MODELS (UPDATED)
# ==========================================

class Expense(models.Model):
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)
    payment_mode = models.CharField(max_length=50, default='Cash Drawer')
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"

class Attendance(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='Absent') # Present, Late, Half-Day, Absent
    
    class Meta:
        unique_together = ('staff', 'date')

    def __str__(self):
        return f"{self.staff.name} - {self.status} ({self.date})"

class OverrideLog(models.Model):
    action_type = models.CharField(max_length=100)
    target = models.CharField(max_length=100)
    impact = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason = models.TextField()
    authorized_by = models.CharField(max_length=100, default='Manager')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} - {self.target}"

class ZReport(models.Model):
    date = models.DateField(unique=True, default=timezone.now)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_expected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mismatch_reason = models.TextField(blank=True, null=True)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    closed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Z-Report - {self.date}"

class Reservation(models.Model):
    customer_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    time = models.TimeField()
    guests = models.IntegerField(default=2)
    status = models.CharField(max_length=20, default='Booked', choices=[('Booked', 'Booked'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - Table {self.table}"

# ==========================================
# INVENTORY & STOCK MODEL
# ==========================================
class InventoryItem(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    stock = models.FloatField(default=0.0)
    unit = models.CharField(max_length=20)
    min_level = models.FloatField(default=5.0)
    price_per_unit = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.stock} {self.unit}"

# ==========================================
# 7. WAITER ALERTS (NEW)
# ==========================================
class WaiterAlert(models.Model):
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20) # 'water', 'bill', 'calling', 'food', 'clean'
    message = models.CharField(max_length=255)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.table.name} - {self.alert_type}"