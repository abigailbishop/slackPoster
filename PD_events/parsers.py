# A collection of web parsers for different urls

import datetime
import json
import requests
from bs4 import BeautifulSoup

import shlex
import subprocess

class Event():
    def __init__(self, title, subtitle, date, link):
        self.title = title
        self.subtitle = subtitle
        self.date = date
        self.python_date = self.parse_date(date)
        self.link = link
        return

    def parse_date(self, date):
        split_date = date.split(',')[0]
        month = split_date.split(' ')[0]
        month_map = {'january': 1, 'february': 2, 'march': 3, 'april': 4,
                     'may': 5, 'june': 6, 'july': 7, 'august': 8,
                     'september': 9, 'october': 10, 'november': 11,
                     'december': 12}
        day = split_date.split(' ')[1][:-2]
        
        current_date = datetime.datetime.now()
        current_month = current_date.month

        if current_month == 12 and month_map[month.lower()] != 12:
            year = current_date.year + 1
        else:
            year = current_date.year

        event_date = datetime.datetime(year, month_map[month.lower()], int(day))
        return event_date
    
class UWMCareerDev():
    def __init__(self):

        #set urls
        pages = [str(x) for x in range(1, 11)]
        self.urls = ["https://grad.wisc.edu/uw-events/?c=career-development&view=list&pg={}".format(x) for x in pages]

        return
        
    def get_events(self, url):
        """
        Return all the events from a webpage

        :param url: the url to be parsed
        :return: :
        """
        try:
            response = requests.get(url)
        except:
            return

        soup = BeautifulSoup(response.text, "html.parser")

        #TODO
        #Alert the media if the lengths don't line up
        titles = [x for x in soup.findAll('h3') if str(x)[11:22] == 'event-title']
        subtitles = [x.string for x in soup.findAll('h4') if str(x)[11:25] == 'event-subtitle']
        dates = [x.string for x in soup.findAll('p') if str(x)[10:20] == 'event-date']
        links = [str(list(title.children)[0]).split('\"')[1] for title in titles]
        events = []
        for title, subtitle, date, link in zip(titles, subtitles, dates, links):
            events.append(Event(title.string, subtitle, date, link))
            
        return events

    def filter_events(self, events):

        current_date = datetime.datetime.now()
        good_events = []
        allowed_range = datetime.timedelta(days=21)
        for event in events:
            if event.python_date < current_date + allowed_range:
                good_events.append(event)
        return good_events
    
def run(string):
    """ run a UNIX command """

    # shlex.split will preserve inner quotes
    prog = shlex.split(string)
    p0 = subprocess.Popen(prog, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)

    stdout0, stderr0 = p0.communicate()
    rc = p0.returncode
    p0.stdout.close()

    return stdout0, stderr0, rc


def slack_post(channel_body):

    payload = {}
    #payload["channel"] = c
    #if username is not None:
    #    payload["username"] = username
    #if icon_emoji is not None:
    #    payload["icon_emoji"] = icon_emoji
    payload["text"] = channel_body
    
    cmd = "curl -X POST --data-urlencode 'payload={}' {}".format(json.dumps(payload), webhook)
    run(cmd)

parser = UWMCareerDev()

with open('webhook', 'r') as webhook_file:
    webhook = str(webhook_file.readline())

for url in parser.urls:
    events = parser.get_events(url)

    events = parser.filter_events(events)
    
    message_body = ''
    for num, e in enumerate(events):
        event_info = str(num + 1) + '. '
        event_info += '*' + e.title + '*' + ': ' + e.subtitle
        event_info += '\n\t\t' + e.date + ' - ' + e.link
        message_body += event_info + '\n'

    slack_post(message_body)



