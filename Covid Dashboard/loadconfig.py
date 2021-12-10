"""Loads the config.json file and store key value pairs into variables"""
import json

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

config_location_type = config['location_type']
config_location = config['location']
country = config['country']

config_covid_terms = config['covid_terms']
newsAPI_key = config['newsAPI_key']
news_outlet_websites = config['news_outlet_websites']
webpage_url = config["local_host_url"]
