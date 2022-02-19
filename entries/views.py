
from django.contrib.admin.models import LogEntry
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView

from .models import Entry
from .utils import generate_graph, weekday, pass_context_of_entry

from datetime import datetime, timedelta
import json
import os
import requests


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
		requested_date = datetime.date(datetime.today())
	else:
		requested_date = datetime.date(datetime(
			year=int(kwargs.get("year")),
			month=int(kwargs.get("month")),
			day=int(kwargs.get("day")),
		))

	pic_tuples = []
	contains_requested_date = False

	for pic in all_pics:
		time = datetime.date(datetime.fromtimestamp(
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
		"existing_prev_day_url":
			"/" + str(pic_tuples[pic_tuples.index(that_date) - 1][0]).replace("-", "/"),
		"existing_next_day_url":
			"/" + str(
				pic_tuples[(pic_tuples.index(that_date) + 1) % len(pic_tuples)][0]
			).replace("-", "/"),
		"prev_day_url":
			"/" + str(requested_date - timedelta(days=1)).replace("-", "/"),
		"next_day_url":
			"/" + str(requested_date + timedelta(days=1)).replace("-", "/"),
	}

	if that_date[1]:
		context["hs_pics"] = that_date[1]

	entries = Entry.objects.filter(day=requested_date)
	if len(entries) > 0:
		context["entry"] = pass_context_of_entry(entries[0])

	return HttpResponse(template.render(context, request))

def index(request, **kwargs):
	template = loader.get_template('index.html')

	context = {"entry": pass_context_of_entry(
		Entry.objects.order_by("-day").first())}

	return HttpResponse(template.render(context, request))

def list_headers(request, **kwargs):
	template = loader.get_template('list_headers.html')

	context = {"entries": tuple(Entry.objects.order_by("-day"))}

	return HttpResponse(template.render(context, request))

def entry(request, **kwargs):
	template = loader.get_template('single_entry.html')

	context = {"entry": pass_context_of_entry(
		Entry.objects.get(pk=kwargs.get("pk")))}

	return HttpResponse(template.render(context, request))

def sync_request_send(request):
	url = 'http://192.168.8.157:8000/sync_recieve'
	serialized_my = serializers.serialize("json", LogEntry.objects.all().reverse())

	response = requests.post(url, json=serialized_my)

	parsed_their = json.loads(response.json())
	parsed_my = json.loads(serialized_my)

	idx = -1
	for idx_good, (my, theirs) in enumerate(zip(parsed_my, parsed_their)):
		if my == theirs:
			idx = idx_good
		else:
			break
	matches = idx+1
	ahead = len(parsed_my) - matches
	behind = len(parsed_their) - matches

	if ahead == 0 == behind:
		msg = "Everything up to date!"
	elif ahead > 0 and behind > 0:
		msg = f"We are behind by {behind} and ahead by {ahead}."
	elif ahead > 0:
		msg = f"We are ahead by {ahead}."
	else: # behind > 0
		msg = f"We are behind by {behind}."

	template = loader.get_template('sync.html')
	context = {
		"matches": idx+1,
		"msg": msg,
	}
	return HttpResponse(template.render(context, request))

# Not safe, but I don't know how to get csrf token in sync_request_send, requests.post
@csrf_exempt
def sync_request_recieve(request):
	return JsonResponse(serializers.serialize("json",
		LogEntry.objects.all().reverse()), safe=False)  # safe=False, so it doesn't have to be a dict

def get_all_entries(request):
	template = loader.get_template('all_entries.html')

	context = {"entries": (pass_context_of_entry(e) for e in Entry.objects.order_by("-day"))}

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
