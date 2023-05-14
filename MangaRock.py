# Version: 3.3.1
# okay, heres the plan, make links its own separate object and have the links update individualy. when the updates, it will then update its parent's display
import os
from nicegui import ui
from typing import Callable

class Type():  # type represents the type of object things are, eg: authors, books, website, ...
	''' Base Type class to be inherited by subclasses to give custom properties\n
	Custom Book class Example: `class Book(Type): all = {}; prop = {'name': None, 'author': None, 'score': None, 'tags': []}`'''
	prop = {'name': None}; all = []  # prop is short for properties, dict provided by sub object; all = list of all loaded obj/works of this class, eg = incase user wishes to iterate through all books
	def __init__(self, *args: list, **kwargs: dict) -> None:
		'''Applies args and kwargs to `self.__dict__` if kwarg is in `self.prop`'''
		kwargs.update({tuple(self.prop.keys())[num]: arg for num, arg in enumerate(args) if arg not in {'', None, *kwargs.values()}})  # convert args into kwargs and update them to kwargs
		if kwargs['name'] == '': kwargs['name'] = self.__class__.all.__len__  # if no name was provided use number as name
		self.__dict__.update(self.prop); Type.all.append(self); self.__class__.all[kwargs['name']] = self  # set self properties to default property values; add self to Works.all; add self to it's class' all dict with name as key
		for key, val in kwargs.items():  # for every kwarg given
			if key in self.__dict__:  # if key of kwarg is in properties
				if val.__class__ is tuple: val = list(val)  # if given val is a tuple then turn given val into a list
				if val.__class__ is list and type(self.prop[key]) is not list:  # if given val is list and default val is not list then
					if val.__len__ > 1: raise TypeError('unexpected multiple values within array')  # if multiple items in list then raise error
					else: val = val[0]  # else unlist list
				elif self.prop[key].__class__ is list and val.__class__ is not list: val = [val]  # if default val is list and given val is not list then put given val in a list
				if self.prop[key].__class__ is int and val.__class__ is not float: val = float(val)  # if default val is float and given val is not float then float given val
				self.__dict__.update({key: val})  # change self property value to given kwarg value

		if 'links' in self.prop:
			for num, link in enumerate(self.links):
				self.links[num] = Link(link)
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
	def __iter__(self) -> object: return self  # required for to iter over
	def __str__(self) -> str: return '<' + self.__class__.__name__ + ' Object: {' + ', '.join([f'{key}: {val}' for key, val in self.__dict__.items() if key != 'name' and val != []]) + '}>'  # returns self in str format
	def __repr__(self) -> str: return f'<{self.name}>'  # represent self as self.name between <>
class Manga(Type):  all = {}; prop = {'name': None, 'links': [], 'chapter': 0, 'series': None, 'author': None, 'score': None, 'tags': []}
class Anime(Type):  all = {}; prop = {'name': None, 'links': [], 'episode': 0, 'series': None, 'score': None, 'tags': []}
class Text(Type):   all = {}; prop = {'name': None, 'links': [], 'chapter': 0, 'fandom': None, 'author': None, 'series': None, 'score': None, 'tags': []}
class Link():
	def __init__(self, link: str) -> None:
		self.site = link.split('/')[2]
		self.link = link
		self.latest = ''
	async def update(self, asession, renderers, sites: dict) -> int | Exception:
		'Finds latest chapter from `self.link` then sets result or an error code to `self.latest`'
		import re, bs4
		# if site is supported
		if self.site not in sites:
			self.latest = Exception('site not supported')  # site not supported
			return
		# connecting to site
		try:
			link = await asession.get(link)  # connecting to the site
		except Exception as e:  # connection error
			self.chs = e
			return
		# render site if necessary
		try:
			if sites[self.site][6]:  # if needs to be rendered
				if __debug__: print('rendering', self.link, '-', self.site)
				with renderers:
					await link.html.arender(retries=2, wait=1, sleep=2, timeout=20, reload=True)
				if __debug__: print('done rendering', self.link, '-', self.site)
		except Exception as e:
			print('failed to render: ', self.name, ' - ', self.site, ', ', e, sep='')  # render error
			self.latest = e
			return

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
			return

		try:
			self.latest = float(re.split(sites[self.site][4], link)[sites[self.site][5]])  # else link parsing went fine: extract latest chapter from link using lookup table
		except Exception as e:
			self.latest = e  # whatever was extracted was not a number


