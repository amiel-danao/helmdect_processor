import firebase_admin
from firebase_admin import credentials, db
import base64
from PIL import Image
from io import BytesIO
from ultralytics import YOLO
import time


# Initialize YOLO model
model = YOLO('best.pt')

# Firebase Initialization
# Firebase Initialization
cred = credentials.Certificate("helmdetect-firebase-adminsdk-utli9-4256deee14.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://helmdetect-default-rtdb.asia-southeast1.firebasedatabase.app'  # Replace with your database URL
})

valid_labels = ['helmet', 'nohelmet', 'rider', 'plate']

# Reference to the Firebase Realtime Database
ref = db.reference('/lol/push')  # Replace with your database reference path
valid_ref = db.reference('/reports')


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




def on_new_child_added(event):
    print("New child added:")
    # Get the data of the added child
    child_data = event.data

    if hasattr(child_data, 'items') and callable(child_data.items):
        for key, data in child_data.items():
            print("Entry ID:", key)
            # print("Entry Data:", data)if hasattr(child_data, 'items') and callable(child_data.items):

            # Checking if 'dataTime' field exists and is greater than the start time of the program
            if 'dateTime' in data:
                if data['dateTime'] > start_time:
                    # Example: Processing image if 'image' field exists in the entry data
                    if 'image' in data:
                        image_base64 = data['image']
                        predicted_labels = process_image(image_base64)
                        if(contains_substring(valid_labels, predicted_labels)):
                            print("Predicted labels for Entry ID", key, ":", 'OK')
                            saveToDatabase(data, predicted_labels)
                else:
                    print(f"Skipping entry as 'dataTime' is not greater than start time: {key}, timestamp: {data['dateTime']}")
            else:
                print(f'Skipped no dateTime: {key}')

def saveToDatabase(data, labels):
    data['number_of_motorcyclist_detected'] = 1
    data['location'] = 'Davao' #TODO add gps
    data['violations'] = 'None'
    data['helmet'] = False
    data['helmet_type'] = 'Unknown'

    if(labels.find("nohelmet") != -1):
        data['helmet'] = False
        data['violations'] = 'No helmetnumber_of_motorcyclist_detected'
    if(labels.find("helmet") != -1):
        data['helmet'] = True        
        data['violations'] = 'None'
    if(labels.find("plate") != -1):
        data['plate_number'] = 'Plate number detected'#TODO: add plate number detection
    else:
        data['plate_number'] = 'Unknown'

    
    valid_ref.push().set(data)


def contains_substring(arr, text):
    return any(substring in text for substring in arr)


start_time = time.time()
print(f'start time is: {start_time}')
# Listen for new child additions
ref.listen(on_new_child_added)

# Keep the script running to continue listening for changes
while True:
    time.sleep(10)  # Keep the program running
