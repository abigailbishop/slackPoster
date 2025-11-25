#!/usr/bin/env python3

from __future__ import print_function

import argparse
import datetime as dt
import json
import os
import platform
import requests
import shlex
import smtplib
import subprocess
import sys
import time
import traceback
from email.mime.text import MIMEText

import feedparser


class Paper:
    """a Paper is a single paper listed on arXiv.  In addition to the
       paper's title, ID, and URL (obtained from arXiv), we also store
       which keywords it matched and which Slack channel it should go
       to"""

    def __init__(self, arxiv_id, title, url, keywords, channels):
        self.arxiv_id = arxiv_id
        self.title = title.replace("'", r"")
        self.url = url
        self.keywords = list(keywords)
        self.channels = list(set(channels))
        self.posted_to_slack = 0

    def __str__(self):
        t = " ".join(self.title.split())  # remove extra spaces
        return u"{} : {}\n  {}\n".format(self.arxiv_id, t, self.url)

    def kw_str(self):
        """ return the union of keywords """
        return ", ".join(self.keywords)

    def __lt__(self, other):
        """we compare Papers by the number of keywords, and then
           alphabetically by the union of their keywords"""

        if len(self.keywords) == len(other.keywords):
            return self.kw_str() < other.kw_str()

        return len(self.keywords) < len(other.keywords)


class Keyword:
    """a Keyword includes: the text we should match, how the matching
       should be done (unique or any), which words, if present, negate
       the match, and what Slack channel this keyword is associated with"""

    def __init__(self, name, matching="any", channel=None, excludes=None):
        self.name = name
        self.matching = matching
        self.channel = channel
        self.excludes = list(set(excludes))

    def __str__(self):
        return "{}: matching={}, channel={}, NOTs={}".format(
            self.name, self.matching, self.channel, self.excludes)

class CompletionError(Exception): pass

