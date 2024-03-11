# Version: 3.6.0, pylint: disable=invalid-name
import asyncio
import os
from functools import partial as wrap
from typing import Any, Iterable, Self

from epicstuff import Dict

from nicegui import app, ui
from nicegui.events import GenericEventArguments

from rich.console import Console; console = Console()
# from rich.traceback import install; install(width=os.get_terminal_size().columns)  # pylint: disable=wrong-import-position


class Work(Dict):
	'''object representing a work, eg: a book, a series, a manga, etc.'''
	formats: Dict
	def __init__(self, format: str, *args: list, **kwargs: dict) -> None:  # pylint:disable=redefined-builtin
		'''Applies args and kwargs to "`self.__dict__`" if kwarg is in `self.formats[format]`'''
		self.format = format
		prop = self.prop = self.formats[format]  # TODO: when format of work is not in settings, handle it instead of just crashing
		# convert args from list to dict then update them to kwargs
		kwargs.update({tuple(prop.keys())[num]: arg for num, arg in enumerate(args) if arg not in ['', None, *kwargs.values()]})
		# set self properties to default property values
		super().__init__(prop)
		# for every kwarg, format it and update `self` with it
		for key, val in kwargs.items():
			# if key of kwarg is in properties
			if key in self:
				# if given val is a tuple then turn given val into a list
				if isinstance(val, tuple): val = list(val)
				# if given val is list and default val is not list then unlist list
				if isinstance(val, list) and not isinstance(prop[key], list):
					# if multiple items in list then raise error
					if len(val) > 1:
						raise TypeError('unexpected multiple values within array')
					# else unlist list
					else:
						val = val[0]
				# if default val is list and given val is not list then put given val in a list
				elif isinstance(prop[key], list) and not isinstance(val, list): val = [val]
				# if default val is int or float and given val is not float then float given val
				if isinstance(prop[key], (int, float)) and not isinstance(val, (int, float)): val = float(val)
				# if default val is int and given val is a decimal-les (without decimals) float : convert to int
				if isinstance(val, float) and int(val) == val:
					val = int(val)
				# change self property value to processed given kwarg value
				self[key] = val
		# if no name was provided, generate a name
		if not self.name: self.name = hash(self)
		# if self has links then turn links into Link objects
		if 'links' in prop:
			for num, link in enumerate(self.links):  # type: ignore
				self.links[num] = Link(link, self)  # type: ignore
	def update(self, what='chapter', source='links'):
		'updates `self.{what}` based on `self.{source}`, or thats the idea anyways'
		# create list of links' latest chapters excluding errors and empty strings then get max
		self[what] = max([link.latest for link in self[source] if not issubclass(link.latest.__class__, Exception) and link.latest != ''])
		if what == 'chapter' and source == 'links':
			for link in self.links:  # pylint: disable=no-member
				link.re()
	@classmethod
	def sort(cls, sort_by: str = 'name', look_up_table: dict | None = None, reverse: bool = True) -> None:
		'''sort `cls.all` by given dict, defaults to name'''
		works = cls.all
		# if `works` is a dict, convert it to a list
		if works.__class__ is dict:
			works = works.values()  # pylint: disable=no-member
		# sort
		if sort_by == 'name':
			# for each work in `works` sort by `work.name`
			works.sort(key=lambda work: work.name, reverse=reverse)
		elif look_up_table is not None:
			# for each work in `works` get `work.sort_by` and convert into number through look up table
			works.sort(key=lambda work: look_up_table[work[sort_by]], reverse=reverse)
		# if `cls.all` is a dict, convert it back to a dict
		if isinstance(cls.all, dict):
			work = {work.name: work for work in works}
		cls.all = works
	def to_dict(self) -> dict:
		'returns `self` as a dictionary'
		return {**{'format': self.format}, **{key: val for key, val in self.items() if val not in ([], "None", None) if key != 'lChs'}}  # convert attributes to a dictionary
	def work(self) -> Self:
		'returns `self`'
		return self
	# def __iter__(self) -> object: return self  # required for to iter over for some reason
	def __hash__(self) -> int:
		return object().__hash__()
	def __str__(self) -> str:
		'returns `self` in `str` format'
		return '<' + self.format + ' Object: {' + ', '.join([f'{key}: {val}' for key, val in self.items() if key != 'name' and val != []]) + '}>'
	def __repr__(self) -> str:
		'represent `self` as `self.name` between <>'
		return f'<{self.name}>'  # pylint: disable=no-member
