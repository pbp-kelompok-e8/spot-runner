from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('event_organizer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventorganizer',
            name='total_events',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='eventorganizer',
            name='rating',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='eventorganizer',
            name='review_count',
            field=models.IntegerField(default=0),
        ),
    ]