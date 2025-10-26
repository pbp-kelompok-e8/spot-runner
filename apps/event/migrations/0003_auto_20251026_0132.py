# apps/event/migrations/0002_auto_....py

from django.db import migrations

def populate_event_categories(apps, schema_editor):
    # Dapatkan model yang sesuai dari App Registry
    # Ini penting agar migrasi dapat dijalankan bahkan jika model Anda berubah di masa depan.
    EventCategory = apps.get_model('event', 'EventCategory') 

    categories = [
        'fun_run',
        '5k',
        '10k',
        'half_marathon',
        'full_marathon'
    ]

    for category_name in categories:
        EventCategory.objects.get_or_create(category=category_name)
        
    # Jika Anda ingin menambahkan fungsi 'reverse' untuk menghapus data saat rollback (optional)
def reverse_populate_event_categories(apps, schema_editor):
    EventCategory = apps.get_model('event', 'EventCategory')
    categories = [
        'fun_run', '5k', '10k', 'half_marathon', 'full_marathon'
    ]
    
    # Hapus hanya kategori yang sudah kita masukkan
    EventCategory.objects.filter(category__in=categories).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0001_initial'), # Pastikan ini mengacu pada migrasi terakhir Anda
    ]

    operations = [
        # Menjalankan fungsi Python di atas
        migrations.RunPython(populate_event_categories, reverse_populate_event_categories),
    ]