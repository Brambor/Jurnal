from datetime import datetime

from django.db import models

from .utils import weekday


class Tag(models.Model):
	def __str__(self):
		return self.tag
	tag = models.CharField(
		max_length=255,
	)


class Done(models.Model):
	def __str__(self):
		return self.done
	done = models.CharField(
		max_length=255,
	)


class Entry(models.Model):
	class Meta:
		verbose_name_plural = "Entries"

	def __str__(self):
		if self.day > datetime.date(datetime.today()):
			prolog = "Todo (date is in future) "
		else:
			prolog = ""

		apendix = ""
		if self.header:
			apendix += f", {self.header}"
		if not self.complete:
			apendix += ", unfinished"

		return (
			f"{prolog}{self.weekday()}, {self.day}, {self.place}{apendix} "
			f"({self.get_len_in_char()} chars)")

	def get_len_in_char(self):
		return len(self.content)+len(self.content_day)+len(self.content_thought)+len(self.content_idea)

	def weekday(self):
		return weekday(self.day.weekday())

	day = models.DateField()
	header = models.CharField(
		max_length=255,
		blank=True,
	)
	content = models.TextField(
		blank=True,
	)
	content_day = models.TextField(
		blank=True,
	)
	content_thought = models.TextField(
		blank=True,
	)
	content_idea = models.TextField(
		blank=True,
	)
	to_do = models.CharField(
		max_length=255,
		blank=True,
	)
	done = models.ManyToManyField(
		Done,
		related_name='entries',
		blank=True,
	)
	tags = models.ManyToManyField(
		Tag,
		related_name='entries',
		blank=True,
	)
	place = models.CharField(
		choices=(
			("M", "M"),
			("T", "T"),
		),
		max_length=255,
		default="M",
	)
	complete = models.BooleanField(
		blank=True,
	)
	created = models.DateTimeField(
		auto_now_add=True,
	)
	edited = models.DateTimeField(
		auto_now=True,
	)
