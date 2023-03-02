# Version: 3.3.1
# okay, heres the plan, make links its own separate object and have the links update individualy. when the updates, it will then update its parent's display
import os, sys


class Type():  # type represents the type of object things are, eg: authors, books, website, ...
	''' Base Type class to be inherited by subclasses to give custom properties\n
	Custom Book class Example: `class Book(Type): prop, all = {'name': None, 'author': None, 'score': None, 'tags': []}, []`'''
	prop = {'name': None}; all = []  # prop is short for properties, dict provided by sub object; all = list of all loaded obj/works of this class, eg = incase user wishes to iterate through all books

	def __init__(self, *args, **kwargs) -> None:
		'''Applies args and kwargs to `self.__dict__` if kwarg is in `self.prop`'''
		for num, arg in enumerate(args):  # convert given args into kwargs
			if arg not in {'', None}:
				kwargs[tuple(self.prop.keys())[num]] = arg  # if arg is not blank then add arg into kwargs
		if kwargs['name'] == '':
			kwargs['name'] = self.__class__.all.__len__  # if no name was provided use number
		self.__dict__.update(self.prop); Type.all.append(self); self.__class__.all[kwargs['name']] = self  # set self properties to default property values; add self to Works.all; add self to it's class' all dict with name as key
		for key, val in kwargs.items():  # for every kwarg given
			if key in self.__dict__:  # if key of kwarg is in properties
				if type(val) is tuple:
					val = list(val)  # if given val is a tuple then turn given val into a list
				if type(val) is list and type(self.prop[key]) is not list:  # if given val is list and default val is not list then
					if len(val) > 1:
						raise TypeError('unexpected multiple values within array')  # if multiple items in list then raise error
					else:
						val = val[0]  # else unlist list
				if type(self.prop[key]) is int and type(val) is not float:
					val = float(val)  # if default val is float and given val is not float then float given val
				if type(self.prop[key]) is list and type(val) is not list:
					val = [val]  # if default val is list and given val is not list then put given val in a list
				self.__dict__.update({key: val})  # change self property value to given kwarg value

	@classmethod
	def sort(cls, sort_by: str = 'name', look_up_table: dict = None, reverse: bool = True) -> None:
		'''sort `cls.all` by given dict, defaults to name'''
		if type(cls.all) is list:
			if sort_by == 'name':
				cls.all.sort(key=lambda work: work.name, reverse=reverse)  # for each work in class.all sort by work.name, untested
			else:
				cls.all.sort(key=lambda work: look_up_table[work.__dict__[sort_by]], reverse=reverse)  # for each work in class.all get work.sort_by and convert into number through look up table
		elif type(cls.all) is dict:
			if sort_by == 'name':
				cls.all = dict(sorted(cls.all.items(), lambda work: work[1].name, reverse=reverse))  # for each work in class.all sort by work.name, untested
			else:
				cls.all = dict(sorted(cls.all.items(), lambda work: look_up_table[work[1].__dict__[sort_by]], reverse=reverse))  # for each work in class.all get work.score and convert into number through look up table
	@classmethod
	def format(cls, base):
		for prop in cls.__dict__:
			if prop.__class__ is list and prop != 'tags':
				for num, obj in enumerate(prop):
					try:
						prop[num] = eval(obj)
					except Exception as e: print('Type.format:', e)

	async def update(self, session) -> list:
		''' Finds latest chapter from `self.links` then appends result to `self.lChs` as a tuple pair containing link index and latest chapter or an error code
		# Error Codes:
			1. -1 = parsing error
			2. -2 = link not supported
			3. -3 = site probably does not support scraping
			4. -4 = Connection Error
			5. -5 = no links
			6. -6 = update purposefully skiped
			7. -7 = failed to render link, probably timeout'''
		import re, bs4
		sites = {  # site:         find,   with,                       then find, and get,       split at, then get, render?; supported sites, might be outdated
			'readmanganato.com':  ('ul',    {'class': 'row-content-chapter'}, 'a',  'href',          '-',        -1, False),
			'www.webtoons.com':   ('ul',    {'id': '_listUl'},                'li', 'id',            '_',        -1, False),
			'manhuascan.com':     ('div',   {'class': 'list-wrap'},           'a',  'href',          '-|\.',      -2, False),
			'zahard.xyz':         ('ul',    {'class': 'chapters'},            'a',  'href',          '/',        -1, False),
			'www.royalroad.com':  ('table', {'id':    'chapters'},            None, 'data-chapters', ' ',         0, False),
			'1stkissmanga.io':    ('li',    {'class': 'wp-manga-chapter'},    'a',  'href',          '-|/',      -2, False),
			'comickiba.com':      ('li',    {'class': 'wp-manga-chapter'},    'a',  'href',          '-|/',      -2,  True),
			'www.manga-raw.club': ('ul',    {'class': 'chapter-list'},        'a',  'href',          '-',        -3,  True)}
		sites['manganato.com'] = sites['readmanganato.com']
		sites['nitroscans.com'] = sites['anshscans.org'] = sites['comickiba.com']
		sites['www.mcreader.net'] = sites['www.manga-raw.club']

		self.lChs = []  # latest chapters, format: (link number, latest chapter from that link)
		try:
			if self.links == []: raise TypeError  # if no links
		except TypeError as e: self.lChs.append((-1, -5, e)); return self.lChs  # then return -5 error "code"
		try:
			if ('do not check for updates' in self.tags) or ('Complete' in self.tags and 'Read' in self.tags) or ('Complete' in self.tags and 'Oneshot' in self.tags): self.lChs.append((-1, -6)); return self.lChs
		except TypeError as e: print(e)  # then pass

		for num, link in enumerate(self.links):  # for each link
			site = link.split('/')[2]

			if site in sites:  # if site is supported
				try: link = await session.get(link)  # connecting to the site
				except Exception as e: self.lChs.append((num, -4, e))  # connection error
				else:
					try:
						if sites[site][6]:  # if needs to be rendered
							if __debug__: print('rendering', self.name, '-', site)
							await link.html.arender(retries=2, wait=1, sleep=2, timeout=20, reload=True)
							if __debug__: print('done rendering', self.name, '-', site)
					except Exception as e: print('failed to render: ', self.name, ' - ', site, ', ', e, sep=''); self.lChs.append((num, -7, e))
					else:
						try:
							link = bs4.BeautifulSoup(link.html.html, 'html.parser')  # link = bs4 object with link html
							if (sites[site][2] is None) and (sites[site][3] is None): link = link.find(sites[site][0], sites[site][1]).contents[0]  # if site does not require second find and the contents are desired: get contents of first tag with specified requirements
							elif sites[site][2] is None: link = link.find(sites[site][0], sites[site][1]).get(sites[site][3])  # if site does not require second find and tag attribute is desired: get specified attribute of first tag with specified attribute
							else: link = link.find(sites[site][0], sites[site][1]).find(sites[site][2]).get(sites[site][3])  # else: get specified attribute of first specified tag under the first tag with specified attribute
						except AttributeError: self.lChs.append((num, -1))  # else there was a parsing error: append link index with error code to lChs
						else: self.lChs.append((num, float(re.split(sites[site][4], link)[sites[site][5]])))  # else link parsing went fine: extract latest chapter from link using lookup table
			else: self.lChs.append((num, -2))  # else: site is not supported, append link index with error code to lChs

		self.lChs.sort(key=lambda lChs: lChs[1], reverse=True)  # sort latest chapters based on lastest chapter
		return self.lChs
	def __iter__(self) -> object:
		return self  # required for to iter over
	def __str__(self) -> str:
		return '<' + self.__class__.__name__ + ' Object: {' + ', '.join([f'{key}: {val}' for key, val in self.__dict__.items() if key != 'name' and val != []]) + '}>'  # returns self in str format
	def __repr__(self) -> str:
		return f'<{self.name}>'  # represent self as self.name between <>
	def asdict(self) -> dict:
		return {**{'format': self.__class__.__name__}, **{key: val for key, val in self.__dict__.items() if val not in ([], "None") if key != 'lChs'}}  # convert attributes to a dictionary


