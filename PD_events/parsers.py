# A collection of web parsers for different urls

import datetime
import json
import requests
from bs4 import BeautifulSoup

import shlex
import subprocess

import numpy as np
import smtplib
from email.mime.text import MIMEText
import sys
import platform

class Event():
    """Defining an event regardless of source """
    def __init__(self, title, subtitle, start_date, end_date, link):
        self.title = title
        self.subtitle = subtitle
        self.start_date = start_date
        self.end_date = end_date
        self.display_date = self.format_python_date()
        self.link = link
        return

    def format_python_date(self):
        """
        Convert a datetime instance to however we want it to
        be displayed in the slack post
        """

        #use self.start_date and self.end_date when formatting the output

        month = self.start_date.month
        month_name = month_map(month, reverse=True).title()

        day = str(self.start_date.day)

        start_hour, start_min = self.start_date.hour, self.start_date.minute
        end_hour, end_min = self.end_date.hour, self.end_date.minute

        start_ampm, end_ampm = 'am', 'am'
        if start_hour > 12: 
            start_hour -= 12
            start_ampm = 'pm'
        elif start_hour == 12:
            start_ampm = 'pm'
        if end_hour > 12: 
            end_hour -= 12
            end_ampm = 'pm' 
        elif end_hour == 12:
            end_ampm = 'pm'

        if start_min == 0:
            start_min_string = '00'
        else:
            start_min_string = str(start_min)

        if end_min == 0:
            end_min_string = '00'
        else:
            end_min_string = str(end_min)

        output = ""
        output += month_name + ' '
        output += day + ', '
        output += str(start_hour) + ':' + start_min_string + start_ampm + '-'
        output += str(end_hour) + ':'+ end_min_string + end_ampm
        
        return output

class UWMCareerDev():
    """Parses Events from UWM Career Development website """
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

        titles = [x for x in soup.findAll('h3') if str(x)[11:22] == 'event-title']
        subtitles = []
        for title in titles:
            if title.find_next_sibling().string is None:
                subtitles.append("")
            else:
                subtitles.append(title.find_next_sibling().string)
        dates = [x.string for x in soup.findAll('p') if str(x)[10:20] == 'event-date']
        links = [str(list(title.children)[0]).split('\"')[1] for title in titles]

        if len(np.unique(
                    [len(x) for x in [titles, subtitles, links, dates]])) != 1:

            body = "{}\n".format(
                           [len(x) for x in [titles, subtitles, links, dates]])

            with open('../emails.txt', 'r') as emails:
                email_addresses = [x.strip() for x in emails.readlines()]

            for mail in email_addresses:
                report(body, ":'(", 
                              "PD-poster@{}".format(platform.node()), mail)

        events = []
        for title, subtitle, date, link in zip(titles, subtitles, dates, links):
            try:
                start_date, end_date = self.parse_date(date)
                events.append(Event(title.string, subtitle, start_date, end_date, link))
            except:
                continue
            
        return events

    def parse_date(self, date):
        #return both start and end date
        split_date = date.split(',')[0]
        month = split_date.split(' ')[0]
        day = split_date.split(' ')[1][:-2]
        
        current_date = datetime.datetime.now()
        current_month = current_date.month
        
        if current_month == 12 and month_map(month.lower()) != 12:
            year = current_date.year + 1
        else:
            year = current_date.year

        split_time = date.split(',')[1].strip()
        garb = split_time.split(':')
        start_hour = int(garb[0])
        start_min = int(garb[1][0:2])
        start_ampm = garb[1][2:4]
        end_hour = int(garb[1][5:])
        end_min = int(garb[2][0:2])
        end_ampm = garb[2][2:4]

        if start_ampm == 'pm' and start_hour != 12: start_hour += 12
        if end_ampm == 'pm' and end_hour != 12: end_hour += 12
    
        month = month_map(month.lower())

        start = datetime.datetime(year, month, int(day), start_hour, start_min)
        end = datetime.datetime(year, month, int(day), end_hour, end_min)

        return start, end
                

