# Version: 3.4.2
import asyncio, os
from nicegui import app, ui
from nicegui.events import GenericEventArguments
from typing import Any, Iterable
from functools import partial as wrap
from stuff import Dict
from rich.console import Console; console = Console()
from rich.traceback import install; install(width=os.get_terminal_size().columns)

class Work():
	''' Base Type class to be inherited by subclasses to give custom properties\n
	Custom Book class Example: `class Book(Type): all = {}; prop = {'name': None, 'author': None, 'score': None, 'tags': []}`'''
	prop: dict = {'name': None}; all: list | dict = []  # prop is short for properties, dict provided by sub object; all = list of all loaded obj/works of this class, eg = incase user wishes to iterate through all books
	def __init__(self, *args: list, **kwargs: dict) -> None:
		'''Applies args and kwargs to `self.__dict__` if kwarg is in `self.prop`'''
		# convert args from list to dict then update them to kwargs
		kwargs.update({tuple(self.prop.keys())[num]: arg for num, arg in enumerate(args) if arg not in {'', None, *kwargs.values()}})  # type: ignore
		# if no name was provided use number as name
		if kwargs['name'] == '': kwargs['name'] = self.__class__.all.__len__  # type: ignore
		# set self properties to default property values
		self.__dict__.update(self.prop)
		# for every kwarg, format it and update `self.__dict__` with it
		for key, val in kwargs.items():
			# if key of kwarg is in properties
			if key in self.__dict__:
				# if given val is a tuple then turn given val into a list
				if val.__class__ is tuple: val = list(val)
				# if given val is list and default val is not list then unlist list
				if val.__class__ is list and type(self.prop[key]) is not list:
					# if multiple items in list then raise error
					if len(val) > 1:
						raise TypeError('unexpected multiple values within array')
					# else unlist list
					else:
						val = val[0]
				# if default val is list and given val is not list then put given val in a list
				elif self.prop[key].__class__ is list and val.__class__ is not list: val = [val]
				# if default val is int or float and given val is not float then float given val
				if self.prop[key].__class__ in (int, float) and type(val) not in (int, float): val = float(val)
				# if default val is int and given val is a decimalles (without decimals) float : convert to int
				if val.__class__ is float and int(val) == val:
					val = int(val)
				# change self property value to given kwarg value
				self.__dict__.update({key: val})
		# if self has links then turn links into Link objects
		if 'links' in self.prop:
			for num, link in enumerate(self.links):  # type: ignore
				self.links[num] = Link(link, self)  # type: ignore
	def update(self, what='chapter', source='links'):
		self.__dict__[what] = max([link.latest for link in self.__dict__[source] if not issubclass(link.latest.__class__, Exception)])
		if what == 'chapter' and source == 'links':
			for link in self.links:
				link.re()
	@classmethod
	def sort(cls, sort_by: str = 'name', look_up_table: dict | None = None, reverse: bool = True) -> None:
		'''sort `cls.all` by given dict, defaults to name'''
		works = cls.all
		# if `works` is a dict, convert it to a list
		if type(works) is dict:
			works = works.values()
		# sort
		if sort_by == 'name':
			# for each work in `works` sort by `work.name`
			works.sort(key=lambda work: work.name, reverse=reverse)
		elif look_up_table is not None:
			# for each work in `works` get `work.sort_by` and convert into number through look up table
			works.sort(key=lambda work: look_up_table[work.__dict__[sort_by]], reverse=reverse)
		# if `cls.all` is a dict, convert it back to a dict
		if type(cls.all) is dict:
			work = {work.name: work for work in works}
		cls.all = works
	def asdict(self) -> dict:
		'returns `self` as a dictionary'
		return {**{'format': self.__class__.__name__}, **{key: val for key, val in self.__dict__.items() if val not in ([], "None", None) if key != 'lChs'}}  # convert attributes to a dictionary
	def __iter__(self) -> object: return self  # required for to iter over for some reason
	def __str__(self) -> str:
		'returns `self` in `str` format'
		return '<' + self.__class__.__name__ + ' Object: {' + ', '.join([f'{key}: {val}' for key, val in self.__dict__.items() if key != 'name' and val != []]) + '}>'
	def __repr__(self) -> str:
		'represent `self` as `self.name` between <>'
		return f'<{self.name}>'  # type: ignore
