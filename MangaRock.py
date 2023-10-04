# Version: 3.3.1
# okay, heres the plan, make links its own separate object and have the links update individualy. when the updates, it will then update its parent's display
import asyncio
from nicegui import app, ui
from nicegui.events import GenericEventArguments
from typing import Any, Iterable
from functools import partial as wrap
from stuff import Dict


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
		# add self to Works.all
		Work.all.append(self)  # type: ignore
		# add self to it's class' all dict with name as key
		self.__class__.all[kwargs['name']] = self  # type: ignore
		# for every kwarg given or from args, format it and update `self.__dict__` with it
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
				# if default val is float and given val is not float then float given val
				if self.prop[key].__class__ is int and type(val) is not float: val = float(val)
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
	def __iter__(self) -> object: return self  # required for to iter over
	def __str__(self) -> str:
		'returns `self` in `str` format'
		return '<' + self.__class__.__name__ + ' Object: {' + ', '.join([f'{key}: {val}' for key, val in self.__dict__.items() if key != 'name' and val != []]) + '}>'
	def __repr__(self) -> str:
		'represent `self` as `self.name` between <>'
		return f'<{self.name}>'  # type: ignore
class Manga(Work): all = {}; prop = {'name': None, 'links': [], 'chapter': 0, 'series': None, 'author': None, 'score': None, 'tags': []}
class Link():
	def __init__(self, link: str, parent: Work) -> None:
		self.site = link.split('/')[2]
		self.link = link
		self.parent = parent
		self.new = self.latest = ''
	async def update(self, renderers, sites: dict, asession) -> float | Exception:
		'''Finds latest chapter from `self.link` then sets result or an error code to `self.latest`
		# Error Codes:
			-999.1 = site not supported
			-999.2 = Connection Error
			-999.3 = rendering error, probably timeout
			-999.4 = parsing error
			-999.5 = whatever was extracted was not a number'''
		import re, bs4
		# if "special" tags are in link, skip
		if 'tags' in self.parent.prop:
			tags = self.parent.tags
			if ('do not check for updates' in tags) or ('Complete' in tags and 'Read' in tags) or ('Oneshot' in tags and 'Read' in tags) or ('Two Shot' in tags and 'Read' in tags):
				self.latest = Exception('skiped')
				return self.re(0)
		# tmp: special stuff for bato.to
		if self.site == 'bato.to': link = self.link.replace('title/', 'rss/series/') + '.xml'
		# if site is supported
		if self.site not in sites:
			self.latest = Exception('site not supported')  # site not supported
			return self.re(-999.1)
		# connecting to site
		try:
			link = await asession.get(self.link)  # connecting to the site
			assert link.ok  # make sure connection was successful
		except Exception as e:  # connection error
			self.latest = e
			return self.re(-999.2)
		# render site if necessary
		try:
			if sites[self.site][6]:  # if needs to be rendered
				if __debug__: print('rendering', self.link, '-', self.site)
				with renderers:
					await link.html.arender(retries=2, wait=1, sleep=2, timeout=20, reload=True)
				if __debug__: print('done rendering', self.link, '-', self.site)
		except Exception as e:
			print('failed to render: ', self.link, ' - ', self.site, ', ', e, sep='')  # render error
			self.latest = e
			return self.re(-999.3)

		try:
			link = bs4.BeautifulSoup(link.html.html, 'html.parser')  # link = bs4 object with link html
			if (sites[self.site][2] is None) and (sites[self.site][3] is None):
				link = link.find(sites[self.site][0], sites[self.site][1]).contents[0]  # if site does not require second find and the contents are desired: get contents of first tag with specified requirements
			elif sites[self.site][2] is None:
				link = link.find(sites[self.site][0], sites[self.site][1]).get(sites[self.site][3])  # if site does not require second find and tag attribute is desired: get specified attribute of first tag with specified attribute
			else:
				link = link.find(sites[self.site][0], sites[self.site][1]).find(sites[self.site][2]).get(sites[self.site][3])  # else: get specified attribute of first specified tag under the first tag with specified attribute
		except AttributeError as e:
			self.latest = e  # parsing error
			return self.re(-999.4)

		try:
			self.latest = float(re.split(sites[self.site][4], link)[sites[self.site][5]])  # else link parsing went fine: extract latest chapter from link using lookup table
		except Exception as e:
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
		self.commands = {'/help': 'help', '/debug': 'debug'}
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
				self.open_tabs.Main.grid = ui.aggrid(gridOptions, theme='alpine-dark').style('height: calc(100vh - 164px)').on('cellDoubleClicked', self._file_opened)
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
				while row[cols[col]] is None:  # while the col is empty
					# shuffle cols "up"
					for mod in range(col, len(cols) - 1):
						row[cols[mod]] = row[cols[mod + 1]]
					# set last col to empty
					row[cols[-1]] = ' '
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
			def add_work(format: str | Work, *args, **kwargs) -> Work:
				'formats `Type` argument and returns the created object'
				# if the format is a string, turn in into an object
				if type(format) is str:
					format = eval(format)
				# return works object
				return format(*args, **kwargs)  # type: ignore

			with open(file, 'r', encoding='utf8') as f:
				from json import load
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
			for key, val in self.settings['to_display'][file].items():  # TODO: maybe turn into list comprehension
				if val[1] == 'group':
					cols.append({'field': key, 'rowGroup': True, 'hide': True})
				else:
					cols.append({'headerName': val[0], 'field': key, 'aggFunc': val[1], 'width': self.settings['default_column_width']})
		except KeyError as e:
			raise Exception('Columns for', e, 'has not been specified in settings.yaml')  # TODO: setup default columns instead of crash
		cols[-1]['resizable'] = False
		# load works from file and refrence them in open_tabs
		works = load_file(file + '.json')
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
			ui.tab(file)
		self.switch_tab(Dict({'args': file}))
		# create panel for file
		with self.panels:
			with ui.tab_panel(file).style('height: calc(100vh - 84px); width: calc(100vw - 32px)'):
				tab.label = ui.label('Reading: ')
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
					'columnDefs': cols,
					'rowData': rows,
					'rowHeight': self.settings['row_height'],
					'animateRows': True,
					'suppressAggFuncInHeader': True,
				}
				tab.grid = self.jailbreak(ui.aggrid(gridOptions, theme='alpine-dark').style('height: calc(100vh - 164px)'))
				tab.grid.on('rowGroupOpened', wrap(self.close_all_other, tab))
				tab.grid.on('cellDoubleClicked', wrap(self.work_selected, tab))
				with ui.row().classes('w-full').style('gap: 0'):
					self._input()  # .style('width: 8px; height: 8px; border:0px; padding:0px; margin:0px')
					ui.button(on_click=lambda: print('placeholder')).props('square').style('width: 40px; height: 40px;')
		# update all works
		await self.update_all(works, tab)
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
	async def update_all(self, works: Iterable, tab: Dict) -> None:
		'updates all works provided'
		from requests_html import AsyncHTMLSession
		async def update_each(work: Work, tab: Dict) -> None:
			async_fix()
			if 'links' in work.prop:
				for link in work.links:  # type: ignore
					async with self.workers:
						# if debug tab open
						if 'debug' in self.open_tabs:
							self.open_tabs.debug.updating.add_rows({'name': link.link})
						new = await link.update(self.renderers, self.settings['sites'], asession)
						# if no new chapters and hide_unupdated_works or update resulted in error and hide_updates_with_errors
						if (new in (0, 0.0) and self.settings['hide_unupdated_works']) or (int(new) == -999 and self.settings['hide_updates_with_errors']):
							await ui.run_javascript(f'var grid = getElement({tab.grid.id}).gridOptions.api; grid.applyTransaction({{remove: [grid.getRowNode({tab.links[link.link]}).data]}})', respond=False)
						else:
							await ui.run_javascript(f"getElement({tab.grid.id}).gridOptions.api.getRowNode({tab.links[link.link]}).setDataValue('nChs', {new})", respond=False)
						# if debug tab open
						if 'debug' in self.open_tabs:
							self.open_tabs.debug.updating.remove_rows({'name': link.link})
							self.open_tabs.debug.done.add_rows({'name': link.link})

		asession = AsyncHTMLSession()
		await asyncio.gather(*[update_each(work, tab) for work in works])
		print('done updating')

	# def update_row(self, ):
	# 	# if no new chapters and hide_unupdated_works or update resulted in error and hide_updates_with_errors
	# 	if (new in (0, 0.0) and self.settings['hide_unupdated_works']) or (int(new) == -999 and self.settings['hide_updates_with_errors']):
	# 		await ui.run_javascript(f'var grid = getElement({tab.grid.id}).gridOptions.api; grid.applyTransaction({{remove: [grid.getRowNode({tab.links[link.link]}).data]}})', respond=False)
	# 	else:
	# 		await ui.run_javascript(f"getElement({tab.grid.id}).gridOptions.api.getRowNode({tab.links[link.link]}).setDataValue('nChs', {new})", respond=False)
	async def handle_input(self, event: GenericEventArguments):
		# if is a command
		if event.sender.value[0] == '/':
			# if is help command
			if event.sender.value == '/help':
				print([f"{key}: {val}" for key, val in self.commands.items()])
			# if is debug command
			elif event.sender.value == '/debug':
				self.debug()
			# if is reload command
			elif event.sender.value == '/reload':
				name = self.tabs._props['model-value']
				# if is not the main tab
				if name != 'Main':
					await self.update_all(self.open_tabs.example.works, self.open_tabs[name])
			elif event.sender.value == '/tmp':
				name = self.tabs._props['model-value']
				self.open_tabs[name].grid.call_api_method('setRowData', self.generate_rowData(self.open_tabs[name].works, [], name))
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
font: [OCR A Extended, 8]  # [font name, font size], not yet implemented
default_column_width: 16  # default: 16
row_height: 32  # default: 32
to_display:  # culumns to display for each Type, do not include name (it's required and auto included)
    example: {author: [Author, group], series: [Series, group], name: [Name, group], nChs: [New Chapters, max], chapter: [Current Chapter, first], tags: [Tags, first]}
    Manga: {author: [Author, group], series: [Series, group], name: [Name, group], nChs: [New Chapters, max], chapter: [Current Chapter, first], tags: [Tags, first]}
