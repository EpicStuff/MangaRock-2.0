# Version: 3.7.1, pylint: disable=invalid-name # ruff: noqa: ERA001, PLC0415
import asyncio
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Self

from epicstuff import BoxDict, Dict, open, rich_trace, rich_try, run_install_trace, show_locals, wrap  # noqa: F401, pylint: disable=W0611,W0622
from nicegui import app, ui
from nicegui.events import GenericEventArguments
from nicegui_aggrid import enterprise

show_locals(False)
enterprise('ag-grid-enterprise.min.js')


class Work(BoxDict):
	'''object representing a work, eg: a book, a series, a manga, etc.'''

	formats: Dict
	_protected_keys = BoxDict._protected_keys | {'formats', 'format'}  # noqa: SLF001

	def __init__(self, format: str, *args: list, **kwargs: dict) -> None:  # pylint:disable=redefined-builtin
		'''Applies args and kwargs to "`self.__dict__`" if kwarg is in `self.formats[format]`'''
		self.format = format
		props = self.formats[format]  # TODO: when format of work is not in settings, handle it instead of just crashing
		# convert args from list to dict then update them to kwargs
		kwargs.update({tuple(props.keys())[num]: arg for num, arg in enumerate(args) if arg not in ['', None, *kwargs.values()]})
		# set self properties to default property values
		super().__init__(props, _convert=True)  # pylint: disable=unexpected-keyword-arg
		# for every kwarg, format it and update `self` with it
		for key, val in kwargs.items():
			if key in self:
				self[key] = val
		# if no name was provided, generate a name
		if self.name is None: self.name = str(id(self))

		self._convert = False  # not super sure why i need this
	def _do_convert(self, value, key) -> Any:  # pylint: disable=unused-argument
		# if is format, do nothing
		if key == 'format':
			pass
		# if is link, turn links into Link objects
		elif key == 'links':
			# if only 1 link given (in the form of a str), convert to list
			if value.__class__ is str:
				value = [value]
			value = [Link(link, self) for link in value if not isinstance(link, Link)]
		else:
			props = self.formats[self.format]
			# if given val is a tuple then turn given val into a list
			if isinstance(value, tuple): value = list(value)
			# if given val is list and default val is not list then unlist list
			if isinstance(value, list) and not isinstance(props[key], list):
				# if multiple items in list then raise error
				if len(value) > 1:
					raise TypeError('unexpected multiple values within array')
				# else unlist list
				value = value[0]
			# if default val is list and given val is not list then put given val in a list
			elif isinstance(props[key], list) and not isinstance(value, list): value = [value]
			# if default val is int or float and given val is not float then float given val
			if isinstance(props[key], (int, float)) and not isinstance(value, (int, float)): value = float(value)
			# if default val is int and given val is a decimal-les (without decimals) float : convert to int
			if isinstance(value, float) and int(value) == value:
				value = int(value)
		# return converted value
		return value
	def re(self):
		'Why is this called re? no idea'
		# create list of links' latest chapters excluding errors and empty strings then get max
		self.chapter = max([link.latest for link in self.links if not issubclass(link.latest.__class__, Exception) and link.latest != ''])
		# update new chapters for each link
		for link in self.links:  # pylint: disable=no-member
			link.re()
	def sort(self):
		pass
	def to_dict(self) -> dict:
		'Returns `self` as a dictionary'
		# d = {'format': self.format}
		# for key, val in self.items():
		# 	if val in ([], "None", None):
		# 		continue
		# 	if key in ('lChs', 'prop'):
		# 		continue
		# 	if key == 'name' and val == str(id(self)):
		# 		continue
		# 	if key == 'links':
		# 		d[key] = [link.to_dict() for link in val]
		# 	else:
		# 		d[key] = val
		# return d
		return {
			**{'format': self.format},
			**{
				key: val if key != 'links' else [link.to_dict() for link in val] for key, val in self.items()
				if val not in ([], "None", None)
				if key not in ('lChs', 'prop')
				if not (key == 'name' and val == str(id(self)))
			},
		}  # convert attributes to a dictionary
	def work(self) -> Self:
		'Returns `self`'
		return self
	def __str__(self) -> str:
		'Returns `self` in `str` format'
		return '<' + self.format + ' Object: {' + ', '.join([f'{key}: {val}' for key, val in self.items() if key != 'name' and val != []]) + '}>'
	def __repr__(self) -> str:
		'Represent `self` as `self.name` between <>'
		return f'<{self.name}>'  # pylint: disable=no-member
