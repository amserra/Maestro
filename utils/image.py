from io import BytesIO
from PIL import Image


def save_thumb(path, thumb_size=(270, 270)):
    img = Image.open(path)

    thumb_image = convert_image(img, thumb_size)
    thumb_image.save("thumb.jpg")


def convert_image(image, size):
    if image.format == 'PNG' and image.mode == 'RGBA':
        background = Image.new('RGBA', image.size, (255, 255, 255))
        background.paste(image, image)
        image = background.convert('RGB')
    elif image.mode == 'P':
        image = image.convert("RGBA")
        background = Image.new('RGBA', image.size, (255, 255, 255))
        background.paste(image, image)
        image = background.convert('RGB')
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    if size:
        image = image.copy()
        image.thumbnail(size, Image.ANTIALIAS)

    buf = BytesIO()
    image.save(buf, 'JPEG')
    return image
