from nicegui import ui
import nicegui
from pathlib import Path

# x = nicegui.dependencies.js_components
# y = x['aggrid']
# z = nicegui.dependencies.js_dependencies
w = nicegui.dependencies.js_dependencies[0]
assert w.dependents == {'aggrid'}, 'Overwriting NiceGUI aggrid failed'
w.path = Path('ag-grid-enterprise.min.js')

columnDefs = [{'headerName': 'Name', 'field': 'name', 'rowGroup': True, 'hide': True},]
rowData = [
	{'link': 1},
	{'link': 2},
	{'link': 3},
]
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
  		'rowHeight': 32,
  		'animateRows': True,
  		'suppressAggFuncInHeader': True,
}
ui.aggrid(gridOptions, theme='alpine-dark').style('height: calc(100vh - 164px)')

ui.run()
