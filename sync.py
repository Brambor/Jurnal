"""
1. Export using:
```
python -Xutf8 manage.py dumpdata -o dbdump_phone.py
```

2. Edit the file, add the following at the begining:
```true = True
false = False
data = ```

3. Run this.

"""

#from difflib import Differ
from copy import deepcopy
from difflib import HtmlDiff
import json
#help(Differ)

from dbdump_phone import data as phone_data
from dbdump_pc import data as pc_data

ignore_fields = {'sessions.session', 'auth.permission', 'admin.logentry', 'auth.user', 'contenttypes.contenttype'
	'entries.machine', 'entries.ipaddress'}

Diff = HtmlDiff()

def get_all_fields(data):
	return set(line["model"] for line in data)

def filter_ignored_fields(data):
	return [line for line in data if line["model"] not in ignore_fields]

def get_model(data, model):
	return [line for line in data if line["model"] == model]

def removed_model(data, model):
	return [line for line in data if line["model"] != model]

def get_by_pk(data, pk):
	for d in data:
		if d["pk"] == pk:
			return d
	raise ValueError(f"Pk {pk} not found.")

def tags_to_dict(data):
	ret = {}
	for line in get_model(data, "entries.tag"):
		ret[line["pk"]] = line["fields"]["tag"]
	return ret

def expanded_tags(data, tags):
	data = deepcopy(data)
	for i, tag_pk in enumerate(data["fields"]["tags"]):
		data["fields"]["tags"][i] = tags[tag_pk]
	return data

def diff(a, b, debug=False):
	"""
	Assumes entries are sorted by pk.
	"""
	same = 0
	different = []
	# not add necesairly, could have been deleted
	add_a = []
	add_b = []

	i_a = 0
	i_b = 0
	while i_a < len(a) and i_b < len(b):
		if a[i_a] == b[i_b]:
			same += 1
			i_a += 1
			i_b += 1
		elif a[i_a]["pk"] == b[i_b]["pk"]:
			# TODO there is some difference
			# Conflict resolution: Sometimes, add them both (they are different), sometimes merge
			different.append(a[i_a]["pk"])
			i_a += 1
			i_b += 1
		elif a[i_a]["pk"] > b[i_b]["pk"]:
			# TODO catchup
			# sometimes add, sometimes (deleted) delete
			add_a.append(a[i_a]["pk"])
			i_a += 1
		else: # <
			# TODO catchup
			# sometimes add, sometimes (deleted) delete
			add_b.append(b[i_b]["pk"])
			i_b += 1

	while i_a < len(a):
		add_a.append(a[i_a]["pk"])
		i_a += 1
	while i_b < len(b):
		add_b.append(b[i_b]["pk"])
		i_b += 1

	print("status")
	print(f"\tsame: {same}")
	print(f"\tdifferent: {len(different)} {different}")
	print(f"\t+a: {len(add_a)} {add_a}")
	print(f"\t+b: {len(add_b)} {add_b}")
	return same, different, add_a, add_b

def replaced(data, fields):
	"""
	Replace all instances of model in data.

	Model extracted from given fields, all fields must have the same model.
	"""
	assert(len(fields) > 0)
	model = fields[0]["model"]
	for f in fields:
		assert(f["model"] == model)

	new_data = removed_model(data, model)
	new_data.extend(fields)
	return new_data

def text_from_dict(data):
	txt = json.dumps(data["fields"], sort_keys=True, indent=2).encode('utf8').decode('unicode-escape')
	txt = split_sentences(txt, 80)
	return txt.splitlines()

def split_sentences(txt, linebreak):
	"""
	Break string by sentences, then words. Linebreak after `linebreak` chars.

	Break by sentences so that if I add 1 char, every following line doesn't start with 1 red char
	"""
	# for space at begining

	for term in (".", "!", "?"):
		txt = f"{term}\n".join(txt.split(f"{term} "))
	new_txt = ""
	for line in txt.splitlines():
		words = [l.strip() for l in line.split()]

		new_line = ""
		while words:
			w = 0

			# add words until limit
			while w < len(words) and len(new_line) + len(words[w]) <= linebreak:
				if new_line not in " ":
					new_line += " "
				new_line += words[w]
				w += 1

			# No words added, so the first word is too long
			if new_line in " " and w < len(words):
				lb = linebreak - len(new_line)  # in case of space at the beggining
				new_line += words[0][:lb]
				words[0] = words[0][lb:]
			else:
				words = words[w:]

			new_txt += f"{new_line}\n"

			# This adds space at begining, if the sentence didn't finish yet.
			# TODO: Keep?
			new_line = " "

	return new_txt

