# Generated by Django 4.1.7 on 2023-05-16 07:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MASTF', '0024_scantask_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='findingtemplate',
            name='internal_id',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='finding',
            name='discovery_date',
            field=models.DateField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='permissionfinding',
            name='discovery_date',
            field=models.DateField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='vulnerability',
            name='discovery_date',
            field=models.DateField(auto_now=True, null=True),
        ),
    ]
