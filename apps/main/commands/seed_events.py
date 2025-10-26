import json
import random
from datetime import datetime
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand
from apps.main.models import Event, EventCategory
from apps.event_organizer.models import EventOrganizer

# Mapping kategori JSON -> Model
CATEGORY_MAP = {
    "Fun Run": "fun_run",
    "5K": "5k",
    "10K": "10k",
    "Half Marathon": "half_marathon",
    "Full Marathon": "full_marathon"
}

# Mapping status JSON -> Model
STATUS_MAP = {
    "Finished": "finished",
    "Coming Soon": "coming_soon",
    "On Going": "on_going"
}

def map_city(raw_city: str):
    """Mapping nama kota JSON ke pilihan model Django"""
    raw = raw_city.lower()

    if "jak" in raw: return "jakarta_pusat"
    if "bek" in raw: return "bekasi"
    if "bog" in raw: return "bogor"
    if "dep" in raw: return "depok"
    if "tan" in raw: return "tangerang"
    
    return "jakarta_barat"  # default


class Command(BaseCommand):
    help = "Seed Event data from dataset/event-dataset.json"

    def handle(self, *args, **kwargs):
        try:
            with open('dataset/event-dataset.json', 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("❌ File event-dataset.json tidak ditemukan!"))
            return

        # Ambil Event Organizer pertama jika ada
        eo_user = EventOrganizer.objects.first()

        created_count = 0
        skipped_count = 0

        for item in data:
            # CATEGORY
            category_key = CATEGORY_MAP.get(item["category"])
            if not category_key:
                skipped_count += 1
                print(f"⚠ Skip event karena kategori tidak dikenal: {item['category']}")
                continue

            category_obj = EventCategory.objects.get(category=category_key)

            # STATUS
            status = STATUS_MAP.get(item["status"], "coming_soon")

            # DATE parsing
            try:
                event_date = make_aware(datetime.strptime(item["eventDate"], "%Y-%m-%d"))
                regis_deadline = make_aware(datetime.strptime(item["regisDeadline"], "%Y-%m-%d"))
            except:
                skipped_count += 1
                print(f"⚠ Skip event karena format tanggal salah: {item['eventname']}")
                continue

            # CREATE EVENT
            event = Event.objects.create(
                user_eo=eo_user,
                name=item["eventname"],
                description=item["description"],
                location=map_city(item["location"]),
                image=item.get("image"),
                event_date=event_date,
                regist_deadline=regis_deadline,
                capacity=int(item["maxParticipant"]),
                total_participans=0,
                full=False,
                event_status=status,
                coin=random.randint(10, 100)
            )

            event.event_category.add(category_obj)
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Seeding selesai! {created_count} event berhasil dibuat, {skipped_count} dilewati."
        ))