class Manga(Work): prop = {'name': None, 'links': [], 'chapter': 0, 'series': None, 'author': None, 'score': None, 'tags': []}
class Text(Work): prop = {'name': None, 'links': [], 'chapter': 0, 'series': None, 'author': None, 'score': None, 'tags': []}
class Series(Work): prop = {'name': None, 'links': [], 'volume': 0, 'author': None, 'score': None, 'tags': []}
class Link():
	def __init__(self, link: str, parent: Work) -> None:
		self.site = link.split('/')[2]
		self.link = link
		self.parent = parent
		self.new = self.latest = ''
	async def update(self, renderers: asyncio.Semaphore, sites: dict, tags_to_skip: list, async_session) -> float | Exception:
		'''Finds latest chapter from `self.link` then sets result or an error code to `self.latest`
		# Error Codes:
			-999.1 = site not supported
			-999.2 = Connection Error
			-999.3 = rendering error, probably timeout
			-999.4 = parsing error
			-999.5 = whatever was extracted was not a number'''
		import re, bs4
		# if site is supported
		if self.site not in sites:
			self.latest = Exception('site not supported')  # site not supported
			return self.re(-999.1)
		# variables
		link = self.link
		sites = sites[self.site]
		# if tags specified in settings are in work, skip
		if 'tags' in self.parent.prop:
			# for each tag/list of tags that are to be skipped
			for tag in tags_to_skip:
				# if tag is str and in work, "skip"
				if tag.__class__ is str and tag in self.parent.tags:
					self.latest = Exception('skipped')
					return self.re(0)
				# if tag is list and all tags in list are in work
				elif tag.__class__ is list and all([t in self.parent.tags for t in tag]):
					self.latest = Exception('skipped')
					return self.re(0)
		# tmp: special stuff for bato.to
		if self.site == 'bato.to': link = self.link.replace('title/', 'rss/series/') + '.xml'
		# connecting to site
		try:
			link = await async_session.get(link, follow_redirects=True)  # connecting to the site
			assert link.status_code == 200  # make sure connection was successful
		except Exception as e:  # connection error
			print('connection error:', self.link)
			console.print_exception(show_locals=True, width=os.get_terminal_size().columns)
			self.latest = e
			return self.re(-999.2)
		# if site needs to be rendered, render
		if sites[6]:
			try:
				print('rendering', self.link, '-', self.site)
				async with renderers:  # limit the number of works rendering at a time
					# render link
					async with link.async_render(reload=True, wait_until='networkidle'): pass
				print('done rendering', self.link, '-', self.site)
			except Exception as e:
				print('failed to render:', self.link)  # render error
				console.print_exception(show_locals=True, width=os.get_terminal_size().columns)
				self.latest = e
				return self.re(-999.3)
		# process link
		try:
			# convert link into bs4 object
			link = bs4.BeautifulSoup(link.content, 'lxml')
			# sites: find, with
			tmp = link.find(sites[0], sites[1])
			assert tmp is not None
			link = tmp
			# if sites: "then find" and "and get" = null
			if sites[2] == sites[3] == None:
				# get contents
				tmp = link.contents[0]
				assert tmp is not None
				link = tmp
			# if sites: "then find" = null
			elif sites[2] is None:
				# get sites: "and get"
				tmp = link.get(sites[3])
				assert tmp is not None
				link = tmp
			# sites: "then find" != null
			else:
				# find sites: "then find"
				tmp = link.find(sites[2])
				assert tmp is not None
				link = tmp
				# if sites: "and get" = null
				if sites[3] is None:
					# get contents
					tmp = link.get_text()
					assert tmp is not None
					link = tmp
				# else
				else:
					# get sites: "and get"
					tmp = link.get(sites[3])
					assert tmp is not None
					link = tmp
		except (AttributeError, AssertionError) as e:
			console.print_exception(show_locals=True, width=os.get_terminal_size().columns)
			self.latest = e  # parsing error
			return self.re(-999.4)
		# convert remaining html to float
		try:
			self.latest = float(re.split(sites[4], link)[sites[5]])  # else link parsing went fine: extract latest chapter from link using lookup table
			# convert latest chapter to int if has .0
			if float(self.latest) == self.latest:
				self.latest = float(self.latest)
		except Exception as e:
			console.print_exception(show_locals=True, width=os.get_terminal_size().columns)
			self.latest = e  # whatever was extracted was not a number
			return self.re(-999.5)

		return self.re()
	def re(self, new: int | float = None) -> int | float:
		'updates `self.new` from `new` arg or calculates if not provided, then returns `self.new`'
		if new is None:
			if not issubclass(self.latest.__class__, Exception):
				new = round(self.latest - self.parent.chapter, 4)
			else:
				new = self.new
		self.new = new
		return new
	def asdict(self):
		return self.link
	def __repr__(self) -> str:
		'represent `self` as `self.link` between <>'
		return f'<{self.link}>'  # type: ignore
