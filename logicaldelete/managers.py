from django.db import models
from django.db.models.manager import BaseManager

from logicaldelete.query import LogicalDeleteQuerySet


class LogicalDeletedManager(BaseManager.from_queryset(LogicalDeleteQuerySet)):
    """
    A manager that serves as the default manager for `logicaldelete.models.Model`
    providing the filtering out of logically deleted objects.  In addition, it
    provides named querysets for getting the deleted objects.
    """
    
    def get_query_set(self, exclude_deleted=True):

        if self.model:
            qs = LogicalDeleteQuerySet(self.model, using=self._db).all()
            if exclude_deleted:
                qs = qs.filter(date_removed__isnull=True)

            if hasattr(self, 'core_filters') and self.core_filters is not None:
                return qs.filter(**self.core_filters)

            return qs
    
    def only_deleted(self):
        if self.model:
            return super(LogicalDeletedManager, self).get_query_set().filter(
                date_removed__isnull=False
            )

    def get(self, *args, **kwargs):
        return self.everything().get(*args, **kwargs)

    def get_or_create(self, **kwargs):
        return self.everything().get_or_create(**kwargs)

    def get_with_deleted(self, *args, **kwargs):
        return self.everything().get(*args, **kwargs)
    
    def filter(self, *args, **kwargs):
        if "pk" in kwargs:
            return self.everything().filter(*args, **kwargs)
        return self.get_query_set().filter(*args, **kwargs)

    def all(self):
        return self.get_query_set().all()

    def all_with_deleted(self):
        return self.everything()

    def everything(self):
        qs = self.get_query_set(False)
        qs.__class__ = LogicalDeleteQuerySet
        # for related manager
        # if hasattr(self, 'core_filters'):
        #     return qs.filter(**self.core_filters)
        return qs
