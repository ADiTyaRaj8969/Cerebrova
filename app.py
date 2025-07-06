from flask import Flask, render_template, request, redirect, url_for, make_response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from ultralytics import YOLO
import os
import uuid
import time
import pytesseract
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client, Client
import requests
load_dotenv()

app = Flask(__name__)

# Supabase setup
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Construct absolute path for model weights and load YOLO model
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yolov8_weights/best.pt")
model = YOLO(model_path)

@app.route('/')
def index():
    result_path = request.args.get('result_path')
    tumor_status = request.args.get('status')
    confidence = request.args.get('confidence')
    tumor_class = request.args.get('tumor_class')
    extracted_text = request.args.get('extracted_text')
    
    return render_template('index.html',
                           result_path=result_path,
                           status=tumor_status,
                           confidence=confidence,
                           tumor_class=tumor_class,
                           extracted_text=extracted_text)

@app.route('/tumor_descriptions')
def tumor_descriptions():
    return render_template('tumor_descriptions.html')

@app.route('/download_report')
def download_report():
    # Get the values from query parameters
    result_path = request.args.get('result_path')
    tumor_status = request.args.get('status')
    confidence = request.args.get('confidence', 'N/A').replace('percent', '%')
    tumor_class = request.args.get('tumor_class', 'Unknown')
    extracted_text = request.args.get('extracted_text', 'No text extracted')

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

    p.showPage()
    p.save()
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=brain_tumor_report.pdf'

    return response

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return "❌ No file uploaded", 400

    file = request.files['image']
    if file.filename == '':
        return "⚠️ Empty filename", 400

    # Generate a unique filename
    unique_id = uuid.uuid4().hex
    timestamp = int(time.time())
    result_filename = f'result_{timestamp}_{unique_id}.jpg'
    
    # Read file into memory
    file_bytes = file.read()
    img = Image.open(BytesIO(file_bytes))

    # Upload to Supabase
    bucket_name = "mri"
    supabase.storage.from_(bucket_name).upload(result_filename, file_bytes)
    
    # Get public URL
    result_path = supabase.storage.from_(bucket_name).get_public_url(result_filename)

    # Run the model on the image
    results = model(img)
    
    # Save the results to a buffer
    res_plotted = results[0].plot()
    im_pil = Image.fromarray(res_plotted)
    buffer = BytesIO()
    im_pil.save(buffer, format="JPEG")
    buffer.seek(0)

    # Upload the result image to Supabase
    supabase.storage.from_(bucket_name).upload(f"processed/{result_filename}", buffer.read())
    
    # Get the public URL for the processed image
    processed_result_path = supabase.storage.from_(bucket_name).get_public_url(f"processed/{result_filename}")

    tumor_detected = False
    detected_class = 'None'
    confidence_score = 0

    if results[0].boxes and len(results[0].boxes) > 0:
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

    try:
        img = Image.open(BytesIO(file_bytes))
        extracted_text = pytesseract.image_to_string(img)
    except Exception as e:
        extracted_text = f"Error extracting text: {e}"

    # Redirect to the index page with the filename and results
    return redirect(url_for('index',
                            result_path=processed_result_path,
                            status='detected' if tumor_detected else 'not_detected',
                            confidence=confidence_score,
                            tumor_class=detected_class,
                            extracted_text=extracted_text))
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
