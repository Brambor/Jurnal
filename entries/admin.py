from django.contrib import admin

from django.forms import Textarea, RadioSelect, ChoiceField
from django.db import models

from .forms import ColumnCheckboxSelectMultiple
from .models import Done, Entry, Image, Person, ReadAt, Tag


class EntryAdmin(admin.ModelAdmin):
	model = Entry
	ordering = ('-day',)
	formfield_overrides = {
		models.TextField : {"widget": Textarea(attrs={"rows": 1, "cols": 120})},
		models.ManyToManyField : {"widget": ColumnCheckboxSelectMultiple(columns=3)},
#		ChoiceField : {"widget": RadioSelect},
	}
#	choice111 = ChoiceField(widget = RadioSelect, choices = (("T", "T"), ("M", "M")))


class ImageAdmin(admin.ModelAdmin):
	model = Image


class ReadAtAdmin(admin.ModelAdmin):
	model = ReadAt


class PersonAdmin(admin.ModelAdmin):
	model = Person


class TagAdmin(admin.ModelAdmin):
	model = Tag


class DoneAdmin(admin.ModelAdmin):
	model = Done


admin.site.register(Tag, TagAdmin)
admin.site.register(Done, DoneAdmin)
admin.site.register(Entry, EntryAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(ReadAt, ReadAtAdmin)
