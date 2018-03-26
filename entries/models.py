
from django.db import models

import datetime


class Tag(models.Model):
	def __str__(self):
		return self.tag
	tag = models.CharField(
		max_length=255,
	)


class Entry(models.Model):
	class Meta:
		verbose_name_plural = "Entries"

	def __str__(self):
		if self.day > datetime.datetime.date(datetime.datetime.today()):
			return "Todo {date}".format(date=str(self.day))
		else:
			apendix = ""
			if self.header:
				apendix += ", {}".format(self.header)
			if not self.complete:
				apendix += ", unfinished"

			return "{weekday}, {date}, {place}{apendix} ({len_in_char} chars)".format(
				weekday=(
					"Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"
				)[self.day.weekday()],
				date=str(self.day),
				place=self.place,
				apendix=apendix,
				len_in_char=len(self.content)+len(self.content_day)+len(self.content_thought)+len(self.content_idea),
			)

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
