# A shell to run the slackPoster once each day

import datetime
import os
import time

# wait to run until after new articles have been posted (posted at 7pm central)
weekdays, weekends = [6, 0, 1, 2, 3], [4, 5]
central_time_posting_hour = 20

print('Script started, waiting for the next even hour to continue')

#also delay the script until 00 minutes so that it will start posteing right at 8pm
while True:
    current_minute = datetime.datetime.now().minute
    if current_minute == 0:
        break
    else:
        time.sleep(60)

print("Staring main loop")

#main loop to run forever
while True:

    day_of_week = datetime.datetime.now().weekday()
    current_hour = datetime.datetime.now().hour

    if day_of_week in weekdays and current_hour == central_time_posting_hour:

        #run slackPoster script
        os.system('python run_slackPoster.py')
        time.sleep(3600)
        
    else:
        time.sleep(3600)

