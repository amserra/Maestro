from operator import itemgetter
from math import sin, cos, sqrt, atan2, radians


# Source: https://stackoverflow.com/a/19412565/9847548
def distance_two_points(lat1, long1, lat2, long2):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(float(lat1))
    lon1 = radians(float(long1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(long2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c  # in kms
    return distance * 1000  # in m


def main(data, metadata, context_configuration):
    if metadata is None or metadata['coordinates'] is None or len(metadata['coordinates']) != 2:
        return None

    location, radius = itemgetter('location', 'radius')(context_configuration)
    lat1, long1 = location.split(',')

    lat2, long2 = metadata['coordinates']

    distance_in_m = distance_two_points(lat1, long1, lat2, long2)

    if distance_in_m <= radius:
        return True
    else:
        return False
