import os
from django.conf import settings
from context.models import Fetcher, PostProcessor, Filter, Classifier, Configuration

BASE_DIR = settings.BASE_DIR

def create_fetchers():
    bing_image = Fetcher.objects.create(
        name='Bing image',
        is_active=True,
        is_default=True,
        type=Fetcher.PYTHON_SCRIPT,
        path=os.path.join(BASE_DIR, 'fetchers', 'fetcher_bing_image_api.py')
    )

    twitter_image = Fetcher.objects.create(
        name='Twitter Images',
        is_active=True,
        is_default=False,
        type=Fetcher.PYTHON_SCRIPT,
        path=os.path.join(BASE_DIR, 'fetchers', 'fetcher_twitter_api_images.py')
    )

    bing_web = Fetcher.objects.create(
        name='Bing web search',
        is_active=True,
        is_default=False,
        type=Fetcher.PYTHON_SCRIPT,
        path=os.path.join(BASE_DIR, 'fetchers', 'fetcher_bing_web_api.py')
    )

    Fetcher.objects.create(
        name='Freesound',
        incompatible_with=[bing_image, twitter_image, bing_web],
        is_active=True,
        is_default=False,
        type=Fetcher.PYTHON_SCRIPT,
        path=os.path.join(BASE_DIR, 'fetchers', 'fetcher_freesound.py')
    )


def create_post_processors():
    PostProcessor.objects.create(
        name='Exif retriever',
        is_active=True,
        type=PostProcessor.PYTHON_SCRIPT,
        data_type=Configuration.IMAGES,
        kind=PostProcessor.METADATA_RETRIEVAL,
        path=os.path.join(BASE_DIR, 'post_processors', 'image', 'metadata', 'exif_retriever.py')
    )


def create_filters():
    Filter.objects.create(
        name='Geolocation filter',
        is_active=True,
        is_builtin=True,
        type=Filter.PYTHON_SCRIPT,
        kind=Filter.METADATA,
        data_type=Configuration.AGNOSTIC,
        path=os.path.join(BASE_DIR, 'filters', 'location.py')
    )

    Filter.objects.create(
        name='Date filter',
        is_active=True,
        is_builtin=True,
        type=Filter.PYTHON_SCRIPT,
        kind=Filter.METADATA,
        data_type=Configuration.AGNOSTIC,
        path=os.path.join(BASE_DIR, 'filters', 'date.py')
    )

