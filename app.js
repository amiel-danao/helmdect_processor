const moment = require('moment');
const axios = require('axios');
const { initializeApp, cert } = require('firebase-admin/app');
const { getStorage, getDownloadURL } = require('firebase-admin/storage');

// Fetch the service account key JSON file contents
const serviceAccount = require('./helmdetect-firebase-adminsdk-utli9-4256deee14.json');

initializeApp({
  credential: cert(serviceAccount),
  databaseURL:  'https://helmdetect-default-rtdb.asia-southeast1.firebasedatabase.app',
  storageBucket: 'helmdetect.appspot.com'
});

const bucket = getStorage().bucket();
// As an admin, the app has access to read and write all data, regardless of Security Rules
const admin = require("firebase-admin");
const db = admin.database();
const ref = db.ref("/test/push");
const proccessImageEndpoint = "http://127.0.0.1:5000/process_image";
const startTime = moment();

ref.on('child_changed', async (snapshot, prevChildKey) => {
  const newPost = snapshot.val();  

  if (!newPost.hasOwnProperty('dateTime')) {
    console.log(`Skipped: ${prevChildKey}, no dateTime`);
    return;
  }

  const firebaseDateTime = moment(newPost.dateTime);
  if (firebaseDateTime.isAfter(startTime)) {
    console.log(`Processing, id: ${prevChildKey}, dateTime: ${newPost.dateTime}`);
    
    if (newPost.hasOwnProperty('image')) {

      const formData = new FormData();
      formData.append('image', newPost.image);

      axios.post(proccessImageEndpoint, formData, {
        headers: {
          'Content-Type': `multipart/form-data; boundary=${formData._boundary}`,
        },
      })
        .then((response) => {
          console.log(`response.data: ${response.data}`);
          if ('error' in response.data) {
            // Error key found in response data
            console.error('Error Response:', response.data.error);
            // Handle error here
          } else {
            // No error key found, proceed with the response data
            console.log('Response Data:', response.data);
            if(!('result' in response.data)){
              return;
            }

            console.log(`Response result is : ${response.data.result}`);
            saveToDatabase(newPost, response.data.result)
            
            // Handle success here
          }
        })
        .catch((error) => {
          // Handle error
          console.error('Error:', error);
        });

    } else {
      console.log(`Skipped: ${prevChildKey}, no image`);
    }
    

    // Example: Process the data, perform tasks, etc.
  } else {
    console.log(`Skipped: ${prevChildKey}, old data`);
  }
});


async function saveToDatabase(data, labels) {
  try {
    data.number_of_motorcyclist_detected = 1;
    data.location = 'Davao'; // TODO: Add GPS coordinates
    data.violations = 'Unknown';
    data.helmet = false;
    data.helmet_type = 'Unknown';
    data.image = await uploadBase64Image(data.image);

    if(data.image == null){
      //TODO: retry image upload
      return;
    }

    if (labels.includes('nohelmet')) {
      data.helmet = false;
      data.violations = 'No helmet';
    }
    if (labels.includes('helmet')) {
      data.helmet = true;
      data.violations = 'None';
    }
    if (labels.includes('plate')) {
      data.plate_number = 'Plate number detected'; // TODO: Add plate number detection
    } else {
      data.plate_number = 'Unknown';
    }

    const validRef = admin.database().ref('reports'); // Replace with your database reference path
    await validRef.push().set(data);
  } catch (error) {
    console.error('Error saving to database:', error);
  }
}

async function uploadBase64Image(base64String) {
  try {

    // Convert base64 string to a buffer
    const imageBuffer = Buffer.from(base64String, 'base64');

    const currentDatetime = moment().format('YYYY-MM-DD_HH-mm-ss');
    const currentDate = moment().format('YYYY-MM-DD');

    const destinationPath = `images/${currentDate}/${currentDatetime}.jpg`;
    const file = bucket.file(destinationPath); // Replace with your desired storage path

    // Upload the buffer to Firebase Storage
    await file.save(imageBuffer, {
      metadata: {
        contentType: 'image/jpeg' // Replace with your image file type
        // You can add more metadata if needed
      }
    });

    const fileRef = bucket.file(destinationPath);
    console.log('File uploaded successfully!');
    return await getDownloadURL(fileRef);
  } catch (error) {
    return null;
  }
}