class AstrophQuery:
    """ a class to define a query to the arXiv astroph papers """

    def __init__(self, start_date, end_date, max_papers, arxiv_channel, old_id=None):
        self.start_date = start_date
        self.end_date = end_date
        self.max_papers = max_papers
        self.old_id = old_id

        self.base_url = "http://export.arxiv.org/api/query?"
        self.sort_query = "max_results={}&sortBy=submittedDate&sortOrder=descending".format(
            self.max_papers)

        self.arxiv_channel = arxiv_channel
        self.suffix_dict = {'astro': '-ph.',
                            'cond': '-mat.',
                            'gr': '-qc',
                            'hep': '-',
                            'math': '-ph',
                            'nlin': '.',
                            'physics': '.',
                            'quant': '-ph'}
        self.subcat_dict = {'astro': ["GA", "CO", "EP", "HE", "IM", "SR"],
                            'cond': ["dis-nn", "mtrl-sci", "mes-hall", "other", "quant-gas", "soft", "stat-mech", "str-el", "supr-con"],
                            'gr': [''],
                            'hep': ["ex", "lat", "ph", "th"],
                            'math': [''],
                            'nlin': ['AO', 'CG', 'CD', 'SI', 'PS'],
                            'nucl': ['ex', 'th'],
                            'physics': ['acc-ph', 'app-ph', 'ao-ph', 'atom-ph', 'atm-clus', 'bio-ph', 'chem-ph', 
                                         'class-ph', 'comp-ph', 'data-an', 'flu-dyn', 'gen-ph', 'geo-ph', 'hist-ph', 'ins-det',
                                         'med-ph', 'optics', 'ed-ph', 'soc-ph', 'plasm-ph', 'pop-ph', 'space-ph'],
                            'quant': ['']}

        self.subcat = self.subcat_dict[self.arxiv_channel] 

    def get_cat_query(self):
        """ create the category portion of the astro ph query """

        cat_query = "%28"  # open parenthesis
        for n, s in enumerate(self.subcat):
            #cat_query += "astro-ph.{}".format(s)
            cat_query += self.arxiv_channel + self.suffix_dict[self.arxiv_channel] + s
            #print(self.subcat)
            if n < len(self.subcat)-1:
                cat_query += "+OR+"
            else:
                cat_query += "%29"  # close parenthesis

        return cat_query

    def get_range_query(self):
        """ get the query string for the date range """

        # here the 2000 on each date is 8:00pm
        range_str = "[{}2000+TO+{}2000]".format(self.start_date.strftime("%Y%m%d"),
                                                self.end_date.strftime("%Y%m%d"))
        range_query = "lastUpdatedDate:{}".format(range_str)
        return range_query

    def get_url(self):
        """ create the URL we will use to query arXiv """

        cat_query = self.get_cat_query()
        range_query = self.get_range_query()

        full_query = "search_query={}+AND+{}&{}".format(cat_query, range_query, self.sort_query)

        print(self.base_url + full_query)

        return self.base_url + full_query

    def do_query(self, fave_authors, query_email, keywords=None, old_id=None):
        """ perform the actual query """

        # note, in python3 this will be bytes not str
        headers = {'User-Agent': f'paperPoster/1.0 ({query_email})'}
        response = requests.get(self.get_url(), headers=headers, timeout=120)
        response = requests.get(self.get_url(), timeout=120)

        # Technically any status code in the 200's should be fine but 200 is 
        # typical for us, so error out if the status code isn't 200
        if response.status_code != 200: 
            body = "I failed on " + args.w.split('/')[0] + ' : ' + self.arxiv_channel
            body +="\n\n"
            body += traceback.format_exc()
            body += "\n\nStatus Code: "
            body += str(response.status_code)
            body += "\n\nResponse Text:\n"
            body += response.text
            body += "\n\nResponse Content:\n"
            body += response.content.decode('utf-8')
            raise CompletionError(body)

        response = response.content
        response = response.replace(b"author", b"contributor")
        
        feed = feedparser.parse(response)

        if feed.feed.opensearch_totalresults == 0:
            sys.exit("no results found")

        results = []

        latest_id = None

        triggered_authors = {}     # Collect papers with authors we like

        for e in feed.entries:

            arxiv_id = e.id.split("/abs/")[-1]
            title = e.title.replace("\n", " ")

            #print(arxiv_id)  # prints literally every arxiv_id in query, good for debugging

            # the papers are sorted now such that the first is the
            # most recent -- we want to store this id, so the next
            # time we run the script, we can pick up from here
            if latest_id is None:
                latest_id = arxiv_id

            # now check if we hit the old_id -- this is where we
            # left off last time.  Note things may not be in id order,
            # so we keep looking through the entire list of returned
            # results.
            if old_id is not None:
                if arxiv_id <= old_id:
                    continue

            # link
            for l in e.links:
                if l.rel == "alternate":
                    url = l.href

            abstract = e.summary

            # Look for specific authors
            contributors = e.contributors
            for c in contributors: 
                if c['name'].lower() in fave_authors.keys(): 
                    # This removes duplicate tagged authors
                    # This doesn't work if we have two dept members w/same name
                    if url in triggered_authors.keys():
                        try:
                            g = triggered_authors[url].index(c['name'].lower())
                        except:
                             triggered_authors[url].append(c['name'].lower())
                    else: 
                        triggered_authors[url] = [c['name'].lower()]


            # any keyword matches?
            # we do two types of matches here.  If the keyword tuple has the "any"
            # qualifier, then we don't care how it appears in the text, but if
            # it has "unique", then we want to make sure only that word matches,
            # i.e., "nova" and not "supernova".  If any of the exclude words associated
            # with the keyword are present, then we reject any match
            keys_matched = []
            channels = []
            for k in keywords:
                # first check the "NOT"s
                excluded = False
                for n in k.excludes:
                    if n in abstract.lower().replace("\n", " ") or n in title.lower():
                        # we've matched one of the excludes
                        excluded = True

                if excluded:
                    continue

                if k.matching == "any":
                    if k.name in abstract.lower().replace("\n", " ") or k.name in title.lower():
                        keys_matched.append(k.name)
                        channels.append(k.channel)

                elif k.matching == "unique":
                    qa = [l.lower().strip('\":.,!?') for l in abstract.split()]
                    qt = [l.lower().strip('\":.,!?') for l in title.split()]
                    if k.name in qa + qt:
                        keys_matched.append(k.name)
                        channels.append(k.channel)

                elif k.matching == "case":
                    qa = [l.strip('\":.,!?') for l in abstract.split()]
                    qt = [l.strip('\":.,!?') for l in title.split()]
                    if k.name in qa + qt:
                        keys_matched.append(k.name)
                        channels.append(k.channel)

            if keys_matched:
                results.append(
                    Paper(arxiv_id, title.replace("   ", " "), url, keys_matched, channels))

        return results, latest_id, triggered_authors


