"""Interface between the back-end to the front end."""
# Libraries
import logging
import webbrowser
import json


from sched import scheduler
from time import strftime, gmtime, time, sleep
from random import choice
from markupsafe import Markup
import schedule

from flask import Flask, render_template, request, redirect, url_for

from loadconfig import webpage_url, config_location, country
from covid_data_handler import covid_data_updater
from covid_data_handler import schedule_covid_updates, cov_scheduler
from covid_news_handling import removed_titles, update_news, news_scheduler, schedule_news_updates


logging.basicConfig(filename="sys.log", level=logging.DEBUG,
                    format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S', encoding='utf-8')
logging.info("--------------------------Starting Up--------------------------")

covid_data_updater(update_name="Initialise Covid Data")
update_news(removed_titles, update_name="Initialise News Articles")

update_queue = []
schedule_widget_remover = scheduler(time, sleep)

used_random_words_combinations = []

app = Flask(__name__)

def widget_remover(update_name: str) -> None:
    """This removes toasts from the update queue GUI"""
    for ele in update_queue:
        if ele['title'] == update_name:
            update_queue.remove(ele)
            logging.info("[%s] Removed from GUI", update_name)
    return

def random_words() -> str:
    """Returns a unique random adjective + noun combonation in title case"""
    with open('words/nouns.txt', encoding='utf-8') as file:
        nouns = file.read().splitlines()
    with open('words/adjectives.txt', encoding='utf-8') as file:
        adjectives = file.read().splitlines()
    words = choice(adjectives) + " " + choice(nouns)
    while words in used_random_words_combinations:
        words = choice(adjectives) + " " + choice(nouns)
        logging.info("Random word combo generated has already seen before! Trying again...")
    used_random_words_combinations.append(words)
    return words.title()

# (in seconds) find time after midnights
def time_until_activate(hour_min: str) -> int:
    """Takes a 24 hour time ('00:00') and returns the seconds until that next time appears."""
    current_hours = gmtime().tm_hour
    current_mins = gmtime().tm_min
    current_secs = gmtime().tm_sec
    secs_after_midnight = current_hours * 60 * 60 + \
        current_mins * 60 + current_secs
    hours, mins = hour_min.split(':')
    target_time_in_secs = int(hours) * 60 * 60 + int(mins) * 60
    activate_time = target_time_in_secs - secs_after_midnight
    if activate_time < 0:
        activate_time += 24 * 60 * 60
    return activate_time


@app.route('/')
def home():
    """Inserts the data into the HTML template"""
    with open('data/covid_data.json', 'r', encoding='utf-8') as file:
        covid_data = json.load(file)
    with open('data/list_of_news.json', 'r', encoding='utf-8') as file:
        list_news = json.load(file)

    for ele in list_news:
        # Displays the hyperlinks, instead of a string of raw HTML code
        ele['content'] = Markup(ele['content'])
    return render_template("index.html",

                           image="coronavirus.gif",
                           title="Covid Dashboard",
                           location=config_location,
                           nation_location=country,
                           local_7day_infections=covid_data['local_7day_cases'],
                           national_7day_infections=covid_data['national_7day_cases'],

                           hospital_cases="Hospital Cases: " +
                           str(covid_data['hospital_cases']),

                           deaths_total="Total Deaths: " +
                           str(covid_data['deaths_total']),
                           news_articles=list_news[:5],
                           updates=update_queue)


@app.route('/index', methods=["GET", "POST"])
def checkboxes():
    """Any time there is user input, this function is called to handle it."""
    with open('data/list_of_news.json', 'r', encoding='utf-8') as file:
        list_news = json.load(file)
    schedule_widget_remover.run(blocking=False)
    cov_scheduler.run(blocking=False)
    news_scheduler.run(blocking=False)

    if request.method == "GET":
        # Closing toasts section:
        news_title = (request.args.get('notif'))
        if news_title:
            for ele in list_news:
                if ele['title'] == news_title:
                    list_news.remove(ele)
                    with open('data/list_of_news.json', 'w', encoding='utf-8') as file:
                        json.dump(list_news, file, indent=4)
                    removed_titles.append(news_title.split("| ", 1)[1])
                    logging.info(
                        "News Article [%s] removed from GUI, and added to list of seen titltes",
                        news_title)
                    logging.info("List of Seen Titles: %s", removed_titles)

        update_title = (request.args.get("update_item"))
        if update_title:  # if the user clicked X on an update_title
            for ele in update_queue:
                if ele['title'] == update_title:
                    update_queue.remove(ele)  # removes the update from the GUI
                    logging.info("[%s] Removed from GUI by User", update_title)
                    if ele["do_again"]:
                        if ele['scheduled_covid_update']:
                            schedule.cancel_job(ele['scheduled_covid_update'])
                            logging.info(
                                "[%s] Cancelled: Scheduled Repeating Covid Data Update",
                                update_title)
                        if ele['scheduled_news_update']:
                            schedule.cancel_job(ele['scheduled_news_update'])
                            logging.info(
                                "[%s] Cancelled: Scheduled Repeating News Update",
                                update_title)
                    else:
                        if ele['scheduled_covid_update']:
                            cov_scheduler.cancel(ele['scheduled_covid_update'])
                            logging.info(
                                "[%s] Cancelled: Scheduled Covid Data Update",
                                update_title)
                        if ele['scheduled_news_update']:
                            news_scheduler.cancel(ele['scheduled_news_update'])
                            logging.info(
                                "[%s] Cancelled: Scheduled News Update",
                                update_title)
                        schedule_widget_remover.cancel(
                            ele['scheduled_close_toast'])
                        logging.info(
                            "[%s] Cancelled: Scheduled Removing Itself from GUI",
                            update_title)

        # Submitting section:
        title = request.args.get('two')
        if title:
            covid_data_bool = bool(request.args.get("covid-data"))
            news_bool = bool(request.args.get("news"))
            is_useful = covid_data_bool or news_bool

            if is_useful:
                content = "Updating: "
                if covid_data_bool:
                    content += "Covid Data, "
                if news_bool:
                    content += "The News, "
                do_again = bool(request.args.get("repeat"))
                if do_again:
                    content += "Repeating "
                due = request.args.get('update')
                if due:
                    content += "At Time: " + due

                for ele in update_queue:
                    if title == ele['title']:
                        logging.warning("Title: [%s] in use, appending unique word combonation",
                        title)
                        title += f" ({random_words()})"
                        logging.info("Title is now: [%s]", title)

                    # title is required if you want to add an update
                update = {
                    'due': due,
                    'do_again': do_again,
                    'title': title,
                    'content': content,
                    'scheduled_news_update': None,
                    'scheduled_covid_update': None,
                    'scheduled_close_toast': None
                }
                logging.info(
                    "Update: [%s] created", update['title'] + " | " + update['content'])
                if do_again:
                    if not due:  # if do_again and not due
                        logging.info(
                            "([%s] Repeating Update Was Set Without Time",
                            update['title'])
                        due = strftime("%H:%M")
                        update['due'] = due
                        update['content'] += "At Time: " + due
                        if covid_data_bool:
                            covid_data_updater(update['title'])
                        if news_bool:
                            update_news(removed_titles, update['title'])
                    if covid_data_bool:
                        update['scheduled_covid_update'] = schedule.every().day.at(
                            due).do(covid_data_updater, ())
                        logging.info(
                            "[%s] Scheduled a Repeating Covid Data Update", update['title'])
                    if news_bool:
                        update['scheduled_news_update'] = schedule.every().day.at(
                            due).do(update_news, (removed_titles, update['title']))
                        logging.info(
                            "[%s] Scheduled a Repeating News Update", update['title'])

                elif not due:  # if not do_again and not due
                    logging.info(
                        "[%s] Was set without time specified (activating immediately)",
                        update['title'])
                    if covid_data_bool:
                        covid_data_updater()
                    if news_bool:
                        update_news(removed_titles, update['title'])

                else:  # if not do_again and due
                    if covid_data_bool:
                        update['scheduled_covid_update'] = schedule_covid_updates(
                            time_until_activate(due), update['title'])
                    if news_bool:
                        update['scheduled_news_update'] = schedule_news_updates(
                            time_until_activate(due), update['title'])
                    update['scheduled_close_toast'] = schedule_widget_remover.enter(
                        time_until_activate(due), 1, widget_remover,
                        (update['title'],))
                    logging.info(
                        "[%s] Scheduled Removing Itself From the GUI", update['title'])

                if due:
                    logging.info("[%s] Added to GUI", update['title'])
                    update_queue.append(update)
                    update_queue.sort(key=lambda item: time_until_activate(
                        item['due']), reverse=False)

            else:
                logging.warning("User tried to create an update of nothing.")

    return redirect(url_for('home'))


if __name__ == '__main__':
    webbrowser.open(webpage_url)
    app.run()