class Link():
	'Link object, can be updated to get latest chapter'

	def __init__(self, link: str, parent: Work) -> None:
		if not link.startswith('http'): link = 'https://' + link
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
			-999.5 = whatever was extracted was not a number
			-999.6 = failed to load plugin
			-999.7 = plugin error'''
		import re

		import bs4

		# if site is not supported
		if self.site not in sites:
			self.latest = Exception('site not supported')  # site not supported
			return self.re(-999.1)
		# variables
		link = self.link
		sites = sites[self.site]
		# if tags specified in settings are in work, skip
		if 'tags' in self.parent:
			# for each tag/list of tags that are to be skipped
			for tag in tags_to_skip:
				# if tag is str and in work, "skip"
				if tag.__class__ is str and tag in self.parent.tags:
					self.latest = Exception('skipped')
					return self.re(0)
				# if tag is list and all tags in list are in work
				if isinstance(tag, list) and all([t in self.parent.tags for t in tag]):
					self.latest = Exception('skipped')
					return self.re(0)
		# if is "plugin"
		if sites[0].split('.')[-1] in ('py', 'pyw'):
			# import plugin
			try:
				plugin = __import__(sites[0][:-3]).__dict__[sites[1]]
			except (ModuleNotFoundError, KeyError) as e:
				console.print_exception(show_locals=True, width=os.get_terminal_size().columns)
				print('plugin loading error:', self.link)
				self.latest = e
				return self.re(-999.6)
			# run plugin
			try:
				self.latest = plugin(self.link)
				return self.re()
			except Exception as e:
				console.print_exception(show_locals=True, width=os.get_terminal_size().columns)
				print('plugin error:', self.link)
				self.latest = e
				return self.re(-999.7)
		# tmp: special stuff for bato.to
		if self.site == 'bato.to': link = self.link.replace('title/', 'rss/series/') + '.xml'
		# tmp: special stuff for royalroad
		if self.site == 'www.royalroad.com':
			import time
			time.sleep(1)
		# connecting to site
		try:
			link = await async_session.get(link, follow_redirects=True)  # connecting to the site
			assert link.status_code == 200  # make sure connection was successful
		except Exception as e:  # connection error
			print('connection error:', self.link)
			# link = str(link)
			# console.print_exception(show_locals=True, width=os.get_terminal_size().columns)
			self.latest = e
			return self.re(-999.2)
		# if site needs to be rendered, render
		if sites[6]:
			try:
				# print('rendering', self.link, '-', self.site)
				async with renderers:  # limit the number of works rendering at a time
					# render link
					async with link.async_render(reload=True, wait_until='networkidle'): pass
				# print('done rendering', self.link, '-', self.site)
			except Exception as e:
				print('failed to render:', self.link)  # render error
				link = str(link)
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
			if sites[2] is None and sites[3] is None:
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
			link = str(link)
			console.print_exception(show_locals=True, width=os.get_terminal_size().columns)
			self.latest = e  # parsing error
			return self.re(-999.4)
		# convert remaining html to float
		try:
			self.latest = float(re.split(sites[4], link)[sites[5]])  # else link parsing went fine: extract latest chapter from link using lookup table
			# convert latest chapter to int if has .0
			if int(self.latest) == self.latest:
				self.latest = int(self.latest)
		except Exception as e:
			link = str(link)
			console.print_exception(show_locals=True, width=os.get_terminal_size().columns)
			self.latest = e  # whatever was extracted was not a number
			return self.re(-999.5)

		return self.re()
	def re(self, new: float = None) -> int | float:
		'Updates `self.new` from `new` arg or calculates if not provided, then returns `self.new`'
		# why this function is called re? I have no idea
		if new is None:
			if not issubclass(self.latest.__class__, Exception):
				new = round(self.latest - self.parent.chapter, 4)
			else:
				new = self.new
		self.new = new
		return new
	def to_dict(self):
		'Convert `self` to a string'
		return self.link
	def work(self) -> Work:
		'Returns `self.parent`'
		return self.parent
	def __repr__(self) -> str:
		'Represent `self` as `self.link` between <>'
		return f'<{self.link}>'
class GUI():  # pylint: disable=missing-class-docstring
	styles = Dict({
		'tab_panel': 'height: calc(100vh - 84px); width: calc(100vw - 32px)',
	})
	def __init__(self, settings: dict, files: list[dict[str, str]]) -> None:
		# setup vars
		self.settings = settings
		self.open_tabs = Dict({'Main': Dict({'name': 'Main'})})
		self.commands = {'/help': 'list all commands', '/debug': 'open debug tab', '/save': 'save all works in tab', '/reupdate': 'reupdate all works in tab', '/reload': 'close and reopen tab (without saving)', '/refresh': 'redraw table, Deprecated: just reload instead', '/close': 'close current tab (without saving)', '/exit': 'exit MangaRock with save', '/quit': 'exit MangaRock without save'}
		# create tab holder with main tab
		with ui.tabs().props('dense') as self.tabs:
			tab = ui.tab('Main')
		# create panel holder
		with ui.tab_panels(self.tabs, value=tab) as self.panels:
			# create main panel
			with ui.tab_panel('Main').style(GUI.styles.tab_panel):
				ui.label('Choose File: ')
				gridOptions = {  # pylint: disable=invalid-name  # noqa: N806
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
				self.open_tabs.Main.grid = ui.aggrid(gridOptions, theme='balham').style('height: calc(100vh - 164px)').on('cellDoubleClicked', self._file_opened)
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
		return ui.input(autocomplete=list(self.commands.keys())).on('keydown.enter', self._handle_input).props('square filled dense="dense" clearable clear-icon="close"').classes('flex-grow')
	def _debug(self) -> None:
		'Opens debug tab'
		# if debug tab is already open, switch to it
		if 'debug' in self.open_tabs:
			self.tabs.set_value('Debug')
			return
		# else create tab
		self.open_tabs.debug = Dict()
		with self.tabs:
			ui.tab('Debug')
		with self.panels:
			with ui.tab_panel('Debug').style(GUI.styles.tab_panel):
				ui.label('Updating:')
				with ui.row().classes('w-full'):
					self.open_tabs.debug.updating = ui.table(columns=[{'name': 'name', 'label': 'updating', 'field': 'name'}], rows=[], row_key='name')
					self.open_tabs.debug.done = ui.table(columns=[{'name': 'name', 'label': 'done', 'field': 'name'}], rows=[], row_key='name')
		# switch to tab
		self.tabs.set_value('Debug')
	def close_tab(self, tab_name: str) -> None:
		'Closes indicated tab'
		# get tab
		tab = self.open_tabs[tab_name]
		# cancel updating works in tab (if tab has tasks)
		if 'tasks' in tab: tab.tasks.cancel()
		# delete stuff
		tab.panel.delete()
		tab.tab.delete()
		del self.open_tabs[tab_name]
		# switch to main tab
		self.tabs.set_value('Main')  # TODO: low, switch to last tab instead of main
	def update_row(self, tab: Dict, link: Link, new_chapters: float = None, current_chapter: float = None) -> None:
		'Updates row with new chapter count'
		# get row
		row = tab.rows[link.index[tab.name]]
		# update "server side" data
		if new_chapters is not None:  # if new_chapter was provided
			row['nChs'] = new_chapters
			# determine visibility
			row['isVisible'] = int(not (
				new_chapters == 0 and self.settings['hide_unupdated_works'] or  # hide if no new chapters and hide_unupdated_works or
				int(new_chapters) == -999 and self.settings['hide_errored_updates']  # hide if new_chapters is error and hide_updates_with_errors
			))
		if current_chapter is not None: row['chapter'] = current_chapter  # if current chapter was provided
		# code to update "client side" data
		js = f'''
				var grid = getElement({tab.grid.id}).gridOptions.api;
				var node = grid.getRowNode('{link.link}').data;
				node.isVisible = {row['isVisible']};
			'''
		if new_chapters is not None: js += f'\nnode.nChs = {new_chapters};'  # if new_chapter was provided
		if current_chapter is not None: js += f'\nnode.chapter = {current_chapter};'  # if current chapter was provided
		# run the javascript
		with tab.grid:
			ui.run_javascript(js + '\ngrid.applyTransaction({update: [node]})')
	async def button_pressed(self):
		'Runs when the button in opened file tab is pressed'
		# name = self.tabs._props['model-value']  # pylint: disable=protected-access
		name = self.tabs.value
		tab = self.open_tabs[name]
		# get selected work, if any
		selected = await tab.grid.get_selected_row() or await ui.run_javascript(f'return getElement({tab.grid.id}).gridOptions.api.getSelectedNodes()[0].groupData')
		# if no work is selected, do nothing
		if not selected:
			print('no work selected')
		else:
			self.edit_work(tab.works[list(selected.values())[0]])
	def edit_work(self, work):
		'Opens new tab to allow for editing a work\'s properties'
		def apply(inputs, work):
			'Applies changes to work'
			for key, val in inputs.items():
				if val.__class__ is ui.textarea:
					work[key] = val.value.split('\n')
				else:
					work[key] = val.value
			# TODO: make sure that the old links got deleted/garbage collected and aren't just floating around somewhere
		# if file already open, switch to it
		if work.name in self.open_tabs:
			self.tabs.set_value(work.name)
			return
		# create Dict for edit work tab and store in open_tabs
		tab = self.open_tabs[work.name] = Dict({'name': work.name})
		# create and switch to tab for file
		with self.tabs:
			tab.tab = ui.tab(work.name)
		self.tabs.set_value(work.name)
		# create panel for file
		with self.panels:
			with ui.tab_panel(tab.tab).style(GUI.styles.tab_panel) as tab.panel:
				ui.label(f'Editing: {work.name}')
				# list to store inputs
				inputs = Dict()
				# for each one of work's properties
				for key, val in work.items():
					# if key is not 'links'
					with ui.row().classes('w-full'):
						# ui.label(key)
						if key == 'links':
							inputs[key] = ui.textarea(key.title(), value='\n'.join([link.to_dict() for link in val])).classes('w-full')
						elif val.__class__ is list:
							inputs[key] = ui.textarea(key.title(), value='\n'.join(val)).classes('w-full')
						else:
							inputs[key] = ui.input(key.title(), value=val).classes('w-full')
				# create buttons to close or apply tab
				with ui.row().classes('w-full'):
					ui.button('Close', on_click=wrap(self.close_tab, work.name)).props('square')
					ui.button('Apply', on_click=wrap(apply, inputs, work)).props('square')
	def save_tab(self, tab, name) -> None:
		'Saves all works in `Works.all` to file specified'
		from json import dump
		with open(self.settings['json_files_dir'] + name + '.json', 'w') as f:
			dump([work.to_dict() for work in tab.works.values()], f, indent='\t')
	@rich_try
	async def _file_opened(self, event: GenericEventArguments) -> None:
		'Runs when a file is selected in the main tab, creates a new tab for the file'
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

			with Path(file).open() as f:
				return load(f, object_hook=lambda kwargs: Work(**kwargs))

		def sort(works: dict | list, settings):
			'''Sort `cls.all` by given dict, defaults to name'''
			was_dict = works.__class__ is dict
			# if `what` is a dict, convert it to a list
			if was_dict:
				works = works.values()
			# sort
			for sort_by in settings.sort_by:
				if sort_by == 'name':
					# for each work in `works` sort by `work.name`
					works.sort(key=lambda work: work.name)
				else:
					try:
						lookup = settings[sort_by + 's']
					except KeyError:
						print('failed to lookup/sort by', sort_by + 's')
					else:
						# for each work in `works` get `work.sort_by` and convert into number through look up table
						works.sort(key=lambda work: lookup[work[sort_by]], reverse=True)
			# if was a dict, convert it back to a dict
			if was_dict:
				works = {work.name: work for work in works}
			return works

		def generate_rowData(works: Iterable, tab: Dict):  # pylint: disable=invalid-name
			'Turns list of works into list of rows that aggrid can use and group'
			index = 0
			# for each work in works
			for work in works:
				# if work format has no links or work has no links
				if 'links' not in work or work.links == []:
					# add work to rows with isVisible set to 0 if hide_works_with_no_links is true else 1
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
			self.tabs.set_value(tab_name)
			return
		# get columns to display
		assert tab_name in self.settings['to_display'], 'Columns for ' + tab_name + ' has not been specified in settings.yaml'  # make sure columns for file has been specified in settings, TODO: do something instead of crash
		cols = [{'field': 'isVisible', 'aggFunc': 'max', 'hide': True}]
		# convert into aggrid cols format
		for key, val in self.settings.to_display[tab_name].items():
			if val[1] == 'group':
				cols.append({'field': key, 'rowGroup': True, 'hide': True})
			else:
				cols.append({'headerName': val[0], 'field': key, 'aggFunc': val[1], 'width': self.settings['default_column_width']})
		cols[-1]['resizable'] = False
		cols[-1]['flex'] = 1  # TODO: test
		# load and sort works from file and reference them in open_tabs
		works = sort(load_file(self.settings['json_files_dir'] + tab_name + '.json'), self.settings)
		tab = self.open_tabs[tab_name] = Dict({
			'name': tab_name,
			'works': {work.name: work for work in works},
			'links': Dict(),
			'reading': None,
			'open': set(),
		})
		# generate rowData
		tab.rows = list(generate_rowData(works, tab))
		# create and switch to tab for file
		with self.tabs:
			tab.tab = ui.tab(tab_name)
		self.tabs.set_value(tab_name)
		# create panel for file
		with self.panels:
			with ui.tab_panel(tab_name).style(GUI.styles.tab_panel) as tab.panel:
				tab.label = ui.label('Reading: ')
				gridOptions = {  # pylint: disable=invalid-name
					'defaultColDef': {
						'resizable': True,
						'suppressMenu': True,
						'suppressMovable': self.settings['disable_col_dragging'],
						'cellRendererParams': {'suppressCount': True},
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
					'rowSelection': 'single',
					':getRowId': 'params => params.data.link',
					':isExternalFilterPresent': '() => true',
					':doesExternalFilterPass': 'params => params.data.isVisible',
				}
				tab.grid = ui.aggrid(gridOptions, theme='balham', auto_size_columns=False).style('height: calc(100vh - 164px)')
				tab.grid.on('rowGroupOpened', wrap(self._close_all_other, tab))
				tab.grid.on('cellDoubleClicked', wrap(self._work_selected, tab))
				with ui.row().classes('w-full').style('gap: 0'):
					self._input()  # .style('width: 8px; height: 8px; border:0px; padding:0px; margin:0px')
					ui.button(on_click=self.button_pressed).props('square').style('width: 40px; height: 40px;')
		# update all works
		await asyncio.sleep(1)
		await self.update_all(tab)
	async def _close_all_other(self, tab: Dict, event: GenericEventArguments) -> None:  # TODO: Low, add more comments
		'Is called whenever a row is opened'
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
		'Updates all works provided'
		from requests_html2 import AsyncHTMLSession

		async def update_each(work: Work, tab: Dict, async_session: AsyncHTMLSession) -> None:
			try:
				if 'links' in work:
					for link in work.links:
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
	async def _work_selected(self, tab: Dict, event: GenericEventArguments) -> None:  # TODO: Low, add comments
		'Runs when a work is selected'
		def open_link(link: str) -> None:
			'Opens link provided in new tab'
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
						work.re()
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
	async def _handle_input(self, event: GenericEventArguments) -> None:
		'Handles input from input box'
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
				# tab.grid.options['rowData'] =
				# tab.grid.update()
				pass  # TODO: update every row using javascript instead of tab.grid.update() so that it doesn't reset stuff
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
						print(exec(entry[1:], globals(), locals()))  # pylint: disable=exec-used
					except Exception:  # pylint: disable=broad-exception-caught
						console.print_exception(width=os.get_terminal_size().columns)
						print(entry)
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
					sleep_time = dateparser.parse(self.settings['autosave']['start'], settings={'PREFER_DATES_FROM': 'past'}) - datetime.datetime.now()
					if sleep_time < datetime.timedelta():
						sleep_time += datetime.timedelta(1)
					await asyncio.sleep(sleep_time.total_seconds())
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
					# save all open files
					for name, tab in self.open_tabs.items():
						if name != 'Main':
							self.save_tab(tab, name)
							with self.tabs:
								ui.notify('Saved ' + name)
					# wait interval
					await asyncio.sleep(interval)
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
    Manga: {name: null, links: [], chapter: 0, series: null, author: null, score: null, tags: []}
    Text: {name: null, links: [], chapter: 0, series: null, author: null, score: null, tags: []}
    Series: {name: null, links: [], volume: 0, author: null, score: null, tags: []}
to_display:  # columns to display for each file, {parameter name: [display name, aggFunc]}
	example: {series: [Series, group], name: [Name, group], nChs: [New Chapters, max], chapter: [Current Chapter, first], tags: [Tags, first]}
sort_by: [name, score]  # default: [name, score], will sort by name then score, default is currently the only working option
check_only_first_x_links: 0  # default: 0, 0 = check all links, will only check/update first x links then hide the rest, not yet implemented
hide_unupdated_works: true  # default: true
hide_works_with_no_links: true  # default: true
hide_errored_updates: false  # default: false
default_column_width: 32  # default: 32
row_height: 32  # default: 32
disable_col_dragging: true  # default: true
workers: 3  # default: 3
renderers: 1  # default: 1
scores: {no Good: -1, null: 0, ok: 1, ok+: 1.1, decent: 1.5, Good-: 1.5, Good: 2, Good+: 2.1, Great: 3}  # numerical value of score used when sorting by score
sites_ignore: []
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
	wattpad.com:       &012 [./plugins/wattpad.py, main]
	null: [*001, *002, *003, *004, *005, *006, *007, *008, *009, *010, *011]  # for aligning reasons
	www.mcreader.net:  *006
	www.mangageko.com: *006
	chapmanganato.com: *008
	readmanganato.com: *008
'''
def main(name: str, *, _dir: str | None = None, settings_file=Path('settings.taml')) -> None:  # pylint: disable=unused-argument
	'Main function.'
	# change environmental variables
	os.environ["MATPLOTLIB"] = "false"
	# change working directory to where file is located unless specified otherwise, just in case
	os.chdir(_dir or Path(__file__).parent)
	if __debug__: print(f'working directory: {Path.cwd()}')
	# setup gui
	settings = load_settings(settings_file)
	with rich_trace:
		gui = GUI(settings, get_files(settings))  # trunk-ignore(pylint/W0612)
	# start gui
	ui.run(dark=settings['dark_mode'], title=name.split('\\')[-1].rstrip('.pyw'), reload=False, show=False)
