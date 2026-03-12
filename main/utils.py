import datetime
import random
import string
import qrcode
import io
from django.core.files.base import ContentFile
from .models import Order, Table

def generate_invoice_number():
    """
    Professional Invoice Format: RR/YEAR/RANDOM_ID
    Example: RR/2026/A9B2
    """
    current_year = datetime.datetime.now().strftime('%Y')
    prefix = "RR"
    
    # Random 4 character alphanumeric string
    random_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    invoice_no = f"{prefix}/{current_year}/{random_id}"
    
    # Ensure uniqueness in database
    if Order.objects.filter(order_id=invoice_no).exists():
        return generate_invoice_number() 
        
    return invoice_no

def format_thermal_data(order_id):
    """
    Thermal printer formatting logic
    """
    try:
        order = Order.objects.get(order_id=order_id)
        items = order.items.all()
        
        data = {
            'order': order,
            'items': items,
            'subtotal': order.total_amount,
            'gst': round(float(order.total_amount) * 0.05, 2),
            'grand_total': round(float(order.total_amount) * 1.05, 2),
            'print_time': datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        }
        return data
    except Order.DoesNotExist:
        return None

def generate_table_qr(table_id):
    """
    DYNAMIC QR GENERATOR: Uses Laptop IP so mobile can open the link
    """
    try:
        table = Table.objects.get(id=table_id)
        
        # 🌟 CRITICAL: Use your Laptop IP here 🌟
        # Replace 192.168.224.41 if your IP changes in future
        base_url = "http://192.168.224.41:8000/menu/"
        full_url = f"{base_url}?table={table.name}"
        
        # Create QR instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(full_url)
        qr.make(fit=True)

        # Create Image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to buffer to store in Django ImageField
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        file_name = f'qr_table_{table.name}.png'
        
        # Update Table model's QR field
        table.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)
        table.save()
        
        return True
    except Exception as e:
        print(f"QR Generation Error: {e}")
        return False