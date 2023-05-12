import os


class Works():  # works refer to all works of literature including books, anime, fanfic, etc.
	''' Base works class to be inherited by subclasses to give custom properties\n
	Custom Book class Example: `class Book(Works): prop, all = {'name': None, 'author': None, 'score': None, 'tags': []}, []`'''
	prop, all = {'name': None}, []  # prop is short for properties, dict provided by sub object; all = list of all loaded obj/works of this class, eg = incase user wishes to iterate through all books

	def __init__(self, *args, **kwargs) -> None:
		'''Applies args and kwargs to `self.__dict__` if kwarg is in `self.prop`'''
		for num, arg in enumerate(args):  # convert given args into kwargs
			if arg not in {'', None}: kwargs[tuple(self.prop.keys())[num]] = arg  # if arg is not blank then add arg into kwargs
		self.__dict__.update(self.prop); Works.all.append(self); self.__class__.all[kwargs['name']] = self  # set self properties to default property values; add self to Works.all; add self to it's class' all dict with name as key
		for key, val in kwargs.items():  # for every kwarg given
			if key in self.__dict__:  # if key of kwarg is in properties
				if type(val) is tuple: val = list(val)  # if given val is a tuple then turn given val into a list
				if type(val) is list and type(self.prop[key]) is not list:  # if given val is list and default val is not list then
					if len(val) > 1: raise TypeError('unexpected multiple values within array')  # if multiple items in list then raise error
					else: val = val[0]  # else unlist list
				if type(self.prop[key]) is int and type(val) is not float: val = float(val)  # if default val is float and given val is not float then float given val
				if type(self.prop[key]) is list and type(val) is not list: val = [val]  # if default val is list and given val is not list then put given val in a list
				self.__dict__.update({key: val})  # change self property value to given kwarg value

	def __iter__(self) -> object: return self  # required for to iter over
	def __str__(self) -> str: return '<' + self.__class__.__name__ + ' Object: {' + ', '.join([f'{key}: {val}' for key, val in self.__dict__.items() if key != 'name' and val != []]) + '}>'  # returns self in str format
	def __repr__(self) -> str: return f'<{self.name}>'  # represent self as self.name between <>
	def asdict(self) -> dict: return {**{'format': self.__class__.__name__}, **{key: val for key, val in self.__dict__.items() if val not in ([], "None") if key != 'lChs'}}  # convert attributes to a dictionary

	@classmethod
	def sort(cls, sort_by: str = 'name', look_up_table: dict = None, reverse: bool = True) -> None:
		'''sort `cls.all` by given dict, defaults to name'''
		if type(cls.all) is list:
			if sort_by == 'name': cls.all.sort(key=lambda work: work.name, reverse=reverse)  # for each work in class.all sort by work.name, untested
			else: cls.all.sort(key=lambda work: look_up_table[work.__dict__[sort_by]], reverse=reverse)  # for each work in class.all get work.sort_by and convert into number through look up table
		elif type(cls.all) is dict:
			if sort_by == 'name': cls.all = dict(sorted(cls.all.items(), lambda work: work[1].name, reverse=reverse))  # for each work in class.all sort by work.name, untested
			else: cls.all = dict(sorted(cls.all.items(), lambda work: look_up_table[work[1].__dict__[sort_by]], reverse=reverse))  # for each work in class.all get work.score and convert into number through look up table

	async def update(self, session) -> list:
		''' Finds latest chapter from `self.links` then appends result to `self.lChs` as a tuple pair containing link index and latest chapter or an error code
		# Error Codes:
			1. -1 = parsing error
			2. -2 = link not supported
			3. -3 = site probably does not support scraping
			4. -4 = Connection Error
			5. -5 = no links
			6. -6 = update purposefully skiped
			7. -7 = failed to render link, probably timeout
			8. -8 = whatever was extracted was not a number'''
		import re, bs4
		sites = {  # site:         find,   with,                       then find,       and get, split at, then get, render?; supported sites, might be outdated
			'www.royalroad.com':  ('table', {'id':    'chapters'},           None, 'data-chapters', ' ',    0, False),  # based on absolute chapter count, not chapter name
			'www.asurascans.com':           ('span',  {'class': 'epcur epcurlast'},    None,            None, ' ',    1, False),
			'www.webtoons.com':   ('ul',    {'id': '_listUl'},               'li',            'id', '_',   -1, False),
			'mangabuddy.com':     ('div',   {'class': 'latest-chapters'},     'a',          'href', '-',   -1, False),
			'mangapuma.com':      ('div',   {'id': 'chapter-list-inner'},     'a',          'href', '-',   -1, False),
			'harimanga.com':      ('ul',    {'class': 'main version-chap no-volumn'}, 'a',  'href', '-|/', -2, False),
			'zahard.xyz':         ('ul',    {'class': 'chapters'},            'a',          'href', '/',   -1, False),
			'www.manga-raw.club': ('ul',    {'class': 'chapter-list'},        'a',          'href', '-|/', -4, False),
			'bato.to':            ('span',  {'class': 'opacity-50'},        None,            None, ' ',     0, False),  # based on absolute chapter count, not chapter name
			'manganato.com':      ('ul',    {'class': 'row-content-chapter'}, 'a',          'href', '-',   -1, False),
			'comickiba.com':      ('li',    {'class': 'wp-manga-chapter'},    'a',          'href', '-|/', -2,  True)}
		sites['flamescans.org'] = sites['www.asurascans.com']
		sites['zinmanga.com'] = sites['harimanga.com']
		sites['www.mcreader.net'] = sites['www.manga-raw.club']
		sites['chapmanganato.com'] = sites['readmanganato.com'] = sites['manganato.com']
		sites['nitroscans.com'] = sites['anshscans.org'] = sites['comickiba.com']

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
						if sites[site][6]:
							if __debug__: print('rendering', self.name, '-', site)
							await link.html.arender(retries=2, wait=1, sleep=2, timeout=20, reload=True)
							if __debug__: print('done rendering', self.name, '-', site)
					except Exception as e: print('failed to render: ', self.name, ' - ', site, ', ', e, sep=''); self.lChs.append((num, -7, e))
					else:
						try:
							link = bs4.BeautifulSoup(link.html.html, 'html.parser')  # link = bs4 object with link html
							if (sites[site][2] is None) and (sites[site][3] is None): link = link.find(sites[site][0], sites[site][1]).contents[0]  # if site does not require second find and the contents are desired: get contents of first tag with specified requirements
							elif sites[site][2] is None: link = link.find(sites[site][0], sites[site][1]).get(sites[site][3])  # if site does not require second find and tag attribute is desired: get specified attribute of first tag with specified attribute
							elif sites[site][3] is None:
								print(link.find(sites[site][0], sites[site][1]).find(sites[site][2]).contents[0])
								link = link.find(sites[site][0], sites[site][1]).find(sites[site][2]).contents[0]  # if contents are desired: get contents
							else: link = link.find(sites[site][0], sites[site][1]).find(sites[site][2]).get(sites[site][3])  # else: get specified attribute of first specified tag under the first tag with specified attribute
						except AttributeError: self.lChs.append((num, -1))  # else there was a parsing error: append link index with error code to lChs
						else:
							try: self.lChs.append((num, float(re.split(sites[site][4], link)[sites[site][5]])))  # else link parsing went fine: extract latest chapter from link using lookup table
							except Exception as e: print('failed to extract lChs: ', self.name, ' - ', site, ', ', e, sep=''); self.lChs.append((num, -8, e))
			else: self.lChs.append((num, -2))  # else: site is not supported, append link index with error code to lChs

		self.lChs.sort(key=lambda lChs: lChs[1], reverse=True)  # sort latest chapters based on lastest chapter
		return self.lChs


