# Document Score Card Tool

This application has been developed by the solution engineering team.  Document Score Card (DSC) is a tool that can create scenarios and test them against uploaded files to receive a scorecard. A scenario consists of ESPs (Entity-Score Pairs). Each ESP requires an xpath and score (ex. /invoice/header/invoiceHeader/tradingPartnerId with a score of 5), it can also have data that can be used for content validation or qualifiers.

This tool's UIs use SPS Commerce's Webui-core styling and angularjs. The database is build in postgres SQL with python.

### How to use it
(update to confluence page to follow testing and bug removal phase)

### How to get it working locally (built/tested in Windows)
*These steps should be a good start for most cases, but not perfect in any means.*

**NOTE:** *gulp (gulpfile.js) is not fully functional for this project, flask takes care of recompiling/updating server when saved*
This project requires:
1. flask (first part of this tutorial is decent to install and learn from: [flask tutorial](http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world))
2. [node.js](https://nodejs.org/en/) (or node-legacy for linux/ubuntu)
3. npm (part of node.js?)
4. bower (installed through npm)

After the items above are installed and the github file downloaded, run flask's virtual environment (by running the activate script in the scripts folder), this allows you to install software/modules without messing with your local machine.

##### Inside a command terminal

First run `npm install` from the folder location with package.json, this installs all of the dependency modules in this file. This will create a new folder `node_modules` in the same folder.

Second run `bower install` from the folder location with bower.json file.  This will install the necessary components needed for the UI, like angularjs and webui-core. This will create a new folder `bower_components` in the location specified in .bowercc

Now what is left is starting the local server to serve up the html files. To do this locate the files flask/scripts/python and the tool's run.py (which should be inside the `application` folder). Run a command as such (location of flask/scripts/python) (location of run.py) which should look similar to `./flask/scripts/python application/run.py`.  This should start the server that will continue to use that command terminal until it is killed, errs, or closes.

### How to update the tool on the solution engineers' server
This can be a little tricky, hoping to find a better way to do so.

First open the tmux where the server is running and kill the process. Do not do anything else in this tmux terminal yet, start from another terminal.

Once changes and updates have been pushed to the github repo, located the github folder/repo on the server.  Do a `git pull` command. Copy the updated DocumentScoreCard folder to the location of the tool's source files. (It is probably best if the old folder is removed? Not sure if `cp` works with same named directories and if they are merged, plus if files are renamed/removed in the repo we do not want them on the server either)

Go back to the tmux terminal, run the `npm install` and `bower install` commands as noted in the previous section.

Next (still in the tmux terminal) go find the file `config.py` and open it. Comment out the section specifying Windows use and uncomment the section for server/ubuntu/linux.Then Find the file `run.py` and open it. Add/change the line `app.run(debug=True)` to `app.run(port=9004)`.

Finally, run the script `run.py` in the way noted in the section above. Detach from the tmux terminal, `ctrl+b, d`.
