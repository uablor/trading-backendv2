#
# NOTE: pip install django-soft-delete 0.9.21
#

from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db.models.fields.related_descriptors import (
    ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor,
)


def get_settings():
    default_settings = dict(
        cascade=True,
    )
    return getattr(settings, 'DJANGO_SOFTDELETE_SETTINGS', default_settings)


class SoftDeleteQuerySet(models.query.QuerySet):
    def delete(self, cascade=None):
        cascade = get_settings().get('cascade', True)
        if cascade:  # delete one by one if cascade
            for obj in self.all():
                obj.delete(cascade=cascade)
        return self.update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class DeletedQuerySet(models.query.QuerySet):
    def restore(self, *args, **kwargs):
        qs = self.filter(*args, **kwargs)
        qs.update(is_deleted=False, deleted_at=None)


class DeletedManager(models.Manager):
    def get_queryset(self):
        return DeletedQuerySet(self.model, using=self._db).filter(is_deleted=True)


class GlobalManager(models.Manager):
    pass


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeleteManager()
    deleted_objects = DeletedManager()
    all_objects = GlobalManager()

    class Meta:
        abstract = True
        ordering = ['-updated_at']

    def delete(self, cascade=None, *args, **kwargs):
        cascade = get_settings().get('cascade', True)
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
        self.after_delete()
        if cascade:
            self.delete_related_objects()

    def restore(self, cascade=None):
        cascade = get_settings().get('cascade', True)
        self.is_deleted = False
        self.deleted_at = None
        self.save()
        self.after_restore()
        if cascade:
            self.restore_related_objects()

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def get_related_objects(self):
        attributes = vars(self._meta.model)
        reverse_attributes = [
            a
            for a, b in attributes.items()
            if type(b) in [ReverseManyToOneDescriptor, ReverseOneToOneDescriptor]
        ]
        related_objects = []
        for reverse_attribute in reverse_attributes:
            try:
                related_objects.extend(list(getattr(self, reverse_attribute).all()))
            except Exception as e:
                pass  # Consider logging the exception
        return related_objects

    def delete_related_objects(self):
        for obj in self.get_related_objects():
            obj.delete()

    def restore_related_objects(self):
        for obj in self.get_related_objects():
            obj.restore()

    def after_delete(self):
        pass

    def after_restore(self):
        pass

    # Experimental zone

    # soft_delete_kwargs = {
    #     'related_objects': ['client', 'brokersms_set', ],
    #     'allow_related_objects_hard_deletion': True,
    #     'cascade': True,
    # }
    #
    # @classmethod
    # def _get_kwargs(cls):
    #     return cls.soft_delete_kwargs
    #
    # @property
    # def _obj_model_class(self):
    #     if self._get_kwargs().get('allow_related_objects_hard_deletion', False):
    #         return models.Model
    #     return SoftDeleteModel
    #
    # def _get_related_objects(self, relation):
    #     qs = getattr(self, relation)
    #     if isinstance(qs, models.Manager):
    #         return qs
    #     elif isinstance(qs, self._obj_model_class):
    #         return qs  # do nothing
    #     return
    #
    # def related_objects(self, raise_exception=False, use_soft_manager=False):
    #     relations = self._get_kwargs().get('related_objects', [])
    #     objects = {}
    #     for relation in relations:
    #         try:
    #             qs = self._get_related_objects(relation)
    #         except ObjectDoesNotExist as e:
    #             if raise_exception:
    #                 raise e
    #             continue
    #         else:
    #             objects[relation] = qs
    #         # try:
    #         #     qs = getattr(self, relation)
    #         #     print('-->', qs, type(qs))
    #         # except ObjectDoesNotExist as e:
    #         #     if raise_exceptions:
    #         #         raise e
    #         #     continue
    #         # else:
    #         #     if isinstance(qs, models.Manager):
    #         #         qs = qs.all()
    #         #     elif isinstance(qs, models.Model):
    #         #         pass  # do nothing
    #         #     else:
    #         #         raise AttributeError
    #         #     objects[relation] = qs
    #     return objects
    #
    # def delete_related_objects(self, raise_exception=False):
    #     for k, qs in self.related_objects(raise_exception=raise_exception).items():
    #         qs.delete()
    #
    # def restore_related_objects(self, raise_exception=False):
    #     for k, qs in self.related_objects(raise_exception=raise_exception).items():
    #         try:
    #             ids = qs.values_list('pk', flat=True)
    #             qs.model.deleted_objects.filter(pk__in=ids).restore()
    #         except AttributeError:
    #             qs.restore()
