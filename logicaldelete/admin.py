from django.contrib import admin, messages
from django.contrib.admin.filters import SimpleListFilter
from django.utils.translation import ugettext_lazy
from datetime import datetime

class ActiveListFilter(SimpleListFilter):
    title = 'Activo'
    parameter_name = 'activo'

    def lookups(self, request, model_admin):
        return (
            ('1', 'Si'),
            ('0', 'No')
            )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == '1':
            return queryset.filter(date_removed__isnull=True)
        if self.value() == '0':
            return queryset.filter(date_removed__isnull=False)

        return queryset.filter(date_removed__isnull=True)


class LogicalModelAdmin(admin.ModelAdmin):
    """
    A base model admin to use in providing access to to logically deleted
    objects.
    """
    
    #list_display = ("id", "active")
    #list_display_filter = ("active",)

    def __init__(self, *args, **kwargs):
        super(LogicalModelAdmin, self).__init__(*args, **kwargs)
        if self.list_display:
            self.list_display += ('active', )
        else:
            pass
            #self.list_display = ('active')

        if self.list_filter:
            self.list_filter += (ActiveListFilter, )
        else:
            self.list_filter = (ActiveListFilter, )

    def get_actions(self, request):
        actions = super(LogicalModelAdmin, self).get_actions(request)

        actions['undelete_selected'] = self.get_action('undelete_selected')

        return actions

    def queryset(self, request):
        qs = self.model._default_manager.everything()
        ordering = self.ordering or ()
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def undelete_selected(self, request, queryset):
        count = queryset.count()
        if count == 0:
            messages.error(request, "No se hay objetos para restaurar")
            return None

        queryset.update(date_removed=None)
    undelete_selected.short_description = ugettext_lazy("Restaurar  %(verbose_name_plural)s seleccionado/s")
