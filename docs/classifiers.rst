Classifiers
===========


Description
-----------

A **classifier** is responsible for the classification of the data object. The classification result can be a number, or a string (label).

**Input**: string (Python built-in type *str*) corresponding to the absolute path where the file is.

**Output**: a number, string, or other that corresponds to the classification of the input.


Skeleton
----------------------------------

You can write your code inside the following function:

.. code-block:: python

    def main(file_path):
        # Open file and perform classification
        return # number, string, or other


Example
-------

This example is used on Maestro. It uses a classifier that, given an audio file, returns its textual representation.


.. code-block:: python

    import torch

    def main(file_path):
        device = torch.device('cpu')  # gpu also works, but our models are fast enough for CPU

        model, decoder, utils = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                               model='silero_stt',
                                               language='en',  # also available 'de', 'es'
                                               device=device)
        (read_batch, split_into_batches,
         read_audio, prepare_model_input) = utils  # see function signature for details

        test_files = [file_path]
        batches = split_into_batches(test_files, batch_size=10)
        model_input = prepare_model_input(read_batch(batches[0]), device=device)

        output = model(model_input)
        for example in output:
            result = decoder(example.cpu())
            return result if result is not None and result != '' else None


Final remarks
-------------
- Return None if something goes wrong, or can't classify
- Exceptions should be handled by the classifier
- API keys can be imported from django.conf. If the classifier is approved, we will contact the developer to exchange the key.