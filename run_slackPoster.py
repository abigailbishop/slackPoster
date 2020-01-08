# Main code to search the arXiv for new articles

import os


main_dict = {'astro': ['astro', 'physics'],
             'wipac': ['astro', 'physics', 'hep'],
             'hep': ['hep', 'physics']}


for name, channels in main_dict.items():
    
    for channel in channels:

        print(name)
        
        os.system('./lazy_astroph.py -w {0}/webhook --channel {1} {0}/inputs'.format(name, channel))
        #os.system('./lazy_astroph.py --dry_run --channel {1} {0}/inputs'.format(name, channel))
        
        os.system('rm ../.lazy_astroph')
