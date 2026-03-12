import os
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurant.settings') # अपना प्रोजेक्ट नाम चेक कर लेना
django.setup()

from main.models import MenuItem, ItemVariant, ItemAddOn

def seed_data():
    items = MenuItem.objects.all()
    print(f"Total {items.count()} items मिले। काम शुरू हो रहा है...")

    for item in items:
        # 1. डमी वेरिएंट्स (Half और Full)
        # Half की कीमत ओरिजिनल से 60% और Full ओरिजिनल कीमत पर
        if not item.variants.exists():
            ItemVariant.objects.create(
                item=item, 
                variant_name="Half", 
                price=float(item.price) * 0.6
            )
            ItemVariant.objects.create(
                item=item, 
                variant_name="Full", 
                price=float(item.price)
            )
            print(f"✅ Variants added for: {item.name}")

        # 2. डमी ऐड-ऑन्स
        if not item.addons.exists():
            ItemAddOn.objects.create(item=item, addon_name="Extra Cheese", price=30)
            ItemAddOn.objects.create(item=item, addon_name="Extra Mayo", price=15)
            print(f"➕ Add-ons added for: {item.name}")

    print("\n🚀 सारा डमी डेटा डल गया! अब एडमिन और मेनू चेक करो।")

if __name__ == "__main__":
    seed_data()