class Fandom(Type):
	prop = {'name': None, 'tags': [], 'children': []}; all = []
class Author(Type):
	prop = {'name': None, 'links': [], 'works': [], 'score': None, 'tags': []}; all = []
class Series(Type):
	prop = {'name': None, 'links': [], 'author': None, 'works': [], 'fandom': [], 'score': None, 'tags': []}; all = []
class Manga(Type):
	prop = {'name': None, 'links': [], 'chapter': 0, 'series': None, 'author': None, 'score': None, 'tags': []}; all = []
class Anime(Type):
	prop = {'name': None, 'links': [], 'episode': 0, 'series': None, 'score': None, 'tags': []}; all = []
class Text(Type):
	prop = {'name': None, 'links': [], 'chapter': 0, 'fandom': None, 'author': None, 'series': None, 'score': None, 'tags': []}; all = []
class Link(Type):
	prop = {'name': None, 'site': None}; all = []


def main(null, dir=os.getcwd().replace('\\', '/'), settings_file='settings.yaml', *args):
	del null; os.chdir(dir)
	settings = load_settings(settings_file)
	gui = GUI(settings, dir)
	file = gui.mode_loading(settings)


def load_settings(settings_file: str):  # setup
	import ruamel.yaml; yaml = ruamel.yaml.YAML(); yaml.indent(mapping=4, sequence=4, offset=2); yaml.default_flow_style = None  # setup yaml
	settings: dict = {}  # change working directory to dir
	default_settings = {'theme': "awbreezedark", 'font': ("OCR A Extended", 8), 'hide_unupdated_works': True, 'hide_works_with_no_links': True, 'sort_by': "score", 'scores': {'no Good': -1, 'None': 0, 'ok': 1, 'ok+': 1.1, 'decent': 1.5, 'Good': 2, 'Good+': 2.1, 'Great': 3}, 'to_display': {'Manga': {'nChs': 'New Chapters', 'chapter': 'Current Chapter', 'tags': 'Tags'}}, 'default_column_width': 45, 'window_size': (640, 360), 'total_updaters': 3, 'total_renderers': 1, 'webbrowser_executable': 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'webbrowser_arg': '--profile-directory="Default" "%l"', 'backup_directory': '/backup'}  # set default settings
	try:
		with open(settings_file, 'r') as file:
			settings = yaml.load(file)
	except FileNotFoundError as e:
		print(e)
	for setting, value in default_settings.items():
		if setting not in settings:
			settings[setting] = value
	with open(settings_file, 'w') as file:
		yaml.dump(settings, file)
	return settings
