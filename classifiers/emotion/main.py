import cv2
import torchvision.transforms as transforms
from PIL import Image
import os
from classifiers.emotion.model import *


def load_trained_model(model_path):
    model = Face_Emotion_CNN()
    model.load_state_dict(torch.load(model_path, map_location=lambda storage, loc: storage), strict=False)
    return model


def main(image_path):
    model = load_trained_model(os.path.join('classifiers', 'emotion', 'FER_trained_model.pt'))

    emotion_dict = {0: 'neutral', 1: 'happiness', 2: 'surprise', 3: 'sadness',
                    4: 'anger', 5: 'disguest', 6: 'fear'}

    val_transform = transforms.Compose([transforms.ToTensor()])

    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    face_cascade = cv2.CascadeClassifier(os.path.join('classifiers', 'emotion', 'haarcascade_frontalface_default.xml'))
    faces = face_cascade.detectMultiScale(img)
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        resize_frame = cv2.resize(gray[y:y + h, x:x + w], (48, 48))
        X = resize_frame / 256
        X = Image.fromarray((resize_frame))
        X = val_transform(X).unsqueeze(0)
        with torch.no_grad():
            model.eval()
            log_ps = model.cpu()(X)
            ps = torch.exp(log_ps)
            top_p, top_class = ps.topk(1, dim=1)
            pred = emotion_dict[int(top_class.numpy())]
        cv2.putText(img, pred, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 1)
        break

    return pred


if __name__ == "__main__":
    main('/Users/amserra/Documents/GitHub/Maestro/contexts_data/alexandre.serra@tecnico.ulisboa.pt/search-for-donald-trump-images/data/full/baa3b70da76009b49e35b9e89752cd8913fd31c7.jpg')
