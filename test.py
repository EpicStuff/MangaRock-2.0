from nicegui import ui

def jailbreak(self, package: str = 'v3/ag-grid-enterprise.min.js') -> None:  # TODO: fix jailbreak broken due to 1.3.0 update
	'upgrade aggrid from community to enterprise'
	import pathlib
	from nicegui.dependencies import libraries
	lib = libraries[next(iter(libraries))]
	assert lib.name == 'ag-grid-community', 'Overwriting NiceGUI aggrid ran into a tiny problem, got wrong lib'
	lib.path = pathlib.Path(package).resolve()


def jail_break(package='v3/ag-grid-enterprise.min.js') -> None:
	import nicegui, pathlib
	assert nicegui.dependencies.js_dependencies[0].dependents == {'aggrid'}, 'Overwriting NiceGUI aggrid ran into a tiny problem'
	nicegui.dependencies.js_dependencies[0].path = pathlib.Path(package)


# jail_break()
# jailbreak(1)
# from nicegui.dependencies import libraries


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

ui.label('test')
grid = ui.aggrid(gridOptions, theme='alpine-dark').style('height: calc(100vh - 164px)')

from nicegui.dependencies import register_library
from pathlib import Path
grid.libraries = [register_library(Path('v3/ag-grid-enterprise.min.js'))]

grid2 = ui.aggrid({})

ui.run(dark=True)
