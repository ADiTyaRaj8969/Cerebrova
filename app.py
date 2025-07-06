from flask import Flask, render_template, request, make_response, jsonify
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from ultralytics import YOLO
import os
import uuid
import time
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Function to load the model from Supabase
def load_model_from_supabase():
    try:
        logging.info("Attempting to download model from Supabase...")
        model_bucket = "model"
        model_file_name = "best.pt"
        
        # Download the model file from Supabase storage
        response = supabase.storage.from_(model_bucket).download(model_file_name)
        
        # Create a temporary file to save the model
        temp_model_path = f"/tmp/{model_file_name}"
        with open(temp_model_path, "wb") as f:
            f.write(response)
        
        logging.info(f"Model downloaded and saved to {temp_model_path}")
        
        # Load the model from the temporary file
        model = YOLO(temp_model_path)
        logging.info("YOLO model loaded successfully from Supabase.")
        return model
    except Exception as e:
        logging.error(f"An error occurred while loading the model from Supabase: {e}", exc_info=True)
        return None

# Load the model
model = load_model_from_supabase()

if model is None:
    logging.critical("Failed to load model from Supabase. Application cannot start.")
    # Depending on the desired behavior, you might want to exit or handle this differently
    # For a web app, you might want to return a 503 Service Unavailable on all requests
    # or have a middleware that checks if the model is loaded.
    # For now, we'll let it proceed, and it will likely fail on the first request that needs the model.

@app.route('/')
def index():
    logging.debug("Serving index page.")
    return render_template('index.html',
                           result_path=None,
                           status=None,
                           confidence=None,
                           tumor_class=None)

@app.route('/tumor_descriptions')
def tumor_descriptions():
    logging.debug("Serving tumor descriptions.")
    return render_template('tumor_descriptions.html')

@app.route('/download_report')
def download_report():
    logging.debug("Generating PDF report.")
    # Get the values from query parameters
    result_path = request.args.get('result_path')
    tumor_status = request.args.get('status')
    confidence = request.args.get('confidence', 'N/A').replace('percent', '%')
    tumor_class = request.args.get('tumor_class', 'Unknown')

    # Create PDF buffer
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    p.drawString(100, 750, "Brain Tumor Analysis Report")
    p.drawString(100, 730, "------------------------------------")

    p.drawString(100, 710, f"Tumor Status: {tumor_status}")
    p.drawString(100, 690, f"Confidence: {confidence}")
    p.drawString(100, 670, f"Tumor Class: {tumor_class}")
    # p.drawString(100, 650, f"Extracted Text: {extracted_text[:200]}...")  # Limit length

    # Add the images to the PDF
    try:
        # Calculate image positions and sizes
        image_width = 200
        image_height = 200
        x_position = 100
        y_position = 400

        if result_path:
            # Draw the result image
            p.drawString(x_position + image_width + 50, y_position + image_height + 20, "Detection Result:")
            p.drawImage(result_path, x_position + image_width + 50, y_position, width=image_width, height=image_height)

    except Exception as e:
        p.drawString(100, 300, f"Error adding images: {e}")
        logging.error(f"Error adding images to PDF: {e}")

    p.showPage()
    p.save()
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=brain_tumor_report.pdf'

    return response

@app.route('/predict', methods=['POST'])
def predict():
    logging.debug("Prediction request received.")
    if 'image' not in request.files:
        logging.error("No file part in request.")
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        logging.error("Empty filename in request.")
        return jsonify({'error': 'Empty filename'}), 400

    try:
        logging.debug(f"Processing file: {file.filename}")
        # Generate a unique filename
        unique_id = uuid.uuid4().hex
        timestamp = int(time.time())
        result_filename = f'result_{timestamp}_{unique_id}.jpg'
        
        # Read file into memory
        file_bytes = file.read()
        img = Image.open(BytesIO(file_bytes))

        # Upload to Supabase
        bucket_name = "mri"
        logging.debug(f"Uploading original image to Supabase bucket: {bucket_name}")
        supabase.storage.from_(bucket_name).upload(result_filename, file_bytes, {'content-type': 'image/jpeg'})
        
        # Run the model on the image
        logging.debug("Running YOLO model on the image.")
        results = model(img)
        
        # Save the results to a buffer
        res_plotted = results[0].plot()
        im_pil = Image.fromarray(res_plotted)
        buffer = BytesIO()
        im_pil.save(buffer, format="JPEG")
        buffer.seek(0)

        # Upload the result image to Supabase
        processed_result_filename = f"processed/{result_filename}"
        logging.debug(f"Uploading processed image to Supabase: {processed_result_filename}")
        supabase.storage.from_(bucket_name).upload(processed_result_filename, buffer.read(), {'content-type': 'image/jpeg'})
        
        # Get the public URL for the processed image
        processed_result_path = supabase.storage.from_(bucket_name).get_public_url(processed_result_filename)
        logging.debug(f"Processed image URL: {processed_result_path}")

        tumor_detected = False
        detected_class = 'None'
        confidence_score = 0

        if results[0].boxes and len(results[0].boxes) > 0:
            logging.debug("Tumor detection boxes found.")
            max_conf = 0
            for box in results[0].boxes:
                class_name = results[0].names[int(box.cls.item())]
                conf = box.conf.item()
                if conf > max_conf:
                    max_conf = conf
                if class_name in ['Glioma', 'Meningioma', 'Pituitary']:
                    tumor_detected = True
                    detected_class = class_name
                    confidence_score = int(conf * 100)
                    break
            if not tumor_detected:
                confidence_score = int(max_conf * 100)

        response_data = {
            'result_path': processed_result_path,
            'status': 'detected' if tumor_detected else 'not_detected',
            'confidence': confidence_score,
            'tumor_class': detected_class
        }
        logging.debug(f"Prediction successful. Returning JSON response: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"An error occurred during prediction: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
