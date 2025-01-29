from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.management import call_command
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateView

from .forms import ReadAtForm, IPForm, MergeForm
from entries import models
from .utils import generate_graph, pass_context_of_entry, get_ip

from copy import deepcopy
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

	entries = models.Entry.objects.filter(day=requested_date)
	if len(entries) > 0:
		context["entry"] = pass_context_of_entry(entries[0])

	return HttpResponse(template.render(context, request))

def index(request):
	template = loader.get_template('index.html')

	e = models.Entry.objects.order_by("-day").first()
	context = {"entry": pass_context_of_entry(e) if e else e}

	return HttpResponse(template.render(context, request))

def list_headers(request):
	template = loader.get_template('list_headers.html')

	l = models.ReadAt.objects.order_by("-date").first()
	context = {
		"entries": tuple(models.Entry.objects.order_by("-day")),
		"last_read": l.entry.pk if l else l,
	}

	return HttpResponse(template.render(context, request))

def entry(request, **kwargs):
	template = loader.get_template('single_entry.html')

	context = {"entry": pass_context_of_entry(
		models.Entry.objects.get(pk=kwargs.get("pk"))),
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
	if parsed_client and parsed_client[0]["model"] == "entries.entry" \
		or parsed_server and parsed_server[0]["model"] == "entries.entry":
		tag_dict = {}
		for tag in models.Tag.objects.all():
			tag_dict[tag.pk] = tag.tag
		done_dict = {}
		for done in models.Done.objects.all():
			done_dict[done.pk] = done.done

	def strs_from_parsed_data(parsed, i):
		# assuming Tag and Done objs were already merged
		ret = [f"pk: {parsed[i]['pk']}"]
		for k, v in parsed[i]["fields"].items():
			# Expand Tag and Done objects to be strings rather than pks
			if parsed[i]["model"] == "entries.entry" and k == "tags":
				ret.append(f"{k}: {', '.join(tag_dict[tag_pk] for tag_pk in v)}")
			elif parsed[i]["model"] == "entries.entry" and k == "done":
				ret.append(f"{k}: {', '.join(done_dict[done_pk] for done_pk in v)}")
			else:
				ret.append(f"{k}: {v}")
		return ret

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
			add_diff(strs_from_parsed_data(parsed_client, i_c),
				     strs_from_parsed_data(parsed_server, i_s),
				     parsed_client[i_c]["pk"])
			i_c += 1
			i_s += 1
		elif parsed_client[i_c]["pk"] < parsed_server[i_s]["pk"]:
			# catchup
			add_diff(strs_from_parsed_data(parsed_client, i_c), "", parsed_client[i_c]["pk"])
			i_c += 1
		else: # >
			# catchup
			add_diff("", strs_from_parsed_data(parsed_server, i_s), parsed_server[i_s]["pk"])
			i_s += 1

	# catchup
	while i_c < len(parsed_client):
		add_diff(strs_from_parsed_data(parsed_client, i_c), "", parsed_client[i_c]["pk"])
		i_c += 1
	while i_s < len(parsed_server):
		add_diff("", strs_from_parsed_data(parsed_server, i_s), parsed_server[i_s]["pk"])
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
		"client_ip": f"{form.cleaned_data['client_ip']}:{form.cleaned_data['port']}",
		"model": form.cleaned_data['model'],
	}

	# GET
	link = f"http://{context['server_ip']}/sync_get_model/{form.cleaned_data['model']}"
	parsed_server = json.loads(requests.get(link).json())

	link = f"http://{context['client_ip']}/sync_get_model/{form.cleaned_data['model']}"
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

def get_entry(parsed, pk):
	# TODO: they selected client, but it doesn't have this pk
	for entry in parsed:
		if entry["pk"] == pk:
			return entry
	raise ValueError(f"PK Not Found: {pk}")

