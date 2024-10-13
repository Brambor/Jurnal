from plotly.offline import plot
import plotly.graph_objs as go

from datetime import datetime
import socket


def generate_graph(x, y_data, title, layout_edit={}):
	data = [
		go.Bar(
			x=x,
			y=y_data[key],
			name=key,
		) for key in y_data
	]

	layout = go.Layout(
		title=title,
		barmode='stack',
		**layout_edit,
	)

	fig = go.Figure(
		data=data,
		layout=layout,
	)

	div = plot(
		fig,
		filename=title,
		output_type='div',
	)

	return div

def get_client_ip(request):
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		ip = x_forwarded_for.split(',')[0]
	else:
		ip = request.META.get('REMOTE_ADDR')
	return ip

weekdays = ("Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle")

def weekday(n):
	"""
	Given int n, 0 <= n <= 6,
	return Czech name of n'th weekday
	"""
	return weekdays[n]

def pass_context_of_entry(entry):
	e = entry
	return {
		"pk": e.pk,
		"day": str(e.day),
		"weekday_date": f"{e.weekday()}, {e.day}",
		"header": e.header,
		"to_do": e.to_do.replace("\n", "; "),
		"image_set": e.image_set.all(),
		"content": e.content,
		"content_day": e.content_day,
		"content_thought": e.content_thought,
		"content_idea": e.content_idea,
		"tags": ", ".join(str(t) for t in e.tags.order_by("tag")),
		"in_future": e.day > datetime.date(datetime.today()),
		"done": ', '.join(str(d) for d in e.done.order_by('done')),
		"place": e.place,
		"timesread": e.timesread(),
	}

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
