# coding=utf-8
from django import forms
from django.core.exceptions import ValidationError


class LogicalModelForm(forms.ModelForm):

    def clean(self):

        cleaned_data = super(LogicalModelForm, self).clean()

        for fields in self._meta.model._meta.unique_together:
            data = {}
            for field in fields:
                data[field] = cleaned_data.get(field)

            data.update({'date_removed__isnull': False})

            if self._meta.model.objects.everything().filter(**data).exclude(id=self.instance.id).exists():
                fields_text = u', '.join(fields)
                raise ValidationError(u'ya existe un registro con los campos: {0}. en los registros borrados. '
                                      u'revise los registros borrados y modifique la informacion'.format(fields_text))

        return cleaned_data
