from exif import Image


def decimal_coords(coords, ref):
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == "S" or ref == "W":
        decimal_degrees = - decimal_degrees
    return decimal_degrees


def image_datetime(img):
    return img.get('datetime_original', None) or img.get('datetime_digitized', None) or img.get('datetime', None)


# Ignoring altitude
def image_coordinates(img):
    try:
        return decimal_coords(img.gps_latitude, img.gps_latitude_ref), decimal_coords(img.gps_longitude, img.gps_longitude_ref)
    except AttributeError:
        return None


# Post processors depend on the data type
# All post processors do the following:
# Dont return exceptions. Instead return None if something goes wrong (exception handeling is with the post processor)
# Return a dict, where the key is the data name and the value the value itself
# The input depends on the data type, but tipically is a string (for files, the file path)
def main(image_path='/Users/amserra/Downloads/IMG_7964/IMG_7964.jpg'):
    try:
        with open(image_path, 'rb') as src:
            img = Image(src)
    except OSError:
        return None

    if not img.has_exif:
        return None

    coordinates = image_coordinates(img)
    datetime = image_datetime(img)

    return {
        'datetime': datetime,
        'coordinates': coordinates
    }