class Fandom(Works): prop, all = {'name': None, 'tags': [], 'children': []}, {}
class Author(Works): prop, all = {'name': None, 'links': [], 'works': [], 'score': 'None', 'tags': []}, {}
class Series(Works): prop, all = {'name': None, 'links': [], 'author': 'None', 'works': [], 'fandom': [], 'score': 'None', 'tags': []}, {}
class Manga(Works): prop, all = {'name': None, 'links': [], 'chapter': 0, 'series': 'None', 'score': 'None', 'tags': []}, {}
class Anime(Works): prop, all = {'name': None, 'links': [], 'episode': 0, 'series': 'None', 'score': 'None', 'tags': []}, {}
class Text(Works): prop, all = {'name': None, 'links': [], 'chapter': 0, 'author': 'None', 'se;ries': 'None', 'score': 'None', 'tags': []}, {}


def update_all(works: list | tuple, pipe_enter) -> None:
	'updates all works provided'
	import asyncio
	from requests_html import AsyncHTMLSession

	async def update_each(num, work, session): pipe_enter.send((num, await work.update(session)))
	async def a_main(): session = AsyncHTMLSession(); await asyncio.gather(*[update_each(num, work, session) for num, work in enumerate(works)])

	asyncio.run(a_main(), debug=False)


