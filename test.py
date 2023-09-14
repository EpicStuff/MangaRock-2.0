from nicegui import ui
from nicegui.dependencies import register_library
from pathlib import Path
from MangaRock import load_settings

library = register_library(Path('v3/ag-grid-enterprise.min.js').resolve())

def jailbreak(grid: ui.aggrid) -> ui.aggrid:
	'upgrade aggrid from community to enterprise'
	# check if targeted library is ag-grid-community
	assert grid.libraries[0].name == 'ag-grid-community', 'Overwriting NiceGUI aggrid ran into a tiny problem, got wrong lib'
	# overwrite aggrid library with enterprise
	grid.libraries[0] = library
	# return grid
	return grid
def format_row(row: dict, settings: dict) -> dict:
	'format row to make grouping work'
	if 'series' not in row or row['series'] is None:
		row['series'] = row['name']
		row['name'] = row['link']
		row['link'] = ' '
	if 'author' not in row or row['author'] is None:
		row['author'] = row['series']
		row['series'] = row['name']
		row['name'] = row['link']
		row['link'] = ' '
	return row


settings = load_settings('v3/settings.yaml')

cols = [{'field': 'id', 'aggFunc': 'first'}]
# cols = []
for key, val in settings['to_display']['example'].items():  # TODO: maybe turn into list comprehension
	if val[1] == 'group':
		cols.append({'field': key, 'rowGroup': True, 'hide': True})
	else:
		cols.append({'headerName': val[0], 'field': key, 'aggFunc': val[1], 'width': settings['default_column_width']})
rows = [
	{'link': 'https://chapmanganato.com/manga-mq990225', 'nChs': '', 'name': 'I Am the Fated Villain', 'chapter': 10.0, 'series': None, 'author': None, 'score': 'Great', 'tags': ['strong lead'], 'id': 0},
	# {'link': 'https://example.com', 'nChs': '', 'name': 'Test 1', 'chapter': 1.0, 'series': 'testing', 'author': 'tester', 'score': None, 'tags': []},
	# {'link': 'https://example.com', 'nChs': '', 'name': 'Test 2', 'chapter': 2.0, 'series': 'testing', 'author': 'tester', 'score': None, 'tags': []},
	# {'link': 'https://example.com/1', 'nChs': '', 'name': 'Test 3', 'chapter': 2.0, 'series': 'testing', 'author': 'tester', 'score': None, 'tags': []},
	# {'link': 'https://example.com/2', 'nChs': '', 'name': 'Test 3', 'chapter': 2.0, 'series': 'testing', 'author': 'tester', 'score': None, 'tags': []},
	# {'link': 'https://example.com/3', 'nChs': '', 'name': 'Test 3', 'chapter': 2.0, 'series': 'testing', 'author': 'tester', 'score': None, 'tags': []},
	{
		'author': 'author‎',
		# 'series': 'series',
		'name': 'name 1',
		'link': 'link 1',
		'id': 1
	},
	{
		'author': 'author‎',
		'series': 'series‏',
		'name': 'name 2',
		'link': 'link 2',
		'id': 2
	}
]

rows = [format_row(row, settings) for row in rows]

gridOptions = {
	'defaultColDef': {
		'resizable': True,
		'suppressMenu': True,
		'cellRendererParams': {'suppressCount': True, },
	},
	'autoGroupColumnDef': {
		'headerName': 'Name',
		'field': 'link',
	},
	'columnDefs': cols,
	'rowData': rows,
	'rowHeight': 32,
	'animateRows': True,
	'suppressAggFuncInHeader': True,
}

ui.label('test')
grid = ui.aggrid(gridOptions, theme='alpine-dark').style('height: calc(100vh - 164px)')
jailbreak(grid)

ui.run(dark=True)