def month_map(month, reverse=False):
    converter =  {'january': 1, 'february': 2, 'march': 3, 'april': 4,
                     'may': 5, 'june': 6, 'july': 7, 'august': 8,
                     'september': 9, 'october': 10, 'november': 11,
                     'december': 12}

    if reverse: 
        converter = {v: k for k, v in converter.items()}


    return converter[month]
        


def filter_events(events):

    current_date = datetime.datetime.now()
    good_events = []
    allowed_range = datetime.timedelta(days=21)
    #if event date < current date night night
    for event in events:
        if (event.end_date < current_date + allowed_range and
             event.end_date > current_date) :
            good_events.append(event)
    start_times = np.array([x.start_date for x in good_events])
    return_events = []
    for arg in np.argsort(start_times):
        return_events.append(good_events[arg])
    return return_events


class PGSCProfDev():
    """Parses Events from the PGSC Professional Development website """
    def __init__(self):

        #set urls
        self.urls = ["https://rmorgan10.github.io/UWMadisonPGSC-PD/"]

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

        #titles = [x for x in soup.findAll('h3') if str(x)[11:22] == 'event-title']
        titles = [x.string for x in soup.findAll('h3')]
        subtitles = [""]*len(titles)
        start_dates = []
        end_dates = []
        for p in [str(x) for x in soup.findAll('p') if str(x)[11:25] == 'When and Where']:
            start_date, end_date = self.parse_date(p)
            start_dates.append(start_date)
            end_dates.append(end_date)
            

        links = self.urls*len(titles)

        if len(np.unique(
                    [len(x) for x in [titles, subtitles, links, start_dates, end_dates]])) != 1:

            body = "{}\n".format(
                           [len(x) for x in [titles, subtitles, links, start_dates, end_dates]])

            with open('../emails.txt', 'r') as emails:
                email_addresses = [x.strip() for x in emails.readlines()]

            for mail in email_addresses:
                report(body, ":'(", 
                              "PD-poster@{}".format(platform.node()), mail)

        events = []
        for title, subtitle, start_date, end_date, link in zip(
                                     titles, subtitles, start_dates, end_dates, links):
            events.append(Event(title.string, subtitle, 
                                 start_date, end_date, link))
            
        return events

    def parse_date(self, date):
        # Input Date: When and Where: April 11, 2020; 2:30-3:30; REMOTE
        
        if date.strip() == "<p><strong>When and Where:</strong> TBD</p>":
            return datetime.datetime(3000, 3, 3), datetime.datetime(3000, 3, 3) 

        rawDate = date[36:].strip().split(';')
        # April 11, 2020;2:30-3:30;REMOTE

        day = rawDate[0].split(',')[0].split(' ')[1]
        month = rawDate[0].split(',')[0].split(' ')[0].lower()
        month = month_map(month)
        year = rawDate[0].split(',')[1].strip()
        rawTime = rawDate[1].strip()
        start_hour = int(rawTime.split('-')[0].split(':')[0])
        start_min = rawTime.split('-')[0].split(':')[1][:2]
        start_ampm = rawTime.split('-')[0].split(':')[1][2:]
        end_hour = int(rawTime.split('-')[1].split(':')[0])
        end_min = rawTime.split('-')[1].split(':')[1][:2]
        end_ampm = rawTime.split('-')[1].split(':')[1][2:]

        if start_ampm == 'pm' and start_hour != 12: start_hour += 12
        if end_ampm == 'pm' and end_hour != 12: end_hour += 12

        start = datetime.datetime(int(year), month, int(day), 
                                     start_hour, int(start_min))
        end = datetime.datetime(int(year), month, int(day), 
                                     end_hour, int(end_min))
 
        return start, end

def report(body, subject, sender, receiver):
    """ send an email """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver

    try:
        sm = smtplib.SMTP('localhost')
        sm.sendmail(sender, receiver, msg.as_string())
    except smtplib.SMTPException:
        sys.exit("ERROR sending mail")

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


def slack_post(channel_body, webhook):
    """ Styles a slack post and pushes it to slack """
    payload = {}
    payload["text"] = channel_body
    
    cmd = "curl -X POST --data-urlencode 'payload={}' {}".format(json.dumps(payload), webhook)
    run(cmd)

