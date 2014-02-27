# -*- coding: utf-8; -*-

from operator import attrgetter

from django.db.models.fields import FieldDoesNotExist
from django.db import transaction
from django.db.models.deletion import Collector, sql, signals
from django.utils.timezone import now
from django.utils import six


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

        for model, instances in self.data.items():
            self.data[model] = sorted(instances, key=attrgetter("pk"))

        # if possible, bring the models in an order suitable for databases that
        # don't support transactions or cannot defer constraint checks until the
        # end of a transaction.
        self.sort()

        with transaction.commit_on_success_unless_managed(using=self.using):

            date_removed = now()

            # send pre_delete signals
            for model, obj in self.instances_with_model():
                if not model._meta.auto_created:
                    signals.pre_delete.send(
                        sender=model, instance=obj, using=self.using
                    )

            # fast deletes
            for qs in self.fast_deletes:
                # We avoid to send an error when I try to update tables in many to many relationships
                try:
                    qs.update(date_removed=date_removed)

                except FieldDoesNotExist:
                    pass

            # update fields
            for model, instances_for_fieldvalues in six.iteritems(self.field_updates):
                query = sql.UpdateQuery(model)
                for (field, value), instances in six.iteritems(instances_for_fieldvalues):
                    query.update_batch([obj.pk for obj in instances],
                                       {field.name: value}, self.using)

            # reverse instance collections
            for instances in six.itervalues(self.data):
                instances.reverse()

            # delete instances
            for model, instances in six.iteritems(self.data):
                query = sql.UpdateQuery(model)
                pk_list = [obj.pk for obj in instances]
                query.update_batch(pk_list, {'date_removed': date_removed}, self.using)

                if not model._meta.auto_created:
                    for obj in instances:
                        signals.post_delete.send(
                            sender=model, instance=obj, using=self.using
                        )

        # update collected instances
        for model, instances_for_fieldvalues in six.iteritems(self.field_updates):
            for (field, value), instances in six.iteritems(instances_for_fieldvalues):
                for obj in instances:
                    setattr(obj, field.attname, value)
        for model, instances in six.iteritems(self.data):
            for instance in instances:
                setattr(instance, model._meta.pk.attname, None)

    def undelete(self):

        for model, instances in self.data.items():
            self.data[model] = sorted(instances, key=attrgetter("pk"))

        # if possible, bring the models in an order suitable for databases that
        # don't support transactions or cannot defer constraint checks until the
        # end of a transaction.
        self.sort()

        with transaction.commit_on_success_unless_managed(using=self.using):

            date_removed = None

            # send pre_delete signals
            for model, obj in self.instances_with_model():
                if not model._meta.auto_created:
                    signals.pre_delete.send(
                        sender=model, instance=obj, using=self.using
                    )

            # fast deletes
            for qs in self.fast_deletes:
                qs.update(date_removed=date_removed)

            # update fields
            for model, instances_for_fieldvalues in six.iteritems(self.field_updates):
                query = sql.UpdateQuery(model)
                for (field, value), instances in six.iteritems(instances_for_fieldvalues):
                    query.update_batch([obj.pk for obj in instances],
                                       {field.name: value}, self.using)

            # reverse instance collections
            for instances in six.itervalues(self.data):
                instances.reverse()

            # delete instances
            for model, instances in six.iteritems(self.data):
                query = sql.UpdateQuery(model)
                pk_list = [obj.pk for obj in instances]
                query.update_batch(pk_list, {'date_removed': date_removed}, self.using)

                if not model._meta.auto_created:
                    for obj in instances:
                        signals.post_delete.send(
                            sender=model, instance=obj, using=self.using
                        )

        # update collected instances
        for model, instances_for_fieldvalues in six.iteritems(self.field_updates):
            for (field, value), instances in six.iteritems(instances_for_fieldvalues):
                for obj in instances:
                    setattr(obj, field.attname, value)
        for model, instances in six.iteritems(self.data):
            for instance in instances:
                setattr(instance, model._meta.pk.attname, None)

    def recover(self):
        self.undelete()