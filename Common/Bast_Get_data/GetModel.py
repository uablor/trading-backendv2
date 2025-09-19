from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins


class Base_GetModel(mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    pass