def load_file(file: str) -> str:
	'Runs `add_work(work)` for each work in file specified then returns the name of the file loaded'
	import json
	def add_work(format: str | Type, *args, **kwargs) -> Type:
		'formats `Type` argument and returns the created object'
		if format.__class__ is str: format = eval(format)  # if the format is a string, turn in into an object
		return format(*args, **kwargs)  # return works object
	with open(file, 'r') as file:
		json.load(file, object_hook=lambda kwargs: add_work(**kwargs))
		return file.rstrip('.json')


class GUI():
	def __init__(self, settings, dir) -> None:
		import tkinter as tk; from tkinter import ttk
		def root_quit(self, e: tk.Event) -> None:  # called when <enter> or <Double-1>
			def execute(entry_input=None) -> None:
				# nonlocal root, stringVar, label, tree, entry, button, file, load_file, save_file, open_url, add_work, root_quit, tree_open, close_tree  # make gui elements and functions available to user
				if entry_input is None: entry_input = stringVar.get()  # if function was not called by root_quit: get entry input
				if entry_input == 'save': save_file(file + '.json')  # if command is save: save file
				elif entry_input == 'update_tree': pass  # not yet implemented
				elif entry_input == 'reupdate': threading.Thread(target=update_all, args=(Works.all,), daemon=True).start()  # if command is reupdate: re-update_all works
				elif entry_input == 'exit': root.destroy(); sys.exit()  # if command is exit: exit without saving
				else:  # if not command
					try: print(eval(entry_input, globals(), locals()))  # try and print eval input
					except Exception:  # if can't eval
						try: print(exec(entry_input, globals(), locals()))  # try and print exec input
						except Exception as e: print(e)  # if can't exec then print error
				entry.delete(0, 'end')  # clear entry

			if e.widget.__class__ == ttk.Treeview:  # if its tree that called
				if self.tree.identify_element(e.x, e.y) == '':  # if double click on nothing
					self.tree.selection_set()  # deselect all
					if self.open_node != '':
						self.tree.item(self.open_node, open=False); self.open_node = ''; self.tree_input = ''  # if there is an open node: close the open node; "clear" tree input
				else:
					self.tree_input = self.tree.selection()[0]  # else something was clicked on: set tree input to selected node
				self.event = 'tree'  # set event to tree
			elif e.widget.__class__ == ttk.Entry:  # if its entry that called
				self.event = 'entry'; self.entry_input = self.stringVar.get(); self.entry.delete(0, 'end');  # set event to entry; set entry_input stringVar; clear entry
				if len(self.entry_input) > 0 and self.entry_input[0] == '/':
					execute(self.entry_input.lstrip('/'))  # if entry_input is a command: execute() command
			self.root.quit()  # resume code
		def tree_open(self, e: tk.Event) -> None:  # runs when a tree node is opened
			node = self.tree.focus()  # set node to opened node
			if '.' in node:
				self.open_children.append(node)  # if is child node: take note
			else:
				if self.open_node != '':
					self.tree.item(self.open_node, open=False)  # close previous open node
				self.open_node = node  # record the new open node

		self.root = tk.Tk(); self.stringVar = tk.StringVar(); self.label = ttk.Label(self.root, justify='left', text='Mode: Reading'); self.tree = ttk.Treeview(self.root, selectmode='browse'); self.scroll = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview); self.entry = ttk.Entry(self.root, textvariable=self.stringVar, font=settings['font']); self.button = ttk.Button(self.root, width=1); self.style = ttk.Style(self.root)  # setup GUI variables
		self.label.grid(row=0, column=0, columnspan=2, sticky='nesw'); self.tree.grid(row=1, column=0, columnspan=2, sticky='nesw'); self.scroll.grid(row=1, column=1, columnspan=1, sticky='nesw'); self.entry.grid(row=2, column=0, sticky='nesw'); self.button.grid(row=2, column=1)  # pack elements onto root
		self.root.title(__file__.split('\\')[-1].rstrip('.py')); self.root.columnconfigure(0, weight=1); self.root.columnconfigure(1, weight=0); self.root.rowconfigure(1, weight=1); self.root.geometry('{}x{}'.format(settings['window_size'][0], settings['window_size'][1]))  # configure root
		self.tree.bind('<Double-1>', lambda e: root_quit(self, e)); self.tree.bind('<Return>', lambda e: root_quit(self, e)); self.tree.bind('<<TreeviewOpen>>', tree_open); self.tree.configure(yscrollcommand=self.scroll.set); self.entry.bind('<Return>', lambda e: root_quit(self, e)); self.entry.focus_set()  # bind events to tree and entry; configure scrollbar to tree
		try:
			self.root.tk.eval(f'''package ifneeded tksvg 0.7 [list load [file join {dir + '/tksvg0.7'} tksvg07t.dll] tksvg]'''); self.root.tk.call('lappend', 'auto_path', dir + '/awthemes-10.3.0'); self.root.tk.call('package', 'require', settings['theme']); self.style.theme_use(settings['theme'])  # do style witchery to import tk theme, no idea what it actually does, found it somewhere online
		except tk.TclError as e:
			print('Could not load theme -', e)  # if style loading fails, print error and continue
		self.style.configure('Treeview', rowheight=settings['font'][1] * 2, font=settings['font']); self.style.configure('Treeview.Item', indicatorsize=0, font=settings['font']); self.style.configure('Treeview.Heading', font=settings['font']); self.style.configure('TLabel', font=settings['font'])  # configure treeview and style fonts

		self.open_node = ''
	def mode_loading(self, settings) -> None:
		import tkinter as tk; import itertools; mode = itertools.cycle(('Adding', 'Settings', 'Reading'))
		self.tree.heading('#0', text='File:', anchor='w'); self.button['command'] = lambda: self.label.configure(text='Mode: ' + mode.__next__())  # configure tree; configure button to cycle modes when pressed
		for num, file in enumerate([file for file in os.listdir() if file[-5:] == '.json']):
			self.tree.insert('', 'end', f'{num}.', text=f'{num}. ' + file.split('.json')[0])  # insert files to tree
		while not Type.all:  # while no works are loaded
			self.root.mainloop()  # wait until <double-1> or <enter>
			if self.event == 'tree' and self.tree_input != '':
				file = load_file(self.tree.item(self.tree_input, 'text').split(' ')[1] + '.json')  # if tree quit and something is selected: load selected file
			elif self.entry_input != '':  # else entry quit and something was entered
				try: file = load_file(self.tree.item(self.entry_input, 'text').split(' ')[1] + '.json')  # try to load file entry input references
				except tk.TclError:  # if entry input was not pointing to a tree node
					try:
						file = load_file(self.entry_input); load_file(self.entry_input + '.json')  # try to load file inputted from entry
					except FileNotFoundError:
						pass  # if fail wait for new input

		Type.sort(settings['sort_by'], settings[settings['sort_by'] + 's'])  # sort works.all by settings
		for subclass in Type.__subclasses__():
			subclass.format()  # connect works to series to authors to fandoms, etc. not yet implemented
		return file


