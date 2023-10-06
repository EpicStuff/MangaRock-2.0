import asyncio, sys
from nicegui import ui, app


class Log():
	def __init__(self, log):
		self.stdout = sys.stdout
		self.log = log
	def write(self, s):
		self.log.push(s)
		# self.log.write(s)
	def flush(self):
		pass
	def isatty(self):
		return False


ui.button('test', on_click=lambda: print('test'))

sys.stdout = tmp(ui.log())
# sys.stdout = tmp(open('test.txt', 'a'))
ui.run(dark=True)
