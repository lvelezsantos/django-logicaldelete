import datetime

from django.db import models, router
from django.db.models.deletion import Collector

from logicaldelete.deletion import LogicalDeleteCollector
from logicaldelete import managers


class LogicalModel(models.Model):
    """
    This base model provides date fields and functionality to enable logical
    delete functionality in derived models.
    """
    
    date_created = models.DateTimeField(default=datetime.datetime.now)
    date_modified = models.DateTimeField(default=datetime.datetime.now)
    date_removed = models.DateTimeField(null=True, blank=True)
    
    objects = managers.LogicalDeletedManager()
    
    def active(self):
        return self.date_removed is None
    active.boolean = True
    active.short_description = 'Activo'
    
    def delete(self, using=None):
        using = using or router.db_for_write(self.__class__, instance=self)
        assert self._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (self._meta.object_name, self._meta.pk.attname)

        collector = LogicalDeleteCollector(using=using)
        collector.collect([self])
        collector.delete()

    delete.alters_data = True

    def delete_complete(self, using=None):
        using = using or router.db_for_write(self.__class__, instance=self)
        assert self._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (self._meta.object_name, self._meta.pk.attname)

        collector = Collector(using=using)
        collector.collect([self])
        collector.delete()

    delete_complete.alters_data = True

    def undelete(self, using=None):
        using = using or router.db_for_write(self.__class__, instance=self)
        assert self._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (self._meta.object_name, self._meta.pk.attname)

        collector = LogicalDeleteCollector(using=using)
        collector.collect([self])
        collector.undelete()

    undelete.alters_data = True

    class Meta:
        abstract = True
