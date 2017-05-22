from django.db import models, router
from django.db.models.deletion import Collector
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from logicaldelete.deletion import LogicalDeleteCollector
from logicaldelete import managers

LOGICAL_DELETION = 4
LOGICAL_RESTORE = 5


class LogicalModel(models.Model):
    """
    This base model provides date fields and functionality to enable logical
    delete functionality in derived models.
    """
    
    date_created = models.DateTimeField(default=timezone.now)
    date_modified = models.DateTimeField(default=timezone.now)
    date_removed = models.DateTimeField(null=True, blank=True)
    
    objects = managers.LogicalDeletedManager()
    #TODO: Create undelete permissions to all models

    def active(self):
        return self.date_removed is None

    active.boolean = True
    active.short_description = _('Active')

    def delete(self, using=None, keep_parents=False):
        using = using or router.db_for_write(self.__class__, instance=self)
        assert self._get_pk_val() is not None, (
            "%s object can't be deleted because its %s attribute is set to None." %
            (self._meta.object_name, self._meta.pk.attname)
        )

        collector = LogicalDeleteCollector(using=using)
        collector.collect([self], keep_parents=keep_parents)
        return collector.delete()

    delete.alters_data = True

    def delete_complete(self, using=None, keep_parents=False):
        using = using or router.db_for_write(self.__class__, instance=self)
        assert self._get_pk_val() is not None, (
            "%s object can't be deleted because its %s attribute is set to None." %
            (self._meta.object_name, self._meta.pk.attname)
        )

        collector = Collector(using=using)
        collector.collect([self], keep_parents=keep_parents)
        return collector.delete()

    delete_complete.alters_data = True

    def undelete(self, using=None, keep_parents=False):
        using = using or router.db_for_write(self.__class__, instance=self)
        assert self._get_pk_val() is not None, (
            "%s object can't be deleted because its %s attribute is set to None." %
            (self._meta.object_name, self._meta.pk.attname)
        )

        collector = LogicalDeleteCollector(using=using)
        collector.collect([self], keep_parents=keep_parents)
        return collector.undelete()

    undelete.alters_data = True

    class Meta:
        abstract = True
