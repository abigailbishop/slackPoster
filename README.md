# slackPoster

This code is essentially copied and pasted from the wonderful 
  [Michel Zingale](https://github.com/zingale). 
His respository is available here: https://github.com/zingale/lazy-astroph


## How it works:

We have directories for each \#papers-\* channel on our slack. 
In each directory is a file called `inputs` containing the name of the 
channel it'll post to and all keywords the code will search arXiv for. 
One may also propose to add `require=2` (or some other number) to the inputs 
to tell the code to only report papers containing 2 or more keywords. 
Each directory also contains a file called `webhook` that contains the link 
to the paperPoster application on each channel. 
The webhook is secret, so this file is ignored by git. 

The main code is `lazy_astroph.py`. 
This is the code that will take all the keyword inputs and search the 
abstracts and titles of the latest arXiv papers for them.

`run_slackPoster.py` contains the instructions that allows us 
to run `lazy_astroph.py` for each \#papers-\* channel. 

This works with feedparser version 5.2.1


## Questions:

If you have any questions about this, you can send a message to 
[Rob Morgan](https://github.com/rmorgan10) or
[Abby Bishop](https://github.com/abigailbishop). 


## To Create a New Channel:

This tutorial is for anyone who would like to impliment this 
  functionality into another Slack workspace and as a reminder for us. 
If you would like a new channel to be added to the UWMadison PGSC Slack,
  please reach out to Abby on Slack. 

1. On Slack, create the channel. 
1. Log into your workspace on [api.slack.com](https://api.slack.com).
1. Click `Your Apps` in the top lefthand corner. 
   If you already have an app you use for this, click this app to open it. 
   Under `Add features and functionality` click `Incoming Webhooks`.
    1. If you have not already created a paper posting app, click 
      `Create an App`. 
    1. Name it whatever you'd like and assign it to the appropriate workspace.
    1. Once created, you will be redirected to the app's `Basic Information` page.
      Here you click `Incoming Webhooks` under `Add features and functionality`
      then move the gray slider next to `Activate Webhooks` 
      into the `On` position.   
1. Click `Add New Webhook to Workspace` at the bottom of the page, 
   then publish it to the channel you just created.
1. You will be redirected back to `Incoming Webhooks` where you should see
   under `Webhook URLs for your Workspace` a new line with 
   a link, the channel you created, and your name. 
   Copy this link. 
   This is a secret link, so don't go publishing it anywhere. 
1. In your `slackPoster` directory on your machine, create a new directory. 
   Name it something relating to the topic of papers you wish to post 
   in this new channel. 
1. In this new directory, open up a new file named `webhook` then 
   paste the link you copied earlier on the first and only line of this file. 
   Note: if you do not run `slackPoster` on the computer you are 
   currently operating on, you will need to transfer the webhook file to 
   the computer used to run `slackPoster` as the file is ignored by git 
   (since the webhook is a secret link).
1. Still in this new directory, create a file titled `inputs`.
    1. The first line of this file should begin as `\#` followed by 
      the name of your new channel. 
      You may also choose to add a space after the channel name followed by
      `requires=2` (or some other number) and this will require at least
      2 words to be in a paper abstract or title, 
      else a given paper will not be reported. 
    1. All subsequent lines contain one word, each being a keyword you'd like
      to search new arXiv paper titles and abstracts for. 
      You may also choose to add a few spaces after a keyword followed by 
        
        `NOT: ` followed by a series of words separated by commas. 
          `slackPoster` will not report papers containing these words in its
          title or abstract. 
          
        `MATCHING: unique` to search only for the given keyword, 
          and not for words that happen to contain the keyword too. 
          For example, if you list `nova`, the script will return papers with 
          nova, supernova, etc in their abstracts and titles. 
          `nova   MATCHING: unique` will only return papers with nova, 
          not supernova too. 
1. Find yourself back in the main `slackPoster`directory and open 
   the file `run_slackPoster.py`. 
   In the `main_dict` add an entry where 
   the key is a string containing the name of the directory you just created
   and the value is a string naming the arXiv categories
   you'd like to search through, separated by commas (no spaces).
   The available options are 
   `astro`, `cond`, `gr`, `hep`, `math`, `nlin`, `physics`, and `quant`.
1. Once you do this, you should be good to go!



## So you want to adjust the inputs:

1. Fork this repository (you will need to be signed into your GitHub account).
2. In your fork, enter the inputs file you wish to change, make your edits, then
   commit the changes to the main branch of your fork 
   (green button at the bottom of the page). 
   You can also do this from a terminal, but I'll leave those instructions up
   to you to know or find.
3. Towards the top of the page you will see your username followed by 
   `/slackPoster`. Beneath this, you will see a tab for `Code` (which you 
   should be in), and a tab for `Pull requests`. Click this tab. 
   Click the green button to the right: `New pull request`. 
   The `base repository` should be your username followed by `/slackPoster`.
   The `base` should be `main`. 
   The `head repository` should be `abigailbishop/slackPoster`.
   The `compare` should be `main`.
   Once this is set you should be able to click `Create Pull Request`. 
   Note: If you fork the repository and some time passes, you may need to do 
   the pull request in reverse first to update your fork. 
   Otherwise, the pull request may announce conflicts. 
4. Once your pull request is submitted, one of the `slackPoster` collaborators
   will review the change and add it to the code. 
   If your change is approved before 7:55am, 
   you should see it reflected that night. 
   Otherwise, it will take effect the following day. 
