# to do:
# add/verify suport for readmng.com
import json
import requests
import re
import threading
from itertools import cycle
from bs4 import BeautifulSoup
from time import sleep


def test():
	# load('picture')
	# manga.arc['The Apostle Of Cards'.lower()].update()
	# for work in All('works'):
	# work.format()
	# save('picture')
	display()


class OBJ():
	prop = {'name': None}

	def __init__(self, args, kwargs):
		self.__dict__.update(self.prop)

		for num, arg in enumerate(args):
			if arg in ('', None, ['']): arg = tuple(self.prop.items())[num][1]  # if arg is blank then set it to default
			if type(arg) is tuple: list(arg)  # if arg is a tuple then turn it into a list
			if type(tuple(self.prop.values())[num]) is int and type(arg) is not float: arg = float(arg)  # if default arg is float and givin arg is not float then float givin arg
			if type(tuple(self.prop.values())[num]) is list and type(arg) is not list: arg = [arg]  # if default arg is list and givin arg is not list then put givin arg in a list
			setattr(self, tuple(self.prop)[num], arg)  # set the self arg to givin arg
		for key, val in kwargs.items():
			if key in self.__dict__:
				if type(val) is tuple: val = list(val)  # if val is a tuple then turn val into a list
				if type(self.prop[key]) is int and type(val) is not float: val = float(val)  # if default val is float and givin val is not float then float givin val
				if type(self.prop[key]) is list and type(val) is not list: val = [val]  # if default val is list and givin val is not list then put givin val in a list
				self.__dict__.update({key: val})

	def __iter__(self):
		return self

	def format(self):
		self.chapter = float(self.chapter)  # to do

	def update(self):  # self.lChs[0][1]: -inf = no link, -2 = link not supported, -1 = Connection Error
		Map = {  # site:		 find,   with,					  then find, and get, split at,  and float
			'wuxiaworld.site':  ('ul',  {'class': 'main version-chap'},   'a',  'href', '-|/',   -2),
			'mangakakalot.com': ('div', {'class': 'chapter-list'},  'a',  'href', '_',  -1),
			'manganelo.com': ('ul',  {'class': 'row-content-chapter'}, 'a',  'href', '_',  -1),
			'readmng.com':   ('ul',  {'class': 'chp_lst'},    'a',  'herf', '/',  -1),
			'www.webtoons.com': ('ul',  {'id': '_listUl'},    'li', 'id',   '_',  -1),
			# 'kissmanga.org':	('h3',  None,							 'a',  'href', '_',		-1),
			'mangatoon.mobi':   ('div', {'class': 'episode-count'},    None, None,   ' ',  5),
			'mangadex.org':  ('a',   {'class': 'text-truncate'},    None, None,   'Ch. | - ', 1)
		}
		Map['read-noblesse.com'] = Map['vipmanhwa.com'] = Map['www.webtoon.xyz'] = Map['topmanhwa.net'] = Map['mangatx.com'] = tuple([*Map['wuxiaworld.site'][:-1], -2])

		self.lChs = [(-1, float('-inf'))]
		for num, link in enumerate(self.links):
			site = link.split('/')[2]

			if site in Map:  # check if site been maped
				try: link = requests.get(link)  # connecting to the site
				except Exception: self.lChs.append((num, -1))  # connection error
				else:
					if not link.ok: self.lChs.append((num, -1))  # connection error
					else:
						try:  # processing html
							if Map[site][2] and Map[site][3] is None: link = BeautifulSoup(link.text, 'html.parser').find(Map[site][0], Map[site][1]).contents[0]
							else: link = BeautifulSoup(link.text, 'html.parser').find(Map[site][0], Map[site][1]).find(Map[site][2]).get(Map[site][3])
						except AttributeError: self.lChs.append((num, -1))
						else: self.lChs.append((num, float(re.split(Map[site][4], link)[Map[site][5]])))
			else: self.lChs.append((num, -2))  # site is not supported

		self.lChs.sort(key=lambda chs: chs[1], reverse=True)


class fandom(OBJ): prop, arc = {'name': None, 'tags': [], 'children': []}, {}
class author(OBJ): prop, arc = {'name': None, 'links': None, 'works': [], 'score': None, 'tags': []}, {}
class series(OBJ): prop, arc = {'name': None, 'links': None, 'author': None, 'works': [], 'fandom': [], 'score': None, 'tags': []}, {}
class fanfic(OBJ): prop, arc = {'name': None, 'links': None, 'author': None, 'chapter': 0, 'fandom': [], 'series': None, 'score': None, 'tags': []}, {}
class anime(OBJ): prop, arc = {'name': None, 'links': None, 'episode': 0, 'series': None, 'score': None, 'tags': []}, {}
class manga(OBJ): prop, arc = {'name': None, 'links': [], 'chapter': 0, 'score': None, 'tags': []}, {}
class light_novel(OBJ): prop, arc = {'name': None, 'links': [], 'chapter': 0, 'score': None, 'tags': []}, {}


score = {'no Good': -1, None: 0, 'ok-': 0.9, 'ok': 1, 'ok+': 1.1, 'Good-': 1.9, 'Good': 2, 'Good+': 2.1, 'Great': 3}


