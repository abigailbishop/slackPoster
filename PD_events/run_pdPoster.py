#!/usr/bin/env python3
from parsers import *

with open('webhook', 'r') as webhook_file:
    webhook = str(webhook_file.readline())

events = []
#loop over parsers
for parser in [UWMCareerDev(),PGSCProfDev()]:
     #loop over urls
    for url in parser.urls:
        events += parser.get_events(url)
          
startnum = 1
#for all events
events = filter_events(events)

message_body = ''
for e in events:
    event_info = str(startnum) + '. '
    if e.subtitle == '': 
        event_info += '*' + e.title + '*'
    else:
        event_info += '*' + e.title + '*' + ': ' + e.subtitle
    event_info += '\n\t\t' + e.display_date + ' - ' + e.link
    message_body += event_info + '\n'
    startnum += 1

slack_post(message_body, webhook)
