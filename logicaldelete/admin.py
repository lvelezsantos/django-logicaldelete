from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.filters import SimpleListFilter
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.utils import model_ngettext, get_deleted_objects
from django.core.exceptions import PermissionDenied
from django.db import router
from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy
from django.utils.translation import ugettext as _

from logicaldelete.actions import undelete_selected, delete_complete
from logicaldelete.forms import LogicalModelForm
from logicaldelete.models import LOGICAL_DELETION, LOGICAL_RESTORE


class ActiveListFilter(SimpleListFilter):
    title = _('Borrados')
    parameter_name = 'delete'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Yes')),
            ('0', _('No')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == '0':
            return queryset.filter(date_removed__isnull=True)

        if self.value() == '1':
            return queryset.filter(date_removed__isnull=False)

        return queryset.filter(date_removed__isnull=True)


class LogicalModelAdmin(admin.ModelAdmin):
    """
    A base model admin to use in providing access to to logically deleted
    objects.
    """
    
    delete_selected_complete_confirmation = None
    form = LogicalModelForm

    def __init__(self, *args, **kwargs):
        super(LogicalModelAdmin, self).__init__(*args, **kwargs)

        if self.list_filter:
            self.list_filter += (ActiveListFilter, )
        else:
            self.list_filter = (ActiveListFilter, )

        if self.exclude:
            self.exclude += ('date_created', 'date_modified', 'date_removed')
        else:
            self.exclude = ('date_created', 'date_modified', 'date_removed')

    def get_actions(self, request):
        actions = super(LogicalModelAdmin, self).get_actions(request)

        new_actions = {
            'undelete_selected': self.get_action(undelete_selected),
        }

        actions.update(new_actions)

        if request.user.is_superuser:
            actions.update({'delete_complete': self.get_action(delete_complete)})

        return actions

    def get_queryset(self, request):
        qs = self.model._default_manager.everything()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def log_deletion(self, request, object, object_repr):
        """
        Log that an object will be logical deleted. Note that this method must be
        called before the logical deletion.

        The default implementation creates an admin LogEntry object.
        """
        from django.contrib.admin.models import LogEntry
        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=object_repr,
            action_flag=LOGICAL_DELETION,
        )

    def log_deletion_complete(self, request, object, object_repr):
        """
        Log that an object will be deleted. Note that this method must be
        called before the deletion.

        The default implementation creates an admin LogEntry object.
        """
        from django.contrib.admin.models import LogEntry, DELETION
        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=object_repr,
            action_flag=DELETION,
        )

    def log_restore(self, request, object, object_repr):
        """
        Log that an object will be restored. Note that this method must be
        called before the restore.

        The default implementation creates an admin LogEntry object.
        """
        from django.contrib.admin.models import LogEntry
        return LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=get_content_type_for_model(object).pk,
            object_id=object.pk,
            object_repr=object_repr,
            action_flag=LOGICAL_RESTORE,
        )