def merge(merge_data, parsed_server, parsed_client, server, client):
	def assing_pk_factory(data, mapping, reserved_pks_orig):
		curr_pk = 1
		def inner(original_entry, do_map):
			nonlocal curr_pk
			data.append(deepcopy(original_entry))
			data[-1]["pk"] = curr_pk
			if do_map and original_entry["pk"] != curr_pk:
				mapping[original_entry["pk"]] = curr_pk
			curr_pk += 1
			while curr_pk in reserved_pks_orig:
				curr_pk += 1
		return inner

	def merge_client(merge_data, merge_i, assign_entry_and_pk, parsed_client):
		m = merge_data[merge_i]["merge"]
		pk = merge_data[merge_i]["pk"]
		# do not skip over Client if we have chosen them
		if m == "Undecided":
			# pk already reserved
			pass
		elif m == client:
			assign_entry_and_pk(get_entry(parsed_client, pk), False)
		elif m == server:
			# Do not copy client data (delete them)
			pass
		elif m == "Both":
			# both, but server doesn't exist
			assign_entry_and_pk(get_entry(parsed_client, pk), False)
		elif m == "Neither":
			pass
		else:
			raise ValueError(f"{m} not in (Undecided, {client}, {server}, Both, Neither)")

	def try_get_assign_entry_factory(assign_entry_and_pk, parsed_client):
		def try_get_assign_entry(pk, do_map):
			"""
			Assign entry from client, if it exists.
			For case when client doesn't exist but client or both were selected.
			"""
			try:
				entry = get_entry(parsed_client, pk)
			except ValueError as e:
				return
			assign_entry_and_pk(entry, do_map)
		return try_get_assign_entry


	reserved_pks = {m["pk"] for m in merge_data if m["merge"] == "Undecided"}

	new_ser = []
	map_pk = {}
	merge_i = 0
	assign_entry_and_pk = assing_pk_factory(new_ser, map_pk, reserved_pks)
	try_get_assign_entry = try_get_assign_entry_factory(assign_entry_and_pk, parsed_client)
	for entry in parsed_server:
		# Add data from client:
		while merge_i < len(merge_data) and merge_data[merge_i]["pk"] < entry["pk"]:
			merge_client(merge_data, merge_i, assign_entry_and_pk, parsed_client)
			merge_i += 1
		# Keep data unafected by migration:
		if merge_i >= len(merge_data) or merge_data[merge_i]["pk"] != entry["pk"]:
			assign_entry_and_pk(entry, True)
			continue

		assert(merge_i >= len(merge_data) or merge_data[merge_i]["pk"] == entry["pk"])
		m = merge_data[merge_i]["merge"]
		# For server:
		if m == "Undecided":
			# not changing the pk
			new_ser.append(deepcopy(entry))
		elif m == client:
			try_get_assign_entry(entry["pk"], True)
		elif m == server:
			assign_entry_and_pk(entry, True)
		elif m == "Both":
			# do it in the same order for the other way around
			# take the true server side first
			if server == "Server":
				assign_entry_and_pk(entry, True)
				try_get_assign_entry(entry["pk"], False)
			else:
				try_get_assign_entry(entry["pk"], False)
				assign_entry_and_pk(entry, True)
		elif m == "Neither":
			map_pk[entry["pk"]] = None
		else:
			raise ValueError(f"{m} not in (Undecided, {client}, {server}, Both, Neither)")
		merge_i += 1

	while merge_i < len(merge_data):
		merge_client(merge_data, merge_i, assign_entry_and_pk, parsed_client)
		merge_i += 1

	return new_ser, map_pk

