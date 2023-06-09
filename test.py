from nicegui import ui


import nicegui, pathlib
assert nicegui.dependencies.js_dependencies[0].dependents == {'aggrid'}, 'Overwriting NiceGUI aggrid ran into a tiny problem'
nicegui.dependencies.js_dependencies[0].path = pathlib.Path('ag-grid-enterprise.min.js')


rowData = [
	{'name': 'test1', 'link': 'abc'},
	{'name': 'test2', 'link': 'def'},
	{'name': 'test3', 'link': 'ghi'},
]
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

open = None

async def tmp(arg):
	global open
	print(arg)

	node_clicked = arg['args']['rowId']

	tmp = await ui.run_javascript(f'getElement({table.id}).gridOptions.api.getRowNode("{node_clicked}").expanded;')
	if not tmp:
		return

	if open is None:
		open = node_clicked
		return

	print('closing:', open)
	await ui.run_javascript(
		f'''
			var x = getElement({table.id}).gridOptions.api;
			var y = x.getRowNode("{open}");
			x.setRowNodeExpanded(y, false);
		''',
		# '''
		# 	var x = getElement(4);
		# 	x.gridOptions.api.forEachNode(function(node) {
		# 		if(node.expanded && node.group && node.id !== ''' + arg['args']['rowId'] + ''') {
		# 				node.setExpanded(false);
		# 		}
		# 	});
		# ''',
		respond=False
	)
	open = node_clicked
	print('now open:', open)

def tmp2(arg):
	print(arg)


table.on('onRowDoubleClicked', tmp2)
# table.on('rowGroupOpened', tmp)

ui.run()
