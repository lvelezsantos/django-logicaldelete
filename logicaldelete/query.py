from django.db.models.deletion import Collector
from django.db.models.query import QuerySet
from logicaldelete.deletion import LogicalDeleteCollector


class LogicalDeleteQuerySet(QuerySet):
    
    def delete(self):
        """
        Mark as deleted the records in the current QuerySet.
        """
        assert self.query.can_filter(),\
        "Cannot use 'limit' or 'offset' with delete."

        del_query = self._clone()

        # The delete is actually 2 queries - one to find related objects,
        # and one to delete. Make sure that the discovery of related
        # objects is performed on the same database as the deletion.
        del_query._for_write = True

        # Disable non-supported fields.
        del_query.query.select_for_update = False
        del_query.query.select_related = False
        del_query.query.clear_ordering(force_empty=True)

        collector = LogicalDeleteCollector(using=del_query.db)
        collector.collect(del_query)
        collector.delete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None

    delete.alters_data = True

    def delete_complete(self):
        """
        Deletes the records in the current QuerySet.
        """
        assert self.query.can_filter(), \
                "Cannot use 'limit' or 'offset' with delete."

        del_query = self._clone()

        # The delete is actually 2 queries - one to find related objects,
        # and one to delete. Make sure that the discovery of related
        # objects is performed on the same database as the deletion.
        del_query._for_write = True

        # Disable non-supported fields.
        del_query.query.select_for_update = False
        del_query.query.select_related = False
        del_query.query.clear_ordering(force_empty=True)

        collector = Collector(using=del_query.db)
        collector.collect(del_query)
        collector.delete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None
    delete_complete.alters_data = True

    def remove(self):
        """
        Deletes the records in the current QuerySet.
        """
        QuerySet.delete(self)

    def undelete(self):
        """
        Mark as deleted the records in the current QuerySet.
        """
        assert self.query.can_filter(),\
        "Cannot use 'limit' or 'offset' with delete."

        del_query = self._clone()

        # The delete is actually 2 queries - one to find related objects,
        # and one to delete. Make sure that the discovery of related
        # objects is performed on the same database as the deletion.
        del_query._for_write = True

        # Disable non-supported fields.
        del_query.query.select_for_update = False
        del_query.query.select_related = False
        del_query.query.clear_ordering(force_empty=True)

        collector = LogicalDeleteCollector(using=del_query.db)
        collector.collect(del_query)
        collector.undelete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None

    remove.alters_data = True

