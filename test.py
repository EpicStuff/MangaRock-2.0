from nicegui import ui

# ui.dark_mode().enable()
label = ui.label('Choose File:')

def tmp(*args):
	print(args)


# grid = ui.aggrid({
#     'columnDefs': [
#         {'headerName': 'Name', 'field': 'name', 'resizable': True},
#         {'headerName': 'Age', 'field': 'age', 'width': 10},
#     ],
#     'rowData': [
#         {'name': 'Alice', 'age': 18},
#         {'name': 'Bob', 'age': 21},
#         {'name': 'Carol', 'age': 42},
#     ],
#     'rowSelection': 'single'
# }).classes(remove='ag-theme-balham').classes('ag-theme-alpine-dark')
# grid.on('cellDoubleClicked', tmp)
# grid.call_api_method('sizeColumnsToFit')
# from tmp2 import data

# grid = ui.aggrid({
# 	'rowData': data,
# 	'columnDefs': [
# 		{'field': 'country', 'rowGroup': True, 'hide': True},
# 		{'field': 'year', 'rowGroup': True, 'hide': True},
# 		{'field': 'athlete'},
# 		{'field': 'sport'},
# 		{'field': 'gold'},
# 		{'field': 'silver'},
# 		{'field': 'bronze'},
# 	],
# 	'defaultColDef': {
# 		'flex': 1,
# 		'minWidth': 100,
# 		'sortable': True,
# 		'resizable': True,
# 	},
# 	'autoGroupColumnDef': {
# 		'minWidth': 200,
# 	},
# 	'animateRows': True,
# }).classes(remove='ag-theme-balham').classes('ag-theme-alpine-dark').style('height: 600px')  # .classes('flex-grow')




with ui.row().classes('w-full no-wrap'):
	ui.input().props('square filled dense="dense" clearable clear-icon="close"').classes('flex-grow').style('width: 8px; height: 8px; border:0px; padding:0px; margin:0px')
	ui.button().props('square').style('width: 40px; height: 40px;')

ui.run(dark=True, title='MangaRock 2.0')