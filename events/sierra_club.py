import re
import requests
import json
from datetime import datetime
import unicodedata
import logging

logger = logging.getLogger(__name__)

def fetch_page(url):
    try:
        r = requests.get(url)
    except Exception as e:
        logger.critical(f"Exception making GET request to {url}: {e}", exc_info=True)
        return
    data = r.json()
    
    return data

def get_event_cost(event_cost_description):
    event_cost_description_lower = event_cost_description.lower()
    currency_re = re.compile(r'(?:[\$]{1}[,\d]+.?\d*)')
    event_costs = re.findall(currency_re, event_cost_description)
    if len(event_costs) == 1 and "donation" not in event_cost_description_lower and "voluntary" not in event_cost_description_lower:
        event_cost = event_costs[0].split(".")[0].replace("$", '')
        event_cost = ''.join(s for s in event_cost if s.isdigit())
    else:
        event_cost = ''

    return event_cost

def schematize_event_time(event_time):
    '''
    Converts a time string like '1:30 pm' to 24hr time like '13:30:00'
    '''
    if not event_time:
        # if event time is an empty string, it's because the API didn't provide it.
        return ''
    try:
        datetime_obj = datetime.strptime(event_time.lower(), "%I:%M %p")
        schematized_event_time = datetime.strftime(datetime_obj, "%H:%M:%S")
    except ValueError:
        logger.warning(f"Exception schematizing this event time: {event_time}", exc_info=True)
        schematized_event_time = ''

    return schematized_event_time


def encode_event_description(event_description):
    '''
    removes if there are any special characters in the description
    '''

    return unicodedata.normalize('NFKD', event_description)


def schematize_event_date(event_date):
    '''
    Converts a date like '2019-12-2' to '2019-12-02'
    '''
    if not event_date:
        # if event date is an empty string, it's because the API didn't provide it.
        return ''
    try:
        datetime_obj = datetime.strptime(event_date, "%Y-%m-%d")
        schematized_event_date = datetime.strftime(datetime_obj, "%Y-%m-%d")
    except ValueError:
        logger.warning(f"Exception schematizing this event date: {event_date}", exc_info=True)
        schematized_event_date = ''

    return schematized_event_date


def handle_ans_page(event_list):
    events = []
    for e in event_list:
        event = {}
        event['Event Name'] = e.get('eventName','')
        event['Event Description'] = encode_event_description(e.get('description', ''))
        start_date = schematize_event_date(e.get('startDate',''))
        event['Event Start Date'] = start_date
        event['Event Start Time'] = schematize_event_time(e.get('startTime',''))
        end_date = schematize_event_date(e.get('endDate',''))
        end_date = end_date if end_date else start_date
        event['Event End Date'] = end_date
        end_time = schematize_event_time(e.get('endTime',''))
        event['Event End Time'] = end_time
        event['All Day Event'] = False
        event['Timezone'] = "America/New_York"
        event['Event Organizers'] = "Sierra Club"
        event['Event Cost'] = get_event_cost(e.get('cost','0'))
        event['Event Currency Symbol'] = "$"
        event['Event Category'] = e.get('eventCategory','')
        event['Event Website'] = e.get('urlToShare','')
        event_venue = e.get('location','')
        event_venue = event_venue if event_venue else "See event website"
        event['Event Venue Name'] = event_venue
        # commenting event show map, latitude and longitude fields for now as The WordPress Event plugin doesn't
        # expect these fields, but we might eventually use their Map plugin, which would need those geo fields
        # events_data['latitude'] = event.get('lat','')
        # events_data['longitude'] = event.get('lng','')
        # events_data['Event Show Map'] = event.get('showOnMap','')
        events.append(event)

    return events

def main():
    url = "https://www.sierraclub.org/sc/proxy?url=https://act.sierraclub.org/events/services/apexrest/eventfeed/ent/6300,5051&_=1548294791086"
    data = fetch_page(url)
    if not data:
        return []
    event_list = data.get('eventList', '')
    events = handle_ans_page(event_list)

    return events


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    events = main()