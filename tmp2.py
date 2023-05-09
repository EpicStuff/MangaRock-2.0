import webbrowser
import PySimpleGUIWeb as sg

urls = {
    'Google':'https://www.google.com',
    'Amazon':'https://www.amazon.com/',
    'NASA'  :'https://www.nasa.gov/',
    'Python':'https://www.python.org/',
}

items = sorted(urls.keys())

sg.theme("DarkBlue")
font = ('Courier New', 16, 'underline')

layout = [[sg.Text(txt, tooltip=urls[txt], enable_events=True, font=font,
    key=f'URL {urls[txt]}')] for txt in items]
window = sg.Window('Hyperlink', layout, size=(250, 150), finalize=True)

while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break
    elif event.startswith("URL "):
        url = event.split(' ')[1]
        webbrowser.open(url)
    print(event, values)

window.close()