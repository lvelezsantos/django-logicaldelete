# -*- coding: utf-8; -*-
from operator import attrgetter

from django.utils.timezone import now
from django.db.models.deletion import Collector, sql, signals
from django.db.models.deletion import ProtectedError



class LogicalDeleteOptions(object):
    """
    Options class for LogicalDeleteModelBase.
    """

    delete_related = True
    safe_deletion = True
    delete_batches = False

    def __init__(self, opts):
        if opts:
            for key, value in opts.__dict__.iteritems():
                setattr(self, key, value)

class LogicalDeleteCollector(Collector):

    def delete(self):

        # sort instance collections
        for model, instances in self.data.items():
            self.data[model] = sorted(instances, key=attrgetter("pk"))

        # if possible, bring the models in an order suitable for databases that
        # don't support transactions or cannot defer constraint checks until the
        # end of a transaction.
        self.sort()

        # send pre_delete signals
        for model, obj in self.instances_with_model():
            if not model._meta.auto_created:
                signals.pre_delete.send(
                    sender=model, instance=obj, using=self.using
                )

        # update fields
        for model, instances_for_fieldvalues in self.field_updates.iteritems():
            query = sql.UpdateQuery(model)
            for (field, value), instances in instances_for_fieldvalues.iteritems():
                query.update_batch([obj.pk for obj in instances],
                                   {field.name: value}, self.using)

        # reverse instance collections
        for instances in self.data.itervalues():
            instances.reverse()

        date_removed = now()

        # delete batches
        for model, batches in self.batches.iteritems():
            print 'batches'

            query = sql.DeleteQuery(model)

            for field, instances in batches.iteritems():
                query.delete_batch([obj.pk for obj in instances], self.using, field)
                #query.update_batch([obj.pk for obj in instances], {'date_removed': date_removed},self.using, field)

        # delete instances
        for model, instances in self.data.iteritems():
            query = sql.UpdateQuery(model)
            pk_list = [obj.pk for obj in instances]
            query.update_batch(pk_list,
                            {'date_removed': date_removed}, self.using)
            #query.delete_batch(pk_list, self.using)

        # send post_delete signals
        for model, obj in self.instances_with_model():
            if not model._meta.auto_created:
                signals.post_delete.send(
                    sender=model, instance=obj, using=self.using
                )

        # update collected instances
        for model, instances_for_fieldvalues in self.field_updates.iteritems():
            for (field, value), instances in instances_for_fieldvalues.iteritems():
                for obj in instances:
                    setattr(obj, field.attname, value)
        for model, instances in self.data.iteritems():
            for instance in instances:
                setattr(instance, model._meta.pk.attname, None)

    def undelete(self):

        # sort instance collections
        for model, instances in self.data.items():
            self.data[model] = sorted(instances, key=attrgetter("pk"))

        # if possible, bring the models in an order suitable for databases that
        # don't support transactions or cannot defer constraint checks until the
        # end of a transaction.
        self.sort()

        # send pre_delete signals
        for model, obj in self.instances_with_model():
            if not model._meta.auto_created:
                signals.pre_delete.send(
                    sender=model, instance=obj, using=self.using
                )

        # update fields
        for model, instances_for_fieldvalues in self.field_updates.iteritems():
            query = sql.UpdateQuery(model)
            for (field, value), instances in instances_for_fieldvalues.iteritems():
                query.update_batch([obj.pk for obj in instances],
                                   {field.name: value}, self.using)

        # reverse instance collections
        for instances in self.data.itervalues():
            instances.reverse()

        #date_removed = now()

        # delete batches
        for model, batches in self.batches.iteritems():


            query = sql.UpdateQuery(model)

            for field, instances in batches.iteritems():
                #query.delete_batch([obj.pk for obj in instances], self.using, field)
                query.update_batch([obj.pk for obj in instances], {'date_removed': None}, self.using)

        # delete instances
        for model, instances in self.data.iteritems():
            query = sql.UpdateQuery(model)
            pk_list = [obj.pk for obj in instances]
            query.update_batch(pk_list,
                            {'date_removed': None}, self.using)
            #query.delete_batch(pk_list, self.using)

        # send post_delete signals
        #for model, obj in self.instances_with_model():
        #    if not model._meta.auto_created:
        #        signals.post_delete.send(
        #            sender=model, instance=obj, using=self.using
        #        )

        # update collected instances
        for model, instances_for_fieldvalues in self.field_updates.iteritems():
            for (field, value), instances in instances_for_fieldvalues.iteritems():
                for obj in instances:
                    setattr(obj, field.attname, value)
        for model, instances in self.data.iteritems():
            for instance in instances:
                setattr(instance, model._meta.pk.attname, None)
