"""This module handles, passes, and processes covid data from both file and
UK Covid API
"""

import logging
import sched
import time
import json

from threading import Event
from uk_covid19 import Cov19API
from loadconfig import config_location_type, config_location, country

def index_of_first_non_empty_csv(list_of_lists: list[list[str]], column_index: int) -> int:
    """Returns the index of the 'starting row'
    - the row with the latest data for the given column
    """
    list_of_lists = list_of_lists[1:]
    for i, ele in enumerate(list_of_lists, start=1):
        if ele[column_index] != "":
            starting_index = i
            return starting_index
    return  # index not found


def parse_csv_data(csv_filename: str) -> list[str]:
    """Returns a list of strings representing each row in a given file"""
    file = open("data/" + csv_filename, "r", encoding="utf-8")
    lstrows = []
    for line in file:
        lstrows.append(line.rstrip())
    file.close()
    return lstrows


def process_covid_csv_data(covid_csv_data: list[str]) -> int:
    """Takes a csv data as a list of strings (representing each row as a string)
    Returns number of cases in the past week, latest hospital cases, latest total deaths
    """
    list_of_lists = []
    for ele in covid_csv_data:
        list_of_lists.append(ele.split(","))

    headers = list_of_lists[0]

    column_for_cases = headers.index("newCasesBySpecimenDate")
    column_for_hospital = headers.index("hospitalCases")
    column_for_deaths = headers.index("cumDailyNsoDeathsByDeathDate")
    starting_row_for_cases_week = index_of_first_non_empty_csv(
        list_of_lists, column_for_cases)
    last_weeks_data = list_of_lists[starting_row_for_cases_week: (
        starting_row_for_cases_week + 7)]

    num_cases_week = 0
    for ele in last_weeks_data:
        num_cases_week += int(ele[column_for_cases])
    row_for_hospital = index_of_first_non_empty_csv(
        list_of_lists, column_for_hospital)
    num_hospital_current = list_of_lists[row_for_hospital][column_for_hospital]

    row_for_deaths = index_of_first_non_empty_csv(
        list_of_lists, column_for_deaths)
    tot_deaths = list_of_lists[row_for_deaths][column_for_deaths]

    return int(num_cases_week), int(num_hospital_current), int(tot_deaths)



# API SECTION
def covid_API_request(location="Exeter", location_type="ltla") -> dict:
    """Returns a dictionary of up to date covid data directly from the API"""
    place = [
        ("areaType=" + location_type),
        ("areaName=" + location)
    ]

    cases_and_deaths = {
        "date": "date",
        "areaName": "areaName",
        "areaCode": "areaCode",
        "newCasesByPublishDate": "newCasesByPublishDate",
        "cumDailyNsoDeathsByDeathDate": "cumDailyNsoDeathsByDeathDate",
        "hospitalCases": "hospitalCases"
    }

    api = Cov19API(
        filters=place,
        structure=cases_and_deaths,
    )
    json_data = api.get_json(as_string=False)
    return json_data


# DICTIONARY HANDLING SECTION
def first_non_empty(lst: list[dict], key: str) -> int:
    """Returns the first non-empty value for a given
    key in an element from a list of dictionaries
    """
    for ele in lst:
        if ele[key] is not None:
            return ele[key]
    return

def first_non_empty_index_finder(lst: list[dict], key: str) -> int:
    """Returns the index of the first non-empty value for a given
    key in an element from a list of dictionaries
    """
    starting_index = 0  # useful for the 7 day cases function.
    for i, ele in enumerate(lst):
        if ele[key] is not None:
            starting_index = i
            return starting_index
    return


# sums the cases over the past 7 days of most recent data
def cases_last_7_days(cov_data: dict, key="newCasesByPublishDate") -> int:
    """Returns the number of cases in the past 7 days, for the covid API"""
    i = (first_non_empty_index_finder(cov_data['data'], key))
    tot = 0
    for k in range(i, i+7):
        daily_cases = ((cov_data['data'])[k])['newCasesByPublishDate']
        tot += daily_cases
    return tot


def covid_data_updater(update_name="test") -> None:
    """Processes relevant data received from API, then saves it into a json file."""
    logging.info("[%s] Started Updating Covid Data", update_name)
    # A little bit clunky, uses many api calls
    data_local = covid_API_request(config_location, config_location_type)
    data_national = covid_API_request(country, "nation")
    covid_data_dic = {
        'deaths_total': first_non_empty(data_national['data'], "cumDailyNsoDeathsByDeathDate"),
        'hospital_cases': first_non_empty(data_national['data'], "hospitalCases"),
        'local_7day_cases': cases_last_7_days(data_local),
        'national_7day_cases': cases_last_7_days(data_national)
    }
    with open('data/covid_data.json', 'w', encoding='utf-8') as file:
        json.dump(covid_data_dic, file, indent=4)
    logging.info('[%s] Finished Updating Covid Data', update_name)
    return


cov_scheduler = sched.scheduler(time.time, time.sleep)


def schedule_covid_updates(update_interval: int, update_name: str) -> Event:
    """Schedules the covid_data_updater function to execute in a given time interval,
    and returns the scheduled event.
    """
    update = cov_scheduler.enter(
        update_interval, 1, covid_data_updater, (update_name,))
    logging.info("[%s] Scheduled a Covid Data Update", update_name)
    return update
