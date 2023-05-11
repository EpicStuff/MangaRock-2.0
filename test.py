from nicegui import ui

# ui.dark_mode().enable()
label = ui.label('Choose File:')

# columns = [{'name': 'files', 'lable': 'Files:', 'field': 'test', 'required': True}]
# ui.table(columns=columns, rows=[{'name': 'exmaple'}])

# columns = [
# 	{'name': 'name', 'label': 'Name', 'field': 'name', 'align': 'left'},
# 	{'name': 'age', 'label': 'Age', 'field': 'age'},
# ]
# rows = [
# 	{'name': 'Alice', 'age': 18},
# 	{'name': 'Bob', 'age': 21},
# 	{'name': 'Carol'},
# ]
# table = ui.table(columns=columns, rows=rows, row_key='name', selection='single').classes('w-full')
# table.add_slot('header', r'''
# 	<q-tr>
# 		<q-th>Name:</q-th>
# 		<q-th auto-width />
# 		<q-th>Age</q-th>
# 	</q-tr>
# ''')
# table.add_slot('body', r'''
# 	<q-tr :props="props">
# 		<q-td auto-width>
# 			<q-btn size="sm" dense
# 				@click="props.expand = !props.expand"
# 				:icon="props.expand ? 'remove' : 'add'" />
# 		</q-td>
# 		<q-td v-for="col in props.cols" :key="col.name" :props="props">
# 			{{ col.value }}
# 		</q-td>
# 	</q-tr>

# 	<q-tr v-show="props.expand" :props="props">
# 		<q-td colspan="100%">
# 			<div class="text-left">This is {{ props.row.name }}.</div>
# 		</q-td>
# 	</q-tr>
# 	<q-tr v-show="props.expand" :props="props">
# 		<q-td colspan="50%">
# 			<div class="text-left">This is {{ props.row.name }}.</div>
# 		</q-td>
# 	</q-tr>
# ''')
def tmp(*args):
	print(args)

grid = ui.aggrid({
    'columnDefs': [
        {'headerName': 'Name', 'field': 'name', 'resizable': True},
        {'headerName': 'Age', 'field': 'age', 'width': 10},
    ],
    'rowData': [
        {'name': 'Alice', 'age': 18},
        {'name': 'Bob', 'age': 21},
        {'name': 'Carol', 'age': 42},
    ],
    'rowSelection': 'single'
}).classes(remove='ag-theme-balham').classes('ag-theme-alpine-dark')
grid.on('cellDoubleClicked', tmp)
# grid.call_api_method('sizeColumnsToFit')
with ui.row():
	ui.input()
	ui.button()


ui.dark_mode().enable()

ui.run(dark=True, title='MangaRock 2.0')
# class tmp():
# 	def __init__(self):
# 	self.input = tk.StringVar(); self.tree = ttk.Treeview(self.root, selectmode='browse'); self.scroll = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview); self.entry = ttk.Entry(self.root, textvariable=self.input, font=settings['font']); self.button = ttk.Button(self.root, width=1); self.style = ttk.Style(self.root); self.open_node = ''  # setup GUI variables
# 	self.label.grid(row=0, column=0, columnspan=2, sticky='nesw'); self.tree.grid(row=1, column=0, columnspan=2, sticky='nesw'); self.scroll.grid(row=1, column=1, columnspan=1, sticky='nesw'); self.entry.grid(row=2, column=0, sticky='nesw'); self.button.grid(row=2, column=1)  # pack elements onto root
# 	self.root.title(__file__.split('\\')[-1].rstrip('.py')); self.root.columnconfigure(0, weight=1); self.root.columnconfigure(1, weight=0); self.root.rowconfigure(1, weight=1); self.root.geometry('{}x{}'.format(settings['window_size'][0], settings['window_size'][1]))  # configure root
# 	self.tree.bind('<Double-1>', lambda e: root_quit(self, e)); self.tree.bind('<Return>', lambda e: root_quit(self, e)); self.tree.bind('<<TreeviewOpen>>', tree_open); self.tree.configure(yscrollcommand=self.scroll.set); self.entry.bind('<Return>', lambda e: root_quit(self, e)); self.entry.focus_set()  # bind events to tree and entry; configure scrollbar to tree
# 	self.root.tk.eval(f'''package ifneeded tksvg 0.7 [list load [file join {dir + '/tksvg0.7'} tksvg07t.dll] tksvg]'''); self.root.tk.call('lappend', 'auto_path', dir + '/awthemes-10.3.0')  # do tk style witchery part 1, no idea what it actually does, found it somewhere online
# 	for theme in settings['themes']:  # for each theme in settings
# 	try: self.root.tk.call('package', 'require', theme); self.style.theme_use(theme)  # do style witchery part 2 to import tk theme
# 	except tk.TclError as e: print('Could not load theme', e)  # if style loading fails, print error
# 	else: break  # if style loading does not fail, stop from loading other themes
# 	self.style.configure('Treeview', rowheight=settings['font'][1] * 2, font=settings['font']); self.style.configure('Treeview.Item', indicatorsize=0, font=settings['font']); self.style.configure('Treeview.Heading', font=settings['font']); self.style.configure('TLabel', font=settings['font'])  # configure treeview and style fonts

# 	def tmp():
# 	root = tk.Tk(); stringVar = tk.StringVar(); label = ttk.Label(root, justify='left', text='Mode: Reading'); tree = ttk.Treeview(root, selectmode='browse'); scroll = ttk.Scrollbar(root, orient="vertical", command=tree.yview); entry = ttk.Entry(root, textvariable=stringVar, font=settings['font']); button = ttk.Button(root, width=1); style = ttk.Style(root)  # setup GUI variables
# 	label.grid(row=0, column=0, columnspan=2, sticky='nesw'); tree.grid(row=1, column=0, columnspan=2, sticky='nesw'); scroll.grid(row=1, column=1, columnspan=1, sticky='nesw'); entry.grid(row=2, column=0, sticky='nesw'); button.grid(row=2, column=1)  # pack elements onto root
# 	root.title(__file__.split('\\')[-1].rstrip('.py')); root.columnconfigure(0, weight=1); root.columnconfigure(1, weight=0); root.rowconfigure(1, weight=1); root.geometry('{}x{}'.format(settings['window_size'][0], settings['window_size'][1]))  # configure root
# 	tree.bind('<Double-1>', root_quit); tree.bind('<Return>', root_quit); tree.bind('<<TreeviewOpen>>', tree_open); tree.configure(yscrollcommand=scroll.set); entry.bind('<Return>', root_quit); entry.focus_set()  # bind events to tree and entry; configure scrollbar to tree
# 	style.configure('Treeview', rowheight=settings['font'][1] * 2, font=settings['font']); style.configure('Treeview.Item', indicatorsize=0, font=settings['font']); style.configure('Treeview.Heading', font=settings['font']); style.configure('TLabel', font=settings['font'])  # configure treeview and style fonts