default_settings = '''
dark_mode: true # default: true
font: [OCR A Extended, 8] # [font name, font size]
default_column_width: 32
row_height: 32
to_display: # culumns to display for each Type, do not include name (it's required and auto included)
    Manga: {nChs: [New Chapters, max], chapter: [Current Chapter, first], tags: [Tags, first]}
    example: {nChs: [New Chapters, max], chapter: [Current Chapter, first], tags: [Tags, first]}
workers: 3
renderers: 1
hide_unupdated_works: true # default: true
hide_works_with_no_links: true # default: true
sort_by: score # defulat: score
# prettier-ignore
scores: {no Good: -1, None: 0, ok: 1, ok+: 1.1, decent: 1.5, Good: 2, Good+: 2.1, Great: 3} # numerical value of score used when sorting by score
# prettier-ignore
sites: #site,                 find,  with,                       then_find, and get,       split at, then get, render?
    manganato.com:      &001 [ul,    class: row-content-chapter, a,         href,          '-',      -1,       false]
    www.webtoons.com:   &002 [ul,    id: _listUl,                li,        id,            _,        -1,       false]
    manhuascan.com:     &003 [div,   class: list-wrap,           a,         href,          '-',      -1,       false]
    zahard.xyz:         &004 [ul,    class: chapters,            a,         href,          /,        -1,       false]
    www.royalroad.com:  &005 [table, id: chapters,               null,      data-chapters, ' ',      0,        false]
    1stkissmanga.io:    &006 [li,    class: wp-manga-chapter,    a,         href,          -|/,      -2,       false]
    comickiba.com:      &007 [li,    class: wp-manga-chapter,    a,         href,          -|/,      -2,       true]
    asura.gg:           &008 [span,  class: epcur epcurlast,     null,      null,          ' ',      1,        false]
    mangapuma.com:      &009 [div,   id: chapter-list-inner,     a,         href,          '-',      -1,       false]
    bato.to:            &010 [item,  null,                       title,     null,          ' ',      -1,       false]
    www.manga-raw.club: &011 [ul,    class: chapter-list,        a,         href,          -|/,      -4,       false]
    null: [*001, *002, *003, *004, *005, *006, *007, *008, *009, *010, *011] # for formatting reasons
    chapmanganato.com:  *001
    readmanganato.com:  *001
    nitroscans.com:     *007
    anshscans.org:      *007
    flamescans.org:     *008
    www.mcreader.net:   *011
'''
def main(name, dir=os.getcwd().replace('\\', '/'), settings_file='settings.yaml', *args):
	import asyncio
	def load_settings(settings_file: str, default_settings: str) -> dict:
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
		try: file = open(settings_file, 'r'); settings.update(yaml.load(file)); file.close()  # try to overwrite the default settings from the settings_file
		except FileNotFoundError as e: print(e)  # except: print error
		with open(settings_file, 'w') as file: yaml.dump(settings, file)  # save settings to settings_file
		format_sites(settings_file); return settings  # format settings_file 'sites:' part then return settings
	async def enter_reading_mode_for_file(file: dict) -> None:
		def load_file(file: str) -> list:
			'Runs `add_work(work)` for each work in file specified then returns the name of the file loaded'
			def add_work(format: str | Type, *args, **kwargs) -> Type:
				'formats `Type` argument and returns the created object'
				if format.__class__ is str: format = eval(format)  # if the format is a string, turn in into an object
				return format(*args, **kwargs)  # return works object

			with open(file, 'r') as file:
				import json
				return json.load(file, object_hook=lambda kwargs: add_work(**kwargs))

		file = file['args']['data']['name']
		if file in gui.open_tabs:
			gui.switch_tab({'args': file})
			return

		cols = [{'headerName': 'Name', 'field': 'name', 'rowGroup': True, 'hide': True},]
		try:
			for key, val in settings['to_display'][file].items():  # todo: maybe turn into list comprehension
				cols.append({'headerName': val[0], 'field': key, 'aggFunc': val[1], 'width': settings['default_column_width']})
		except KeyError as e:
			print('Columns for', e, 'has not been specified in settings.yaml'); raise Exception  # todo: setup default columns instead of crash
		cols[-1]['resizable'] = False

		gui.open_tabs[file] = load_file(file + '.json')
		gui.mode_reading(file, cols, generate_rowData(gui.open_tabs[file]), open_work)

		await update_all(gui.open_tabs[file])
	async def update_all(works: list | tuple) -> None:
		'updates all works provided'
		async def update_each(work: Type) -> None:
			if 'links' in work.prop:
				for link in work.links:
					async with workers:
						if __debug__: print('updating', link.link, '-', link.site)
						await link.update(asession, renderers, settings['sites'])
						if __debug__: print('done updating', link.link, '-', link.site)
					pass  # todo: update link in gui
			update_grid()

		from requests_html import AsyncHTMLSession
		asession = AsyncHTMLSession()
		workers, renderers = asyncio.Semaphore(settings['workers']), asyncio.Semaphore(settings['renderers'])
		await asyncio.gather(*[update_each(work) for work in works])
	def generate_rowData(works, rows=[]):
		for work in works:
			for link in work.links:
				rows.append({'name': work.name, 'link': link.link, 'chapter': work.chapter, 'tags': work.tags},)

		return rows
	def open_work(event): print('selected events:', event)

	os.chdir(dir)  # change working directory to where file is located unless specified otherwise
	gui = GUI(load_settings(settings_file, default_settings))  # load settings and setup gui
	gui.mode_loading([{'name': file.split('.json')[0]} for file in os.listdir() if file[-5:] == '.json'], enter_reading_mode_for_file)
	# enter_reading_mode_for_file gets called by gui.mode_loading when a file is selected
	# update_all gets called by enter_reading_mode_for_file once it its done
	ui.run(dark=True, title=name.split('\\')[-1].rstrip('.pyw'))


