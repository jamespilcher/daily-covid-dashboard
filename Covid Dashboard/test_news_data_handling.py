"""Tests the functions within news_data_handling"""

from covid_news_handling import news_API_request
from covid_news_handling import update_news
from covid_news_handling import duplicate_article_remover
from covid_news_handling import schedule_news_updates

def test_news_API_request():
    """Tests news_API_request"""
    assert news_API_request()
    assert news_API_request('Covid COVID-19 coronavirus') == news_API_request()

def test_update_news():
    """Tests update_news"""
    update_news('test')

def test_duplicate_article_remover():
    """Tests duplicate_article_remover"""
    list_of_dictionaries_with_duplicates = [
        {"title" : "1"},
        {"title" : "2"},
        {"title" : "3"},
        {"title" : "4"},
        {"title" : "2"},
        {"title" : "2"},
        {"title" : "3"}
        ]

    list_of_dictionaries_without_duplicates = [
        {"title" : "1"},
        {"title" : "2"},
        {"title" : "3"},
        {"title" : "4"}
        ]
    list_of_dictionaries = duplicate_article_remover(list_of_dictionaries_with_duplicates)
    assert list_of_dictionaries == list_of_dictionaries_without_duplicates

def test_schedule_news_updates():
    """Tests schedule_news_updates"""
    schedule_news_updates(update_interval=10, update_name='update test')
