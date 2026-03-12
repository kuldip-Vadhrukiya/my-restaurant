from django.core.management.base import BaseCommand
from main.models import Category, MenuItem
import random

class Command(BaseCommand):
    help = 'Seeds the database with 10 Categories and 50 realistic Menu Items'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Clearing old menu data...'))
        # Puraana kachra saaf kar rahe hain taaki duplicate na ho
        MenuItem.objects.all().delete()
        Category.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Generating Real Menu Data...'))

        # 1. 10 Asali Categories
        categories_data = [
            {"name": "Soups", "icon": "fa-bowl-hot", "order": 1},
            {"name": "Starters", "icon": "fa-utensils", "order": 2},
            {"name": "Punjabi Main Course", "icon": "fa-fire", "order": 3},
            {"name": "Gujarati Special", "icon": "fa-plate-wheat", "order": 4},
            {"name": "Tandoor Breads", "icon": "fa-bread-slice", "order": 5},
            {"name": "Rice & Biryani", "icon": "fa-bowl-rice", "order": 6},
            {"name": "Chinese", "icon": "fa-bowl-food", "order": 7},
            {"name": "Pizzas & Fast Food", "icon": "fa-pizza-slice", "order": 8},
            {"name": "Desserts", "icon": "fa-ice-cream", "order": 9},
            {"name": "Beverages", "icon": "fa-mug-hot", "order": 10},
        ]

        created_categories = {}
        for cat in categories_data:
            obj = Category.objects.create(
                name=cat["name"], icon=cat["icon"], sort_order=cat["order"], is_active=True
            )
            created_categories[cat["name"]] = obj

        # 2. 50 Asali Menu Items (Perfect Data)
        menu_items_data = [
            # SOUPS
            {"cat": "Soups", "name": "Tomato Soup", "price": 110, "desc": "Fresh roasted tomato soup with croutons.", "veg": True, "jain": True, "kids": True, "prep": 10},
            {"cat": "Soups", "name": "Sweet Corn Soup", "price": 120, "desc": "Creamy corn soup, lightly spiced.", "veg": True, "jain": True, "kids": True, "prep": 10},
            {"cat": "Soups", "name": "Veg Manchow Soup", "price": 130, "desc": "Spicy dark soup with crispy noodles.", "veg": True, "jain": False, "spicy": True, "prep": 12},
            {"cat": "Soups", "name": "Hot & Sour Soup", "price": 130, "desc": "Classic Indo-Chinese spicy and tangy soup.", "veg": True, "jain": False, "spicy": True, "prep": 12},
            {"cat": "Soups", "name": "Lemon Coriander Soup", "price": 125, "desc": "Refreshing clear soup with lemon zest.", "veg": True, "jain": False, "prep": 10},

            # STARTERS
            {"cat": "Starters", "name": "Paneer Tikka Dry", "price": 240, "desc": "Charcoal grilled paneer chunks.", "veg": True, "jain": False, "bestseller": True, "prep": 15},
            {"cat": "Starters", "name": "Hara Bhara Kabab", "price": 190, "desc": "Crispy spinach and green peas patties.", "veg": True, "jain": False, "prep": 15},
            {"cat": "Starters", "name": "Chilli Paneer Dry", "price": 220, "desc": "Crispy paneer tossed in spicy soy sauce.", "veg": True, "jain": False, "spicy": True, "prep": 15},
            {"cat": "Starters", "name": "Crispy Corn", "price": 180, "desc": "Deep fried corn kernels tossed with spices.", "veg": True, "jain": False, "kids": True, "prep": 12},
            {"cat": "Starters", "name": "Cheese Garlic Bread", "price": 160, "desc": "Oven baked bread loaded with cheese.", "veg": True, "jain": False, "kids": True, "prep": 10},

            # PUNJABI MAIN COURSE
            {"cat": "Punjabi Main Course", "name": "Paneer Butter Masala", "price": 260, "desc": "Paneer in rich tomato-cashew gravy.", "veg": True, "jain": True, "bestseller": True, "prep": 20},
            {"cat": "Punjabi Main Course", "name": "Kaju Curry", "price": 290, "desc": "Roasted cashews in mild creamy gravy.", "veg": True, "jain": True, "chef": True, "prep": 20},
            {"cat": "Punjabi Main Course", "name": "Veg Kadai", "price": 220, "desc": "Mixed vegetables tossed in kadai masala.", "veg": True, "jain": False, "spicy": True, "prep": 18},
            {"cat": "Punjabi Main Course", "name": "Dal Makhani", "price": 190, "desc": "Slow-cooked black lentils with butter and cream.", "veg": True, "jain": True, "bestseller": True, "prep": 15},
            {"cat": "Punjabi Main Course", "name": "Palak Paneer", "price": 240, "desc": "Paneer cubes in creamy spinach puree.", "veg": True, "jain": False, "prep": 18},

            # GUJARATI SPECIAL
            {"cat": "Gujarati Special", "name": "Gujarati Thali (Unlimited)", "price": 250, "desc": "Authentic full Gujarati meal with farsan and sweet.", "veg": True, "jain": True, "bestseller": True, "prep": 5},
            {"cat": "Gujarati Special", "name": "Sev Tameta Nu Shaak", "price": 160, "desc": "Sweet & spicy tomato curry topped with sev.", "veg": True, "jain": True, "prep": 15},
            {"cat": "Gujarati Special", "name": "Bharela Ringan", "price": 180, "desc": "Stuffed brinjal cooked in peanut-sesame gravy.", "veg": True, "jain": False, "prep": 20},
            {"cat": "Gujarati Special", "name": "Lasaniya Batata", "price": 170, "desc": "Spicy garlic and potato curry.", "veg": True, "jain": False, "spicy": True, "prep": 15},
            {"cat": "Gujarati Special", "name": "Kadhi Khichdi", "price": 150, "desc": "Comforting yellow kadhi served with soft khichdi.", "veg": True, "jain": True, "kids": True, "prep": 10},

            # TANDOOR BREADS
            {"cat": "Tandoor Breads", "name": "Butter Naan", "price": 45, "desc": "Soft tandoori bread brushed with butter.", "veg": True, "jain": True, "kids": True, "prep": 5},
            {"cat": "Tandoor Breads", "name": "Garlic Naan", "price": 60, "desc": "Naan topped with minced garlic and cilantro.", "veg": True, "jain": False, "bestseller": True, "prep": 5},
            {"cat": "Tandoor Breads", "name": "Tandoori Roti", "price": 30, "desc": "Whole wheat bread baked in clay oven.", "veg": True, "jain": True, "prep": 5},
            {"cat": "Tandoor Breads", "name": "Lachha Paratha", "price": 50, "desc": "Layered whole wheat crispy flatbread.", "veg": True, "jain": True, "prep": 8},
            {"cat": "Tandoor Breads", "name": "Cheese Stuffed Kulcha", "price": 90, "desc": "Rich bread stuffed with processed cheese.", "veg": True, "jain": False, "kids": True, "prep": 10},

            # RICE & BIRYANI
            {"cat": "Rice & Biryani", "name": "Veg Dum Biryani", "price": 220, "desc": "Aromatic basmati rice cooked with veggies & spices.", "veg": True, "jain": False, "bestseller": True, "prep": 20},
            {"cat": "Rice & Biryani", "name": "Jeera Rice", "price": 140, "desc": "Basmati rice tossed with roasted cumin.", "veg": True, "jain": True, "kids": True, "prep": 10},
            {"cat": "Rice & Biryani", "name": "Dal Khichdi", "price": 180, "desc": "Homestyle mix of rice and yellow lentils with tadka.", "veg": True, "jain": True, "kids": True, "prep": 15},
            {"cat": "Rice & Biryani", "name": "Hyderabadi Biryani", "price": 240, "desc": "Spicy green masala biryani served with raita.", "veg": True, "jain": False, "spicy": True, "prep": 20},
            {"cat": "Rice & Biryani", "name": "Peas Pulao", "price": 160, "desc": "Mildly spiced rice with green peas.", "veg": True, "jain": True, "prep": 12},

            # CHINESE
            {"cat": "Chinese", "name": "Veg Hakka Noodles", "price": 180, "desc": "Stir-fried noodles with crunchy vegetables.", "veg": True, "jain": False, "kids": True, "prep": 12},
            {"cat": "Chinese", "name": "Schezwan Noodles", "price": 190, "desc": "Spicy noodles tossed in schezwan sauce.", "veg": True, "jain": False, "spicy": True, "prep": 12},
            {"cat": "Chinese", "name": "Veg Fried Rice", "price": 170, "desc": "Classic wok-tossed Chinese rice.", "veg": True, "jain": False, "prep": 12},
            {"cat": "Chinese", "name": "Manchurian Gravy", "price": 200, "desc": "Veg dumplings in soy-garlic dark sauce.", "veg": True, "jain": False, "prep": 15},
            {"cat": "Chinese", "name": "Paneer Chilli Gravy", "price": 230, "desc": "Spicy paneer cubes in Chinese style gravy.", "veg": True, "jain": False, "spicy": True, "chef": True, "prep": 15},

            # PIZZAS & FAST FOOD
            {"cat": "Pizzas & Fast Food", "name": "Margherita Pizza", "price": 200, "desc": "Classic cheese and tomato pizza.", "veg": True, "jain": True, "kids": True, "prep": 18},
            {"cat": "Pizzas & Fast Food", "name": "Tandoori Paneer Pizza", "price": 260, "desc": "Spicy paneer, onions, and capsicum topping.", "veg": True, "jain": False, "bestseller": True, "prep": 18},
            {"cat": "Pizzas & Fast Food", "name": "French Fries", "price": 120, "desc": "Crispy salted potato fries.", "veg": True, "jain": True, "kids": True, "prep": 10},
            {"cat": "Pizzas & Fast Food", "name": "Peri Peri Fries", "price": 140, "desc": "Fries tossed in spicy peri peri mix.", "veg": True, "jain": False, "spicy": True, "prep": 10},
            {"cat": "Pizzas & Fast Food", "name": "Veg Club Sandwich", "price": 150, "desc": "Triple layered sandwich with veggies and cheese.", "veg": True, "jain": True, "prep": 12},

            # DESSERTS
            {"cat": "Desserts", "name": "Sizzling Brownie", "price": 220, "desc": "Hot walnut brownie with vanilla ice cream and chocolate syrup.", "veg": True, "jain": True, "bestseller": True, "chef": True, "prep": 10},
            {"cat": "Desserts", "name": "Gulab Jamun (2 pcs)", "price": 80, "desc": "Hot soft milk dumplings in sugar syrup.", "veg": True, "jain": True, "kids": True, "prep": 5},
            {"cat": "Desserts", "name": "Rasmalai", "price": 120, "desc": "Soft cottage cheese discs in sweet saffron milk.", "veg": True, "jain": True, "prep": 5},
            {"cat": "Desserts", "name": "Vanilla Ice Cream", "price": 60, "desc": "Classic vanilla scoop.", "veg": True, "jain": True, "kids": True, "prep": 2},
            {"cat": "Desserts", "name": "Chocolate Pastry", "price": 110, "desc": "Rich dark chocolate pastry.", "veg": True, "jain": True, "kids": True, "prep": 2},

            # BEVERAGES
            {"cat": "Beverages", "name": "Masala Chaas", "price": 40, "desc": "Spiced buttermilk to aid digestion.", "veg": True, "jain": False, "bestseller": True, "prep": 2},
            {"cat": "Beverages", "name": "Sweet Lassi", "price": 70, "desc": "Thick sweetened yogurt drink.", "veg": True, "jain": True, "kids": True, "prep": 5},
            {"cat": "Beverages", "name": "Fresh Lime Soda", "price": 60, "desc": "Refreshing lime drink, sweet or salted.", "veg": True, "jain": True, "prep": 5},
            {"cat": "Beverages", "name": "Cold Coffee", "price": 90, "desc": "Blended iced coffee.", "veg": True, "jain": True, "prep": 5},
            {"cat": "Beverages", "name": "Mineral Water (1L)", "price": 20, "desc": "Packaged drinking water.", "veg": True, "jain": True, "prep": 1},
        ]

        count = 0
        for item in menu_items_data:
            cat_obj = created_categories[item["cat"]]
            MenuItem.objects.create(
                category=cat_obj,
                name=item["name"],
                price=item["price"],
                description=item["desc"],
                is_veg=item.get("veg", True),
                is_jain=item.get("jain", False),
                is_spicy=item.get("spicy", False),
                is_kids_friendly=item.get("kids", False),
                is_bestseller=item.get("bestseller", False),
                is_chef_special=item.get("chef", False),
                prep_time=item.get("prep", 15),
                is_available=True
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ BOOM! Successfully added 10 Categories and {count} Menu Items to the Database!'))