class GUI():
	def __init__(self, settings: dict) -> None:
		self.settings = settings
		self.open_tabs = {'Main': {}}
		ui.query('div').style('gap: 0')
		with ui.tabs().props('dense') as self.tabs:
			ui.tab('Main')
		self.tab_panels = ui.tab_panels(self.tabs, value='Main')
	def switch_tab(self, event: dict):
		self.tabs.props(f'model-value={event["args"]}')
		self.tab_panels.props(f'model-value={event["args"]}')
	def update_grid(self, tab):
		rows = generate_rowData(self.open_tabs[tab])
		gui.
	def mode_loading(self, files: list, func_select: Callable) -> None:
		with self.tab_panels:
			with ui.tab_panel('Main').style('height: calc(100vh - 84px); width: calc(100vw - 32px)'):  # create main tab panel
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
					# 'rowStyle': {'margin-top': '-4px'}  # not doing anything
				}
				self.grid = ui.aggrid(gridOptions, theme='alpine-dark').style('height: calc(100vh - 164px)').on('cellDoubleClicked', func_select)
				with ui.row().classes('w-full'):
					ui.input().props('square filled dense="dense" clearable clear-icon="close"').classes('flex-grow')
					ui.button().props('square').style('width: 40px; height: 40px;')
	def mode_reading(self, file: str, columnDefs: list, rowData: list, func_select: Callable) -> None:
		self.tabs.on('update:model-value', self.switch_tab)
		with self.tabs:
			ui.tab(file)
		# switch to (newly created) tab
		self.switch_tab({'args': file})
		# populate tab panel
		with self.tab_panels:
			with ui.tab_panel(file).style('height: calc(100vh - 84px); width: calc(100vw - 32px)'):
				ui.label('Reading: ')
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
					'rowHeight': self.settings['row_height'],
					'animateRows': True,
					'suppressAggFuncInHeader': True,
				}
				self.grid = ui.aggrid(gridOptions, theme='alpine-dark').style('height: calc(100vh - 164px)').on('cellDoubleClicked', lambda event: func_select(self, event))
				with ui.row().classes('w-full').style('gap: 0'):
					ui.input().props('square filled dense="dense" clearable clear-icon="close"').classes('flex-grow')  # .style('width: 8px; height: 8px; border:0px; padding:0px; margin:0px')
					ui.button().props('square').style('width: 40px; height: 40px;')


if __name__ in {"__main__", "__mp_main__"}:
	import tracemalloc
	tracemalloc.start()

	import sys
	main(*sys.argv)