# def update_all(works: list | tuple, pipe_enter, settings) -> None:
# 	'updates all works provided'
# 	import asyncio
# 	from requests_html import AsyncHTMLSession
# 	updaters, renderers = asyncio.Semaphore(settings['total_updaters']), asyncio.Semaphore(settings['total_renderers'])

# 	async def update_each(num, work, session):
# 		async with updaters:
# 			pipe_enter.send((num, await work.update(session, renderers)))

# 	async def a_main(): session = AsyncHTMLSession(); await asyncio.gather(*[update_each(num, work, session) for num, work in enumerate(works)])

# 	asyncio.run(a_main())


# import json, itertools, subprocess; from multiprocessing import Process, Pipe

# global event, tree_input, entry_input, open_node, open_children, reading  # predeclare variables

# def load_file(file: str) -> None: 'Runs `add_work(work)` for each work in file specified'; f = open(file, 'r'); json.load(f, object_hook=lambda kwargs: add_work(**kwargs)); f.close(); return file.rstrip('.json')
# def save_file(file: str) -> None: 'Saves all works in `Works.all` to file specified'; file = open(file, 'w'); json.dump(Works.all, file, indent='\t', default=lambda work: work.asdict()); file.close()
# def root_exit() -> None: nonlocal file; save_file(file + '.json'); root.destroy(); sys.exit()  # bound to WM_DELETE_WINDOW, runs on window close, saves to file loaded and exits program