def replace_with_imported(
	data_new, pk_mapping, model_Merging,
	models_FKs, models_FKs_read, models_FKs_write, FK_update_fields,
	models_MtoMs, models_MtoMs_read, models_MtoMs_write, MtoM_update_fields,
):
	# 1. Find the max of current pk MAX_PK_CURRENT.
	max_pk_current = max(p.pk for p in model_Merging.objects.all()) if model_Merging.objects.first() else 0
	# 2. Find the max of imported pk MAX_PK_IMPORTED.
	max_pk_imported = max(d["pk"] for d in data_new) if data_new else 0
	# 3. MAX_PK = max(MAX_PK_CURRENT, MAX_PK_IPORTED)
	max_pk = max(max_pk_current, max_pk_imported) + 1
	# 4. Make a tmp Person with PK=MAX_PK
		# TODO assuming it exists
		# get a Person
		# make JSON
	if model_Merging.objects.first():
		data = json.loads(serializers.serialize("json", (model_Merging.objects.first(),)))
		data[0]["pk"] = max_pk
			# write to a file
		# TODO? tmpfile = TemporaryNamedFile(mode="w+", encoding="utf-8")
		with open("merge_file.json", mode="w+", encoding="utf-8") as myfile:
			myfile.write(json.dumps(data))
			# import the file
		call_command("loaddata", "merge_file.json")
	# 5. A list of ReadAt pk mapping readat_mapping {ReadAt_pk : Person_pk}
	FK_mappings = []
	for model_FK, model_FK_read, model_FK_write, fields \
	in zip(models_FKs, models_FKs_read, models_FKs_write, FK_update_fields):
		model_mapping = {}
		# 6. Change the PK of ReadAt from old_PK to MAX_PK.
		objs = model_FK.objects.all()
		for r in objs:
			model_mapping[r.pk] = model_FK_read(r)
			model_FK_write(r, max_pk)
		model_FK.objects.bulk_update(objs, fields, batch_size=100)
		FK_mappings.append(model_mapping)
	# 5. for MtoM
	MtoM_mappings = []
	for model_MtoM, model_MtoM_read in zip(models_MtoMs, models_MtoMs_read):
		model_mapping = {}
		# 6. doesn't apply to MtoMs, just make mapping
		for r in model_MtoM.objects.all():
			model_mapping[r.pk] = model_MtoM_read(r)
		MtoM_mappings.append(model_mapping)
	# 7. Delete all Person whose PK < MAX_PK, there are no ForeginKeys to them after the previous step.
	model_Merging.objects.filter(pk__lt=max_pk).delete()
	# 8. Import new data (there is no overlap between the duplicate and imported data).
	if data_new:
		with open("merge_file.json", mode="w+", encoding="utf-8") as myfile:
			myfile.write(json.dumps(data_new))
			# import the file
		call_command("loaddata", "merge_file.json")
	# 9. Change the PK of ReadAt from MAX_PK to pk provided by mapping.
	#    new_pk = pk_mapping[readat_mapping[ReadAt_pk]] (or something like that).
	print("pk_mapping:", pk_mapping)
	print("FK_mappings:", FK_mappings)
	for model_FK, FK_mapping, model_FK_write, fields \
	in zip(models_FKs, FK_mappings, models_FKs_write, FK_update_fields):
		objs = model_FK.objects.all()
		for r in objs:
			m_r = FK_mapping[r.pk]
			if m_r in pk_mapping:
				m_r = pk_mapping[m_r]
			print(f"FK {r.pk}: {FK_mapping[r.pk]} -> {m_r}")
			if m_r == None:
				# delete in the next step
				continue
			model_FK_write(r, m_r)
		model_FK.objects.bulk_update(objs, fields, batch_size=100)

	# ManyToManyField - update pk by pk_mapping
	print("MtoM_mappings:", MtoM_mappings)
	for model_MtoM, MtoM_mapping, model_MtoM_write, fields \
	in zip(models_MtoMs, MtoM_mappings, models_MtoMs_write, MtoM_update_fields):
		objs = model_MtoM.objects.all()
		for r in objs:
			m_r = MtoM_mapping[r.pk]
			m_r = tuple(pk_mapping[x] if x in pk_mapping else x for x in m_r)
			print(f"MtoM {r.pk}: {MtoM_mapping[r.pk]} -> {m_r}")
			model_MtoM_write(r, m_r)
		model_MtoM.objects.bulk_update(objs, fields, batch_size=100)
	# 10. Delete tmp Person, also CASCADE delete ForeginKeys left from the previous step.
	model_Merging.objects.filter(pk=max_pk).delete()

def sync_process_diff(request):
	# recieve database and my-migrations
	if request.method != "POST":
		raise Exception("need a POST request to acces this page")
	merge_data = []
	for pk, merge_action in zip(request.POST.getlist("pk"), request.POST.getlist("merge")):
		form = MergeForm({"pk":int(pk),"merge":merge_action})
		if not form.is_valid():
			raise Exception("Form was not valid")
		merge_data.append(form.cleaned_data)

	# GET
	link = f"http://{request.POST['server_ip']}/sync_get_model/{request.POST['model']}"
	parsed_server = json.loads(requests.get(link).json())

	link = f"http://{request.POST['client_ip']}/sync_get_model/{request.POST['model']}"
	try:
		parsed_client = json.loads(requests.get(link).json())
	except json.decoder.JSONDecodeError:
		context["error"] = f"Couldn't connect to {link}."
		return HttpResponse(template.render(context, request))

	data_new_server, mapping_server = merge(merge_data, parsed_server, parsed_client, "Server", "Client")
	data_new_client, mapping_client = merge(merge_data, parsed_client, parsed_server, "Client", "Server")

	# UPDATE SERVER
	link = f"http://{request.POST['server_ip']}/sync_update"
	post_data = {
		"model":request.POST['model'],
		"new_data":data_new_server,
		"pk_mapping": mapping_server,
	}
	post_response = requests.post(link, json=post_data)
	if not post_response.ok:
		print("post_response:", post_response)
		print("post_response.text is in `some file.html`")
		with open("some file.html", "w", encoding="utf-8") as f:
			f.write(post_response.text)
		raise Exception(f"Response was not OK from {link}")

	# UPDATE CLIENT
	link = f"http://{request.POST['client_ip']}/sync_update"
	post_data = {
		"model":request.POST['model'],
		"new_data":data_new_client,
		"pk_mapping": mapping_client,
	}
	post_response = requests.post(link, json=post_data)
	if not post_response.ok:
		print("post_response:", post_response)
		print("post_response.text is in `some file.html`")
		with open("some file.html", "w", encoding="utf-8") as f:
			f.write(post_response.text)
		raise Exception(f"Response was not OK from {link}")

	template = loader.get_template('sync_diff_check.html')
	context = {
		"data_new_server": data_new_server,
		"data_new_client": data_new_client,
		"mapping_server": mapping_server,
		"mapping_client": mapping_client,
	}

	return HttpResponse(template.render(context, request))

