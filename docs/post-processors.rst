Post-processors
===============


Description
-----------

A **post-processor** is responsible for modifying the data objects of a datastream. This can be either on modifying the data object itself (e.g. the image), or extract some metadata from it and store it on the metadata field.
So, we have two types of post-processors:

- **Metadata** post-processors, which extract data from the object and return a set of metadata.
- **Data** post-processors, which modify the data object, and return a new, modified data object.

Also, post-processors are targeted to a specific data type. Currently, Maestro supports Image and Sound data types.

**Input (both types)**: string (Python built-in type *str*) that contains an absolute path to the file.

**Output (metadata post-processor)**: a dict (Python built-in type *dict*), where each key-value pair contains a specific metadata feature.

**Output (data post-processor)**: a binary file (Python built-in type *bytes*, or *BytesIO*) that represents the new file.


Skeleton (metadata post-processor)
----------------------------------

You can write your code inside the following function:

.. code-block:: python

    def main(path):
        # Read file, do your operations

        return {
            'key1': value1,
            'key2': value2,
            # etc.
        }


Skeleton (data post-processor)
----------------------------------

You can write your code inside the following function:

.. code-block:: python

    def main(path):
        # Read file, do your operations

        # Return a bytes or BytesIO binary representation of the file
        return bytes()


Example
-------

This example is used on Maestro to retrieve EXIF metadata of an Image.


.. code-block:: python

    from exif import Image

    def decimal_coords(coords, ref):
        decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
        if ref == "S" or ref == "W":
            decimal_degrees = - decimal_degrees
        return decimal_degrees


    def image_datetime(img):
        return img.get('datetime_original', None) or img.get('datetime_digitized', None) or img.get('datetime', None)


    def image_coordinates(img):
        try:
            return decimal_coords(img.gps_latitude, img.gps_latitude_ref), decimal_coords(img.gps_longitude, img.gps_longitude_ref)
        except AttributeError:
            return None


    def main(image_path):
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


Final remarks
-------------

- In the case of a metadata post-processor, if no metadata is obtained, an empty dict should be returned
- In the case of a data post-processor, if no data object is obtained, an empty bytes variable should be returned
- Return None if something goes wrong
- Exceptions should be handled by the post-processor
- API keys can be imported from django.conf. If the post-processor is approved, we will contact the developer to exchange the key.