# def open_url(link: str) -> None:
# 	'opens url provided in chrome profile specified in settings'
# 	try: subprocess.run(f'"{settings["chrome_path"]}" --profile-directory="{settings["chrome_profile"]}" "{link}"')  # try to open link
# 	except FileNotFoundError as e: print(e); print('Incorrect Chrome Path')  # if chrome is not found: print error


# def update_tree() -> None:  # To-Do: rewrite
# 	# for num, work in enumerate(Works.all):
# 	# 	"updates work's node's and its links' column values"  # To-Do: re show works that have been hidden if there now is new chapters
# 	# 	try: work.lChs[0]
# 	# 	except (IndexError, AttributeError): continue  # if work has no links or has not yet been updated: skip
# 	# 	if work.lChs[0][1] < 0: nChs = work.lChs[0][1]  # if all work's links are errors: set nChs to error code
# 	# 	else:  # else work has updated without error
# 	# 		nChs = work.lChs[0][1] - work.chapter  # set nChs to lastest chapter - current chapter
# 	# 		if settings['hide_unupdated_works'] and not nChs > 0: tree.detach(num)  # if hide_unupdated_works = True and there are no new chapters
# 	# 	if 'nChs' in tree['columns']:  # if tree has a new chapters column
# 	# 		tree.set(num, 'nChs', f'{nChs:g}')  # set its new chapters to new chapters
# 	# 		for link_pair in work.lChs:  # for each of its links
# 	# 			if link_pair[1] >= 0: tree.set(f'{num}.{link_pair[0]}', 'nChs', f'{link_pair[1] - work.chapter:g}')  # if link has updated without error: set the new chapters to new chapters
# 	# 	if 'chapter' in tree['columns']:  # if tree has a chapters column
# 	# 		tree.set(num, 'chapter', f'{work.chapter:g}')  # set its chapters to work.chapter
# 	# 		for link_pair in work.lChs: tree.set(f'{num}.{link_pair[0]}', 'chapter', f'{link_pair[1]:g}')  # for each of its links: set chapter to the link's latest chapter
# 	# 	if 'lChs' in tree['columns']: tree.set(num, 'lChs', f'{work.lChs[0][1]:g}')  # if tree has a latest chapters column: set its latest chapter to its latest chapter
# 	# root.after(10, update_tree)
# 	pass