def load_settings(settings_file: Path, _default_settings: str = default_settings) -> dict:
	'Load and return settings from indicated file, overwriting default settings'
	def format_sites(settings_file: Path) -> None:  # puts spaces between args so that the 2nd arg of the 1st list starts at the same point as the 2nd arg of the 2nd list and so on
		with settings_file.open() as f: file = f.readlines()  # loads settings_file into file
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

	from taml import taml
	taml.width = 4096
	settings = taml.loads(_default_settings)  # set default_settings
	try:
		with settings_file.open() as file:
			settings.update(taml.load(file))
	except FileNotFoundError:
		print('settings file not found, creating new settings file')
	# "fix" json_files_dir if necessary
	if settings.json_files_dir[-1] != '/': settings.json_files_dir += '/'
	with settings_file.open('w') as file:
		data = settings.data
		taml.dump(data, file)  # save settings to settings_file  # ruff-ignore(pylint/W0212)
	format_sites(settings_file)   # format settings_file 'sites:' part
	# "save" formats to `Work`
	Work.formats = Dict(settings.formats)
	# return settings
	return settings
def get_files(settings) -> list[dict[str, Any]]:
	'Returns list of files in json_files_dir that ends with .json'
	return [{'name': file.split('.json')[0]} for file in os.listdir(settings['json_files_dir']) if file.split('.')[-1] == 'json']


if __name__ in {"__main__", "__mp_main__"}:
	import sys

	import nicegui
	print('Using nicegui version:', nicegui.__version__)
	main(*sys.argv)
