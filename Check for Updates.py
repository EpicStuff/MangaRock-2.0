import requests
from threading import Thread as thread
from time import sleep
from html.parser import HTMLParser


class Tag(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'a' and attrs[0][0] == 'href':
            self.data.append(attrs[0][1].rstrip('/'))


class Data(HTMLParser):
    def handle_data(self, data):
        for char in ('\n', '\r', '\t', ' '):
            data = data.replace(char, '')
        if data == '':
            return
        self.data.append(data)


class FanFic(HTMLParser):
    def handle_data(self, data):
        try: data = data.split(' - Chapters: ')[1]
        except Exception: return
        self.data.append(data)


stories = []
#################################################################
#   stories = [[Name, Current Chapter, Link, link, link ...],    #
#             [Name, Current Chapter, Link, link, link ...],    #
#             ...                                         ]]    #
#   stories = [Name, Current Chapter, Link, link, link ...]       #
#################################################################
latestChs = []


def findLateChs(stories):
    global latestChs
    for story in stories:
        if story[0][0] in ('#', '\n'):  # if this line in comics is a comment or blank
            latestChs.append(None)
        else:
            latestChs.append(lastChOf(story[2]))


def lastChOf(link, silent=True, debug=False, site='www.com', seek=0):
    mList = {
        'kissmanga.org': (Tag(), 30000, '_', -1),
        'www.readmng.com': (Tag(), 60000, '/', -1),
        'mangadex.org': (Data(), 60000, 'Ch.', 1),
        'getmanhwa.co': (Tag(), 60000, '-', 1),
        'www.fanfiction.net': (FanFic(), 30000, '-', 0),
        'www.webtoons.com': (Data(), 20000, '#', 1)}
    link = link.rstrip('\n')
    site = link.split('/')[2]
    HTML = mList[site][0]
    HTML.data = []
    if debug: print('the site is', site)

    try:
        link = requests.get(link)
    except Exception:
        if not silent: print('Could not connect')
        return 'Could not connect to'
    if not link.ok:
        if not silent: print('Link is no longer valid')
        return 'The link is no longer valid:'
    if debug: print('link is', link)

    HTML.feed(link.iter_content(mList[site][1], True).__next__())
    if debug: print(*HTML.data, sep='\n')
    while True:
        try:
            if not silent: print(float(HTML.data[seek].split(mList[site][2])[mList[site][3]]))
            return float(HTML.data[seek].split(mList[site][2])[mList[site][3]])
        except (ValueError, IndexError):
            seek += 1
        if seek > len(HTML.data):
            if not silent: print('Latest chapter not found in data provided')
            return 'Latest chapter not found in data provided'


def output(reading, seek=0, site=2, toPrint=''):
    global stories, latestChs
    while seek < len(stories):
        try: latestChs[seek]
        except IndexError: pass
        else:
            if latestChs[seek] is None: print(', '.join(stories[seek]), end='')
            elif latestChs[seek] in ('Could not connect to', 'The link is no longer valid:', 'Latest chapter not found in data provided'): print(latestChs[seek], stories[seek][2])
            else:
                toPrint = '{}: {:g} [from {} to {:g}]'.format(stories[seek][0], latestChs[seek] - float(stories[seek][1]), stories[seek][1].rstrip("\n"), latestChs[seek])
                if latestChs[seek] != float(stories[seek][1]):
                    toPrint = input(toPrint + ', Read?: ')
                    if toPrint == 'y':
                        while True:
                            toPrint = input(stories[seek][site] + '\nChapters Read: ')
                            if toPrint == 'u':
                                site += 1
                            else:
                                try:
                                    stories[seek][1] = str(float(stories[seek][1]) + float(toPrint)).replace('.0', '')
                                except ValueError: break
                                else: break
                    elif toPrint == '': pass
                    elif toPrint[0] == 'u':
                        toPrint += '1'
                        seek -= int(toPrint[1])
                        continue
            seek += 1
            site = 2
        sleep(0.1)


def saveArray(_arr, _file, _line=''):
    while True:
        _line = input('Writing To: ' + _file + ' Proceed?: ')
        if _line == 'y':
            with open(_file, 'w') as _file:
                for _elm in _arr:
                    print(*_elm, sep=', ', end='', file=_file)
            break
        elif _line == 'r':
            return True
        elif _line == 'n':
            break


def main(file='main', reading=True):
    global stories, findLateChs
    while True:
        try:
            with open(file + '.txt') as f:
                stories = [line.split(', ') for line in f]

            findLatestChs = thread(target=findLateChs, args=[stories])
            findLatestChs.start()
            output(reading)

            if reading:
                while saveArray(stories, file + '.txt'):
                    output(reading)
            break
        except KeyboardInterrupt:
            if reading:
                saveArray(stories, file + '.txt')
        except Exception:
            input()


if __name__ == '__main__':
    main()
    input('Enter to Exit')
