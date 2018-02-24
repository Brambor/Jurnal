from django.contrib import admin

from django.forms import Textarea, RadioSelect, ChoiceField
from django.db import models

from .forms import ColumnCheckboxSelectMultiple
from .models import Entry, Tag


class EntryAdmin(admin.ModelAdmin):
	model = Entry
	ordering = ('-day',)
	formfield_overrides = {
		models.TextField : {"widget": Textarea(attrs={"rows": 20, "cols": 120})},
		models.ManyToManyField : {"widget": ColumnCheckboxSelectMultiple(columns=3)},
#		ChoiceField : {"widget": RadioSelect},
	}
#	choice111 = ChoiceField(widget = RadioSelect, choices = (("T", "T"), ("M", "M")))


class TagAdmin(admin.ModelAdmin):
	model = Tag


admin.site.register(Tag, TagAdmin)
admin.site.register(Entry, EntryAdmin)
