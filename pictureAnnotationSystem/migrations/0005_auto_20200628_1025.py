# Generated by Django 3.0.7 on 2020-06-28 10:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pictureAnnotationSystem', '0004_auto_20200627_1935'),
    ]

    operations = [
        migrations.CreateModel(
            name='PictureInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pic_url', models.CharField(max_length=100, null=True)),
                ('pic_user', models.CharField(max_length=32, null=True)),
                ('pic_time', models.DateTimeField()),
            ],
        ),
        migrations.RemoveField(
            model_name='annotationinfo',
            name='old_url',
        ),
        migrations.AddField(
            model_name='annotationinfo',
            name='pic_info',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pictureAnnotationSystem.PictureInfo'),
        ),
    ]