def main(file='', sort_by=score):
	for mode in cycle(('reading', 'adding')):
		try:
			while file == '':
				file = input('Mode: ' + mode + '\nInput File: ')
			if not load(file): file = ''
			else: break
		except KeyboardInterrupt: pass
	if mode == 'reading':
		try: read(sort_by)
		except KeyboardInterrupt:
			print('saving ...')
			save(file)
	elif mode == 'adding':
		for Type in cycle((manga, anime, fanfic)):
			try:
				while True:
					print('Format: ' + Type.__name__)
					args = [input('Name: ')]
					try:
						if args[0].lower() in Type.arc:
							print('Manga all ready exists')
							continue
						for prop in Type.prop:
							if prop == 'name': continue
							elif Type.prop[prop] == []: args.append(input(prop.title() + ': ').split(','))
							else: args.append(input(prop.title() + ': '))
						add(Type, *args)
					except KeyboardInterrupt: pass
			except KeyboardInterrupt: save(file)


# Each manga/anime/fanfic/etc. are to be refered to as work
# mangas/animes/fanfics/etc. are to be refered to as obj
# all works are to be refered to as objs


def All(*args, sort_by=None):
	if args in ((), ('all',)): args = (fandom, author, series, fanfic, anime, manga)
	if args == ('works',): args = (fanfic, anime, manga)

	if sort_by is None: return tuple([obj for objs in args for obj in objs.arc.values()])
	if sort_by is score: return tuple(sorted([work for obj in args for work in obj.arc.values()], key=lambda work: sort_by[work.score], reverse=True))


def add(format, name, *args, **kwargs):
	if type(format) is str: format = eval(format)
	format.arc[name.lower()] = format([name, *args], kwargs)


def load(file):
	try:
		with open(file + '.json', 'r') as file: json.load(file, object_hook=lambda kwargs: add(**kwargs))
		return True
	except FileNotFoundError:
		print('File does not exist')
		return False
	# except json.decoder.JSONDecodeError: pass


def save(file):
	for obj in All():
		try: delattr(obj, 'lChs')
		except AttributeError: pass
	with open(file + '.json', 'w') as file:
		json.dump(All(), file, indent=4, default=lambda obj: {**{'format': obj.__class__.__name__}, **{key: item for key, item in obj.__dict__.items() if item not in ([], None)}})


def display(objs='all', debug=True, works=None, thread=False, sort_by=None):
	if works is None: works = All(objs, sort_by=sort_by)
	if debug:
		for work in works:
			print('\t' + work.name + ':')
			print('\t\t' + 'format:', work.__class__.__name__)
			for key, value in work.__dict__.items():
				if key != 'name': print('\t\t' + key + ':', value)
			print()
	else:
		global reading, running
		if thread:
			while running: sleep(0.01)
			running = True
		toPrint = [None] * len(works)
		# size = (112, 34)
		size = (80, 24)
		for num, work in enumerate(works):
			if not hasattr(work, 'lChs'): toPrint[num] = '{:>3}. {}\n'.format(num, work.name + ':')  # work has not been updated
			elif work.lChs[0][1] == float('-inf'): toPrint[num] = ''  # has been updated and no link
			elif work.lChs[0][1] in (-2, -1): toPrint[num] = '{0:>3}. {1:.<{2}.{2}} Connection Error\n'.format(num, work.name + ': ', size[0] - 24)  # terminal is not to small and connection error
			elif work.lChs[0][1] - work.chapter <= 0: toPrint[num] = ''  # there are no new updates
			else: toPrint[num] = '{0:>3}. {1:.<{2}.{2}} {3:0>3g} [{4:0>3g} to {5:0>3g}]\n'.format(num, work.name + ': ', size[0] - 24, work.lChs[0][1] - work.chapter, work.chapter, work.lChs[0][1])  # terminal is not too small and updated
		toPrint = tuple(filter(lambda e: e != '', toPrint))
		print('\n\n', *toPrint[:size[1]], sep='', end='')
		if thread and reading: print('\nRead To: ', end='')
		elif thread: print('\nRead: ', end='')
		if thread: running = False


def read(sort_by=None, objs='works', works=None, Thread=0):
	if Thread == 0:
		global reading, running
		reading, running = False, False
		# threading.excepthook = lambda e: e
		works = All(objs, sort_by=sort_by)

		threading.Thread(target=read, kwargs={'works': works, 'Thread': 1}, daemon=True).start()
		threading.Thread(target=read, kwargs={'works': works, 'Thread': 2}, daemon=True).start()

		threading.enumerate()[-1].join()
	elif Thread == 1:  # the update thread
		for work in works:
			work.update()
			display(None, False, works, True)
	elif Thread == 2:  # the take input thread
		while True:
			display(None, False, works, True)
			# take input and make sure its a number
			r = input()
			try: r = float(r)
			except ValueError:
				while r[0:3] == '>>>':  # if its a command then run it
					try: print(eval(r[3:]))
					except Exception:
						try: exec(r[3:])
						except Exception as e: print(e)
					r = input()
				continue
			# split the number into work # and link #
			r, s = map(int, str(r).split('.'))

			try: print(works[r].links[s])  # open website
			except IndexError: continue
			reading = True
			while reading:
				display(None, False, works, True)
				s = input()
				if s == '0': works[r].chapter, reading = works[r].lChs[0][1], False
				else:
					try: s = float(s)
					except ValueError:
						if s == '': reading = False
					else: works[r].chapter, reading = s, False


if __name__ == '__main__':
	import os
	print(os.get_terminal_size())
	# try: main()
	# except Exception: print(traceback.format_exc())
	main()
	exit()
	# test()
