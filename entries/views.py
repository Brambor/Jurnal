
from django.http import HttpResponse
from django.template import loader

from .models import Entry

import datetime
import os


def greetings(request, **kwargs):
	template = loader.get_template('greetings.html')

	hs_arenas_and_decks = [
		"D:\Hearthstone - arenas and packs\{p}".format(
			p=p
		) for p in os.listdir("D:\Hearthstone - arenas and packs")
	]
	hs_other = [
		"D:\Hearthstone - other\{p}".format(
			p=p
		) for p in os.listdir("D:\Hearthstone - other")]
	all_pics = hs_arenas_and_decks + hs_other

	for p in all_pics:
		if "png" not in p:
			del all_pics[all_pics.index(p)]

	if kwargs.get("year") is None:
		requested_date = datetime.datetime.date(datetime.datetime.today())
	else:
		requested_date = datetime.datetime.date(datetime.datetime(
			year=int(kwargs.get("year")),
			month=int(kwargs.get("month")),
			day=int(kwargs.get("day")),
		))

	pic_tuples = []
	contains_requested_date = False

	for pic in all_pics:
		time = datetime.datetime.date(datetime.datetime.fromtimestamp(
			os.path.getmtime(pic))
		)
		added = False
		for check in pic_tuples:
			if check[0] == time:
				added = True
				pic_tuples[pic_tuples.index(check)][1].append(pic)
				break
		if not added:
			pic_tuples.append((time, [pic]))
		if requested_date == time:
			contains_requested_date = True

	if not contains_requested_date:
		pic_tuples.append((requested_date, []))
	pic_tuples.sort()

	for pic in pic_tuples:
		if pic[0] == requested_date:
			that_date = pic  # sort that_day
			break

	context = {
		"date": "{weekday}, {date}".format(
			weekday=(
				"Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"
			)[requested_date.weekday()],
			date=requested_date,
		),
		"existing_prev_day_url":
			"/" + str(pic_tuples[pic_tuples.index(that_date) - 1][0]).replace("-", "/"),
		"existing_next_day_url":
			"/" + str(
				pic_tuples[(pic_tuples.index(that_date) + 1) % len(pic_tuples)][0]
			).replace("-", "/"),
		"prev_day_url":
			"/" + str(requested_date - datetime.timedelta(days=1)).replace("-", "/"),
		"next_day_url":
			"/" + str(requested_date + datetime.timedelta(days=1)).replace("-", "/"),
	}

	if that_date[1]:
		context["has_hs_pics"] = True
		context["hs_pics"] = that_date[1]
	else:
		context["has_hs_pics"] = False

	entries = Entry.objects.filter(day=requested_date)
	if len(entries) > 0:
		context["has_entry"] = True
		context["entry"] = entries[0].content.replace("\n", "</br>")
		tags = entries[0].tags.all()
		if len(tags) > 0:
			context["has_tags"] = True
			context["tags"] = ", ".join(str(t) for t in tags)
		else:
			context["has_tags"] = False
	else:
		context["has_entry"] = False

	return HttpResponse(template.render(context, request))


def get_all_entries(request):
	template = loader.get_template('all_entries.html')

	context = {"entries": []}

	entries = Entry.objects.order_by("-day")
	for e in entries:
		to_add = {}
		to_add["day"] = "{weekday}, {date}".format(
			weekday=str((
				"Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"
			)[e.day.weekday()]),
			date=str(e.day),
		)
		if e.header:
			to_add["has_header"] = True
			to_add["header"] = e.header
		if e.to_do:
			to_add["has_to_do"] = True
			to_add["to_do"] = e.to_do.replace("\n", "; ")
		to_add["content"] = e.content
		tags = e.tags.all().order_by("tag")
		if len(tags) > 0:
			to_add["has_tags"] = True
			to_add["tags"] = ", ".join(str(t) for t in tags)
		else:
			to_add["has_tags"] = False
		if e.day > datetime.datetime.date(datetime.datetime.today()):
			to_add["in_future"] = True
		to_add["place"] = e.place
		context["entries"].append(to_add)

	return HttpResponse(template.render(context, request))
