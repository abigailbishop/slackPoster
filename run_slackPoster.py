#!/usr/bin/env python3

# Main code to search the arXiv for new articles

import os


main_dict = {
             'astro': 'astro,physics',
             'wipac': 'astro,physics,hep',
             'hep': 'hep,physics',
             'amo': 'physics',
             'biophysics' : 'physics',
             'condmat': 'cond,quant,physics',
             'plasma': 'physics,astro'
}

# read from gitignored-email file to get addresses
with open('emails.txt', 'r') as emails:
     email_addresses = ','.join([x.strip() for x in emails.readlines()])

for name, channels in main_dict.items():

     print(name)

     # For production
     os.system('./lazy_astroph.py -w {0}/webhook --channel {1} {0}/inputs'.format(name, channels))

     # For testing on personal slack channel
     #os.system('./lazy_astroph.py -w test_webhook --channel {1} {0}/inputs -m {2}'.format(name, channels, email_addresses))
     #os.system('./lazy_astroph.py -w test_webhook --channel {1} {0}/inputs'.format(name, channels))
     #break
     
     # For running without updating param files or posting to Slack
     #os.system('./lazy_astroph.py --dry_run --channel {1} {0}/inputs'.format(name, channels))