def send_all_emails(papers, mail):
    """ 
    Handle a list of emails, or single email, or null argument. Then trigger
    slackPoster's send_email function.
    
    :param papers: list of paper objects returned by search_astroph
    :param mail: comma-separated list of email addresses OR
                 single email address OR
                 None if no addresses to send mail to
    """
    if mail:
        email_addresses = mail.split(',')
        for email_address in email_addresses:
            send_email(papers, mail=email_address.strip())

    return


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


def search_astroph(keywords, fave_authors, arxiv_channel, query_email,  old_id=None):
    """ do the actual search though astro-ph by first querying astro-ph
        for the latest papers and then looking for keyword matches"""

    today = dt.date.today()
    day = dt.timedelta(days=1)

    max_papers = 200

    # we pick a wide-enough search range to ensure we catch papers
    # if there is a holiday

    # also, something wierd happens -- the arxiv ids appear to be
    # in descending order if you look at the "pastweek" listing
    # but the submission dates can vary wildly.  It seems that some
    # papers are held for a week or more before appearing.
    q = AstrophQuery(today - 10*day, today, max_papers, arxiv_channel, old_id=old_id)
    #print(q.get_url())

    try:
        papers, last_id, authors = q.do_query(fave_authors, query_email,
                                              keywords=keywords, old_id=old_id)
    except CompletionError:
        time.sleep(5)
        try:
            papers, last_id, authors = q.do_query(fave_authors, query_email,
                                                  keywords=keywords, old_id=old_id)
        except CompletionError:
            sys.exit()

    papers.sort(reverse=True)

    return papers, last_id, authors


def send_email(papers, mail=None):

    # compose the body of our e-mail
    body = ""

    # sort papers by keywords
    current_kw = None
    for p in papers:
        if not p.kw_str() == current_kw:
            current_kw = p.kw_str()
            body += "\nkeywords: {}\n\n".format(current_kw)

        body += u"{}\n".format(p)

    # e-mail it
    if not len(papers) == 0:
        if not mail is None:
            report(body, "astro-ph papers of interest",
                   "lazy-astroph@{}".format(platform.node()), mail)
        else:
            print(body)

def backup_plan(string):
    """
    try string as a command 15 times, if fails send an email and give up
    exit lazy_astroph if fail so that param files are not updated

    :param string: a command to be run
    """

    # run 15 times or until it works
    counter = 0
    while counter < 15:
        counter += 1
        stdout0, stderr0, rc = run(string)

        if int(rc) == 0: 
            break
            
        time.sleep(120)
    
    # if it worked, we're done
    if int(rc) == 0: return

    # othewrwise, give up so param files don't write, but email us first
    body = "Broken, I am. Save me, you must.\n\n" + str(stdout0) 
    body += '\n' + str(stderr0) + '\n' + "Error Code: " + str(rc) 
    
    with open('emails.txt', 'r') as emails:
        email_addresses = [x.strip() for x in emails.readlines()]
    
    for mail in email_addresses:
        report(body, ":'(", "lazy-astroph@{}".format(platform.node()), mail)

    sys.exit()

    return


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


def slack_post(papers, channel_req, authors, fave_authors, 
                    username=None, icon_emoji=None, webhook=None):
    """ post the information to a slack channel """

    # loop by channel
    for c in channel_req:
        channel_body = ""
        found_urls, unique_papers = [], []
        for p in papers:
            if p.url in found_urls:
                continue
            else:
                found_urls.append(p.url)
                unique_papers.append(p)
        num = 0
        for p in unique_papers:
            if not p.posted_to_slack:
                if (c in p.channels) and (len(p.keywords) >= channel_req[c]):
                    if p.url in authors.keys():
                        channel_body += ("\n"
"*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -*\n")
                    if len(p.keywords) >= channel_req[c]:
                        num += 1
                        keywds = ", ".join(p.keywords).strip()
                        channel_body += "{0}. {1}\n\t\t[{3}] - {2}\n".format(
                                                   num, p.title, p.url, keywds)
                        #channel_body += u"{} [{}]\n\n".format(p, keywds)
                        p.posted_to_slack = 1
                    if p.url in authors.keys():
                        for peep in authors[p.url]: 
                            channel_body += ("\n\t\t:point_up::star-struck: "
                            "*Congrats <{}> on your paper!!*".format(
                                                       fave_authors[peep]))
                            channel_body += ":tada::sparkles:\n"
                        channel_body += ("\n"
"*- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -*\n")

        if webhook is None:
            print("channel: {}".format(c))
            continue

        payload = {}
        payload["channel"] = c
        if username is not None:
            payload["username"] = username
        if icon_emoji is not None:
            payload["icon_emoji"] = icon_emoji
        payload["text"] = channel_body

        cmd = "curl -X POST --data-urlencode 'payload={}' {}".format(json.dumps(payload), webhook)
        backup_plan(cmd)

