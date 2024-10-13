# equivalent to
# lambda json, idx: int(json[idx]["pk"])
def pk_to_int(json, idx):
	return int(json[idx]["pk"])

def bin_search_for_val(json, val, comp):
	"""
	json is searched dict, must be sorted by val in ascending order
	val is searched for
	comp(json, idx) on json must return comparable to val
	"""
	min_i = 0
	max_i = len(json) - 1
	if not (comp(json, min_i) <= val <= comp(json, max_i)):
		return -1

	while min_i < max_i:
		middle_i = min_i + (max_i - min_i + 1) // 2
		middle_val = comp(json, middle_i)
		if val > middle_val:
			min_i = middle_i + 1
		elif val < middle_val:
			max_i = middle_i - 1
		elif val == middle_val:
			return middle_i

	# min_i == max_i
	if comp(json, min_i) == val:
		return min_i

	return -1


x = bin_search_for_val([
		{"pk": "-5"},
		{"pk": "-4"},
		{"pk": "1"},
		{"pk": "2"},
		{"pk": "3"},
	],
	1,
	lambda json, idx: int(json[idx]["pk"])
	)

print(x)