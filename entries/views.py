
from django.contrib.admin.models import LogEntry
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView

from .forms import ReadAtForm
from .models import Entry, IPAddress, Machine
from .utils import generate_graph, get_client_ip, weekday, pass_context_of_entry, get_ip

from datetime import datetime, timedelta
import json
import os
import requests
import subprocess


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


"""
HOW to connect:
1) python manage.py runserver 0.0.0.0:8000
2) go to http://192.168.8.157:8000/sync in browser
"""
def sync_request_send(request):
	# check all machines (TODO: should do that after page load with JavaScript)
	'''
	for machine in Machine.objects.all():
		print(f"Machine: {machine}")
		for ip in IPAddress.objects.filter(machine=machine):

			"""
			print(f"ping {ip}")
			a = ""
			p = subprocess.Popen(f'ping {ip.address}', capture_output=True)
			p.wait()
#			print(p.poll())
			print(p)
#			help(p)
			"""
			print(f"\tping {ip}")
			subprocess.Popen(f"ping {ip.address}", stdout=subprocess.PIPE)
			out = subprocess.run(['ping', ip.address], capture_output=True)
			print(f"MSG ''{out.stdout.decode()}'")
			# MACHINE REACHABLE

			# port isn't supposed to be pinged
			url = f'{ip.address}:8000'
	'''

	# same git version ??? TODO (compare hashes of last commit)
	# TODO hardcoded to Jade-AD
	context = {"data": []}
	for machine in Machine.objects.all():
		for ip in IPAddress.objects.filter(machine=machine):
			print(ip)
#			url = 'http://192.168.8.184:8000/sync_recieve'  # mobile
#			url = 'http://192.168.8.157:8000/sync_recieve'  # pc
			"""
			for debug:
			q1 = LogEntry.objects.all().reverse()[:1000]
			q2 = [] #LogEntry.objects.all().reverse()[1005:1006]
			serialized_my = serializers.serialize("json", list(chain(q1, q2)))
			"""
			url = f'http://{ip.address}:8000/sync_recieve'  # pc
			serialized_my = serializers.serialize("json", LogEntry.objects.all().reverse())

			try:
				response = requests.post(url, json=serialized_my)
			except requests.exceptions.ConnectionError as e:  # Timeout, Unreachable IP etc.
				context["data"].append({
					"machine": machine,
					"matches": "?",
					"msg": repr(e),
					"log": ["?"],
				})
				continue

			print("RESPONSE:")
			print("len:", len(response.json()))
			print("\\RESPONSE")
			parsed_their = json.loads(response.json())
			parsed_my = json.loads(serialized_my)

			# DIFF

			changes = {}

			# action_flag: 1=ADDED, 2=CHANGED, 3=DELETED
			for le in parsed_my:
				le = le["fields"]
				le_id = (le["content_type"], le["object_id"])
				if le_id not in changes:
					changes[le_id] = []
				changes[le_id].append(tuple(le[x] for x in (
					"action_time", "object_repr", "action_flag", "change_message")))

			# LOG

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
				# TODO merge possible?
			elif ahead > 0:
				msg = f"We are ahead by {ahead}."
				# TODO send database
			else: # behind > 0
				msg = f"We are behind by {behind}."
				# TODO retrieve their database (not users, just models!)
			# TODO You, mobile, have to apply these changes

			context["data"].append({
				"machine": machine,
				"matches": idx+1,
				"msg": msg,
				"log": {
					"ahead": list(l["fields"] for l in parsed_my[matches:]),
					"behind": list(l["fields"] for l in parsed_their[matches:]),
				}
			})

			# I don't need any more connection per this address
			# Should optimize this, ask in paralel all of them
			print("\tsuccess")
			break

	template = loader.get_template('sync.html')
	return HttpResponse(template.render(context, request))

	# TODO INACCESIBLE
	url = 'http://localhost:8000/sync_complete'  # replace with other python app url or ip

# Not safe, but I don't know how to get csrf token in sync_request_send, requests.post
@csrf_exempt
def sync_request_recieve(request):
	# if machine is allowed, return
	# if not allowed, add it's IP to list of IP's
	print("SYNC connection from:", get_client_ip(request))  # has to be in Middleware
	return JsonResponse(serializers.serialize("json",
		LogEntry.objects.all().reverse()), safe=False)  # safe=False, so it doesn't have to be a dict

def sync_request_complete(request):
	# TODO apply changes
	return HttpResponse()

def sync_page(request):
	print(get_ip())
	template = loader.get_template('sync_page.html')

	# TODO QR code of page to connect to to scan with a phone
	context = {"your_ip": get_ip()}

	return HttpResponse(template.render(context, request))

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
