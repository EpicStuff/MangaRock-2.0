from nicegui import ui
import asyncio, random


c = False

async def tmp(event):
	# grid.options['rowData'][0]['age'] = random.randint(0, 100)
	# grid.call_api_method('refreshCells')
	# grid.update()
	# await ui.run_javascript('document.getElementById(6).class="test"', respond=False)
	global c

	a = [
		{'name': 'Alice', 'age': 99},
		{'name': 'Bob', 'age': 21},
		{'name': 'Carol', 'age': 42},]
	b = [
		{'name': 'Alice', 'age': 1},
		{'name': 'Carol', 'age': 99},]

	c = not c
	print(c)
	if c: grid.call_api_method('setRowData', a)
	else: grid.call_api_method('setRowData', b)

grid = ui.aggrid({
	'columnDefs': [
		{'headerName': 'Name', 'field': 'name'},
		{'headerName': 'Age', 'field': 'age'},
	],
	'rowData': [
		{'name': 'Alice', 'age': 18},
		{'name': 'Bob', 'age': 21},
		{'name': 'Carol', 'age': 42},
	],
	'defaultColDef': {
		'editable': True,
            },
}, theme='alpine-dark')

ui.button('Test', on_click=tmp)

ui.run(dark=True)
