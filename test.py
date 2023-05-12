from nicegui import ui
def tmp(*args):
	print(args)


label = ui.label('Choose File:')

rowData = [
    {'orgHierarchy': ['A']},
    {'orgHierarchy': ['A', 'B']},
    {'orgHierarchy': ['C', 'D']},
    {'orgHierarchy': ['E', 'F', 'G', 'H']},
];
def getDataPath(data):
    return data.orgHierarchy
def valueGetter(params):
	if params.data:
		return 'Provided'
	return 'Filler'


from tmp2 import rowData
gridOptions = {
    'columnDefs': [
        # we're using the auto group column by default!
        {'field': 'jobTitle'},
        {'field': 'employmentType'},
    ],
    'defaultColDef': {
        'flex': 1,
    },
    'autoGroupColumnDef': {
        'headerName': 'Organisation Hierarchy',
        'minWidth': 300,
        'cellRendererParams': {
            'suppressCount': True,
        },
    },
    'rowData': rowData,
    'treeData': True,  # enable Tree Data mode
    'animateRows': True,
    'groupDefaultExpanded': -1,  # expand all groups by default
    'getDataPath': lambda data: data.orgHierarchy,
};
grid = ui.aggrid(gridOptions, theme='alpine-dark')

with ui.row().classes('w-full no-wrap'):
	ui.input().props('square filled dense="dense" clearable clear-icon="close"').classes('flex-grow').style('width: 8px; height: 8px; border:0px; padding:0px; margin:0px')
	ui.button().props('square').style('width: 40px; height: 40px;')

ui.run(dark=True, title='MangaRock 2.0')
