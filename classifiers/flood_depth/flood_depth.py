import tensorflow as tf
from tensorflow.python.framework import ops
from tensorflow.keras.models import load_model
from tensorflow.keras.layers import Layer
from tensorflow.keras import backend as K
from tensorflow.keras.utils import get_custom_objects
from tensorflow.keras.preprocessing.image import load_img, img_to_array
import numpy as np
import os


def softargmax(x, beta=1e10):
    x = tf.convert_to_tensor(x)
    x_range = tf.range(x.shape.as_list()[-1], dtype=x.dtype)
    return tf.reduce_sum(tf.nn.softmax(x*beta) * x_range, axis=-1)


def custom_activation_more_1m(x):
    return K.clip(K.relu(x), 1, max_value=None)


def custom_activation_less_1m(x):
    return K.clip(K.relu(x), 0, 1)


class OutputLayer(Layer):

    def __init__(self, **kwargs):
        super(OutputLayer, self).__init__(**kwargs)
        self.supports_masking = True
        self.__name__ = 'outputLayer'

    def call(self, inputs, **kwargs):
        result = softargmax(inputs[0])
        return K.switch(K.less(result, 0.5),
                        K.zeros_like(inputs[1]),
                        K.switch(K.less(result, 1.5),
                                inputs[1],
                                inputs[2]))

    def get_config(self): return super(OutputLayer, self).get_config()

    def compute_output_shape(self, input_shape): return (None, 1)


get_custom_objects().update({'outputlayer': OutputLayer()})



def load_model_from_path(path):
    custom_object = {
        'OutputLayer': OutputLayer,
        'custom_activation_more_1m': custom_activation_more_1m,
        'custom_activation_less_1m': custom_activation_less_1m
    }
    g_model = load_model(path, custom_objects=custom_object)
    return g_model


def pre_process_img(img):
    x = load_img(img, target_size=(224, 224))
    x = img_to_array(x)
    x = np.divide(x, 255)
    return np.expand_dims(x, axis=0)


def main(image_path):
    weights_path = os.path.join('classifiers', 'flood_depth', 'weights.hdf5')
    g_model = load_model_from_path(weights_path)

    predictions = g_model.predict(pre_process_img(image_path), batch_size=1)

    label = np.argmax(predictions[0])
    height = round(predictions[1][0][0], 4)
    if label == 0:  # no flood case
        return None
    else:
        # convert numpy float32 to python float
        return float(height)


# if __name__ == "__main__":
#     # Label returns a number (0, 1, or 2), saying if is no flood, flood less 1 meter, or flood more 1 meter
#     number_to_label = ["No Flood", "Flood less 1 meter", "Flood more 1 meter"]
#
#     predictions = main()
#     label = np.argmax(predictions[0])
#     height = round(predictions[1][0][0], 4)
#
#     print(f"Predictions: {predictions}")
#     print(f"Label: {number_to_label[label]} ({label})")
#     print(f"Height: {height}")
