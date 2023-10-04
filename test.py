import asyncio
from nicegui import ui, app

async def tmp():
	await ui.run_javascript('window.addEventListener("load", () =>)', respond=False)

def tmp2(e):
	print('tmp2')


ui.button('test', on_click=tmp).on('load', tmp2)

app.on_connect(tmp2)

ui.run(dark=True)
