# Generated by Django 3.0.7 on 2020-06-27 01:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pictureAnnotationSystem', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotationinfo',
            name='annotation_id',
            field=models.IntegerField(null=True),
        ),
    ]
