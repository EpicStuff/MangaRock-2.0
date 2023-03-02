# import scrapy
# from scrapy.crawler import CrawlerProcess


# test = []

# class TestSpider(scrapy.Spider):
# 	name = 'test'
# 	start_urls = ['https://webscraper.io/test-sites/e-commerce/allinone', 'https://webscraper.io/test-sites/e-commerce/static', 'https://webscraper.io/test-sites/e-commerce/allinone-popup-links', 'https://webscraper.io/test-sites/e-commerce/ajax', 'https://webscraper.io/test-sites/e-commerce/more', 'https://webscraper.io/test-sites']

# 	def parse(self, response):
# 		global test
# 		test.append(response.body)


# if __name__ == "__main__":
# 	process = CrawlerProcess()
# 	process.crawl(TestSpider)
# 	process.start()
# 	print('-----------------------------')
# 	print(test)


# sites = {  # site:         find,   with,                       then find, and get,       split at, then get, render?; supported sites, might be outdated
#     'manganato.com':      ('ul',    {'class': 'row-content-chapter'}, 'a',  'href',          '-',        -1, False),
#     'www.webtoons.com':   ('ul',    {'id': '_listUl'},                'li', 'id',            '_',        -1, False),
#     'manhuascan.com':     ('div',   {'class': 'list-wrap'},           'a',  'href',          '-',        -1, False),
#     'zahard.xyz':         ('ul',    {'class': 'chapters'},            'a',  'href',          '/',        -1, False),
#     'www.royalroad.com':  ('table', {'id':    'chapters'},            None, 'data-chapters', ' ',         0, False),
#     '1stkissmanga.io':    ('li',    {'class': 'wp-manga-chapter'},    'a',  'href',          '-|/',      -2, False),
#     'comickiba.com':      ('li',    {'class': 'wp-manga-chapter'},    'a',  'href',          '-|/',      -2,  True),
#     'asura.gg':           ('span',  {'class': 'epcur epcurlast'},    None,   None,           ' ',         1, False),
#     'mangapuma.com':      ('div',   {'id': 'chapter-list-inner'},     'a',  'href',           '-',       -1, False),
#     'bato.to':            ('item',  None,                           'title',  None,           ' ',       -1, False),
#     'www.manga-raw.club': ('ul',    {'class': 'chapter-list'},        'a',  'href',           '-|/',     -4, False)}
# sites['chapmanganato.com'] = sites['readmanganato.com'] = sites['manganato.com']
# sites['nitroscans.com'] = sites['anshscans.org'] = sites['comickiba.com']
# sites['www.mcreader.net'] = sites['www.manga-raw.club']
# sites['flamescans.org'] = sites['asura.gg']


import ruamel.yaml; yaml = ruamel.yaml.YAML(); yaml.indent(mapping=4, sequence=4, offset=2); yaml.default_flow_style = None

with open('settings.yaml', 'r') as file:
	settings = yaml.load(file)
# with open('test.yaml', 'w') as file:
# 	yaml.dump(settings, file)

input()

# with open('test.yaml', 'r') as f:
# 	file = f.readlines()

# for num, line in enumerate(file):
# 	if line[0:6] == 'sites:':
# 		start = num
# 		break

# i = 0; adding = []; done = []
# while len(done) != len(file[start:]):
# 	if len(adding) + len(done) == len(file[start:]):
# 		adding = []
# 	for num, line in enumerate(file[start:], start):
# 		if num in done:
# 			continue
# 		if line[i] == '\n':
# 			done.append(num)
# 		elif num in adding:
# 			if line[i + 1] != ' ':
# 				file[num] = line[0:i] + ' ' + line[i:]
# 		elif line[i] == ',' or (line[i] == ':' and line[i + 1:].lstrip(' ')[0] in ('&', '*')):
# 			adding.append(num)
# 	i += 1

# with open('test.yaml', 'w') as f:
# 	f.writelines(file)