class GUI():
	def _input(self) -> ui.input:
		return ui.input(autocomplete=list(self.commands.keys())).on('keydown.enter', self.handle_input).props('square filled dense="dense" clearable clear-icon="close"').classes('flex-grow')
	def __init__(self, settings: dict, files: list[dict[str, str]]) -> None:
		# setup vars
		self.settings = settings
		self.open_tabs = Dict({'Main': Dict({'name': 'Main'})})
		self.commands = {'/help': 'list all commands', '/debug': 'open debug tab', '/save': 'save all works in tab', '/reupdate': 'reupdate all works in tab', '/reload': 'close and reopen tab (without saving)', '/refresh': 'redraw table', '/close': 'close current tab (without saving)', '/exit': 'exit MangaRock with save', '/quit': 'exit MangaRock without save'}
		# create tab holder
		with ui.tabs().props('dense').on('update:model-value', self.switch_tab) as self.tabs:
			# create main tab
			tab = ui.tab('Main')
		# create panel holder
		with ui.tab_panels(self.tabs, value=tab) as self.panels:
			# create main panel
			with ui.tab_panel('Main').style('height: calc(100vh - 84px); width: calc(100vw - 32px)'):
				ui.label('Choose File: ')
				gridOptions = {
					'defaultColDef': {
						'resizable': True,
						'suppressMenu': True,
					},
					'columnDefs': [
						{'headerName': 'Name', 'field': 'name', 'resizable': False},
					],
					'rowData': files,
					'rowHeight': self.settings['row_height'],
				}
				self.open_tabs.Main.grid = ui.aggrid(gridOptions, theme='alpine-dark' if self.settings['dark_mode'] else 'balham').style('height: calc(100vh - 164px)').on('cellDoubleClicked', self._file_opened)
				with ui.row().classes('w-full'):
					self._input()
					ui.button(on_click=lambda: print('placeholder')).props('square').style('width: 40px; height: 40px;')
		# setup semaphores for `update_all()`
		self.workers, self.renderers = asyncio.Semaphore(self.settings['workers']), asyncio.Semaphore(self.settings['renderers'])
		# css stuff and stuff
		ui.query('div').style('gap: 0')
		app.on_connect(self._on_reload)
	def jailbreak(self, grid: ui.aggrid, package: str = 'ag-grid-enterprise.min.js') -> ui.aggrid:
		'upgrade aggrid from community to enterprise'
		from nicegui.dependencies import register_library
		from pathlib import Path
		# if allready jailbroken, return grid
		if grid.libraries[0].name == 'ag-grid-enterprise':
			return grid
		# check if targeted library is ag-grid-community
		assert grid.libraries[0].name == 'ag-grid-community', 'Overwriting NiceGUI aggrid ran into a tiny problem, got wrong lib'
		# if self.library does not exist, register library
		try:
			self.library
		except AttributeError:
			self.library = register_library(Path(package).resolve())
		# overwrite aggrid library with enterprise
		grid.libraries[0] = self.library
		# return grid
		return grid
	def switch_tab(self, event: GenericEventArguments | Dict) -> None:
		self.tabs.props(f"model-value={event.args}")
		self.panels.props(f"model-value={event.args}")
	def generate_rowData(self, works: Iterable, rows: list, tab_name: str) -> list:
		'turns list of works into list of rows that aggrid can use and group'
		def format_rowData(row: dict, cols: dict) -> dict:
			'format row to make grouping work, "shuffles" the "data" "up" if "entry" "above" is empty'
			# remove the columns that are not grouped
			cols = dict(cols)
			for key, val in cols.copy().items():
				if val[1] != 'group':
					del cols[key]
			cols = list(cols.keys()) + ['link']
			# add link, name identifiers
			try:
				row['link'] += '‎'
			except KeyError:  # if row is not a link
				cols = cols[:-1]  # remove link from cols
			row['name'] += '‏'
			# shuffle "row"s "up"
			for col in range(len(cols)):  # for each col
				try:
					while row[cols[col]] is None:  # while the col is empty
						# shuffle cols "up"
						for mod in range(col, len(cols) - 1):
							row[cols[mod]] = row[cols[mod + 1]]
						# set last col to empty
						row[cols[-1]] = ' '
				except Exception as e:  # skip row if error, i think
					print('format_rowData error:', e)
			return row
		# for each work in works
		for num_work, work in enumerate(works):
			# if type of work has no links
			if 'links' not in work.prop:
				# add work to rows
				rows.append(work.__dict__)
				rows[-1]['id'] = num_work  # this line may be redundant
			# if work has no links
			elif work.links == []:
				# if hide_works_with_no_links then skip this work
				if self.settings['hide_works_with_no_links']:
					continue
				# else add work to rows
				rows.append(work.__dict__)
				rows[-1]['id'] = num_work  # this line may be redundant
				continue
			# for each link in work
			for num_link, link in enumerate(work.links):
				# if link has updated and has no new chapters and hide_unupdated_works
				if link.new != '' and link.new == 0 and self.settings['hide_unupdated_works']:
					# skip this link
					continue
				# process link and add it to rows
				tmp = work.__dict__.copy()
				del tmp['links']
				rows.append({'id': (num_work, num_link), 'link': link.link, 'nChs': link.new, **tmp})
		return [format_rowData(row, self.settings['to_display'][tab_name]) for row in rows]
	async def _file_opened(self, event: GenericEventArguments) -> None:
		'runs when a file is selected in the main tab, creates a new tab for the file'
		def load_file(file: str) -> list | Any:
			'Runs `add_work(work)` for each work in file specified then returns the name of the file loaded'
			from json import load
			def add_work(format: str | Work, *args, **kwargs) -> Work:
				'formats `Type` argument and returns the created object'
				# if the format is a string, turn in into an object
				if type(format) is str:
					format = eval(format)
				# return works object
				return format(*args, **kwargs)  # type: ignore

			with open(file, 'r', encoding='utf8') as f:
				return load(f, object_hook=lambda kwargs: add_work(**kwargs))
		# extract file name from event
		file = event.args['data']['name']
		# if file allready open, switch to it
		if file in self.open_tabs:
			self.switch_tab(Dict({'args': file}))
			return
		# get columns to display
		cols = [{'field': 'id', 'aggFunc': 'first', 'hide': True}]
		try:
			cols = cols + [{'field': key, 'rowGroup': True, 'hide': True} if val[1] == 'group' else {'headerName': val[0], 'field': key, 'aggFunc': val[1], 'width': self.settings['default_column_width']} for key, val in self.settings['to_display'][file].items()]
		except KeyError as e:
			raise Exception('Columns for', e, 'has not been specified in settings.yaml')  # TODO: setup default columns instead of crash
		cols[-1]['resizable'] = False
		# load works from file and refrence them in open_tabs
		works = load_file(self.settings['json_files_dir'] + file + '.json')
		tab = self.open_tabs[file] = Dict({'name': file, 'works': works, 'links': {}})
		tab.reading = None
		tab.open = set()
		# create links dict with "index" of link
		num = 0
		for work in works:
			for link in work.links:
				tab.links[link.link] = num
				num += 1
		# generate rowData
		rows = self.generate_rowData(works, [], file)
		# create and switch to tab for file
		with self.tabs:
			tab.tab = ui.tab(file)
		self.switch_tab(Dict({'args': file}))
		# create panel for file
		with self.panels:
			with ui.tab_panel(file).style('height: calc(100vh - 84px); width: calc(100vw - 32px)') as tab.panel:
				tab.label = ui.label('Reading: ')
				gridOptions = {
					'defaultColDef': {
						'resizable': True,
						'suppressMenu': True,
						'suppressMovable': self.settings['disable_col_dragging'],
						'cellRendererParams': {'suppressCount': True, },
					},
					'autoGroupColumnDef': {
						'headerName': 'Name',
						'field': 'link',
					},
					'columnDefs': cols,
					'rowData': rows,
					'rowHeight': self.settings['row_height'],
					'animateRows': True,
					'suppressAggFuncInHeader': True,
				}
				tab.grid = self.jailbreak(ui.aggrid(gridOptions, theme='alpine-dark' if self.settings['dark_mode'] else 'balham').style('height: calc(100vh - 164px)'))
				tab.grid.on('rowGroupOpened', wrap(self.close_all_other, tab))
				tab.grid.on('cellDoubleClicked', wrap(self.work_selected, tab))
				with ui.row().classes('w-full').style('gap: 0'):
					self._input()  # .style('width: 8px; height: 8px; border:0px; padding:0px; margin:0px')
					ui.button(on_click=lambda: print('placeholder')).props('square').style('width: 40px; height: 40px;')
		# update all works
		await asyncio.sleep(1)
		await self.update_all(tab)
	async def close_all_other(self, tab: Dict, event: GenericEventArguments):  # TODO: add more comments
		'is called whenever a row is opened'
		tab_opened = event.args['rowId']
		# if the row being opened is "empty"
		if await ui.run_javascript(f'return getElement({event.sender.id}).gridOptions.api.getRowNode("{tab_opened}").childrenAfterSort[0].key') in {None, ' '}:
			# if not (the child of the row being opened has "valid" data instead of key)
			if not await ui.run_javascript(f'''
				var child = getElement({event.sender.id}).gridOptions.api.getRowNode('{tab_opened}').childrenAfterSort[0]
				return ('data' in child) && (child.data.link != ' ')
			'''):
				# close the row being opened
				await ui.run_javascript(f'''
					var grid = getElement({event.sender.id}).gridOptions.api;
					grid.setRowNodeExpanded(grid.getRowNode("{tab_opened}"), false);
				''', respond=False)
				return
		# if the row being opened is a child of the currently opened row, do nothing
		elif await ui.run_javascript(f'return getElement({event.sender.id}).gridOptions.api.getRowNode("{tab_opened}").parent.id') in tab.open:
			pass
			# TODO: make this work to "advanced grouped rows", opening a sub row does not close the other opened sub rows of the same parent
		# if event was caused by (assumidly) closing the opened row, take note of it and `return`
		elif tab_opened in tab.open:
			tab.open.remove(tab_opened)
			return
		# if this event was called by a row being (auto) closed, do nothing
		elif not await ui.run_javascript(f"getElement({event.sender.id}).gridOptions.api.getRowNode('{tab_opened}').expanded"):
			return
		# else close all previous open row
		else:
			for open_tab in tab.open:
				await ui.run_javascript(f'''
					var grid = getElement({event.sender.id}).gridOptions.api;
					grid.setRowNodeExpanded(grid.getRowNode("{open_tab}"), false);
				''', respond=False)
		# set open to new opened row
		tab.open.add(tab_opened)
	async def work_selected(self, tab: Dict, event: GenericEventArguments):  # TODO: add comments
		'runs when a work is selected'
		# get ending of row text and id
		try:
			value, id = await ui.run_javascript(f'''
				var node = getElement({event.sender.id}).gridOptions.api.getRowNode('{event.args['rowId']}')
				return [node.key, node.aggData.id]
			''')
		except TimeoutError:
			value, id = await ui.run_javascript(f'''
				var node = getElement({event.sender.id}).gridOptions.api.getRowNode('{event.args['rowId']}')
				return [node.data.link, node.data.id]
			''')
		# if neither name nor link was selected, do nothing
		if value[-1] not in {'‎', '‏'}:
			return
		# stuff
		event = event.args
		# if reading
		if tab.reading:
			# get work
			work = tab.works[id[0]]
			# if link is selected
			if value[-1] == '‎':
				link = work.links[id[1]]
				# if same link is reselected or previous selected is a work and link selected is first
				if link == tab.reading or (issubclass(tab.reading.__class__, Work) and link == tab.reading.links[0]):
					# set work's chapter the link's latest chapter
					work.chapter = link.latest
					# TODO: deal with the case that the link has not been updated yet
					tab.reading = None
			# if name is selected
			else:
				# if same work is reselected or work selected is parent of reading link
				if work == tab.reading or tab.reading in work.links:
					# set work's chapter to latest chapter
					work.update()
					tab.reading = None
			# if no longer reading
			if not tab.reading:
				# change label
				tab.label.set_text('Reading:')
				# update grid
				self.re_grid(tab)
				return
		# if not reading or diffrent work is selected
		tab.reading = tab.works[id[0]]
		# change label
		tab.label.set_text('Reading: ' + tab.reading.name)
		# if is link
		if value[-1] == '‎':
			# set reading to link
			tab.reading = tab.reading.links[id[1]]
			# open link
			await self.open_link(value)
		# if is name
		elif value[-1] == '‏':
			# open link
			await self.open_link(tab.reading.links[0].link)

			# work = tab.works[event['rowIndex']]
			# if work == tab.reading:
			# 	work.update()
			# 	tab.label.set_text('Reading:')
			# 	tab.reading = None
			# 	self.update_grid(tab.grid, self.generate_rowData(tab.works, []))
			# 	return
	async def open_link(self, link: str) -> None:
		await ui.run_javascript(f"window.open('{link}')", respond=False)
	async def update_all(self, tab: Dict) -> None:
		'updates all works provided'
		from requests_html2 import AsyncHTMLSession
		async def update_each(work: Work, tab: Dict, async_session: AsyncHTMLSession) -> None:
			async_fix()
			try:
				if 'links' in work.prop:
					for link in work.links:  # type: ignore
						async with self.workers:
							# if debug tab open
							if 'debug' in self.open_tabs:
								self.open_tabs.debug.updating.add_rows({'name': link.link})
							new = await link.update(self.renderers, self.settings['sites'], self.settings['tags_to_skip'], async_session)
							# if no new chapters and hide_unupdated_works or update resulted in error and hide_updates_with_errors
							if (new in (0, 0.0) and self.settings['hide_unupdated_works']) or (int(new) == -999 and self.settings['hide_updates_with_errors']):
								await ui.run_javascript(f'var grid = getElement({tab.grid.id}).gridOptions.api; grid.applyTransaction({{remove: [grid.getRowNode({tab.links[link.link]}).data]}})', respond=False)
							else:
								await ui.run_javascript(f"getElement({tab.grid.id}).gridOptions.api.getRowNode({tab.links[link.link]}).setDataValue('nChs', {new})", respond=False)
							# if debug tab open
							if 'debug' in self.open_tabs:
								self.open_tabs.debug.updating.remove_rows({'name': link.link})
								self.open_tabs.debug.done.add_rows({'name': link.link})
			except asyncio.CancelledError:
				pass  # TODO: if debug tab open, remove work from 'updating' column/card

		async with AsyncHTMLSession() as async_session:
			tab.tasks = asyncio.gather(*[update_each(work, tab, async_session) for work in tab.works], return_exceptions=True)
			await tab.tasks
		print('done updating', tab.name)
	if None:  # to fold def update_row
		# def update_row(self, ):
		# 	# if no new chapters and hide_unupdated_works or update resulted in error and hide_updates_with_errors
		# 	if (new in (0, 0.0) and self.settings['hide_unupdated_works']) or (int(new) == -999 and self.settings['hide_updates_with_errors']):
		# 		await ui.run_javascript(f'var grid = getElement({tab.grid.id}).gridOptions.api; grid.applyTransaction({{remove: [grid.getRowNode({tab.links[link.link]}).data]}})', respond=False)
		# 	else:
		# 		await ui.run_javascript(f"getElement({tab.grid.id}).gridOptions.api.getRowNode({tab.links[link.link]}).setDataValue('nChs', {new})", respond=False)
		pass
	def close_tab(self, tab_name: str) -> None:
		'closes indicated tab'
		# get tab
		tab = self.open_tabs[tab_name]
		# cancel updating works in tab
		tab.tasks.cancel()
		# delete stuff
		tab.panel.delete()
		tab.tab.delete()
		# switch to main tab
		del self.open_tabs[tab_name]
		self.switch_tab(Dict({'args': 'Main'}))
	async def handle_input(self, event: GenericEventArguments):
		import sys
		# if is a command
		if event.sender.value[0] == '/':
			# get name of open tab
			name = self.tabs._props['model-value']
			tab = self.open_tabs[name]
			command = event.sender.value
			# if is help command: list all commands
			if command == '/help':
				print([f"{key}: {val}" for key, val in self.commands.items()])
			# if is debug command: open debug tab
			elif command == '/debug':
				self.debug()
			# if is reload command and not the main tab: reupdate all
			elif command == '/reupdate' and name != 'Main':
				tab.tasks.cancel()
				await self.update_all(tab)
			# if is refresh command: re"draw" grid
			elif command == '/refresh':
				self.re_grid(tab_name=name)
			# if is reload: re load file
			elif command == '/reload':
				if name == 'Main':
					pass
				else:
					self.close_tab(name)
					await self._file_opened(Dict({'args': {'data': {'name': name}}}))
			# if is save or exit command: save all works in tab and
			elif command == '/save' and name != 'Main':
				save_to_file(tab.works, self.settings['json_files_dir'] + name + '.json')
				ui.notify('Saved ' + name)
			elif command == '/exit':
				# save all open tabs
				for name, tab in self.open_tabs.items():
					if name != 'Main':
						save_to_file(tab.works, self.settings['json_files_dir'] + name + '.json')
						ui.notify('Saved ' + name)
				# close app
				app.shutdown()
				sys.exit()
			# if is close command: close current tab
			elif command == '/close' and name != 'Main':
				self.close_tab(name)
			# if is quit command: exit without saving
			elif command == '/quit':
				app.shutdown()
				sys.exit()
		# clear input
		event.sender.set_value(None)
	def debug(self):
		'opens debug tab'
		# if debug tab is allready open, switch to it
		if 'debug' in self.open_tabs:
			self.switch_tab(Dict({'args': 'Debug'}))
			return
		# else create tab
		self.open_tabs.debug = Dict()
		with self.tabs:
			ui.tab('Debug')
		with self.panels:
			with ui.tab_panel('Debug').style('height: calc(100vh - 84px); width: calc(100vw - 32px)'):
				ui.label('Updating:')
				with ui.row().classes('w-full'):
					self.open_tabs.debug.updating = ui.table(columns=[{'name': 'name', 'label': 'updating', 'field': 'name'}], rows=[], row_key='name')
					self.open_tabs.debug.done = ui.table(columns=[{'name': 'name', 'label': 'done', 'field': 'name'}], rows=[], row_key='name')
		# switch to tab
		self.switch_tab(Dict({'args': 'Debug'}))
	def _on_reload(self):
		for tab_name in self.open_tabs:
			if tab_name not in {'Main', 'Debug'}:
				self.re_grid(tab_name=tab_name)
	def re_grid(self, tab: Dict = None, tab_name: str = None) -> None:
		'reloads the grid of the specified tab'
		if tab is None:
			tab = self.open_tabs[tab_name]
		tab.grid.call_api_method('setRowData', self.generate_rowData(tab.works, [], tab.name))