class Link():
	'link object, can be updated to get latest chapter'
	def __init__(self, link: str, parent: Work) -> None:
		self.site = link.split('/')[2]
		self.link = link
		self.parent = parent
		self.new = self.latest = ''
		self.index = {}
	async def update(self, renderers: asyncio.Semaphore, sites: dict, tags_to_skip: list, async_session) -> float | Exception:
		'''Finds latest chapter from `self.link` then sets result or an error code to `self.latest`
		# Error Codes:
			-999.1 = site not supported
			-999.2 = Connection Error
			-999.3 = rendering error, probably timeout
			-999.4 = parsing error
			-999.5 = whatever was extracted was not a number'''
		import re

		import bs4

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
		# why this function is called re? I have no idea
		if new is None:
			if not issubclass(self.latest.__class__, Exception):
				new = round(self.latest - self.parent.chapter, 4)
			else:
				new = self.new
		self.new = new
		return new
	def to_dict(self):
		'convert `self` to a string'
		return self.link
	def work(self) -> Work:
		'returns `self.parent`'
		return self.parent
	def __repr__(self) -> str:
		'represent `self` as `self.link` between <>'
		return f'<{self.link}>'  # type: ignore
class GUI():  # pylint: disable=missing-class-docstring
	def __init__(self, settings: dict, files: list[dict[str, str]]) -> None:
		# setup vars
		self.settings = settings
		self.open_tabs = Dict({'Main': Dict({'name': 'Main'})})
		self.commands = {'/help': 'list all commands', '/debug': 'open debug tab', '/save': 'save all works in tab', '/reupdate': 'reupdate all works in tab', '/reload': 'close and reopen tab (without saving)', '/refresh': 'redraw table, Deprecated: just reload instead', '/close': 'close current tab (without saving)', '/exit': 'exit MangaRock with save', '/quit': 'exit MangaRock without save'}
		# create tab holder with main tab
		with ui.tabs().props('dense').on('update:model-value', self.switch_tab) as self.tabs:
			tab = ui.tab('Main')
		# create panel holder
		with ui.tab_panels(self.tabs, value=tab) as self.panels:
			# create main panel
			with ui.tab_panel('Main').style('height: calc(100vh - 84px); width: calc(100vw - 32px)'):
				ui.label('Choose File: ')
				gridOptions = {  # pylint: disable=invalid-name
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
		# create popup
		with ui.dialog() as self.popup, ui.card().props('square'):
			self.popup_text = ui.markdown('')
			ui.button('Close', on_click=self.popup.close).props('square')
		# setup semaphores for `update_all()`
		self.workers, self.renderers = asyncio.Semaphore(self.settings['workers']), asyncio.Semaphore(self.settings['renderers'])
		# css stuff and stuff
		ui.query('div').style('gap: 0')
		# run stuff
		ui.timer(0, self.stuff, once=True)
	def _input(self) -> ui.input:
		return ui.input(autocomplete=list(self.commands.keys())).on('keydown.enter', self.handle_input).props('square filled dense="dense" clearable clear-icon="close"').classes('flex-grow')
	def _debug(self) -> None:
		'opens debug tab'
		# if debug tab is already open, switch to it
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
	def jailbreak(self, grid: ui.aggrid, package: str = 'ag-grid-enterprise.min.js') -> ui.aggrid:
		'upgrade aggrid from community to enterprise'
		from pathlib import Path

		from nicegui.dependencies import register_library

		# if already jailbroken, return grid
		if grid.libraries[0].name == 'ag-grid-enterprise':
			return grid
		# check if targeted library is ag-grid-community
		assert grid.libraries[0].name == 'ag-grid-community', 'Overwriting NiceGUI aggrid ran into a tiny problem, got wrong lib'
		# if self.library does not exist, register library
		try:
			self.library
		except AttributeError:
			self.library = register_library(Path(package).resolve())  # pylint: disable=attribute-defined-outside-init
		# overwrite aggrid library with enterprise
		grid.libraries[0] = self.library
		# return grid
		return grid
	def switch_tab(self, event: GenericEventArguments | Dict) -> None:
		'switch to tab indicated by event'
		self.tabs.props(f"model-value={event.args}")
		self.panels.props(f"model-value={event.args}")
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
	def update_row(self, tab: Dict, link: Link, new_chapters: float = None, current_chapter: float = None) -> None:
		'updates row with new chapter count'
		row = tab.rows[link.index[tab.name]]
		# update "server side" data
		if new_chapters is not None:  # if new_chapter was provided
			row['nChs'] = new_chapters
			# determine visibility
			row['isVisible'] = int(not (
				new_chapters == 0 and self.settings['hide_unupdated_works'] or  # hide if no new chapters and hide_unupdated_works or
				int(new_chapters) == -999 and self.settings['hide_updates_with_errors']  # hide if new_chapters is error and hide_updates_with_errors
			))
		if current_chapter is not None: row['chapter'] = current_chapter  # if current chapter was provided
		# code to update "client side" data
		js = f'''
				var grid = getElement({tab.grid.id}).gridOptions.api;
				var node = grid.getRowNode('{link.link}').data;
				node.isVisible = {row['isVisible']};
			'''
		if new_chapters is not None: js += f'\nnode.nChs = {new_chapters};'  # if new_chapter was provided
		if current_chapter is not None: js += f'\nnode.chapter = {current_chapter};'    # if current chapter was provided
		# run the javascript
		with tab.grid:
			ui.run_javascript(js + '\ngrid.applyTransaction({update: [node]})')
	def save_tab(self, tab, name) -> None:
		'Saves all works in `Works.all` to file specified'
		from json import dump
		with open(self.settings['json_files_dir'] + name + '.json', 'w', encoding='utf8') as f:
			dump(list(tab.works.values()), f, indent='\t', default=lambda work: work.to_dict())
	async def _file_opened(self, event: GenericEventArguments) -> None:
		'runs when a file is selected in the main tab, creates a new tab for the file'
		def load_file(file: str) -> list | Any:
			'Runs `add_work(work)` for each work in file specified then returns the name of the file loaded'
			from json import load
			# def add_work(*args, _format: str = None, **kwargs) -> Work:
			# 	'formats `Type` argument and returns the created object'
			# 	# if no `_format` is provided: look for `format` in `kwargs`
			# 	if _format is None:
			# 		assert 'format' in kwargs, 'work has no format specified'
			# 		format = kwargs.pop('format')
			# 	# return works object
			# 	return Work(format, *args, **kwargs)

			with open(file, 'r', encoding='utf8') as f:
				return load(f, object_hook=lambda kwargs: Work(**kwargs))
		def generate_rowData(works: Iterable, tab: Dict):  # pylint: disable=invalid-name
			'turns list of works into list of rows that aggrid can use and group'
			index = 0
			# for each work in works
			for work in works:
				# if work format has no links or work has no links
				if 'links' not in work.prop or work.links == []:
					# add work to rows with isVisible set to 0 if hide_works_with_no_links is true else 1
					'work.index[tab.name] = index  # unnecessary'
					index += 1
					yield {**work, 'isVisible': 0 if self.settings['hide_works_with_no_links'] else 1}  # TODO: Low, do the shuffle up thing but down for works with no links, or maybe readd the disable opening rows with no children
				else:
					# for each link in work
					for link in work.links:
						# if link has updated and has no new chapters and hide_unupdated_works
						if link.new != '' and link.new == 0 and self.settings['hide_unupdated_works']:
							# skip this link
							continue
						# process link and add it to rows
						link.index[tab.name] = index
						index += 1
						tab.links[link.link] = link
						yield {**work, 'links': None, 'link': link.link, 'nChs': link.new, 'isVisible': 1}
		# extract file name from event
		tab_name = event.args['data']['name']
		# if file already open, switch to it
		if tab_name in self.open_tabs:
			self.switch_tab(Dict({'args': tab_name}))
			return
		# get columns to display
		assert tab_name in self.settings['to_display'], 'Columns for ' + tab_name + ' has not been specified in settings.yaml'  # make sure columns for file has been specified in settings, TODO: do something instead of crash
		cols = [{'field': 'isVisible', 'aggFunc': 'max', 'hide': True}]
		cols += [{'field': key, 'rowGroup': True, 'hide': True} if val[1] == 'group' else {'headerName': val[0], 'field': key, 'aggFunc': val[1], 'width': self.settings['default_column_width']} for key, val in self.settings['to_display'][tab_name].items()]  # convert into aggrid cols forma
		cols[-1]['resizable'] = False
		# load works from file and reference them in open_tabs
		works = load_file(self.settings['json_files_dir'] + tab_name + '.json')
		tab = self.open_tabs[tab_name] = Dict({'name': tab_name, 'works': {work.name: work for work in works}, 'links': {}, 'reading': None, 'open': set()})
		# generate rowData
		tab.rows = list(generate_rowData(works, tab))
		# create and switch to tab for file
		with self.tabs:
			tab.tab = ui.tab(tab_name)
		self.switch_tab(Dict({'args': tab_name}))
		# create panel for file
		with self.panels:
			with ui.tab_panel(tab_name).style('height: calc(100vh - 84px); width: calc(100vw - 32px)') as tab.panel:
				tab.label = ui.label('Reading: ')
				gridOptions = {  # pylint: disable=invalid-name
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
					'rowData': tab.rows,
					'rowHeight': self.settings['row_height'],
					'animateRows': True,
					'suppressAggFuncInHeader': True,
					'groupAllowUnbalanced': True,
					':getRowId': 'params => params.data.link',
					':isExternalFilterPresent': '() => true',
					':doesExternalFilterPass': 'params => params.data.isVisible',
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
	async def close_all_other(self, tab: Dict, event: GenericEventArguments) -> None:  # TODO: Low, add more comments
		'is called whenever a row is opened'
		tab_opened = event.args['rowId']
		# if the row being opened is a child of the currently opened row, do nothing
		if await ui.run_javascript(f'return getElement({event.sender.id}).gridOptions.api.getRowNode("{tab_opened}").parent.id') in tab.open:
			pass
			# TODO: Low, make this work to "advanced grouped rows", opening a sub row does not close the other opened sub rows of the same parent
		# if event was caused by (assumedly) closing the opened row, take note of it and `return`
		elif tab_opened in tab.open:
			tab.open.remove(tab_opened)
			return
		# if this event was called by a row being (auto) closed, do nothing
		elif not await ui.run_javascript(f"getElement({event.sender.id}).gridOptions.api.getRowNode('{tab_opened}').expanded"):
			return
		# else close all previous open row
		else:
			for open_tab in tab.open:
				ui.run_javascript(f'''
					var grid = getElement({event.sender.id}).gridOptions.api;
					grid.setRowNodeExpanded(grid.getRowNode("{open_tab}"), false);
				''')
		# set open to new opened row
		tab.open.add(tab_opened)
	async def update_all(self, tab: Dict) -> None:
		'updates all works provided'
		from requests_html2 import AsyncHTMLSession
		async def update_each(work: Work, tab: Dict, async_session: AsyncHTMLSession) -> None:
			try:
				if 'links' in work.prop:
					for link in work.links:  # type: ignore
						async with self.workers:
							# if debug tab open
							if 'debug' in self.open_tabs:
								self.open_tabs.debug.updating.add_rows({'name': link.link})
							# update link and row
							self.update_row(tab, link, await link.update(self.renderers, self.settings['sites'], self.settings['tags_to_skip'], async_session))
							# if debug tab open
							if 'debug' in self.open_tabs:
								self.open_tabs.debug.updating.remove_rows({'name': link.link})
								self.open_tabs.debug.done.add_rows({'name': link.link})
			except asyncio.CancelledError as e:
				print(e)  # TODO: if debug tab open, remove work from 'updating' column/card

		async with AsyncHTMLSession() as async_session:
			tab.tasks = asyncio.gather(*[update_each(work, tab, async_session) for work in tab.works.values()], return_exceptions=True)
			await tab.tasks
		print('done updating', tab.name)
	async def work_selected(self, tab: Dict, event: GenericEventArguments) -> None:  # TODO: Low, add comments
		'runs when a work is selected'
		def open_link(link: str) -> None:
			'opens link provided in new tab'
			ui.run_javascript(f"window.open('{link}')")
		event = Dict(event.args)
		# if neither work nor link was selected (not series, author, etc.), do nothing
		if 'name' not in event.rowId.split('-') and 'data' not in event: return  # NOTE: check for if this is work may break if work's name has `-name-` in it
		# if reading
		if tab.reading:
			# if link was selected
			if 'data' in event:
				# get link
				link = tab.links[event.value]
				# if same link is reselected or previous selected is a work and link selected is first
				if link == tab.reading or (isinstance(tab.reading, Work) and link == tab.reading.links[0]):
					# if link has not been updated yet
					if link.latest == '':
						print('link has not been updated yet')
						return
					# set work's chapter the link's latest chapter
					work = link.parent
					work.chapter = link.latest
					tab.reading = None
			# if name is selected
			else:
				# get work
				work = tab.works[event.value]
				# if same work is reselected or work selected is parent of reading link
				if work == tab.reading or tab.reading in work.links:
					# set work's chapter to latest chapter
					try:
						work.update()
					except (ValueError, TypeError):
						print('work has not been updated yet')
						return
					tab.reading = None
			# if no longer reading
			if not tab.reading:
				# change label
				tab.label.set_text('Reading:')
				# update grid
				for link in work.links:  # for each link in work that has been affected
					# update "server side" data
					self.update_row(tab, link, link.re(), work.chapter)
				return
		# if not reading or different work is selected
		# if link was selected
		if 'data' in event:
			# set reading to link and change label
			tab.reading = tab.links[event.value]
			tab.label.set_text('Reading: ' + tab.reading.parent.name)
			# open link
			open_link(event.value)
		# if is name
		else:
			# set reading to link and change label
			tab.reading = tab.works[event.value]
			tab.label.set_text('Reading: ' + tab.reading.name)
			# open link
			open_link(tab.reading.links[0].link)
	async def handle_input(self, event: GenericEventArguments) -> None:
		'handles input from input box'
		# if input is empty, do nothing
		if event.sender.value == '':
			return
		# get name of open tab, the tab, and the value
		name = self.tabs._props['model-value']  # pylint: disable=protected-access
		tab = self.open_tabs[name]
		entry = event.sender.value
		# if is a command
		if event.sender.value[0] == '/':
			# if is help command: list all commands
			if entry == '/help':
				self.popup_text.set_content('\n\n'.join([f"{key}: {val}" for key, val in self.commands.items()]))
				self.popup.open()
			# if is error command: open error codes
			elif entry == '/error':
				self.popup_text.set_content('''
					Error Codes:\n
					    -999.1: site not supported\n
					    -999.2: Connection Error\n
					    -999.3: rendering error, probably timeout\n
					    -999.4: parsing error\n
					    -999.5: whatever was extracted was not a number
				''')
				self.popup.open()
			# if is debug command: open debug tab
			elif entry == '/debug':
				self._debug()
			# if is reload command and not the main tab: reupdate all
			elif entry == '/reupdate' and name != 'Main':
				tab.tasks.cancel()
				await self.update_all(tab)
			# if is refresh command: re"draw" grid
			elif entry == '/refresh':
				tab.grid.update()
			# if is reload: re load file
			elif entry == '/reload':
				if name == 'Main':
					self.open_tabs.Main.grid.options['rowData'] = get_files(self.settings)
					self.open_tabs.Main.grid.update()
				else:
					self.close_tab(name)
					await self._file_opened(Dict({'args': {'data': {'name': name}}}))
			# if is save or exit command: save all works in tab and
			elif entry == '/save' and name != 'Main':
				self.save_tab(tab, name)
				ui.notify('Saved ' + name)
			elif entry == '/exit':
				# save all open tabs
				for name, tab in self.open_tabs.items():
					if name != 'Main':
						self.save_tab(tab, name)
						ui.notify('Saved ' + name)
				# close app
				app.shutdown()
			# if is close command: close current tab
			elif entry == '/close' and name != 'Main':
				self.close_tab(name)
			# if is quit command: exit without saving
			elif entry == '/quit':
				app.shutdown()
			elif entry == '/test':
				pass
			# if is not a command: eval or exec as python code and print output
			else:
				try:
					print(eval(entry[1:], globals(), locals()))  # pylint: disable=eval-used
				except Exception:  # pylint: disable=broad-exception-caught
					try:
						print(exec(entry, globals(), locals()))  # pylint: disable=exec-used
					except Exception as e:  # pylint: disable=broad-exception-caught
						print(e)  # pylint: disable=eval-used
		# if is not a command
		# if reading
		elif tab.reading:
			try:
				# if entry starts with +/-
				if event.sender.value[0] in ('+', '-'):
					# increase current chapter by input
					tab.reading.work().chapter += float(event.sender.value)
				# otherwise
				else:
					# set current chapter to input
					tab.reading.work().chapter = float(event.sender.value)
				# TODO: maybe merge the following few lines and the ones in `work_selected()` into a function
				# change label
				tab.label.set_text('Reading:')
				# update grid
				for link in tab.reading.work().links:
					self.update_row(tab, link, link.re(), tab.reading.work().chapter)
				# exit reading mode
				tab.reading = None
			except ValueError as e:
				print(e)
		else:
			# TODO: make it so you can select the work by name or something
			pass
		# clear input
		event.sender.set_value(None)
	async def stuff(self):
		async def autosave():
			import datetime

			import dateparser
			import pytimeparse

			# if autosave interval is not provided, disable autosave
			if self.settings['autosave']['interval'] is None:
				return
			# if autosave start is provided
			if self.settings['autosave']['start']:
				# try to parse then wait until start time
				try:
					await asyncio.sleep((dateparser.parse(self.settings['autosave']['start'], settings={'PREFER_DATES_FROM': 'future'}) - datetime.datetime.now()).total_seconds())
				except (ValueError, TypeError):
					ui.notify('failed to parse start time, starting now')
			# parse interval
			try:
				interval = float(self.settings['autosave']['interval']) * 60
			except ValueError:
				interval = pytimeparse.parse(self.settings['autosave']['interval'])
			if interval is None:
				with self.tabs:
					ui.notify('failed to parse interval, autosave disabled')
			elif interval <= 0:
				with self.tabs:
					ui.notify('autosave interval needs to be > 0, autosave disabled')
			else:
				while True:
					print('test')
					await asyncio.sleep(interval)
					for name, tab in self.open_tabs.items():
						if name != 'Main':
							self.save_tab(tab, name)
							with self.tabs:
								ui.notify('Saved ' + name)
		# "runs" stuff
		await asyncio.gather(autosave())


# pylint: disable-next=invalid-name
default_settings = '''
dark_mode: true  # default: true
font: [OCR A Extended, 8]  # [font name, font size], not yet implemented
json_files_dir: ./  # default: ./
tags_to_skip: [Skip, [Complete, Read]]  # works with specified tags will have update skipped and be hidden, [A, [B, C]] = A or (B and C)
autosave:  # default: null, null = disabled, accepts reasonable inputs (eg.: 8:30 pm, 30 min)
    start: null     # when to start autosaving, does nothing if interval is null
    interval: null  # interval to autosave, starts whenever if start is null, if is single number, assumes minutes
formats:  # each format can have its own properties, specify name of property and default value, name is required (i think)
    manga: {name: null, links: [], chapter: 0, series: null, author: null, score: null, tags: []}
to_display:  # columns to display for each Type, do not include name (it's required and auto included)
    example: {series: [Series, group], name: [Name, group], nChs: [New Chapters, max], chapter: [Current Chapter, first], tags: [Tags, first]}
default_column_width: 16  # default: 16
hide_unupdated_works: true  # default: true
hide_works_with_no_links: true  # default: true
hide_updates_with_errors: false  # default: false
row_height: 32  # default: 32
disable_col_dragging: true  # default: true
workers: 3  # default: 3
renderers: 1  # default: 1
sort_by: score  # default: score, score is currently only working option
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
    mangadex.org:      &011 [div,   class: text-center,         null,      null,          -|\\.,     -1,       true]
    null: [*001, *002, *003, *004, *005, *006, *007, *008, *009, *010, *011]  # for aligning reasons
    www.mcreader.net:  *006
    www.mangageko.com: *006
    chapmanganato.com: *008
    readmanganato.com: *008
'''
def main(name: str, *args, _dir: str | None = None, settings_file='settings.yaml') -> None:  # pylint: disable=unused-argument
	'Main function'
	# change environmental variables
	os.environ["MATPLOTLIB"] = "false"
	# change working directory to where file is located unless specified otherwise, just in case
	os.chdir(_dir or os.path.dirname(os.path.realpath(__file__)))
	if __debug__: print(f'working directory: {os.getcwd()}')
	# setup gui
	settings = load_settings(settings_file)
	gui = GUI(settings, get_files(settings))  # pylint: disable=unused-variable
	# start gui
	ui.run(dark=settings['dark_mode'], title=name.split('\\')[-1].rstrip('.pyw'), reload=False)
def load_settings(settings_file: str, _default_settings: str = default_settings) -> dict:
	'load and return settings from indicated file, overwriting default settings'
	def format_sites(settings_file: str) -> None:  # puts spaces between args so that the 2nd arg of the 1st list starts at the same point as the 2nd arg of the 2nd list and so on
		with open(settings_file, 'r', encoding='utf8') as f: file = f.readlines()  # loads settings_file into file
		start = [num for num, line in enumerate(file) if line[0:6] == 'sites:'][0]  # gets index of where 'sites:' start
		col = 0; adding = set(); done = set()
		# remove all extra spaces from 'sites:' line
		while '  ' in file[start][14:]:
			file[start] = file[start][:14] + file[start][14:].replace('  ', ' ')
		# remove all the other extra spaces
		for line_num in range(start, len(file)):
			while '   ' in file[line_num][4:]:
				file[line_num] = file[line_num][:4] + file[line_num][4:].replace('   ', '  ')
		# while not all lines have been formatted
		while len(done) != len(file[start:]):
			if len(adding) + len(done) == len(file[start:]): adding = set()  # if all lines after and including 'sites:' are in adding then remove everything from adding
			for line_num, line in enumerate(file[start:], start):  # for each line after and including 'sites:'
				if line[0:9] == '    null:': done.add(line_num)
				if line_num in done: continue  # skip completed lines
				if line[col] == '\n': done.add(line_num)  # add line's index to done when it reaches the end
				elif line_num in adding and line[col + 1] != ' ': file[line_num] = line[0:col] + ' ' + line[col:]  # if line is in adding and next char is not ' ' then add space into line at i
				elif line[col] == ',' or (line[col] == ':' and line[col + 1:].lstrip(' ')[0] in ('&', '*', '[')): adding.add(line_num)  # if elm endpoint is reached, add line into adding
			col += 1  # increase column counter
		with open(settings_file, 'w', encoding='utf8') as f: f.writelines(file)  # write file to settings_file

	import ruamel.yaml; yaml = ruamel.yaml.YAML(); yaml.indent(mapping=4, sequence=4, offset=2); yaml.default_flow_style = None; yaml.width = 4096  # setup yaml
	settings = yaml.load(_default_settings.replace('\t', ''))  # set default_settings
	try: file = open(settings_file, 'r', encoding='utf8'); settings.update(yaml.load(file)); file.close()  # try to overwrite the default settings from the settings_file
	except FileNotFoundError: print('settings file not found, creating new settings file')
	with open(settings_file, 'w', encoding='utf8') as file: yaml.dump(settings, file)  # save settings to settings_file
	format_sites(settings_file);   # format settings_file 'sites:' part

	# "save" formats to `Work`
	Work.formats = Dict(settings['formats'])
	# return settings
	return settings
def get_files(settings) -> list[dict[str, Any]]:
	'returns list of files in json_files_dir that ends with .json'
	return [{'name': file.split('.json')[0]} for file in os.listdir(settings['json_files_dir']) if file.split('.')[-1] == 'json']


if __name__ in {"__main__", "__mp_main__"}:
	import sys
	main(*sys.argv)
