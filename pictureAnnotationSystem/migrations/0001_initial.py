# Generated by Django 3.0.7 on 2020-06-27 01:50

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AnnotationInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_url', models.CharField(max_length=100)),
                ('annotation_text', models.CharField(max_length=255)),
                ('annotation_time', models.DateTimeField()),
            ],
        ),
    ]
