# A shell to run the slackPoster once each day

import datetime
import os
import time

# wait to run until after new articles have been posted (posted at 7pm central)
weekdays, weekends = [6, 0, 1, 2, 3], [4, 5]
central_time_posting_hour = 20

while True:

    day_of_week = datetime.datetime.now().weekday()
    current_hour = datetime.datetime.now().hour

    if day_of_week in weekdays and current_hour == central_time_posting_hour:

        #run slackPoster script
        os.system('python run_slackPoster.py')
        time.sleep(3600)
        
    else:
        time.sleep(3600)

