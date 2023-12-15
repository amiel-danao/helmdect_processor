from ultralytics import YOLO
from PIL import Image
from io import BytesIO
import base64

# Load a pretrained YOLOv8n model
model = YOLO('best.pt')

image = "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"

valid_labels = ['helmet', 'nohelmet', 'rider', 'plate']

def process_image(base64_string):
    # Convert base64 string to image
    decoded = base64.b64decode(base64_string)
    img = Image.open(BytesIO(decoded))

    # Run inference on the image using YOLO model
    # results = model.predict(img, size=320, conf=0.1)
    results = model.predict(img, save=True, imgsz=320, conf=0.1)

    classes = []
    for result in results:
        for box in result.boxes:
            class_id = int(box.data[0][-1])
            classes.append(model.names[class_id])

    return ' '.join(classes)


def contains_substring(arr, text):
    return any(substring in text for substring in arr)

predicted_labels = process_image(image)
print(predicted_labels)


if(contains_substring(valid_labels, predicted_labels)):
    print("OK ka kokey")


# Run inference on 'bus.jpg' with arguments
# result = model.predict('sample2.jpg', save=True, imgsz=320, conf=0.1)
# print(result)
# boxes = result[0].boxes
# print(boxes)