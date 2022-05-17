Filters
=======


Description
-----------

A **filter** is responsible for deciding if an object matches a set of configurations, and return its decision. To make this inference, it has a set of parameters available.

**Input**: 3 inputs are provided, in the following order:

- **data**: the path to the data object;
- **metadata**: a dictionary (Python built-in type *dict*), containing a set of key-value pairs retreived from the post-processing stage;
- **context_configuration**: a set of extra parameters associated with the context. These are: start_date, end_date, location, and radius, which represent some of the fields configurable in a search context. SInce they are all optional, if they are not set their value is None.

**Output**: a boolean (Python built-in type *bool*), or None, stating that the object was (True), wasn't (False), or couldn't (None) be filtered.


Skeleton
----------------------------------

You can write your code inside the following function:

.. code-block:: python

    def main(data, metadata, context_configuration):
        # Do some logical computations here
        return # boolean, or None


Example
-------

This example is used on Maestro to filter data objects by start and end date.


.. code-block:: python

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


Final remarks
-------------
- Return None if something goes wrong, or can't infer based on the provided parameters
- Exceptions should be handled by the filter
- API keys can be imported from django.conf. If the filter is approved, we will contact the developer to exchange the key.