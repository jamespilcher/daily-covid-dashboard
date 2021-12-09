# Daily Covid Dashboard
![Covid19](https://c.files.bbci.co.uk/D505/production/_115033545_gettyimages-1226314512.jpg)
---
## Contents:
---
- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Altering Config File](#altering-the-config-file)
- [Running The Program](#running-the-program)
- [So How Does The Program Work?](#so-how-does-the-program-work)
    - [On server launch](#on-server-launch)
    - [On user input](#on-user-input)
    - [How do updates work?](#how-do-updates-work)
    - [Updating the template](#updating-the-template)
- [Modules + Function Documentation](#modules)
    - [covid_data_handler.py](#covid_data_handler)
    - [covid_news_handling.py](#covid_news_handling)
    - [interface.py](#interface)
    - [loadconfig.py](#loadconfig)
    - [Testing Modules](#testing-modules)
- [Logging Info](#logging-info)
- [Possible Improvements](#possible-improvements)
- [Info and License](#info-and-license)
## Introduction:
---
This code provides the front and back end for a UK Covid Data and News Dashboard. This dashboard application coordinates information about COVID infection rates from the Public Health England API and news stories about Covid from an appropriate news API (newsapi.org). The user can: schedule (and cancel) updates for the data or the news articles via a form, read the latest news from the past 7 days (sorted by newest), and remove articles if they wish.

## Prerequisites:
---
External Libraries Used:
- uk-covid19: https://publichealthengland.github.io/coronavirus-dashboard-api-python-sdk/
    ```html
    pip install uk-covid19
    ```
- newsapi:    https://newsapi.org/docs/client-libraries/python 
    ```html
    pip install news api
    ```
- schedule:   https://pypi.org/project/schedule/
    ```html
    pip install schedule
    ```
- Flask:      https://flask.palletsprojects.com/en/2.0.x/installation/#python-version
    ```html
    pip install flask
    ```
## Running The Program:
---
-   Open and run the interface(.py) file. 
-   The server will start and your browser will automatically navigate to the right url.
## Altering The Config File:
---
In config.json:
##### "location_type" can be:
-   "ltla" - Lower Tier Local Authority
-    "utla" - Upper Tier Local Authority
-    "region" - Region (E.g. North West)

##### "location" is the location within the given region type:
-   location and location_type have an "is a" relationship
    -   "South West" is a "region"
    -   "Devon" is a "utla"
    -   "Exeter" is a "ltla"
    -    "location" is a "location_type"

##### "country" must be a nation that is a member of the UK (as this software uses the UK Covid API)
-   England, Scotland, Wales, Northern Ireland
##### "local_host_url" is the url that the interface module will open your browser to navigate to
-   Leave as 'http://127.0.0.1:5000/' for the standard local host url

##### "covid_terms" add terms separated by a whitespace. e.g. "Covid Vaccine Coronavirus Booster"
-   The news API will return articles that include at least one of these terms
##### "newsAPI_key"  Insert it in the config file as a string. 
-    Get a NewsAPI key from here: https://newsapi.org/docs/get-started
##### "news_outlet_websites" a string of news domains seperated by a comma then a white space (", ")
-   These are the sites that articles will be taken from




## So How Does The Program Work?
---
- [On server launch](#on-server-launch)
- [On user input](#on-user-input)
- [How do updates work?](#how-do-updates-work?)
- [Updating the template](#updating-the-template))
### On server launch:
---
- Logging is set up
- covid_data_updater and update_news are called, in order to intialise the data (as a file)
- update_queue (what is shown in the GUI) is initialised as a blank list
- used_random_word_combinations is initialised as a blank list
- a sched object, schedule_widget_remover is created.
- The files are read and embedded into the template (under the home function). Therefore Covid Data and news is shown to the user (the first 5 articles!)
- A web browser is launched on the host URL http://127.0.0.1:5000/ (this can be changed in the config file)
- imported variables from other modules that are also initialised:
    -   removed_titles, an empty list that is appended to as news toasts close
    -   cov_scheduler, the sched object for scheduling covid updates
    -   news_scheduler, the sched object for scheduling news updates

### On user input:
---
The data stored in list_of_news.json is turned into a variable of type list, called list_news
- If a user sets an update:
    -   We know if a user has done so if a title for the update is returned (as a title is a precondition for submitting an update)
    -   First we check if the update is 'useful'. 'Useful' being defined as: "does the user want to update either covid data or the news", if not, don't do anything (apart from log that it happened!).
    -   If it is useful, we then get other 'facts' about the update. Does the user want the update to repeat (True/False)? What time does the user want it to happen at ("XX:XX"). We also use this info to generate a values for a dictionary called 'update'.
    -   Next we check if the same title has previously been submitted, if so append a unique random adjective and noun to it, to remove duplicate titles. (we append this random adjective and noun combonation to used_random_words_combinations)
    -   update stores: the time it wants to execute, whether its a repeating update, the title, the content, and scheduled events for each scheduler (covid, news, and widget removal - widget removal acts like a self destruct timer in order to remove from the GUI on completion).
    -   Knowing what kind of update is intended, the code processes it and updates the schedulers accordingly, which in turn stores the events in the update's corresponding dictionary - so that they have the ability to be cancelled later on if necessary...
    -   This update dictionary is then appended to a list called update_queue, which is displayed to the user by the title and content being rendered in the template once we return home(). The use of update_queue also allows us to refer to the events stored in each dictionary. Again, this allows us to cancel them...

- If a user closes a news toast:
    -   The title of the toast is stored in a variable called news_title.
    -   Loop through list_news, if news_title is equal to a title from list_news, remove that element from news_list, then dump list_news (now without that article) into the original list_of_news.json.
    -   Append that news_title to a list of removed_titles. Each time news data is updated, the program will check the recieved news with the removed_titles list for any matching titles, and if so, it will remove the corrosponding articles from the list.
- If a user closes an update toast.
    -   The title of the toast is stored in a variable called update_title.
    -   We then loop through the update_queue, comparing if each elements 'title' key is equal to update_title.
    -   If it is, that means we have found the scheduled update we want to cancel.
    -   First we remove the element from the update_queue (meaning it is no longer displayed in the GUI).
    -   Next we cancel the scheduled updates stored in the dictionary (including the self-destructing widget remover!)
### How do updates work?
---
The news and covid updates work very similarly. Once a scheduled update reaches it's activation time (or on server launch) the following happens:
- Covid Data Update:
    -   New Local data and national data is called from the UK Covid API. 
    -   The desired data is then processed and placed into a dictionary.
    -   Dictionary is 'dumped' into covid_data.json
- News Update:
    -   Relevant News is pulled from the news API. This news from the past 7 days, is sorted by newest, and only from configurable sources (and containing the configurable key words). This returns a dictionary.
    -   As long as we get the data back, indicated by the 'status' key, we continue onward.
    -   The 'articles' key contains a list of articles. We filter these articles to remove duplicates!
    -   We also format the title to make it look nicer, we shorten the content and we attach a html hyperlink to its 'content' as a string. When displaying, we 'MarkUp' this content, in order to make it so you can actually click the link.
    -  Once fully processed, we dump this list of articles to list_of_news.json, which is later put into the template...
### Updating the template
---
After user input/refresh after update we redirect 'home'

@app.route('/')
def home():
This is where we go after User input or an update (including right after launch).
-   Data is loaded from covid_data.json, and list_of_news.json and stored as a dictionary (covid_data) and a list of dictionaries (list_news) respectively.
    -   The 'content' value for each element in list_news is then 'Marked Up' as mentioned earlier, meaning it's hyperlinks will be interactable.
-   This data is then inserted into the render template, along with text and images that appear on the website.
    - Note: list_news is sliced in order to only show the first 5 each time we return home (list_news[:5])

## The UI From a User Perspective:
---

##### Updates:
-   Scheduled updates are displayed on the left hand side of the UI, and have a unique title and associated content. This is in a readable form, that will look similar to:
Sample Title
Updating: Covid Data, The News, Repeating At Time: 09:58
- If a submitted update with a title that is already in the queue, a unique random adjective and noun will be added to the title (in order to stop duplicate title names).
- Scheduled Updates can: Repeat, Update news, Update covid data.
    - If the submitted update doesn't have news or data selected, then no update will be a set, and a log message will be added.
- Updates will execute at the specified time, and will be sorted by soonest to execution.
    - If no time is specified they will activate immediately. (and if it is repeating, it will be scheduled to happen at the time you pressed submit every day).
- On completion the updates will be removed from the UI. Repeating updates must be manually removed.
- The user can also close widgets from the update queue, and in turn cancel the updates associated with them.

##### News Articles:
- Displayed on the right hand side of the UI. News articles are from the past 7 days, sorted by newest. Only display the first 5 at a time. The sources are set in the config file. It only contains headlines that contain at least one of the configurable key words.
- News articles can be read by clicking on the "Read Here" hyperlink.
- News articles can be closed, and won't reappear when a news update is next called.

##### Other:
-   There is a coronavirus gif at the top which is nice...
    - To change, go into the static folder and place in your image. Then in the interface, look for return render_template.
    - Change 'coronavirus.gif' to the name and file type of your image.


## Modules + Function Documentation:
---
### Modules:

- [covid_data_handler.py](#covid_data_handler)
- [covid_news_handling.py](#covid_news_handling)
- [interface.py](#interface)
- [loadconfig.py](#loadconfig)
- [Testing Modules](#testing-modules)

### covid_data_handler
---
covid_data_handler.py handles, passes, and processes covid data from both file and the UK Covid API.
##### index_of_first_non_empty_csv(list_of_lists: list, column_index: int) -> int:
-   Returns the index of the 'starting row' - the row with the latest data for the given column.
##### parse_csv_data(csv_filename: str) -> list[str]:
-   Returns a list of strings representing each row in a given file.
##### process_covid_csv_data(covid_csv_data: list[str]) -> int:
-   Takes a csv data as a list of strings (representing each row as a string), returns number of cases in the past week, latest hospital cases, latest total deaths.
##### covid_API_request(location="Exeter", location_type="ltla") -> dict:
-   Returns a dictionary of up to date covid data directly from the API.
##### first_non_empty(lst: list[dict], key: str) -> int:
-   Returns the first non-empty value for a given key in an element from a list of dictionaries.
##### first_non_empty_index_finder(lst: list[dict], key: str) -> int:
-   Returns the index of the first non-empty value for a given key in an element from a list of dictionaries.
##### cases_last_7_days(cov_data: dict, key="newCasesByPublishDate") -> int:
-   Returns the number of cases in the past 7 days, for the covid API.
##### covid_data_updater(update_name="test") -> None:
-   Processes relevant data received from API, then saves it into a json file.
##### schedule_covid_updates(update_interval: int, update_name: str) -> Event:
-   Schedules the covid_data_updater function to execute in a given time interval, and returns the scheduled event.

### covid_news_handling
---
covid_news_handling.py handles and processes data returned from News API.
##### news_API_request(covid_terms="Covid COVID-19 coronavirus") -> dict:
-   Returns a dictionary of news data from the API. Data is from the past 7 days, sorted by newest, and from configurable sources. This data is as a dictionary, where the key 'articles' contains a list of dictionaries for each article.
##### duplicate_article_remover(list_of_dictionaries: list[dict]) -> list[dict]:
-   Returns a list of dictionaries that don't have duplicate values for the key 'title'. Essentially cleans up messy data.
##### update_news(seen_titles: list[str], update_name="test") -> None:
-   Updates the list_of_news.json file
##### schedule_news_updates(update_interval: int, update_name: str) -> Event:
-   Schedules the update_news function to execute in a given time interval, and returns the scheduled event.

### interface
---
interface.py is interface between the back-end to the front end.
##### widget_remover(update_name: str) -> None:
-   This removes toasts from the update queue GUI.
##### random_words() -> str:
-   Returns a unique random adjective + noun combonation in title case.
##### time_until_activate(hour_min: str) -> int:
-   Takes a 24 hour time ('00:00') and returns the seconds until that next time appears.

##### @app.route('/')
##### home():
-   Inserts data into the HTML template
##### @app.route('/index', methods=["GET", "POST"])
##### checkboxes():
-   Any time there is user input, this function is called to handle it.

### loadconfig
---
loadconfig.py loads the config.json file and store values into variables, which can then be imported into the necessary modules

### Testing modules:
---
Essentially each of the functions within test_covid_data_handler, test_interface, and test_news_data_handler can be run to see whether the code is executing as intended.

## Possible Improvements:
---
- A windows style (1) (2) (3) for duplicate update names would be nice, but admittedly less fun.
- Change the displayed contents of scheduled updates into something more visually appealing.

## Logging Info
---

An detailed app history is created by logging events to the sys.log file. All user inputs are logged, along with updates that commence, various functions that are called, and events that happen throughout the program. The logs are formatted with the date and time, and often indicate what object caused the log to be written (e.g if an update commences, the name of the scheduled update that caused it will be formatted into the logs)


## Info and License:
---

- Github: https://github.com/jamespilcher/daily-covid-dashboard
- Author: James H. Pilcher (2021)
- Email: Pilcherjames0@gmail.com
- License: MIT License
