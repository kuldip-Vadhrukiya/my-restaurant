import os
import django
import urllib.request
import random
from django.core.files.base import ContentFile

# 1. Django Environment Setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant.settings')
django.setup()

from main.models import Category, MenuItem

print("\n🧹 Cleaning old menu data...")
Category.objects.all().delete()
MenuItem.objects.all().delete()

print("🌍 Downloading High-Quality Food Images (It will take 5-10 seconds)...")

# 2. Reliable Image URLs (Unsplash API)
IMAGE_URLS = {
    'Starters': 'https://images.unsplash.com/photo-1541529086526-db283c563270?w=600&q=80',
    'Paneer': 'https://images.unsplash.com/photo-1631452180519-c014fe946bc0?w=600&q=80',
    'Veg': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=600&q=80',
    'Breads': 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=600&q=80',
    'Rice': 'https://images.unsplash.com/photo-1631515243349-e0cb75bfceb1?w=600&q=80',
    'Chinese': 'https://images.unsplash.com/photo-1585032226651-759b368d7246?w=600&q=80',
    'Dessert': 'https://images.unsplash.com/photo-1551024601-bec78aea704b?w=600&q=80',
    'Beverage': 'https://images.unsplash.com/photo-1544145945-f90425340c7e?w=600&q=80',
}

image_cache = {}
for key, url in IMAGE_URLS.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        image_cache[key] = urllib.request.urlopen(req).read()
        print(f"✅ Image loaded for {key}")
    except Exception as e:
        print(f"❌ Failed for {key}: {e}")
        image_cache[key] = b''

