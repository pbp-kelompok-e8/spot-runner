import json
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from apps.main.models import User

# Mapping role dari JSON -> Model
ROLE_MAP = {
    "participant": "runner",
    "organizer": "event_organizer"
}

class Command(BaseCommand):
    help = "Seed User data from dataset/user-dataset.json"

    def handle(self, *args, **kwargs):
        try:
            with open('dataset/user-dataset.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("❌ File user-dataset.json tidak ditemukan!"))
            return

        created_count = 0
        skipped_count = 0

        for item in data:
            # Role mapping
            role = ROLE_MAP.get(item["role"], "runner")

            # Skip jika email sudah ada
            if User.objects.filter(email=item["email"]).exists():
                skipped_count += 1
                print(f"⚠ Skip karena email sudah terdaftar: {item['email']}")
                continue

            # Create user
            User.objects.create(
                username=item["username"],
                email=item["email"],
                password=make_password(item["password"]),
                role=role,
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Seeding Users selesai! {created_count} user berhasil dibuat, {skipped_count} dilewati."
        ))
