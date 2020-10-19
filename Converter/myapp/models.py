from django.db import models


class Document(models.Model):
    docfile = models.FileField(upload_to='documents')

# Загружает файл по пути "media/documents"
