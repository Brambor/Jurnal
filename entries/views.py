from django.apps import apps
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.views.generic.base import TemplateView

from .forms import ReadAtForm, IPForm, MergeForm
from .models import Entry
from .utils import generate_graph, pass_context_of_entry, get_ip

from datetime import datetime, timedelta
from difflib import HtmlDiff
import json
import os
import requests


def greetings(request, **kwargs):
	template = loader.get_template('greetings.html')

	hs_arenas_and_decks = [
		"D:\Pictures\Hearthstone - arenas and packs\{p}".format(
			p=p
		) for p in os.listdir("D:\Pictures\Hearthstone - arenas and packs")
	]
	hs_other = [
		"D:\Pictures\Hearthstone - arenas and packs\{p}".format(
			p=p
		) for p in os.listdir("D:\Pictures\Hearthstone - arenas and packs")]
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

def index(request):
	template = loader.get_template('index.html')

	context = {"entry": pass_context_of_entry(
		Entry.objects.order_by("-day").first())}

	return HttpResponse(template.render(context, request))

def list_headers(request):
	template = loader.get_template('list_headers.html')

	context = {"entries": tuple(Entry.objects.order_by("-day"))}

	return HttpResponse(template.render(context, request))

def entry(request, **kwargs):
	template = loader.get_template('single_entry.html')

	context = {"entry": pass_context_of_entry(
		Entry.objects.get(pk=kwargs.get("pk"))),
		"single_entry": True}

	return HttpResponse(template.render(context, request))

def add_read_at(request, **kwargs):
	# if this is a POST request we need to process the form data
	read_at = None
	if request.method == 'POST':
		# create a form instance and populate it with data from the request:
		form = ReadAtForm(request.POST)
		# check whether it's valid:
		if form.is_valid():
			# process the data in form.cleaned_data as required
			read_at = form.save()
			# TODO redirect to a new URL, redirected to self

	# if a GET (or any other method), create a prepopulated form
	else:
		form = ReadAtForm(initial={"entry": kwargs.get("pk")})

	template = loader.get_template('add_ReadAt.html')

	context = {
		"form": form,
		"pk": kwargs.get("pk"),
		"read_at": read_at,
	}

	return HttpResponse(template.render(context, request))

def sync_connect(request):
	template = loader.get_template('sync_connect.html')
	# TODO QR code of page to connect to to scan with a phone
	context = {"your_ip": get_ip(), "ip_form": IPForm()}
	return HttpResponse(template.render(context, request))

def generate_html_diff(parsed_client, parsed_server, diff_wrap):
	def str_from_parsed_data(parsed, i):
		return (f"pk: {parsed[i]['pk']}", *(f"{k}: {v}" for k, v in parsed[i]["fields"].items()))

	def add_diff(a, b, add_pk):
		html_diffs.append((Diff.make_table(a, b, fromdesc="Client", todesc="Server"),
			MergeForm(initial={"pk":add_pk})))

	Diff = HtmlDiff(wrapcolumn=diff_wrap)
	i_c = 0
	i_s = 0
	html_diffs = []
	while i_c < len(parsed_client) and i_s < len(parsed_server):
		if parsed_client[i_c] == parsed_server[i_s]:
			i_c += 1
			i_s += 1
		elif parsed_client[i_c]["pk"] == parsed_server[i_s]["pk"]:
			# there is some difference
			add_diff(str_from_parsed_data(parsed_client, i_c),
				     str_from_parsed_data(parsed_server, i_s),
				     parsed_client[i_c]["pk"])
			i_c += 1
			i_s += 1
		elif parsed_client[i_c]["pk"] < parsed_server[i_s]["pk"]:
			# catchup
			add_diff(str_from_parsed_data(parsed_client, i_c), "", parsed_client[i_c]["pk"])
			i_c += 1
		else: # >
			# catchup
			add_diff("", str_from_parsed_data(parsed_server, i_s), parsed_server[i_s]["pk"])
			i_s += 1

	# catchup
	while i_c < len(parsed_client):
		add_diff(str_from_parsed_data(parsed_client, i_c), "", parsed_client[i_c]["pk"])
		i_c += 1
	while i_s < len(parsed_server):
		add_diff("", str_from_parsed_data(parsed_server, i_s), parsed_server[i_s]["pk"])
		i_s += 1
	return html_diffs

def sync_diff(request):
	""" Make a form generating the new database for a model and my-migration for both databases """

	if request.method != "POST":
		raise Exception("need a POST request to acces this page")
	form = IPForm(request.POST)
	if not form.is_valid():
		raise Exception("Form was not valid")

	template = loader.get_template('sync_diff.html')
	context = {
		"server_ip": request.get_host(),
		"client_ip": form.cleaned_data['client_ip'],
	}

	# GET
	link = f"http://{request.get_host()}/sync_get_model/{form.cleaned_data['model']}"
	parsed_server = json.loads(requests.get(link).json())

	link = (f"http://{form.cleaned_data['client_ip']}:{form.cleaned_data['port']}/sync_get_model/"
		f"{form.cleaned_data['model']}")
	try:
		parsed_client = json.loads(requests.get(link).json())
	except json.decoder.JSONDecodeError:
		context["error"] = f"Couldn't connect to {link}."
		return HttpResponse(template.render(context, request))

	# DIFF
	context["html_diffs"] = generate_html_diff(parsed_client, parsed_server, form.cleaned_data['diff_wrap'])

	return HttpResponse(template.render(context, request))

def sync_get_model(request, model_name):
	# return the required model in JSON
	model = apps.get_model("entries", model_name)
	data = serializers.serialize("json", model.objects.all())
	return HttpResponse(json.dumps(data), content_type='application/json')

def sync_process_diff(request):
	pass
	# recieve database and my-migrations
	# send database and my migrations to self
	# send database and their migrations to them

def sync_recieve_changes(request):
	pass
	#it recieves what should be overriten


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

		# Characters each day

		y_chars_data = {
			'content': [len(e.content) for e in entries],
			'day': [len(e.content_day) for e in entries],
			'thought': [len(e.content_thought) for e in entries],
			'idea': [len(e.content_idea) for e in entries],
		}

		context['graph_chars'] = generate_graph(x, y_chars_data, 'Characters each day', {'width': 1887}) # to prevent horizontal scalebar

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

		context['graph_ratio'] = generate_graph(x, y_ratio_data, 'Day ratio', {'height':311}) #933/3

		# Average chars per day since init

		y_average_data = {key: [] for key in y_chars_data}
		total_chars = {key: 0 for key in y_chars_data}
		for key in y_chars_data:
			for i, chars in enumerate(y_chars_data[key]):
				total_chars[key] += chars
				y_average_data[key].append(total_chars[key]//(i+1))

		context['graph_average'] = generate_graph(x, y_average_data, 'Average chars per day since init', {'height':311})

		# Average chars last 7 days

		y_average_7_days_data = {key: y_average_data[key][:7] for key in y_chars_data}
		total_chars = {key: sum(y_chars_data[key][:7]) for key in y_chars_data}

		for key in y_chars_data:
			for i, chars in enumerate(y_chars_data[key][7:]):
				total_chars[key] += chars - y_chars_data[key][i]
				y_average_7_days_data[key].append(total_chars[key]//7)

		context['graph_average_7_days'] = generate_graph(x, y_average_7_days_data, 'Average chars last 7 days', {'height':311})

		return context