# 3. Menu Data (Format: Name, Price, is_spicy, is_jain, prep_time)
MENU_DATA = {
    "Soups & Starters": {
        "icon": "fa-solid fa-mug-hot", "img_key": "Starters", "items": [
            ("Tomato Soup", 110, False, True, 10), ("Manchow Soup", 130, True, False, 10),
            ("Sweet Corn Soup", 120, False, True, 10), ("Hot & Sour Soup", 125, True, False, 10),
            ("Paneer Chilli Dry", 220, True, False, 15), ("Veg Manchurian Dry", 190, True, False, 15),
            ("Crispy Veg", 180, False, False, 15), ("Paneer 65", 210, True, False, 15),
            ("Hara Bhara Kabab", 160, False, True, 12), ("Cheese Corn Balls", 190, False, True, 15),
            ("Veg Crispy", 170, True, False, 12), ("Mushroom Chilli", 230, True, False, 15),
            ("French Fries", 110, False, True, 10), ("Peri Peri Fries", 130, True, True, 10)
        ]
    },
    "Paneer Special": {
        "icon": "fa-solid fa-cheese", "img_key": "Paneer", "items": [
            ("Paneer Butter Masala", 260, True, True, 20), ("Kadai Paneer", 250, True, True, 20),
            ("Paneer Tikka Masala", 280, True, False, 20), ("Shahi Paneer", 270, False, True, 20),
            ("Mutter Paneer", 240, True, False, 20), ("Palak Paneer", 230, False, False, 20),
            ("Paneer Bhurji", 260, True, True, 15), ("Paneer Handi", 250, True, False, 20),
            ("Paneer Toofani", 290, True, False, 25), ("Paneer Lababdar", 280, False, True, 20),
            ("Paneer Pasanda", 270, False, False, 20), ("Cheese Butter Masala", 290, True, True, 20)
        ]
    },
    "Veg Main Course": {
        "icon": "fa-solid fa-leaf", "img_key": "Veg", "items": [
            ("Mix Veg", 210, False, True, 15), ("Veg Kolhapuri", 230, True, False, 18),
            ("Veg Jaipuri", 240, True, False, 18), ("Veg Kadai", 220, True, False, 15),
            ("Chana Masala", 200, True, True, 15), ("Aloo Gobi", 190, False, False, 15),
            ("Dum Aloo", 180, False, False, 15), ("Bhindi Masala", 170, True, False, 15),
            ("Sev Tamatar", 160, True, True, 12), ("Lasuni Palak", 210, True, False, 15),
            ("Kaju Curry", 280, False, True, 20), ("Kaju Masala", 270, True, True, 20)
        ]
    },
    "Indian Breads": {
        "icon": "fa-solid fa-bread-slice", "img_key": "Breads", "items": [
            ("Tandoori Roti", 25, False, True, 5), ("Butter Roti", 30, False, True, 5),
            ("Plain Naan", 40, False, True, 5), ("Butter Naan", 50, False, True, 5),
            ("Garlic Naan", 60, False, False, 5), ("Cheese Garlic Naan", 80, False, False, 7),
            ("Lachha Paratha", 50, False, False, 5), ("Pudina Paratha", 55, False, False, 5),
            ("Missi Roti", 45, False, True, 5), ("Aloo Kulcha", 70, True, False, 8),
            ("Paneer Kulcha", 90, False, False, 8), ("Roomali Roti", 45, False, True, 5)
        ]
    },
    "Rice & Biryani": {
        "icon": "fa-solid fa-bowl-rice", "img_key": "Rice", "items": [
            ("Steamed Rice", 110, False, True, 10), ("Jeera Rice", 130, False, True, 10),
            ("Dal Fry", 150, True, True, 15), ("Dal Tadka", 160, True, False, 15),
            ("Veg Pulao", 170, False, True, 15), ("Peas Pulao", 160, False, True, 15),
            ("Kashmiri Pulao", 190, False, True, 15), ("Veg Biryani", 220, True, False, 20),
            ("Hyderabadi Biryani", 240, True, False, 20), ("Paneer Biryani", 250, True, False, 20)
        ]
    },
    "Chinese Delights": {
        "icon": "fa-solid fa-bowl-food", "img_key": "Chinese", "items": [
            ("Veg Fried Rice", 180, True, False, 15), ("Schezwan Fried Rice", 200, True, False, 15),
            ("Triple Schezwan Rice", 250, True, False, 20), ("Veg Hakka Noodles", 190, True, False, 15),
            ("Schezwan Noodles", 210, True, False, 15), ("Chilli Garlic Noodles", 200, True, False, 15),
            ("Paneer Fried Rice", 220, True, False, 15), ("Singapore Fried Rice", 210, True, False, 15)
        ]
    },
    "Desserts": {
        "icon": "fa-solid fa-ice-cream", "img_key": "Dessert", "items": [
            ("Gulab Jamun (2 pcs)", 60, False, True, 5), ("Rasgulla (2 pcs)", 60, False, True, 5),
            ("Vanilla Ice Cream", 70, False, True, 5), ("Chocolate Ice Cream", 80, False, True, 5),
            ("Sizzling Brownie", 180, False, True, 10), ("Kaju Katli", 120, False, True, 5),
            ("Fruit Salad with Ice Cream", 140, False, True, 5), ("Moong Dal Halwa", 110, False, True, 5)
        ]
    },
    "Beverages": {
        "icon": "fa-solid fa-martini-glass-empty", "img_key": "Beverage", "items": [
            ("Mineral Water", 20, False, True, 2), ("Masala Chaas", 40, True, True, 5),
            ("Sweet Lassi", 50, False, True, 5), ("Fresh Lime Soda", 60, False, True, 5),
            ("Cold Coffee", 80, False, True, 5), ("Mango Milkshake", 110, False, True, 5),
            ("Oreo Milkshake", 130, False, True, 5), ("Virgin Mojito", 90, False, True, 5),
            ("Blue Lagoon Mocktail", 120, False, True, 5), ("Masala Tea", 30, True, True, 5)
        ]
    }
}

print("\n🚀 Creating Categories and Menu Items...")

sort_counter = 1
total_items = 0

for cat_name, data in MENU_DATA.items():
    # 1. Create Category
    category = Category.objects.create(
        name=cat_name, icon=data["icon"], sort_order=sort_counter
    )
    sort_counter += 1
    
    # 2. Create Items for this Category
    for item in data["items"]:
        name, price, is_spicy, is_jain, prep_time = item
        
        menu_item = MenuItem(
            category=category,
            name=name,
            price=price,
            description=f"Delicious and freshly prepared {name}.",
            is_spicy=is_spicy,
            is_jain=is_jain,
            prep_time=prep_time,
            is_bestseller=random.choice([True, False, False]), # 33% chance to be a bestseller
            is_chef_special=random.choice([True, False, False, False]) # 25% chance
        )
        
        # 3. Attach High-Quality Image from Cache
        img_bytes = image_cache.get(data["img_key"])
        if img_bytes:
            filename = f"{name.replace(' ', '_').lower()}.jpg"
            menu_item.image.save(filename, ContentFile(img_bytes), save=False)
            
        menu_item.save()
        total_items += 1

print(f"\n🎉 BOOM! Successfully added {Category.objects.count()} Categories and {total_items} Menu Items with real images!")
print("Run 'python manage.py runserver' and check your Menu page!")