def doit():
    """ the main driver for the lazy-astroph script """

    # parse runtime parameters
    parser = argparse.ArgumentParser()

    parser.add_argument("-m", help="e-mail address to send report to. Use comma-separated list for multiple.",
                        type=str, default=None)
    parser.add_argument("inputs", help="inputs file containing keywords",
                        type=str, nargs=1)
    parser.add_argument("-w", help="file containing slack webhook URL",
                        type=str, default=None)
    parser.add_argument("-u", help="slack username appearing in post",
                        type=str, default=None)
    parser.add_argument("-e", help="slack icon_emoji appearing in post",
                        type=str, default=None)
    parser.add_argument("--dry_run",
                        help="don't send any mail or slack posts and don't update the marker where we left off",
                        action="store_true")
    parser.add_argument("--channel", type=str, default="astro", 
                        help="Name of arXiv channel that you're searching") 
    parser.add_argument("--query_email", type=str, required=True,
                        help="Email address used for arXiv query header") 
    global args 
    args = parser.parse_args()
    
    directory_name = args.inputs[0][0:-7]
    
    # get the keywords
    keywords = []
    try:
        f = open(args.inputs[0], "r")
    except:
        sys.exit("ERROR: unable to open inputs file")
    else:
        channel = None
        channel_req = {}
        for line in f:
            l = line.lower().rstrip()

            if l == "":
                continue

            elif l.startswith("#") or l.startswith("@"):
                # this line defines a channel
                ch = l.split()
                channel = ch[0]
                if len(ch) == 2:
                    requires = int(ch[1].split("=")[1])
                else:
                    requires = 1
                channel_req[channel] = requires

            else:
                # this line has a keyword (and optional NOT keywords)
                if "not:" in l:
                    kw, nots = l.split("not:")
                    kw = kw.strip()
                    excludes = [x.strip() for x in nots.split(",")]
                else:
                    kw = l.strip()
                    excludes = []

                if kw[len(kw)-1] == "-":
                    matching = "unique"
                    kw = kw[:len(kw)-1]
                else:
                    matching = "any"

                keywords.append(Keyword(kw, matching=matching,
                                        channel=channel, excludes=excludes))

    # Search though each arXiv channel, save all the papers. 
    channels_to_search = args.channel.split(',')
    papers = []
    last_id = []

    # Load in file of selected authors we like to support
    fave_authors = {}
    author_file = "fave_authors.txt"
    with open(author_file, 'r') as f:
        for line in f: 
            line = line.strip()
            key = line.split(';')[0].lower()
            value = line.split(';')[1]
            fave_authors[key] = value

    all_authors = {}
    for channel_n in range(len(channels_to_search)):

        # have we done this before? if so, read the .lazy_astroph file to get
        # the id of the paper we left off with
        param_file = directory_name + "/.lazy_astroph-{}".format(
                                                  channels_to_search[channel_n])
        try:
            f = open(param_file, "r")
        except:
            old_id = None
        else:
            old_id = f.readline().rstrip()
            f.close()

        #search the channels
        papers_tmp, last_id_tmp, authors = search_astroph(keywords,fave_authors,
               arxiv_channel=channels_to_search[channel_n], 
               query_email=args.query_email, old_id=old_id)
        for k, v in authors.items():
            all_authors[k] = v

        print("doit last_id_tmp", last_id_tmp)
        for paper in papers_tmp:
            papers.append(paper)
        last_id.append([param_file, last_id_tmp])

    print([x.keywords for x in papers])

    if not args.dry_run:
        send_all_emails(papers, args.m)

        if not args.w is None:
            try:
                f = open(args.w)
            except:
                sys.exit("ERROR: unable to open webhook file")

            webhook = str(f.readline())
            f.close()
        else:
            webhook = None

        slack_post(papers, channel_req, all_authors, fave_authors, 
                    icon_emoji=args.e, 
                    username=args.u, webhook=webhook)

        for ids in last_id:
            print("writing param_file", ids[0])
            try:
                f = open(ids[0], "w+")
            except:
                sys.exit("ERROR: unable to open parameter file for writting")
            else:
                f.write(ids[1])
                f.close()
    else:
        send_all_emails(papers, mail=None)

if __name__ == "__main__":
    print(dt.datetime.now())
    doit()
