import os
import django

# ตั้งค่า Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Core.Settings.prod")  # เปลี่ยนตาม settings ของคุณ
django.setup()

from Apps.Account.models import User

# สร้าง superuser ถ้ายังไม่มี
admin_email = os.environ.get("ADMIN_EMAIL", "admin@gmail.com")
admin_password = os.environ.get("ADMIN_PASSWORD", "Admin1234!")

if not User.objects.filter(email=admin_email).exists():
    User.objects.create_superuser(
        email=admin_email,
        password=admin_password,
        username="admin",
        is_verify=True
    )
    print(f"Superuser created: {admin_email}")
else:
    print("Superuser already exists.")
