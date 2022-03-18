from datetime import datetime
from operator import itemgetter
import pytz


def main(data, metadata, context_configuration):
    if metadata is None or metadata['datetime'] is None:
        return None

    start_date, end_date = itemgetter('start_date', 'end_date')(context_configuration)
    datetime_obj = datetime.strptime(metadata['datetime'], '%Y:%m:%d %H:%M:%S')
    utc = pytz.UTC
    datetime_obj = utc.localize(datetime_obj)

    if start_date is None and end_date is None:
        return None

    if start_date is not None and end_date is None:
        return start_date <= datetime_obj
    elif start_date is None and end_date is not None:
        return end_date >= datetime_obj
    else:  # both are not None
        return start_date <= datetime_obj <= end_date