default_settings = '''
dark_mode: true  # default: true
json_files_dir: ./  # default: ./
tags_to_skip: [Skip, [Complete, Read]]  # works with specified tags will have update skipped and be hidden, [A, [B, C]] = A or (B and C)
font: [OCR A Extended, 8]  # [font name, font size], not yet implemented
default_column_width: 16  # default: 16
row_height: 32  # default: 32
disable_col_dragging: true  # default: true
to_display:  # culumns to display for each Type, do not include name (it's required and auto included)
    example: {author: [Author, group], series: [Series, group], name: [Name, group], nChs: [New Chapters, max], chapter: [Current Chapter, first], tags: [Tags, first]}
workers: 3  # defualt: 3
renderers: 1  # default: 1
hide_unupdated_works: true  # default: true
hide_works_with_no_links: true  # default: true
hide_updates_with_errors: false  # default: false
sort_by: score  # defulat: score, score is currently only working option
# prettier-ignore
scores: {no Good: -1, None: 0, ok: 1, ok+: 1.1, decent: 1.5, Good: 2, Good+: 2.1, Great: 3}  # numerical value of score used when sorting by score
sites_ignore: []
# prettier-ignore
sites:  # site,         find,        with,                       then_find, and get,       split at, then get, render?
    www.royalroad.com: &001 [table, id: chapters,               null,      data-chapters, ' ',      0,        false]  # based on absolute chapter count, not chapter name
    www.webtoons.com:  &002 [ul,    id: _listUl,                li,        id,            _,        -1,       false]
    bato.to:           &003 [item,  null,                       title,     null,          ' ',      -1,       false]
    mangafire.to:      &004 [div,   class: list-body,           li,        data-number,   ' ',      0,        false]
    mangabuddy.com:    &005 [div,   class: latest-chapters,     a,         href,          '-',      -1,       false]
    www.mgeko.com:     &006 [ul,    class: chapter-list,        a,         href,          -|/,      -4,       false]
    zahard.xyz:        &007 [ul,    class: chapters,            a,         href,          /,        -1,       false]
    manganato.com:     &008 [ul,    class: row-content-chapter, a,         href,          '-',      -1,       false]
    reaper-scans.com:  &009 [span,  class: epcur epcurlast,     null,      null,          ' ',      1,        false]
    manhuaplus.com:    &010 [ul,    class: version-chap,        a,         href,          -|/,      -2,       false]
    mangadex.org:      &011 [div,   class: text-center,         null,      null,          -|\.,     -1,       true]
    null: [*001, *002, *003, *004, *005, *006, *007, *008, *009, *010, *011]  # for aligning reasons
    www.mcreader.net:  *006
    www.mangageko.com: *006
    chapmanganato.com: *008
    readmanganato.com: *008
    # flamescans.org:  *009

'''
def main(name: str, dir: str | None = None, settings_file='settings.yaml', *args):
	'Main function, being "revised"'
	import os
	# change working directory to where file is located unless specified otherwise, just in case
	os.chdir(dir or os.path.dirname(os.path.realpath(__file__)))
	if __debug__: print(f'working directory: {os.getcwd()}')
	# setup gui
	settings = load_settings(settings_file, default_settings)
	files = [{'name': file.split('.json')[0]} for file in os.listdir(settings['json_files_dir']) if file.split('.')[-1] == 'json']
	gui = GUI(settings, files)
	# start gui
	ui.run(dark=settings['dark_mode'], title=name.split('\\')[-1].rstrip('.pyw'), reload=False)
