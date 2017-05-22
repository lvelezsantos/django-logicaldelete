from django.db import models

from logicaldelete.query import LogicalDeleteQuerySet


class LogicalDeletedManager(models.Manager):
    """
    A manager that serves as the default manager for `logicaldelete.models.Model`
    providing the filtering out of logically deleted objects.  In addition, it
    provides named querysets for getting the deleted objects.
    """
    
    def get_query_set(self):

        if self.model:
            return LogicalDeleteQuerySet(self.model, using=self._db).filter(
                date_removed__isnull=True
            )
    
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

    def everything(self):
        if self.model:
            return LogicalDeleteQuerySet(self.model, using=self._db).all()
