from plotly.offline import plot
import plotly.graph_objs as go


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
		filename='basic-bar',
		output_type='div',
	)

	return div
