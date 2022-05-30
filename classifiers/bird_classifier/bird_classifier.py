from torchvision import transforms
import torch
from PIL import Image


def main(image_path):
    transform_test = transforms.Compose([
        transforms.Resize((600, 600), Image.BILINEAR),
        transforms.CenterCrop((448, 448)),
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
    ])

    model = torch.hub.load('nicolalandro/ntsnet-cub200', 'ntsnet', pretrained=True, **{'topN': 6, 'device': 'cpu', 'num_classes': 200})
    model.eval()

    img = Image.open(image_path)
    scaled_img = transform_test(img)
    torch_images = scaled_img.unsqueeze(0)

    with torch.no_grad():
        top_n_coordinates, concat_out, raw_logits, concat_logits, part_logits, top_n_index, top_n_prob = model(torch_images)

        _, predict = torch.max(concat_logits, 1)
        pred_id = predict.item()
        bird_class = model.bird_classes[pred_id]

    splitted = bird_class.split('.')
    if len(splitted) != 2:
        return bird_class

    return splitted[1].replace('_', ' ')

