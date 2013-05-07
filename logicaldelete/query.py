from django.db.models.query import QuerySet
from logicaldelete.deletion import LogicalDeleteCollector


class LogicalDeleteQuerySet(QuerySet):
    
    def delete(self):
        print 'estoy en el queryset'
        """
        Mark as deleted the records in the current QuerySet.
        """
        assert self.query.can_filter(),\
        "Cannot use 'limit' or 'offset' with delete."

        del_query = self._clone()
        print del_query

        # The delete is actually 2 queries - one to find related objects,
        # and one to delete. Make sure that the discovery of related
        # objects is performed on the same database as the deletion.
        del_query._for_write = True

        # Disable non-supported fields.
        del_query.query.select_for_update = False
        del_query.query.select_related = False
        del_query.query.clear_ordering()

        collector = LogicalDeleteCollector(using=del_query.db)
        collector.collect(del_query)
        collector.delete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None

    delete.alters_data = True

    def remove(self):
        """
        Deletes the records in the current QuerySet.
        """
        QuerySet.delete(self)

    remove.alters_data = True

