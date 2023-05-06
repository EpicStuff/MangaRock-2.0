#mangaRock 2.8.10, modified to work on repl.it
import json
import requests
import re
import os
import threading
from bs4 import BeautifulSoup
from time import sleep


temp_link_var=[]

class OBJ():
	prop = {'name': None}

	def __init__(self, args, kwargs):
		self.__dict__.update(self.prop)

		for num, arg in enumerate(args):
			if arg in ('', None, ['']): arg = tuple(self.prop.items())[num][1]  # if arg is blank then set it to default
			if type(arg) is tuple: list(arg)  # if arg is a tuple then turn it into a list
			if type(tuple(self.prop.values())[num]) is int and type(arg) is not float: arg = float(arg)    # if default arg is float and givin arg is not float then float givin arg
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

	def update(self):  # self.lChs[0][1]: -inf = no link, -3 = parsing error, -2 = link not supported, -1 = Connection Error
		Map = {  # site:         find,   with,                      then find, and get, split at,  and float
			'wuxiaworld.site':    ('ul',  {'class': 'main version-chap'},   'a',  'href', '-|/',      -2),
			'mangakakalot.com':   ('div', {'class': 'chapter-list'},        'a',  'href', '_',        -1),
			'manganato.com':      ('ul',  {'class': 'row-content-chapter'}, 'a',  'href', '-',        -1),
			'readmng.com':        ('ul',  {'class': 'chp_lst'},             'a',  'href', '/',        -1),
			'www.webtoons.com':   ('ul',  {'id': '_listUl'},                'li', 'id',   '_',        -1),
			'kissmanga.org':      ('h3',  None,                             'a',  'href', '_',        -1),
			'mangadex.org':       ('a',   {'class': 'text-truncate'},       None, None,   'Ch. | - ',  1),
			'mangatoon.mobi':     ('div', {'class': 'episode-count'},       None, None,   ' ',         5),
			'zahard.top':         ('ul',  {'class': 'chapters'},            'a',  'href', '/',        -1),
			'www.manga-raw.club': ('ul',  {'class': 'chapter-list'},        'a',  'href', '-',        -3)
		}
		Map['readmanganato.com'] = Map['manganato.com']
		Map['1stkissmanga.com'] = Map['read-noblesse.com'] = Map['vipmanhwa.com'] = Map['www.webtoon.xyz'] = Map['topmanhwa.com'] = Map['topmanhwa.net'] = Map['mangatx.com'] = Map['wuxiaworld.site']

		self.lChs = [(-1, float('-inf'))]
		if ('Complete' or 'do not check for updates') in self.tags: return

		for num, link in enumerate(self.links):
			site = link.split('/')[2]

			if site in ('mangadex.org', 'www.youtube.com'): continue

			if site in Map:  # check if site been maped
				try: link = requests.get(link)  # connecting to the site
				except Exception: self.lChs.append((num, -1))  # connection error
				else:
					if not link.ok: self.lChs.append((num, -1))  # connection error
					else:
						try:  # processing html
							if (Map[site][2] and Map[site][3]) is None: link = BeautifulSoup(link.text, 'html.parser').find(Map[site][0], Map[site][1]).contents[0]
							else: link = BeautifulSoup(link.text, 'html.parser').find(Map[site][0], Map[site][1]).find(Map[site][2]).get(Map[site][3])
						except AttributeError: self.lChs.append((num, -3))
						else: self.lChs.append((num, float(re.split(Map[site][4], link)[Map[site][5]])))
			else: self.lChs.append((num, -2))  # site is not supported

		self.lChs.sort(key=lambda chs: chs[1], reverse=True)


class fandom(OBJ): prop, arc = {'name': None, 'tags': [], 'children': []}, {}
class author(OBJ): prop, arc = {'name': None, 'links': None, 'works': [], 'score': None, 'tags': []}, {}
class series(OBJ): prop, arc = {'name': None, 'links': None, 'author': None, 'works': [], 'fandom': [], 'score': None, 'tags': []}, {}
class fanfic(OBJ): prop, arc = {'name': None, 'links': None, 'author': None, 'chapter': 0, 'fandom': [], 'series': None, 'score': None, 'tags': []}, {}
class anime(OBJ): prop, arc = {'name': None, 'links': None, 'episode': 0, 'series': None, 'score': None, 'tags': []}, {}
class manga(OBJ): prop, arc = {'name': None, 'links': [], 'chapter': 0, 'score': None, 'series': None, 'author': None, 'tags': []}, {}
class text(OBJ): prop, arc = {'name': None, 'links': [], 'chapter': 0, 'author': None, 'series': None, 'score': None, 'tags': []}, {}


