# tumblr-bracket-runner
Python program utilizing the Tumblr API allowing users to run poll tournaments partially automatically.

Has two uses:
(1) Takes in a comma seperated value list and creates Tumblr poll posts (in the drafts or queue section) based on parameters and content in said csv.
(2) Takes in a comma seperated value list (which has already been used to create Tumblr poll posts) and reads the results of said polls, exporting them into a new csv (which can be used as the input for the tournament's next round).

In both cases, also requires the name of the tumblr blog, and a text document containing keys authorizing the application to post to said blog (this is a workaround that should be ideally replaced with simpler authorization).

# TODO
- Add ability to authorize the app using just Tumblr login credentials
- User Interface
