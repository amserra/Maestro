import torch


def main(image_path):
    # Model
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

    # Images
    imgs = [image_path]  # batch of images

    # Inference
    results = model(imgs)
    try:
        return results.pandas().xyxy[0]['name'].values.tolist()
    except:
        return None

