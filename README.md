# slackPoster

This code is essentially copied and pasted from the wonderful Michel Zingale. 
His respository is available here: https://github.com/zingale/lazy-astroph


## How it works:

We have directories for each \#papers-\* channel on our slack. 
In each directory is a file called `inputs` containing the name of the 
channel it'll post to, how many keywords are required, 
and all keywords the code will search arXiv for. 
One may also propose to add `require=2` (or some other number) to tell the
code to only report papers containing 2 or more keywords. 
Each directory also contains a file called `webhook` that contains the link 
to the paperPoster application on each channel. 
The webhook is secret, so this file is ignored by git. 

The main code is `lazy_astroph.py`. 
This is the code that will take all the keyword inputs and search the
 abstracts and titles of the latest arXiv papers for them.

`run_slackPoster.py` contains the instructions that allow us 
to run `lazy_astroph.py` for each \#papers-\* channel. 
`run.py` makes the code run everynight at 8pm CDT. 


## So you want to adjust the inputs:

1. Fork this repository (you will need to be signed into your GitHub account).
2. In your fork, enter the inputs file you wish to change, make your edits, then
   commit the changes to the master branch of your fork 
   (green button at the bottom of the page). 
   You can also do this from a terminal, but I'll leave those instructions up
   to you to know or find.
3. Towards the top of the page you will see your username followed by 
   `_/slackPoster`. Beneath this, you will see a tab for `Code` (which you 
   should be in), and a tab for `Pull requests. Click this tab. 
   Click the green button to the right `New pull request`. 
   The `base repository` should be your username followed by `/slackPoster`.
   The `base` should be `master`. 
   The `head repository` should be `abigailbishop/slackPoster`.
   The `compare` should be `master`.
   Once this is set you should be able to click `Create Pull Request`. 
   Note: If you fork the repository and some time passes, you may need to do 
   the pull request in reverse first to update your fork. 
   Otherwise, the pull request may yell at you. 
4. Once your pull request is submitted, one of the slackPoster collaborators
   will review the change and add it to the code. 
   Some time after this, the person running the code will update the code on 
   their machine and you will see the change reflected. 


## Questions:

If you have any questions about this, you can send a message to 
Rob Morgan or Abby Bishop on Slack. 
