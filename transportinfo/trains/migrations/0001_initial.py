# Generated by Django 2.2 on 2020-08-01 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LatestDepartures',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('station', models.CharField(max_length=3)),
                ('earliest', models.DateTimeField()),
                ('services', models.TextField()),
            ],
        ),
    ]
