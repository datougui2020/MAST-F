# Generated by Django 4.1.7 on 2023-03-23 15:02

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MASTF', '0005_findingtemplate_remove_scan_scanner_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scan',
            name='start_date',
            field=models.DateField(default=datetime.datetime.now),
        ),
    ]
