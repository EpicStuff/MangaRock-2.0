from nicegui import ui


import nicegui, pathlib
assert nicegui.dependencies.js_dependencies[0].dependents == {'aggrid'}, 'Overwriting NiceGUI aggrid ran into a tiny problem'
nicegui.dependencies.js_dependencies[0].path = pathlib.Path('ag-grid-enterprise.min.js')


rowData = [{'name': 'test', 'link': 'abc'}]
columnDefs = [{'headerName': 'Name', 'field': 'name', 'rowGroup': True, 'hide': True},]

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
	'columnDefs': columnDefs,
	'rowData': rowData,
	'animateRows': True,
	'suppressAggFuncInHeader': True,
}


table = ui.aggrid(gridOptions)

# async def count():
# 	rows = await ui.run_javascript(f'getElement({table.id}).gridOptions.api.getSelectedRows()')
# 	print(rows)
# 	ui.notify(f'{len(rows)} selected')


# async def test(arg):
# 	print(arg)
# 	test = await ui.run_javascript(f'getElement({table.id}).gridOptions.api.getRowNode("1")', respond=False)
# 	# print(test)


ui.button('Select', on_click=lambda: table.call_api_method('selectAll'))
# ui.button('Deselect', on_click=lambda: table.call_api_method('deselectAll'))

# table.on('cellDoubleClicked', test)

# ui.run()
async def test():
	r = await ui.run_javascript(
		f'''
			var x = getElement({table.id}).gridOptions.api;
			var y = x.getRowNode(1);
			return x;
		''',
		# respond=False
	)
	# r = await ui.run_javascript(
	# 	f'''
	# 		return "Test";
	# 	''',
	# )
	print(r)

ui.button('test', on_click=test)
ui.run()
