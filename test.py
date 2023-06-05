from nicegui import ui
import asyncio

ui.label('Hello World')

async def test():
    ui.run()


asyncio.run(test())
