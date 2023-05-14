from nicegui import ui
import asyncio
from time import sleep

async def tmp():
	global x, l
	x = x - 1
	print('start:', x)
	await asyncio.sleep(1)
	print('done:', x)
	l.set_text(str(x))

async def a_gen():
	global x
	for y in range(3):
		await tmp(x)
		yield

async def a_main(event):
	global x, l
	x = x + 3
	await asyncio.gather(tmp(), tmp(), tmp())

x = 0
l = ui.label('0')
ui.button('Test', on_click=a_main)

ui.run(dark=True)
