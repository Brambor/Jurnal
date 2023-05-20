import re
from bs4 import BeautifulSoup
from datetime import datetime

from django import template

from ..models import Entry
from ..utils import weekday


register = template.Library()

@register.filter
def squish_ul_linebreaks(value):
	"""
	Prepare lists created by <ul> for filter 'linebreaks' by removing newlines
	around <ul> (within <ul></ul> & strip after </ul>)

	For each value = <ul>A</ul>B
	set A = A.striplines()
	set B = B.strip()
	"""
	return squish_linebreaks_procedure(squish_linebreaks_procedure(value, "<ul>", "</ul>"), "<ol>", "</ol>")

def squish_linebreaks_procedure(value, tag, end_tag):
	ul_index = value.find(tag)
	replacements_indexes = []  # (list)(<int start, int end>)
	while ul_index != -1:
		start = ul_index
		end_ul_index = value.find(end_tag, start)
		# counts of ul and \ul
		ul = 0
		end_ul = 0
		next_ul_index = value.find(tag, ul_index+1)
		while ul != end_ul or 0 <= next_ul_index < end_ul_index:
			if ul < end_ul:
				x = value.find(tag, ul_index+1)
				if x == -1:
					raise ValueError(f"We were supposed to find {tag}! Invalid html syntax!")
				ul_index = x
				ul += 1
			else:
				x = value.find(end_tag, end_ul_index+1)
				if x == -1:
					raise ValueError(f"We were supposed to find {tag}! Invalid html syntax!")
				end_ul_index = x
				end_ul += 1
			next_ul_index = value.find(tag, ul_index+1)
		end = end_ul_index
		replacements_indexes.append((start,end+5))
		ul_index = value.find(tag, ul_index+1)

	for start, end in reversed(replacements_indexes):
		value = value.replace(value[end:], value[end:].strip())
		value = value.replace(value[start:end],
			"".join(x.strip() if x.endswith(">") else f'{x.strip()}\n' for x in value[start:end].splitlines()))

	return value


def decorate_date(match):
	"""
	Find all dates in format YYYY-MM-DD in match and replace it by clickable
	<a href="#...">...</a> date if there is an entry of that day.
	Otherwise return date with warning saying format is incorect, or that
	not exactly one entry with given day exists.

	match is a re.Match
	"""
	y, m, d = (int(i) for i in match.group().split("-"))
	try:
		day = datetime(year=y, month=m, day=d)
	except ValueError:
		return f"<i>{match.group()} (incorect date format)</i>"
	entries = Entry.objects.filter(day=day)
	if not entries:
		return f"<i>{weekday(day.weekday())}, {match.group()} (no entry)</i>"
	elif len(entries) > 1:
		return f"<i>{match.group()} (huh, found {len(entries)} entries)</i>"
	else:
		e = entries.first()
		return (f'<i><a href="#{e.day}">{e.weekday()}, {match.group()}, '
			f'{e.header if e.header else "(no header)"}</a></i>')


@register.filter
def date_tag_a(value):
	"""
	Find all dates in format YYYY-MM-DD in value and replace it by clickable
	<a href="#...">...</a> date.
	"""
	return re.sub("\d{4}-\d{2}-\d{2}", decorate_date, value)
