# Generated by Django 3.0.7 on 2020-06-28 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pictureAnnotationSystem', '0005_auto_20200628_1025'),
    ]

    operations = [
        migrations.AddField(
            model_name='pictureinfo',
            name='pic_height',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='pictureinfo',
            name='pic_width',
            field=models.IntegerField(null=True),
        ),
    ]