# def update_nodes(pipe_exit):
# 	while pipe_exit.poll():
# 		num, lChs = pipe_exit.recv(); work = Works.all[num]; work.lChs = lChs; del lChs
# 		try: tree.focus(num)
# 		except Exception as e: print('update_nodes() cannot focus:', e, work); continue
# 		update_node(num, work)
# 	root.after(100, update_nodes, pipe_exit)

# def update_node(num: int, work: Works):
# 	nonlocal settings
# 	nChs = work.lChs[0][1] - work.chapter  # set nChs to lastest chapter - current chapter
# 	if (settings['hide_unupdated_works'] and nChs == 0) or (settings['hide_works_with_no_links'] and work.lChs[0][1] == -5): tree.detach(num)
# 	else:
# 		if work.lChs[0][1] < 0: nChs = work.lChs[0][1]  # if all work's links are errors: set nChs to error code
# 		if 'nChs' in tree['columns']: tree.set(num, 'nChs', f'{nChs:g}')  # if tree has a new chapters column: set its new chapters to new chapters
# 		if 'chapter' in tree['columns']: tree.set(num, 'chapter', f'{work.chapter:g}')  # if tree has a chapters column: set its chapters to work.chapter
# 		if 'lChs' in tree['columns']: tree.set(num, 'lChs', f'{work.lChs[0][1]:g}')  # if tree has a latest chapters column: set its latest chapter to its latest chapter
# 		for link_pair in work.lChs:  # for each of its links:
# 			if link_pair[1] >= 0:  # if link is not error and has updated:
# 				if 'nChs' in tree['columns']: tree.set(f'{num}.{link_pair[0]}', 'nChs', f'{link_pair[1] - work.chapter:g}')  # if tree has a new chapters column: set new chapters to the link's new chapters
# 				if 'chapter' in tree['columns']: tree.set(f'{num}.{link_pair[0]}', 'chapter', f'{link_pair[1]:g}')  # if tree has a chapters column: set chapter to the link's latest chapter


# def close_tree(to_close: list | tuple, to_open: str = None) -> None:
# 	'closes all nodes provided with the option of leaving one open'
# 	for node in to_close: tree.item(node, open=False)  # for all open nodes that need closing: close node
# 	if to_open is not None: tree.item(to_open, open=True)  # of a node needs to be opened: open node


# 	del num, dir; tree_input = ''; entry_input = ''; open_node = ''; open_children = []; mode = label.cget('text')  # delete obsolete variables; (re)set variables that need reseting

