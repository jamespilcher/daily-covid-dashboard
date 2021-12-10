"""Handles and processes data returned from News API."""
import time
import sched
import json
import logging

from threading import Event
from datetime import date, timedelta
import requests

from loadconfig import newsAPI_key, config_covid_terms, news_outlet_websites

def news_API_request(covid_terms="Covid COVID-19 coronavirus") -> dict:
    """Returns a dictionary of news data from the API.
    Data is from the past 7 days, sorted by newest, and from configurable sources
    This data is as a dictionary, where the key 'articles' contains a list of dictionaries for each
    article.
    """
    last_week = date.today() - timedelta(days=7)
    last_week_date = last_week.strftime("%Y-%m-%d")
    terms = covid_terms.replace(" ", " OR ") # allows for all keywords to be searched at once

    url = "https://newsapi.org/v2/everything?qInTitle=" + terms + "&language=en" + "&domains=" + \
        news_outlet_websites + "&from=" + last_week_date + "&sortBy=publishedAt" + \
        "&pageSize=100" + "&apiKey=" + newsAPI_key
    return requests.get(url).json()

def duplicate_article_remover(list_of_dictionaries: list[dict]) -> list[dict]:
    """Returns a list of dictionaries that don't have duplicate values for the key 'title'
    Essentially cleans up messy data.
    """
    titles_seen = []
    non_duplicates = []
    for ele in list_of_dictionaries:
        if ele['title'].lower() in titles_seen:
            logging.info("Duplicate headline found (and dealt with)")
            continue
        else:
            titles_seen.append(ele['title'].lower())
            non_duplicates.append(ele)
    return non_duplicates

def update_news(seen_titles: list[str], update_name="test") -> None:
    """Updates the list_of_news.json file"""
    logging.info("[%s] Started Updating News", update_name)
    all_news = news_API_request(config_covid_terms)
    if all_news['status'] != 'ok':
        logging.critical('[%s] Failed to update news', update_name)
        logging.critical('[' + update_name + "] " + all_news['message'])
        articles = []

    else:
        articles = all_news['articles']
        articles = duplicate_article_remover(articles)

        for i in seen_titles:                   # removes read titles.
            for k in articles:
                if i == k['title']:
                    articles.remove(k)

        for ele in articles:
            ele['title'] = "[" + ele['source']['name'] + "] | " + ele["title"]
            content = ele['content'][:185] + "... "
            ele['content'] = content + ("<br> <a href='" + ele['url'] + \
                "' target='_blank'" + ">Read Here</a>")         # target='_blank' opens in new tab
        logging.info("[%s] Finshed Updating News", update_name)

    with open('data/list_of_news.json', 'w', encoding='utf-8') as file:
        json.dump(articles, file, indent=4)
    return

removed_titles = []

news_scheduler = sched.scheduler(time.time, time.sleep)

def schedule_news_updates(update_interval: int, update_name: str) -> Event:
    """Schedules the update_news function to execute in a given time interval,
    and returns the scheduled event
    """
    update = news_scheduler.enter(update_interval,1, update_news, (removed_titles, update_name,))
    logging.info("[%s] Scheduled a News Update", update_name)
    return update