def create_classifiers():
    Classifier.objects.create(
        name='Speech to text',
        is_active=True,
        source_url='https://pytorch.org/hub/snakers4_silero-models_stt/',
        type=Classifier.PYTHON_SCRIPT,
        data_type=Configuration.SOUNDS,
        path=os.path.join(BASE_DIR, 'classifiers', 'speech_to_text', 'speech_text.py'),
        return_type='STR',
        return_choices=''
    )

    Classifier.objects.create(
        name='Emotion detector',
        is_active=True,
        source_url='https://github.com/shangeth/Facial-Emotion-Recognition-PyTorch-ONNX',
        type=Classifier.PYTHON_SCRIPT,
        data_type=Configuration.IMAGES,
        path=os.path.join(BASE_DIR, 'classifiers', 'emotion', 'main.py'),
        return_type='STR',
        return_choices="'neutral', 'happiness', 'surprise', 'sadness', 'anger', 'disguest', 'fear'"
    )

    Classifier.objects.create(
        name='Object detector',
        is_active=True,
        source_url='https://pytorch.org/hub/ultralytics_yolov5/',
        type=Classifier.PYTHON_SCRIPT,
        data_type=Configuration.IMAGES,
        path=os.path.join(BASE_DIR, 'classifiers', 'object_detector', 'object_detector.py'),
        return_type='STR',
        return_choices="'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'"
    )

    Classifier.objects.create(
        name='Bird species',
        is_active=True,
        source_url='https://pytorch.org/hub/nicolalandro_ntsnet-cub200_ntsnet/',
        type=Classifier.PYTHON_SCRIPT,
        data_type=Configuration.IMAGES,
        path=os.path.join(BASE_DIR, 'classifiers', 'bird_classifier', 'bird_classifier.py'),
        return_type='STR',
        return_choices="'Black_footed_Albatross', 'Laysan_Albatross', 'Sooty_Albatross', 'Groove_billed_Ani', 'Crested_Auklet', 'Least_Auklet', 'Parakeet_Auklet', 'Rhinoceros_Auklet', 'Brewer_Blackbird', 'Red_winged_Blackbird', 'Rusty_Blackbird', 'Yellow_headed_Blackbird', 'Bobolink', 'Indigo_Bunting', 'Lazuli_Bunting', 'Painted_Bunting', 'Cardinal', 'Spotted_Catbird', 'Gray_Catbird', 'Yellow_breasted_Chat', 'Eastern_Towhee', 'Chuck_will_Widow', 'Brandt_Cormorant', 'Red_faced_Cormorant', 'Pelagic_Cormorant', 'Bronzed_Cowbird', 'Shiny_Cowbird', 'Brown_Creeper', 'American_Crow', 'Fish_Crow', 'Black_billed_Cuckoo', 'Mangrove_Cuckoo', 'Yellow_billed_Cuckoo', 'Gray_crowned_Rosy_Finch', 'Purple_Finch', 'Northern_Flicker', 'Acadian_Flycatcher', 'Great_Crested_Flycatcher', 'Least_Flycatcher', 'Olive_sided_Flycatcher', 'Scissor_tailed_Flycatcher', 'Vermilion_Flycatcher', 'Yellow_bellied_Flycatcher', 'Frigatebird', 'Northern_Fulmar', 'Gadwall', 'American_Goldfinch', 'European_Goldfinch', 'Boat_tailed_Grackle', 'Eared_Grebe', 'Horned_Grebe', 'Pied_billed_Grebe', 'Western_Grebe', 'Blue_Grosbeak', 'Evening_Grosbeak', 'Pine_Grosbeak', 'Rose_breasted_Grosbeak', 'Pigeon_Guillemot', 'California_Gull', 'Glaucous_winged_Gull', 'Heermann_Gull', 'Herring_Gull', 'Ivory_Gull', 'Ring_billed_Gull', 'Slaty_backed_Gull', 'Western_Gull', 'Anna_Hummingbird', 'Ruby_throated_Hummingbird', 'Rufous_Hummingbird', 'Green_Violetear', 'Long_tailed_Jaeger', 'Pomarine_Jaeger', 'Blue_Jay', 'Florida_Jay', 'Green_Jay', 'Dark_eyed_Junco', 'Tropical_Kingbird', 'Gray_Kingbird', 'Belted_Kingfisher', 'Green_Kingfisher', 'Pied_Kingfisher', 'Ringed_Kingfisher', 'White_breasted_Kingfisher', 'Red_legged_Kittiwake', 'Horned_Lark', 'Pacific_Loon', 'Mallard', 'Western_Meadowlark', 'Hooded_Merganser', 'Red_breasted_Merganser', 'Mockingbird', 'Nighthawk', 'Clark_Nutcracker', 'White_breasted_Nuthatch', 'Baltimore_Oriole', 'Hooded_Oriole', 'Orchard_Oriole', 'Scott_Oriole', 'Ovenbird', 'Brown_Pelican', 'White_Pelican', 'Western_Wood_Pewee', 'Sayornis', 'American_Pipit', 'Whip_poor_Will', 'Horned_Puffin', 'Common_Raven', 'White_necked_Raven', 'American_Redstart', 'Geococcyx', 'Loggerhead_Shrike', 'Great_Grey_Shrike', 'Baird_Sparrow', 'Black_throated_Sparrow', 'Brewer_Sparrow', 'Chipping_Sparrow', 'Clay_colored_Sparrow', 'House_Sparrow', 'Field_Sparrow', 'Fox_Sparrow', 'Grasshopper_Sparrow', 'Harris_Sparrow', 'Henslow_Sparrow', 'Le_Conte_Sparrow', 'Lincoln_Sparrow', 'Nelson_Sharp_tailed_Sparrow', 'Savannah_Sparrow', 'Seaside_Sparrow', 'Song_Sparrow', 'Tree_Sparrow', 'Vesper_Sparrow', 'White_crowned_Sparrow', 'White_throated_Sparrow', 'Cape_Glossy_Starling', 'Bank_Swallow', 'Barn_Swallow', 'Cliff_Swallow', 'Tree_Swallow', 'Scarlet_Tanager', 'Summer_Tanager', 'Artic_Tern', 'Black_Tern', 'Caspian_Tern', 'Common_Tern', 'Elegant_Tern', 'Forsters_Tern', 'Least_Tern', 'Green_tailed_Towhee', 'Brown_Thrasher', 'Sage_Thrasher', 'Black_capped_Vireo', 'Blue_headed_Vireo', 'Philadelphia_Vireo', 'Red_eyed_Vireo', 'Warbling_Vireo', 'White_eyed_Vireo', 'Yellow_throated_Vireo', 'Bay_breasted_Warbler', 'Black_and_white_Warbler', 'Black_throated_Blue_Warbler', 'Blue_winged_Warbler', 'Canada_Warbler', 'Cape_May_Warbler', 'Cerulean_Warbler', 'Chestnut_sided_Warbler', 'Golden_winged_Warbler', 'Hooded_Warbler', 'Kentucky_Warbler', 'Magnolia_Warbler', 'Mourning_Warbler', 'Myrtle_Warbler', 'Nashville_Warbler', 'Orange_crowned_Warbler', 'Palm_Warbler', 'Pine_Warbler', 'Prairie_Warbler', 'Prothonotary_Warbler', 'Swainson_Warbler', 'Tennessee_Warbler', 'Wilson_Warbler', 'Worm_eating_Warbler', 'Yellow_Warbler', 'Northern_Waterthrush', 'Louisiana_Waterthrush', 'Bohemian_Waxwing', 'Cedar_Waxwing', 'American_Three_toed_Woodpecker', 'Pileated_Woodpecker', 'Red_bellied_Woodpecker', 'Red_cockaded_Woodpecker', 'Red_headed_Woodpecker', 'Downy_Woodpecker', 'Bewick_Wren', 'Cactus_Wren', 'Carolina_Wren', 'House_Wren', 'Marsh_Wren', 'Rock_Wren', 'Winter_Wren', 'Common_Yellowthroat'"
    )

    Classifier.objects.create(
        name='Flood depth',
        is_active=True,
        source_url='https://github.com/jorgemspereira/Classifying-Geo-Referenced-Photos',
        type=Classifier.PYTHON_SCRIPT,
        data_type=Configuration.IMAGES,
        path=os.path.join(BASE_DIR, 'classifiers', 'flood_depth', 'flood_depth.py'),
        return_type='INT',
        return_choices="Real number"
    )


def main():
    create_fetchers()
    create_post_processors()
    create_filters()
    create_classifiers()


if __name__ == '__main__':
    main()