# def reading_mode():
# 	# setup for reading mode
# 	if mode == 'Mode: Reading':  # if is reading mode
# 		tree.delete(*tree.get_children()); tree['columns'] = tuple(settings['to_display'][file])  # clear tree; set tree columns
# 		tree.heading('#0', text='Name', anchor='w'); tree.column('#0', minwidth=30, width=tree.winfo_width() - settings['default_column_width'] * len(settings['to_display'][file]))  # configure default column text and width
# 		button['command'] = lambda: print('not yet implemented'); root.protocol('WM_DELETE_WINDOW', root_exit)  # configure button press; bind window close to root_exit()
# 		for key, val in settings['to_display'][file].items():  # for each column need to be displayed based on settings
# 			tree.heading(key, text=val, anchor='w'); tree.column(key, minwidth=30, width=settings['default_column_width'])  # configure text and width
# 		for num, work in enumerate(Works.all):  # for all works
# 			try:
# 				if settings['hide_unupdated_works'] and 'Complete' in work.tags and 'Read' in work.tags: continue  # if work is completed and read(past tense) and hide_unupdated_works = True: then skip it
# 			except AttributeError: pass  # if work does not have a tags property then don't bother with the link above
# 			tree.insert('', 'end', num, text=f'{num}. {work.name}')  # insert it into tree
# 			for key in settings['to_display'][file]:  # for each column value that needs to be set
# 				if key in {'nChs', 'lChs'}: continue  # skip nChs abd lChs, will be set later, To-Do: turn this into a try: except for series without chapters at stuff
# 				elif type(work.__dict__[key]) is list: tree.set(num, key, ', '.join(work.__dict__[key]))  # if is list, convert into string then set column value to it
# 				else: tree.set(num, key, f'{work.__dict__[key]:g}')  # else is not list: set column value to work.prop value, defined in settings
# 			try:  # if work has link attribute
# 				for link_num, link in enumerate(work.links):  # for each of work's links
# 					tree.insert(num, 'end', f'{num}.{link_num}', text='\t' + link.lstrip('https://'))  # insert it with the link without the https:// as text
# 			except AttributeError: pass  # else just skip
# 		pipe_exit, pipe_enter = Pipe(False)
# 		Process(target=update_all, args=(Works.all, pipe_enter, settings), daemon=True).start()
# 		root.after(100, update_nodes, pipe_exit)
# 		del key, val, num, work, link_num, link, mode   # delete obsolete variables
# # reading mode
# 		while True:
# 			root.mainloop()  # wait until <double-1> or <enter>
# 			entry.focus_set()  # set the focus to entry so the user can type in stuff without having to select the entry
# 			if reading:  # if work has been selected
# 				selected_parent: int = reading.split('.')[0]; selected_work = Works.all[int(selected_parent)]
# 				if event == 'tree' and tree_input != '':  # if user double clicked and something is selected
# 					if tree_input == selected_parent: selected_work.chapter = selected_work.lChs[0][1]  # if same parent is reselected: set chapter to latest chapter
# 					elif tree_input == reading:  # elif same link is selected
# 						if tree.set(tree_input, 'nChs') == '': close_tree(open_children); continue  # if link has not yet been updated: close link node; do nothing
# 						else: selected_work.chapter = tree.set(tree_input, 'chapter')  # else: set chapter to link's latest chapter
# 					elif tree_input.split('.')[0] == selected_parent: open_url(tree.item(tree_input, 'text')); close_tree(open_children, tree_input); reading = tree_input; continue  # elif diffrent link is selected and previous selection is part of the same work: open new selected link; close other open link nodes; update reading var; continue
# 					else: reading = False  # else if some other work or other work's link was selected: take note (skip exiting reading mode and proceed to open selected link)
# 				elif event == 'entry' and entry_input != '':  # if user pressed enter on entry and enter is not blank
# 					try: entry_input = float(entry_input)  # if entry enter is invalid
# 					except ValueError: continue  # continue
# 					if entry_input == 0.0:  # if entry enter is 0
# 						if '.' in reading: selected_work.chapter = tree.set(reading, 'chapter')  # if link was selected then set chapter to link's latest chapter
# 						else: selected_work.chapter = selected_work.lChs[0][1]  # else set chapter to latest chapter
# 					else: selected_work.chapter = entry_input  # else set chapter whatever was entered
# 				if reading:  # if previously noted else was not executed
# 					label['text'] = 'Mode: Reading'; tree.selection_set(); close_tree(open_children); tree.item(open_node, open=False); open_node = ''; update_node(selected_parent, selected_work); reading = False; continue  # exit "reading mode part 2" and close + deselect previously selected node + open link nodes
# 			if event == 'tree' and tree_input == '': continue  # if nothing was double clicked then do nothing
# 			if event == 'entry':  # if <enter>, select tree node based on number entered
# 				if entry_input == '': tree.selection_set(); tree.item(open_node, open=False); open_node = ''; continue  # if nothing was entered: deselect and close all nodes; do nothing
# 				else:
# 					try: tree.selection_set(entry_input); tree_input = entry_input  # try to set selection to whatever is entered in entry
# 					except tk.TclError as e: print(e); continue  # if entry is gibberish do nothing
# 			if '.' in tree_input: open_url(tree.item(tree_input, 'text'))  # if node is a link node: open url from node text
# 			else: open_url(Works.all[int(tree_input)].links[0])  # else set link to "first" link of selected node
# 			reading = tree_input; tree_input = tree_input.split('.')[0]; tree.selection_set(tree_input); label['text'] = f'Reading: {Works.all[int(tree_input)].name}'  # set reading to selected node; set tree_input to work even if link was selected; set tree.selection to tree_input; change label
# 			tree.item(tree_input, open=True); open_node = tree_input  # open record work node
if __name__ == '__main__':
	main(*sys.argv)