def main(dir=os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')):
	import json, itertools, threading, json5, sys, subprocess
	from tkinter import ttk; import tkinter as tk
	from multiprocessing import Process, Pipe

	def load_file(file: str) -> None: 'Runs `add_work(work)` for each work in file specified'; f = open(file, 'r'); json.load(f, object_hook=lambda kwargs: add_work(**kwargs)); f.close(); return file.rstrip('.json')
	def save_file(file: str) -> None: 'Saves all works in `Works.all` to file specified'; file = open(file, 'w'); json.dump(Works.all, file, indent='\t', default=lambda work: work.asdict()); file.close()
	def root_exit() -> None: nonlocal file; save_file(file + '.json'); root.destroy(); sys.exit()  # bound to WM_DELETE_WINDOW, runs on window close, saves to file loaded and exits program

	def open_url(link: str) -> None:
		import webbrowser, pyperclip
		if os.name == 'posix':
			pyperclip.copy(link)
		else:
			try: subprocess.run(f'"{settings["chrome_path"]}" --profile-directory="{settings["chrome_profile"]}" "{link}"')  # try to open link
			except FileNotFoundError as e: print(e); print('Incorrect Chrome Path')  # if chrome is not found: print error
	def add_work(format: str | Works, *args, **kwargs) -> Works:
		'formats `format` argument and returns the created object'
		if type(format) is str: format = eval(format)  # if the format is a string, turn in into an object
		if format in (Author, Series): return 'Not yet implemented'
		return format(*args, **kwargs)  # return works object
	def update_nodes(pipe_exit):
		while pipe_exit.poll():
			num, lChs = pipe_exit.recv(); work = Works.all[num]; work.lChs = lChs; del lChs
			try: tree.focus(num)
			except Exception as e: print('update_nodes() cannot focus:', e, work); continue
			update_node(num, work)
		root.after(100, update_nodes, pipe_exit)
	def update_node(num: int, work: Works):
		nonlocal settings
		try:
			nChs = work.lChs[0][1] - work.chapter  # set nChs to lastest chapter - current chapter
		except AttributeError:
			nChs = -10
			work.lChs = [[-10, -10]]
		if (settings['hide_unupdated_works'] and nChs == 0) or (settings['hide_works_with_no_links'] and work.lChs[0][1] == -5): tree.detach(num)
		else:
			if work.lChs[0][1] < 0: nChs = work.lChs[0][1]  # if all work's links are errors: set nChs to error code
			if 'nChs' in tree['columns']: tree.set(num, 'nChs', f'{nChs:g}')  # if tree has a new chapters column: set its new chapters to new chapters
			if 'chapter' in tree['columns']: tree.set(num, 'chapter', f'{work.chapter:g}')  # if tree has a chapters column: set its chapters to work.chapter
			if 'lChs' in tree['columns']: tree.set(num, 'lChs', f'{work.lChs[0][1]:g}')  # if tree has a latest chapters column: set its latest chapter to its latest chapter
			for link_pair in work.lChs:  # for each of its links:
				if link_pair[1] >= 0:  # if link is not error and has updated:
					if 'nChs' in tree['columns']: tree.set(f'{num}.{link_pair[0]}', 'nChs', f'{link_pair[1] - work.chapter:g}')  # if tree has a new chapters column: set new chapters to the link's new chapters
					if 'chapter' in tree['columns']: tree.set(f'{num}.{link_pair[0]}', 'chapter', f'{link_pair[1]:g}')  # if tree has a chapters column: set chapter to the link's latest chapter
	def x(entry_input=None) -> None:  # called when button is press in reading mode
		nonlocal root, stringVar, label, tree, entry, button, file, load_file, save_file, open_url, add_work, root_quit, tree_open, close_tree  # make gui elements and functions available to user
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
	def root_quit(e: tk.Event) -> None:  # called when <enter> or <Double-1>
		nonlocal event, tree_input, entry_input, open_node
		if e.widget.__class__ == ttk.Treeview:  # if its tree that called
			if tree.identify_element(e.x, e.y) == '':  # if double click on nothing
				tree.selection_set()  # deselect all
				if open_node != '': tree.item(open_node, open=False); open_node = ''; tree_input = ''  # if there is an open node: close the open node; "clear" tree input
			else: tree_input = tree.selection()[0]  # else something was clicked on: set tree input to selected node
			event = 'tree'  # set event to tree
		elif e.widget.__class__ == ttk.Entry:  # if its entry that called
			event = 'entry'; entry_input = stringVar.get(); entry.delete(0, 'end');  # set event to entry; set entry_input stringVar; clear entry
			if len(entry_input) > 0 and entry_input[0] == '/': execute(entry_input.lstrip('/'))  # if entry_input is a command: execute() command
		root.quit()  # resume code
	def tree_open(e: tk.Event) -> None:  # runs when a tree node is opened
		nonlocal open_node, open_children
		node = tree.focus()  # set node to opened node
		if '.' in node: open_children.append(node)  # if is child node: take note
		else:
			if open_node != '': tree.item(open_node, open=False)  # close previous open node
			open_node = node  # record the new open node
	def close_tree(to_close: list | tuple, to_open: str = None) -> None:
		'closes all nodes provided with the option of leaving one open'
		for node in to_close: tree.item(node, open=False)  # for all open nodes that need closing: close node
		if to_open is not None: tree.item(to_open, open=True)  # of a node needs to be opened: open node
	def execute(entry_input=None) -> None:
		print('executing')
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


# setup
	os.chdir(dir)  # change working directory to dir
	event = ''; tree_input = ''; entry_input = ''; open_node = ''; open_children = []; reading = False  # predeclare variables
	settings = {'themes': ["awbreezedark"], 'font': ("OCR A Extended", 8), 'hide_unupdated_works': True, 'hide_works_with_no_links': True, 'sort_by': "score", 'scores': {'no Good': -1, 'None': 0, 'ok': 1, 'ok+': 1.1, 'decent': 1.5, 'Good': 2, 'Good+': 2.1, 'Great': 3}, 'to_display': {'Manga': {'nChs': 'New Chapters', 'chapter': 'Current Chapter', 'tags': 'Tags'}}, 'default_column_width': 45, 'window_size': (640, 360), 'webbrowser_executable': 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'webbrowser_arg': '--profile-directory="Default" "%l"', 'backup_directory': '/backup'}  # set default settings
	try: file = open('settings.json5', 'r'); settings.update(json5.load(file)); file.close()  # open settings file then replace default settings from file
	except FileNotFoundError as e: print(e)  # if file does not exits: pass
	with open('settings.json5', 'w') as file: json5.dump(settings, file, indent='\t')  # To-Do: find a way to also save comments

# setup GUI
	root = tk.Tk(); stringVar = tk.StringVar(); label = ttk.Label(root, justify='left', text='Mode: Reading'); tree = ttk.Treeview(root, selectmode='browse'); scroll = ttk.Scrollbar(root, orient="vertical", command=tree.yview); entry = ttk.Entry(root, textvariable=stringVar, font=settings['font']); button = ttk.Button(root, width=1); style = ttk.Style(root)  # setup GUI variables
	label.grid(row=0, column=0, columnspan=2, sticky='nesw'); tree.grid(row=1, column=0, columnspan=2, sticky='nesw'); scroll.grid(row=1, column=1, columnspan=1, sticky='nesw'); entry.grid(row=2, column=0, sticky='nesw'); button.grid(row=2, column=1)  # pack elements onto root
	root.title(__file__.split('\\')[-1].rstrip('.py')); root.columnconfigure(0, weight=1); root.columnconfigure(1, weight=0); root.rowconfigure(1, weight=1); root.geometry('{}x{}'.format(settings['window_size'][0], settings['window_size'][1]))  # configure root
	tree.bind('<Double-1>', root_quit); tree.bind('<Return>', root_quit); tree.bind('<<TreeviewOpen>>', tree_open); tree.configure(yscrollcommand=scroll.set); entry.bind('<Return>', root_quit); entry.focus_set()  # bind events to tree and entry; configure scrollbar to tree
	for theme in settings['themes']:
		try: root.tk.eval(f'''package ifneeded tksvg 0.7 [list load [file join {dir + '/tksvg0.7'} tksvg07t.dll] tksvg]'''); root.tk.call('lappend', 'auto_path', dir + '/awthemes-10.3.0'); root.tk.call('package', 'require', theme); style.theme_use(theme)  # do style witchery to import tk theme, no idea what it actually does, found it somewhere online
		except tk.TclError as e:
			print('Could not load theme', e)  # if style loading fails, print error and continue
			continue
		break
	style.configure('Treeview', rowheight=settings['font'][1] * 2, font=settings['font']); style.configure('Treeview.Item', indicatorsize=0, font=settings['font']); style.configure('Treeview.Heading', font=settings['font']); style.configure('TLabel', font=settings['font'])  # configure treeview and style fonts

	# style.configure('TButton', maxheight=2)  # i dont think this actually does anything

# loading mode, label is pre configured, To-Do: make so cant open nodes, not crash if file selected is invalid
	mode = itertools.cycle(('Adding', 'Settings', 'Reading'))
	tree.heading('#0', text='File:', anchor='w'); button['command'] = lambda: label.configure(text='Mode: ' + mode.__next__())  # configure tree; configure button to cycle modes when pressed
	for num, file in enumerate([file for file in os.listdir() if file[-5:] == '.json']): tree.insert('', 'end', f'{num}.', text=f'{num}. ' + file.split('.json')[0])  # insert files to tree
	while not Works.all:  # while no works are loaded
		root.mainloop()  # wait until <double-1> or <enter>
		if event == 'tree' and tree_input != '': file = load_file(tree.item(tree_input, 'text').split(' ')[1] + '.json')  # if tree quit and something is selected: load selected file
		elif entry_input != '':  # else entry quit and something was entered
			try: file = load_file(tree.item(entry_input, 'text').split(' ')[1] + '.json')  # try to load file entry input references
			except tk.TclError:  # if entry input was not pointing to a tree node
				try: file = load_file(entry_input); load_file(entry_input + '.json')  # try to load file inputted from entry
				except FileNotFoundError: pass  # if fail wait for new input

	Works.sort(settings['sort_by'], settings[settings['sort_by'] + 's'])  # sort works.all by settings
	# Works.format()  # connect works to series to authors to fandoms, etc. not yet implemented

	del num, dir; tree_input = ''; entry_input = ''; open_node = ''; open_children = []; mode = label.cget('text')  # delete obsolete variables; (re)set variables that need reseting

# setup for reading mode
	if mode == 'Mode: Reading':  # if is reading mode
		tree.delete(*tree.get_children()); tree['columns'] = tuple(settings['to_display'][file])  # clear tree; set tree columns
		tree.heading('#0', text='Name', anchor='w'); tree.column('#0', minwidth=30, width=tree.winfo_width() - settings['default_column_width'] * len(settings['to_display'][file]))  # configure default column text and width
		button['command'] = lambda: print('not yet implemented'); root.protocol('WM_DELETE_WINDOW', root_exit)  # configure button press; bind window close to root_exit()
		for key, val in settings['to_display'][file].items():  # for each column need to be displayed based on settings
			tree.heading(key, text=val, anchor='w'); tree.column(key, minwidth=30, width=settings['default_column_width'])  # configure text and width
		for num, work in enumerate(Works.all):  # for all works
			try:
				if settings['hide_unupdated_works'] and 'Complete' in work.tags and 'Read' in work.tags: continue  # if work is completed and read(past tense) and hide_unupdated_works = True: then skip it
			except AttributeError: pass  # if work does not have a tags property then don't bother with the link above
			tree.insert('', 'end', num, text=f'{num}. {work.name}')  # insert it into tree
			for key in settings['to_display'][file]:  # for each column value that needs to be set
				if key in {'nChs', 'lChs'}: continue  # skip nChs abd lChs, will be set later, To-Do: turn this into a try: except for series without chapters at stuff
				elif type(work.__dict__[key]) is list: tree.set(num, key, ', '.join(work.__dict__[key]))  # if is list, convert into string then set column value to it
				else: tree.set(num, key, f'{work.__dict__[key]:g}')  # else is not list: set column value to work.prop value, defined in settings
			try:  # if work has link attribute
				for link_num, link in enumerate(work.links):  # for each of work's links
					tree.insert(num, 'end', f'{num}.{link_num}', text='\t' + link.lstrip('https://'))  # insert it with the link without the https:// as text
			except AttributeError: pass  # else just skip
		pipe_exit, pipe_enter = Pipe(False)
		Process(target=update_all, args=(Works.all, pipe_enter), daemon=True).start()
		root.after(100, update_nodes, pipe_exit)
		del key, val, num, work, link_num, link, mode   # delete obsolete variables

# reading mode
		while True:
			root.mainloop()  # wait until <double-1> or <enter>
			entry.focus_set()  # set the focus to entry so the user can type in stuff without having to select the entry
			if reading:  # if work has been selected
				selected_parent: int = reading.split('.')[0]; selected_work = Works.all[int(selected_parent)]
				if event == 'tree' and tree_input != '':  # if user double clicked and something is selected
					if tree_input == selected_parent: selected_work.chapter = selected_work.lChs[0][1]  # if same parent is reselected: set chapter to latest chapter
					elif tree_input == reading:  # elif same link is selected
						if tree.set(tree_input, 'nChs') == '': close_tree(open_children); continue  # if link has not yet been updated: close link node; do nothing
						else: selected_work.chapter = tree.set(tree_input, 'chapter')  # else: set chapter to link's latest chapter
					elif tree_input.split('.')[0] == selected_parent: open_url(tree.item(tree_input, 'text')); close_tree(open_children, tree_input); reading = tree_input; continue  # elif diffrent link is selected and previous selection is part of the same work: open new selected link; close other open link nodes; update reading var; continue
					else: reading = False  # else if some other work or other work's link was selected: take note (skip exiting reading mode and proceed to open selected link)
				elif event == 'entry' and entry_input != '':  # if user pressed enter on entry and enter is not blank
					try: entry_input = float(entry_input)  # if entry enter is invalid
					except ValueError: continue  # continue
					if entry_input == 0.0:  # if entry enter is 0
						if '.' in reading: selected_work.chapter = tree.set(reading, 'chapter')  # if link was selected then set chapter to link's latest chapter
						else: selected_work.chapter = selected_work.lChs[0][1]  # else set chapter to latest chapter
					else: selected_work.chapter = entry_input  # else set chapter whatever was entered
				if reading:  # if previously noted else was not executed
					label['text'] = 'Mode: Reading'; tree.selection_set(); close_tree(open_children); tree.item(open_node, open=False); open_node = ''; update_node(selected_parent, selected_work); reading = False; continue  # exit "reading mode part 2" and close + deselect previously selected node + open link nodes

			if event == 'tree' and tree_input == '': continue  # if nothing was double clicked then do nothing
			if event == 'entry':  # if <enter>, select tree node based on number entered
				if entry_input == '': tree.selection_set(); tree.item(open_node, open=False); open_node = ''; continue  # if nothing was entered: deselect and close all nodes; do nothing
				else:
					try: tree.selection_set(entry_input); tree_input = entry_input  # try to set selection to whatever is entered in entry
					except tk.TclError as e: print(e); continue  # if entry is gibberish do nothing
			if '.' in tree_input: open_url(tree.item(tree_input, 'text'))  # if node is a link node: open url from node text
			else: open_url(Works.all[int(tree_input)].links[0])  # else set link to "first" link of selected node

			reading = tree_input; tree_input = tree_input.split('.')[0]; tree.selection_set(tree_input); label['text'] = f'Reading: {Works.all[int(tree_input)].name}'  # set reading to selected node; set tree_input to work even if link was selected; set tree.selection to tree_input; change label
			tree.item(tree_input, open=True); open_node = tree_input  # open record work node


def get_lchs(link: str) -> list:
	from multiprocessing import Process, Pipe
	pipe_exit, pipe_enter = Pipe(False)
	tmp = Manga(name='debug', links=link)
	# Process(target=update_all, args=(Works.all, pipe_enter)).start()
	# print(pipe_exit.recv())
	update_all(Works.all, pipe_enter)
	return tmp.lChs


if __name__ == '__main__':
	main()
	# print(get_lchs('https://bato.to/title/104579'))
