# Generated by Django 4.1.7 on 2023-04-23 05:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('MASTF', '0010_merge_0002_alter_package_type_0009_alter_host_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='HostTemplate',
            fields=[
                ('template_id', models.UUIDField(primary_key=True, serialize=False)),
                ('domain_name', models.CharField(max_length=256)),
                ('ip_adress', models.CharField(max_length=32, null=True)),
                ('owner', models.CharField(max_length=255, null=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='host',
            name='domain',
        ),
        migrations.RemoveField(
            model_name='host',
            name='scan',
        ),
        migrations.AddField(
            model_name='host',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='MASTF.hosttemplate'),
        ),
    ]
