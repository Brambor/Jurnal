
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.template import loader

from .models import Entry
from .utils import generate_graph, weekday

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
			weekday=weekday(requested_date.weekday()),
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
		to_add["day"] = str(e.day)
		to_add["weekday_date"] = "{weekday}, {date}".format(
			weekday=e.weekday(),
			date=str(e.day),
		)
		if e.header:
			to_add["has_header"] = True
			to_add["header"] = e.header
		if e.to_do:
			to_add["has_to_do"] = True
			to_add["to_do"] = e.to_do.replace("\n", "; ")
		if e.image_set.exists():
			to_add["image_set"] = e.image_set.all()
		to_add["content"] = e.content
		to_add["content_day"] = e.content_day
		to_add["content_thought"] = e.content_thought
		to_add["content_idea"] = e.content_idea
		tags = e.tags.order_by("tag")
		if len(tags) > 0:
			to_add["has_tags"] = True
			to_add["tags"] = ", ".join(str(t) for t in tags)
		if e.day > datetime.datetime.date(datetime.datetime.today()):
			to_add["in_future"] = True
		done = e.done.order_by('done')
		if len(done) > 0:
			to_add['has_done'] = True
			to_add['done'] = ', '.join(str(d) for d in done)
		to_add["place"] = e.place
		context["entries"].append(to_add)

	return HttpResponse(template.render(context, request))

class GraphView(TemplateView):

	template_name = "graph.html"

	def get_context_data(self, **kwargs):
		context = super(GraphView, self).get_context_data(**kwargs)

		entries = Entry.objects.order_by('day')

		x = [e.day for e in entries]

		# Characters per day

		y_chars_data = {
			'content': [len(e.content) for e in entries],
			'day': [len(e.content_day) for e in entries],
			'thought': [len(e.content_thought) for e in entries],
			'idea': [len(e.content_idea) for e in entries],
		}

		context['graph_chars'] = generate_graph(x, y_chars_data, 'Characters', {'width': 1887}) # to prevent horizontal scalebar

		# Day ratio

		y_sum = []
		for i in range(len(y_chars_data['content'])):
			y_sum.append(sum(y_chars_data[key][i] for key in y_chars_data))

		y_ratio_data = {key: [] for key in y_chars_data}
		for key in y_chars_data:
			for i in range(len(y_chars_data[key])):
				if y_sum[i] != 0:
					y_ratio_data[key].append(y_chars_data[key][i]*100/y_sum[i])
				else:
					y_ratio_data[key].append(0)

		context['graph_ratio'] = generate_graph(x, y_ratio_data, 'Ratios', {'height':311}) #933/3

		# Average chars per day

		y_average_data = {key: [] for key in y_chars_data}
		total_chars = {key: 0 for key in y_chars_data}
		for key in y_chars_data:
			for i, chars in enumerate(y_chars_data[key]):
				total_chars[key] += chars
				y_average_data[key].append(total_chars[key]//(i+1))

		context['graph_average'] = generate_graph(x, y_average_data, 'Average', {'height':311})

		# Average chars last seven days

		y_average_7_days_data = {key: y_average_data[key][:7] for key in y_chars_data}
		total_chars = {key: sum(y_chars_data[key][:7]) for key in y_chars_data}

		for key in y_chars_data:
			for i, chars in enumerate(y_chars_data[key][7:]):
				total_chars[key] += chars - y_chars_data[key][i]
				y_average_7_days_data[key].append(total_chars[key]//7)

		context['graph_average_7_days'] = generate_graph(x, y_average_7_days_data, 'Average of last 7 days', {'height':311})

		return context
