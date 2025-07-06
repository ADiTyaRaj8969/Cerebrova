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

app = Flask(__name__)

# Define the persistent storage path for Render
UPLOAD_FOLDER = '/var/data/uploads'

# Construct absolute path for model weights and load YOLO model
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yolov8_weights/best.pt")
model = YOLO(model_path)

@app.route('/')
def index():
    result_filename = request.args.get('result_filename')
    result_path = None
    if result_filename:
        # Construct the public URL for the image, which is served from the symlinked 'static/uploads' directory
        result_path = url_for('static', filename=f'uploads/{result_filename}')

    tumor_status = request.args.get('status')
    confidence = request.args.get('confidence')
    tumor_class = request.args.get('tumor_class')
    extracted_text = request.args.get('extracted_text')
    
    return render_template('index.html',
                           result_path=result_path,
                           status=tumor_status,
                           confidence=confidence,
                           tumor_class=tumor_class,
                           extracted_text=extracted_text,
                           result_filename=result_filename) # Pass filename for the download link

@app.route('/tumor_descriptions')
def tumor_descriptions():
    return render_template('tumor_descriptions.html')

@app.route('/download_report')
def download_report():
    # Get the values from query parameters
    result_filename = request.args.get('result_filename')
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

        if result_filename:
            # Construct the full filesystem path to the image on the persistent disk
            image_path = os.path.join(UPLOAD_FOLDER, result_filename)
            # Draw the result image
            p.drawString(x_position + image_width + 50, y_position + image_height + 20, "Detection Result:")
            p.drawImage(image_path, x_position + image_width + 50, y_position, width=image_width, height=image_height)

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
    
    # Define the full path on the persistent disk
    save_path = os.path.join(UPLOAD_FOLDER, result_filename)
    
    # Save the uploaded file to the persistent disk
    file.save(save_path)

    # Run the model and save the result over the original image
    results = model(save_path)
    results[0].save(filename=save_path)

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
        img = Image.open(save_path)
        extracted_text = pytesseract.image_to_string(img)
    except Exception as e:
        extracted_text = f"Error extracting text: {e}"

    # Redirect to the index page with the filename and results
    return redirect(url_for('index',
                            result_filename=result_filename,
                            status='detected' if tumor_detected else 'not_detected',
                            confidence=confidence_score,
                            tumor_class=detected_class,
                            extracted_text=extracted_text))
    
if __name__ == '__main__':
    # Create the upload folder if it doesn't exist (for local testing)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
