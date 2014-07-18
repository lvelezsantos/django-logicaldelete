from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.filters import SimpleListFilter
from django.contrib.admin.util import model_ngettext, get_deleted_objects
from django.core.exceptions import PermissionDenied
from django.db import router
from django.http import Http404
from django.template.response import TemplateResponse
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy
from django.utils.translation import ugettext as _
from logicaldelete.forms import LogicalModelForm


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
            'undelete_selected': self.get_action('undelete_selected'),
        }

        actions.update(new_actions)

        if request.user.is_superuser:
            actions.update({'delete_complete': self.get_action('delete_complete')})

        return actions

    def get_queryset(self, request):
        qs = self.model._default_manager.everything()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def undelete_selected(self, request, queryset):
        """
        Restores an element and all its child elements

        :type request: object
        :param request:
        :param queryset:
        """
        count = queryset.count()
        if count == 0:
            messages.error(request, _("No items to restore"))
            return None

        opts = self.model._meta
        app_label = opts.app_label

        # TODO: Check user has undelete permission for the actual model
        # Check that the user has delete permission for the actual model
        #if not self.has_delete_permission(request):
        #    raise PermissionDenied
        if not self.has_change_permission(request):
            raise PermissionDenied

        if not request.user.is_staff:
            return PermissionDenied

        using = router.db_for_write(self.model)

        # Populate deletable_objects, a data structure of all related objects that
        # will also be deleted.
        deletable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, self.admin_site, using)

        # The user has already confirmed the deletion.
        # Do the deletion and return a None to display the change list view again.
        if request.POST.get('post'):

            #if perms_needed:
            #    raise PermissionDenied

            n = queryset.count()
            if n:
                for obj in queryset:
                    obj_display = force_unicode(obj)
                    self.log_change(request, obj, u'se ha restaurado {0}'.format(obj_display))
                queryset.undelete()
                self.message_user(request, _("se han restaurado con exito %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(self.opts, n)
                })
            # Return None to display the change list page again.
            return None

        if len(queryset) == 1:
            objects_name = force_unicode(opts.verbose_name)
        else:
            objects_name = force_unicode(opts.verbose_name_plural)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": objects_name}
        else:
            title = _("Are you sure?")

        context = {
            "title": title,
            "objects_name": objects_name,
            "deletable_objects": [deletable_objects],
            'queryset': queryset,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": opts,
            "app_label": app_label,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }

        # Display the confirmation page
        return TemplateResponse(request, self.delete_selected_complete_confirmation or [
            "admin/%s/%s/undelete_selected_confirmation.html" % (app_label, opts.object_name.lower()),
            "admin/%s/undelete_selected_confirmation.html" % app_label,
            "admin/undelete_selected_confirmation.html"
        ], context, current_app=self.admin_site.name)
    undelete_selected.short_description = ugettext_lazy("Restaurar  %(verbose_name_plural)s seleccionado/s")

    def delete_complete(self, request, queryset):
        """
        Default action which deletes the selected objects.

        This action first displays a confirmation page whichs shows all the
        deleteable objects, or, if the user has no permission one of the related
        childs (foreignkeys), a "permission denied" message.

        Next, it delets all selected objects and redirects back to the change list.
        """
        opts = self.model._meta
        app_label = opts.app_label

        # Check that the user has delete permission for the actual model
        if not self.has_delete_permission(request):
            raise PermissionDenied

        if not request.user.is_superuser:
            return PermissionDenied

        using = router.db_for_write(self.model)

        # Populate deletable_objects, a data structure of all related objects that
        # will also be deleted.
        deletable_objects, perms_needed, protected = get_deleted_objects(
            queryset, opts, request.user, self.admin_site, using)

        # The user has already confirmed the deletion.
        # Do the deletion and return a None to display the change list view again.
        if request.POST.get('post'):

            if perms_needed:
                raise PermissionDenied

            n = queryset.count()
            if n:
                for obj in queryset:
                    obj_display = force_unicode(obj)
                    self.log_deletion(request, obj, obj_display)
                queryset.delete_complete()
                self.message_user(request, _("Successfully deleted %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(self.opts, n)
                })
            # Return None to display the change list page again.
            return None

        if len(queryset) == 1:
            objects_name = force_unicode(opts.verbose_name)
        else:
            objects_name = force_unicode(opts.verbose_name_plural)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": objects_name}
        else:
            title = _("Are you sure?")

        context = {
            "title": title,
            "objects_name": objects_name,
            "deletable_objects": [deletable_objects],
            'queryset': queryset,
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": opts,
            "app_label": app_label,
            'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        }

        # Display the confirmation page
        return TemplateResponse(request, self.delete_selected_complete_confirmation or [
            "admin/%s/%s/delete_selected_complete_confirmation.html" % (app_label, opts.object_name.lower()),
            "admin/%s/delete_selected_complete_confirmation.html" % app_label,
            "admin/delete_selected_complete_confirmation.html"
        ], context, current_app=self.admin_site.name)

    delete_complete.short_description = ugettext_lazy("Elimina completamente lo(a)s %(verbose_name_plural)s seleccionado(a)/s")