score = {'no Good': -1, None: 2.9, 'ok-': 0.9, 'ok': 1, 'ok+': 1.1, 'Good-': 1.9, 'Good': 2, 'Good+': 2.1, 'Great': 3}


def main(file='', sort_by=score, mode='reading'):
	load()
	try: read(sort_by)
	except KeyboardInterrupt:
		os.system('clear')
		print('saving ...')
		save()
		os.system('clear')


def All(*args, sort_by=None):
	if args in ((), ('all',)): args = (fandom, author, series, fanfic, anime, manga)
	if args == ('works',): args = (fanfic, anime, manga)

	if sort_by is None: return tuple([obj for objs in args for obj in objs.arc.values()])
	if sort_by is score: return tuple(sorted([work for obj in args for work in obj.arc.values()], key=lambda work: sort_by[work.score], reverse=True))


def add(format, name, *args, **kwargs):
	if type(format) is str: format = eval(format)
	format.arc[name.lower()] = format([name, *args], kwargs)


def load(file='manga'):
	try:
		with open(file + '.json', 'r') as file: json.load(file, object_hook=lambda kwargs: add(**kwargs))
		return True
	except FileNotFoundError:
		print('File does not exist')
		return False
	# except json.decoder.JSONDecodeError: pass


def save(file='manga'):
	for obj in All():
		try: delattr(obj, 'lChs')
		except AttributeError: pass
	with open(file + '.json', 'w') as file:
		json.dump(All(), file, indent=4, default=lambda obj: {**{'format': obj.__class__.__name__}, **{key: item for key, item in obj.__dict__.items() if item not in ([], None)}})


def display(objs='all', debug=True, works=None, thread=False, sort_by=None):
	if works is None: works = All(objs, sort_by=sort_by)
	else:
		global reading, running
		if thread:
			while running: sleep(0.01)
			running = True
		toPrint = [None] * len(works)
		try: size = os.get_terminal_size().columns - 26
		except OSError: size = 120
			
		size = 20
			
		for num, work in enumerate(works):
			if not hasattr(work, 'lChs'): toPrint[num] = '{:>3}. {:.{}}\n'.format(num, work.name + ':', size + 19)  # work has not been updated
			# elif work.lChs[0][1] == float('-inf'): toPrint[num] = ''  # has been updated and no link
			elif size < 1 and work.lChs[0][1] in (-2, -1): toPrint[num] = '{:>3}. Error\n'.format(num)  # terminal is too small and connection error
			elif size > 0 and work.lChs[0][1] in (-2, -1): toPrint[num] = '{0:>3}. {1:.<{2}.{2}} Connection Error\n'.format(num, work.name + ': ', size)  # terminal is not to small and connection error
			elif work.lChs[0][1] == -3: toPrint[num] = '{0:>3}. {1:.<{2}.{2}} Parsing Error\n'.format(num, work.name + ': ', size)
			elif work.lChs[0][1] - work.chapter <= 0: toPrint[num] = ''  # there are no new updates
			elif size < 1: toPrint[num] = '{0:>3}. {1:0>3g}\n'.format(num, work.lChs[0][1] - work.chapter)  # terminal is too small and updated
			elif size > 0: toPrint[num] = '{0:>3}. {1:.<{2}.{2}} {3:0>3g} [{4:0>3g} to {5:0>3g}]\n'.format(num, work.name + ': ', size, work.lChs[0][1] - work.chapter, work.chapter, work.lChs[0][1])  # terminal is not too small and updated
		toPrint = tuple(filter(lambda e: e != '', toPrint))
		os.system('clear')
		if len(toPrint) > os.get_terminal_size().lines - 2: print(*toPrint[:os.get_terminal_size().lines - 2], sep='', end='')
		else: print(*toPrint, sep='', end='')
		if thread and reading: print('\nRead To{}: '.format(temp_link_var), end='')
		elif thread: print('\nRead: ', end='')
		if thread: running = False


def read(sort_by=None, objs='works', works=None, Thread=0):
	global reading, running, temp_link_var
	if Thread == 0:
		reading, running = False, False
		works = All(objs, sort_by=sort_by)

		threading.Thread(target=read, kwargs={'works': works, 'Thread': 1}, daemon=True).start()
		threading.Thread(target=read, kwargs={'works': works, 'Thread': 2}, daemon=True).start()

		try: s = os.get_terminal_size().columns
		except OSError: [t.join() for t in threading.enumerate()]
		while True:
			if s != os.get_terminal_size().columns:
				display(None, False, works, True)
				s = os.get_terminal_size().columns
			sleep(0.01)
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

			try: temp_link_var = works[r].links  # open website
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
	main()