@csrf_exempt
def sync_update(request):
	if request.method != "POST":
		raise Exception("need a POST request to acces this page")

	d = json.loads(request.body)
	model = d["model"]
	new_data = d["new_data"]
	# somehow key went from int to str in post
	pk_mapping = dict((int(k), v) for k, v in d["pk_mapping"].items())

	print("model:", model)
	print("pk_mapping:", pk_mapping)

	# Backup
	with open(settings.PATH_DATABASE, "rb") as f:
		data = f.read()
	os.makedirs(settings.DIR_DATABASE_BACKUP, exist_ok=True)
	# delete all backups but the newest NUM_BACKUPS (-(-1) since a new one will be created)
	for fn in sorted(os.listdir(settings.DIR_DATABASE_BACKUP))[:-settings.NUM_BACKUPS+1]:
		filename = os.path.join(settings.DIR_DATABASE_BACKUP, fn)
		print("deleting backup:", filename)
		os.remove(filename)
	# create new backup
	backup_path = f'db_backup_{datetime.now().strftime("%Y-%m-%d__%H-%M-%S")}.sqlite3'
	print(f"creating backup: {backup_path}")
	with open(os.path.join(settings.DIR_DATABASE_BACKUP, backup_path), "wb") as f:
		f.write(data)

	# Sync the models, replace_with_imported will alter the database
	if model == "Tag":
		def read_pks(obj):
			return tuple(o.pk for o in obj.tags.all())
		def write_pks(obj, new_pks):
			obj.tags.set(new_pks)
		replace_with_imported(new_data, pk_mapping, models.Tag,
			(), (), (), (),
			(models.Entry,), (read_pks,), (write_pks,), (("tags",),))
	elif model == "Done":
		def read_pks(obj):
			return tuple(o.pk for o in obj.done.all())
		def write_pks(obj, new_pks):
			obj.done.set(new_pks)
		replace_with_imported(new_data, pk_mapping, models.Done,
			(), (), (), (),
			(models.Entry,), (read_pks,), (write_pks,), (("done",),))
	# TODO sync Image file objects, this just does the annotations etc.
	elif model == "Image":
		def read_pks(obj):
			return tuple(o.pk for o in obj.images.all())
		def write_pks(obj, new_pks):
			obj.images.set(new_pks)
		replace_with_imported(new_data, pk_mapping, models.Image,
			(), (), (), (),
			(models.Entry,), (read_pks,), (write_pks,), (("images",),))
	elif model == "Entry":
		def read_pk(obj):
			return obj.entry_id
		def write_pk(obj, new_pk):
			obj.entry_id = new_pk
		replace_with_imported(new_data, pk_mapping, models.Entry,
			(models.ReadAt,), (read_pk,), (write_pk,), (("entry",),),
			(), (), (), ())
	elif model == "Person":
		def read_pk(obj):
			return obj.read_by_id
		def write_pk(obj, new_pk):
			obj.read_by_id = new_pk
		replace_with_imported(new_data, pk_mapping, models.Person,
			(models.ReadAt,), (read_pk,), (write_pk,), (("entry",),),
			(), (), (), ())
	elif model == "ReadAt":
		replace_with_imported(new_data, pk_mapping, models.ReadAt,
			(), (), (), (),
			(), (), (), ())
	else:
		return
	return HttpResponse(status=204)


def get_all_entries(request):
	template = loader.get_template('all_entries.html')

	l = models.ReadAt.objects.order_by("-date").first()
	context = {
		"entries": tuple(pass_context_of_entry(e) for e in models.Entry.objects.order_by("-day")),
		"last_read": l.entry.pk if l else l,
	}

	return HttpResponse(template.render(context, request))

class GraphView(TemplateView):

	template_name = "graph.html"

	def get_context_data(self, **kwargs):
		context = super(GraphView, self).get_context_data(**kwargs)

		entries = models.Entry.objects.order_by('day')

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