workers: 3  # defualt: 3
renderers: 1  # default: 1
hide_unupdated_works: true  # default: true
hide_works_with_no_links: true  # default: true
hide_updates_with_errors: false  # default: false
sort_by: score # defulat: score
# prettier-ignore
scores: {no Good: -1, None: 0, ok: 1, ok+: 1.1, decent: 1.5, Good: 2, Good+: 2.1, Great: 3} # numerical value of score used when sorting by score
# prettier-ignore
sites: #site,                    find,        with,                        then_find, and get,        split at, then get, render?
    www.royalroad.com:           &001 [table, id: chapters,                None,      data-chapters', ' ',      0,        false]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             # based on absolute chapter count, not chapter name
    www.webtoons.com:            &002 [ul,    id: _listUl,                 li,        id',            _,        -1,       false]
    bato.to:                     &003 [item,  None,                        title,     None,           ' ',      -1,       false]
    mangabuddy.com:              &004 [div,   class: latest-chapters,      a,         href,           '-',      -1,       false]
    mangapuma.com:               &005 [div,   id: chapter-list-inner,      a,         href,           '-',      -1,       false]
    www.manga-raw.club:          &006 [ul,    class: chapter-list,         a,         href,           -|/,      -4,       false]
    zahard.xyz:                  &007 [ul,    class: chapters,             a,         href,           /,        -1,       false]
    manganato.com:               &008 [ul,    class: row-content-chapter,  a,         href,           '-',      -1,       false]
    flamescans.org:              &009 [span,  class: epcur epcurlast,      None,      None,           ' ',      1,        false]
    null: [*001, *002, *003, *004, *005, *006, *007, *008, *009]
    www.mcreader.net:            *006
    www.mangageko.com:           *006
    chapmanganato.com:           *008
    readmanganato.com:           *008

'''
def main(name: str, dir: str | None = None, settings_file='settings.yaml', *args):
	'Main function, being "revised"'
	import os
	# change working directory to where file is located unless specified otherwise, just in case
	os.chdir(dir or os.path.dirname(os.path.realpath(__file__)))
	if __debug__: print(f'working directory: {os.getcwd()}')
	# setup gui
	settings = load_settings(settings_file, default_settings)
	files = [{'name': file.split('.json')[0]} for file in os.listdir() if file.split('.')[-1] == 'json']
	gui = GUI(settings, files)
	# start gui
	ui.run(dark=True, title=name.split('\\')[-1].rstrip('.pyw'), reload=False)
def load_settings(settings_file: str, default_settings: str = default_settings) -> dict:
	def format_sites(settings_file: str) -> None:  # puts spaces between args so that the 2nd arg of the 1st list starts at the same point as the 2nd arg of the 2nd list and so on
		with open(settings_file, 'r') as f: file = f.readlines()  # loads settings_file into file
		start = [num for num, line in enumerate(file) if line[0:6] == 'sites:'][0]  # gets index of where 'sites:' start
		i = 0; adding = set(); done = set()
		while len(done) != len(file[start:]):  # while not all lines have been formatted
			if len(adding) + len(done) == len(file[start:]): adding = set()  # if all lines after and including 'sites:' are in adding then remove everything from adding
			for num, line in enumerate(file[start:], start):  # for each line after and including 'sites:'
				if line[0:9] == '    null:': done.add(num)
				if num in done: continue  # skip completed lines
				if line[i] == '\n': done.add(num)  # add line's index to done when it reaches the end
				elif num in adding and line[i + 1] != ' ': file[num] = line[0:i] + ' ' + line[i:]  # if line is in adding and next char is not ' ' then add space into line at i
				elif line[i] == ',' or (line[i] == ':' and line[i + 1:].lstrip(' ')[0] in ('&', '*', '[')): adding.add(num)  # if elm endpoint is reached, add line into adding
			i += 1  # increase column counter
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


if __name__ in {"__main__", "__mp_main__"}:
	# import tracemalloc
	# from multiprocessing import freeze_support
	# tracemalloc.start()
	# freeze_support()

	import sys
	main(*sys.argv)
