from django.db import models
from .soft_delete_models import SoftDeleteModel


class Base_model(SoftDeleteModel):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