def load_settings(settings_file: str, default_settings: str = default_settings) -> dict:
	def format_sites(settings_file: str) -> None:  # puts spaces between args so that the 2nd arg of the 1st list starts at the same point as the 2nd arg of the 2nd list and so on
		with open(settings_file, 'r') as f: file = f.readlines()  # loads settings_file into file
		start = [num for num, line in enumerate(file) if line[0:6] == 'sites:'][0]  # gets index of where 'sites:' start
		col = 0; adding = set(); done = set()
		while '  ' in file[start][14:]:
			file[start] = file[start][:14] + file[start][14:].replace('  ', ' ')  # remove all extra spaces from 'sites:' line
		for line_num, line in enumerate(file[start:], start):  # remove all the other extra spaces, TODO: replace enumerate with range
			while '   ' in file[line_num][4:]:
				file[line_num] = file[line_num][:4] + file[line_num][4:].replace('   ', '  ')
		while len(done) != len(file[start:]):  # while not all lines have been formatted
			if len(adding) + len(done) == len(file[start:]): adding = set()  # if all lines after and including 'sites:' are in adding then remove everything from adding
			for line_num, line in enumerate(file[start:], start):  # for each line after and including 'sites:'
				if line[0:9] == '    null:': done.add(line_num)
				if line_num in done: continue  # skip completed lines
				if line[col] == '\n': done.add(line_num)  # add line's index to done when it reaches the end
				elif line_num in adding and line[col + 1] != ' ': file[line_num] = line[0:col] + ' ' + line[col:]  # if line is in adding and next char is not ' ' then add space into line at i
				elif line[col] == ',' or (line[col] == ':' and line[col + 1:].lstrip(' ')[0] in ('&', '*', '[')): adding.add(line_num)  # if elm endpoint is reached, add line into adding
			col += 1  # increase column counter
		with open(settings_file, 'w') as f: f.writelines(file)  # write file to settings_file

	import ruamel.yaml; yaml = ruamel.yaml.YAML(); yaml.indent(mapping=4, sequence=4, offset=2); yaml.default_flow_style = None; yaml.width = 4096  # setup yaml
	settings = yaml.load(default_settings.replace('\t', ''))  # set default_settings
	try: file = open(settings_file, 'r', encoding='utf8'); settings.update(yaml.load(file)); file.close()  # try to overwrite the default settings from the settings_file
	except FileNotFoundError as e: print(e)  # except: print error
	with open(settings_file, 'w') as file: yaml.dump(settings, file)  # save settings to settings_file
	format_sites(settings_file); return settings  # format settings_file 'sites:' part then return settings
def async_fix():
	'fixes runing `run_javascript()` "inside" `asyncio.gather`'
	from nicegui import globals
	globals.index_client.content.slots['default'].__enter__()  # not quite sure what this does, but it works
def save_to_file(works: Iterable, file: str) -> None:
	'Saves all works in `Works.all` to file specified'
	from json import dump
	with open(file, 'w', encoding='utf8') as f:
		dump(works, f, indent='\t', default=lambda work: work.asdict())


if __name__ in {"__main__", "__mp_main__"}:
	import sys
	main(*sys.argv)