# TEST diff
txt = "a"*7 + " f " + "b"*6 + f". {'c'*8}! d" + "e"*13
tst = """aaaaa
 aa f
 bbbb
 bb.
ccccc
 ccc!
deeee
 eeee
 eeee
 e
"""
assert(tst == split_sentences(txt, 5))

phone_data = filter_ignored_fields(phone_data)
pc_data = filter_ignored_fields(pc_data)

print(f"len(phone_data) = {len(phone_data)}")
print(f"len(pc_data) = {len(pc_data)}")


print("equal models")
assert(get_all_fields(phone_data) == get_all_fields(pc_data))

print("\n\nDIFF")

# 'entries.tag' NEEDS nothing
print("entries.tag")
a = get_model(phone_data, "entries.tag")
b = get_model(pc_data, "entries.tag")
#print(a[0])
assert(a == b)


# 'entries.done' NEEDS nothing
print("entries.done")
a = get_model(phone_data, "entries.done")
b = get_model(pc_data, "entries.done")
#print(a[0])
assert(a == b)

# 'entries.person' NEEDS nothing
print("entries.person")
a = get_model(phone_data, "entries.person")
b = get_model(pc_data, "entries.person")

# TODO: different must be 0 for fast-forward
same, _, _, _ = diff(a, b)
if same == len(a):
	print("fast forward a (us); just do a = b")
	a = b
	phone_data = replaced(phone_data, b)
elif same == len(b):
	print("fast forward b (them); just do b = a")
	b = a
	pc_data = replaced(pc_data, a)
else:
	raise NotImplementedError
assert(a == b)






# 'entries.entry' NEEDS tag, done
# TODO: assuming tag & done didn't merge (only fast forward)
print("entries.entry")
a = get_model(phone_data, "entries.entry")
b = get_model(pc_data, "entries.entry")
#print(a[0])

# TODO: different must be 0 for fast-forward
same, different, add_a, add_b = diff(a, b, True)

tags_a = tags_to_dict(phone_data)
tags_b = tags_to_dict(pc_data)

for pk in different:
	print(f'made diff of {pk}')
	a_str = text_from_dict(expanded_tags(get_by_pk(a, pk), tags_a))
	b_str = text_from_dict(expanded_tags(get_by_pk(b, pk), tags_b))
	#print(a_str)
	html_str = Diff.make_file(a_str, b_str, charset='utf-8')
	#html_str = list(Diff.compare(a_str, b_str))
	#for line in html_str:
	#	print(line)
	with open(f"something/something_{pk}.html", "w", encoding="utf-8") as file:
		file.write(html_str)

if add_b:
	b_pk = add_b[0]
	print("\t", "first add b (them):")
	print("\t", get_by_pk(b, b_pk))
else:
	print("\t", "b (they) add nothing")


if add_a:
	a_pk = add_a[0]
	print("\t", "first add a (us):")
	print("\t", get_by_pk(a, a_pk))
else:
	print("\t", "a (we) add nothing")

print(a[0])

assert(a == b)





"""
# TODO: finish
# 'entries.readat' NEEDS ENTRY, PERSON
# From perspective of phone
print("entries.readat")
# us
a = get_model(phone_data, "entries.readat")
# them
b = get_model(pc_data, "entries.readat")
print(a[0])

same = diff(a, b)

if same > 0:
	same_idx = same - 1
else:
	# TODO: everything is different
	raise NotImplementedError
print("last equal:")
assert(a[same_idx] == b[same_idx])
print(b[same_idx])

print("add b (them):")
for l in b[same:]:
	print(l)

print("add a (us):")
for l in a[same:]:
	print(l)
#print(a)
#print(b)
assert(a == b)
"""












# 'entries.image'




diff = 0
for a, b in zip(phone_data, pc_data):
	diff += a == b
print(diff)