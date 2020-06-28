from django.db import models


class PictureInfo(models.Model):
    pic_url = models.CharField(null=True, max_length=100)
    pic_user_ip = models.CharField(null=True, max_length=32)
    pic_user_address = models.CharField(null=True, max_length=50)
    pic_width = models.IntegerField(null=True)
    pic_height = models.IntegerField(null=True)
    pic_time = models.DateTimeField()


class AnnotationInfo(models.Model):
    pic_info = models.ForeignKey(PictureInfo, on_delete=models.CASCADE, null=True)
    annotation_id = models.IntegerField(null=True)
    annotation_type = models.CharField(null=True, max_length=20)
    annotation_points = models.TextField(null=True)
    annotation_text = models.TextField(null=True)
    annotation_time = models.DateTimeField()
