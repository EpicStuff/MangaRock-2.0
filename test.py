from nicegui import ui
def tmp(*args):
	print(args)


label = ui.label('Choose File:')

def getDataPath(data):
	return data.orgHierarchy;


gridOptions = {
	'columnDefs': [
		{'field': 'group'},
		{'field': 'jobTitle'},
		{'field': 'employmentType'}
	],
	'autoGroupColumnDef': {
		'headerName': "Group",
		'width': 300,
		'cellRendererParams': {
			'suppressCount': True
		}
	},
	'rowData': [
		{'group': 'Erica', 'orgHierarchy': ['Erica'], 'jobTitle': "CEO", 'employmentType': "Permanent"},
		{'group': 'Malcolm', 'orgHierarchy': ['Erica', 'Malcolm'], 'jobTitle': "VP", 'employmentType': "Permanent"}
	],
	'rowSelection': 'multiple',
	'treeData': 1,
	'animateRows': True,
	# 'treeData': True,
	'getDataPath': ['Erica', 'Malcolm']
}
grid = ui.aggrid(gridOptions, theme='alpine-dark')

with ui.row().classes('w-full no-wrap'):
	ui.input().props('square filled dense="dense" clearable clear-icon="close"').classes('flex-grow').style('width: 8px; height: 8px; border:0px; padding:0px; margin:0px')
	ui.button().props('square').style('width: 40px; height: 40px;')

ui.run(dark=True, title='MangaRock 2.0')
