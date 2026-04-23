from flask import Flask, render_template, request, make_response, jsonify
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from ultralytics import YOLO
import os
import uuid
import time
import requests as http
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, static_folder='static', template_folder='templates')

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set as environment variables.")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# YOLO model — loaded once at startup (preload_app = True in gunicorn)
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, "yolov8_weights", "best.pt")
if not os.path.exists(model_path):
    raise RuntimeError(f"Model weights not found at {model_path}")
model = YOLO(model_path)
logging.info("YOLO model loaded.")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/tumor_descriptions')
def tumor_descriptions():
    return render_template('tumor_descriptions.html')


@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    try:
        unique_id = uuid.uuid4().hex
        timestamp = int(time.time())
        result_filename = f'result_{timestamp}_{unique_id}.jpg'

        file_bytes = file.read()
        img = Image.open(BytesIO(file_bytes)).convert('RGB')

        # Upload original to Supabase
        supabase.storage.from_("mri").upload(
            result_filename, file_bytes, {'content-type': 'image/jpeg'}
        )

        # Run detection
        results = model(img)

        # Plot result — YOLO returns BGR, convert to RGB for PIL
        res_bgr = results[0].plot()
        im_pil = Image.fromarray(res_bgr[:, :, ::-1])

        buf = BytesIO()
        im_pil.save(buf, format="JPEG")
        buf.seek(0)

        # Upload annotated result to Supabase
        processed_filename = f"processed/{result_filename}"
        supabase.storage.from_("mri").upload(
            processed_filename, buf.read(), {'content-type': 'image/jpeg'}
        )
        processed_url = supabase.storage.from_("mri").get_public_url(processed_filename)

        # Parse detections
        tumor_detected = False
        detected_class = 'None'
        confidence_score = 0
        tumor_classes = {'Glioma', 'Meningioma', 'Pituitary'}

        if results[0].boxes and len(results[0].boxes) > 0:
            max_conf = 0
            for box in results[0].boxes:
                class_name = results[0].names[int(box.cls.item())]
                conf = box.conf.item()
                if conf > max_conf:
                    max_conf = conf
                if class_name in tumor_classes and not tumor_detected:
                    tumor_detected = True
                    detected_class = class_name
                    confidence_score = int(conf * 100)
            if not tumor_detected:
                confidence_score = int(max_conf * 100)

        return jsonify({
            'result_path': processed_url,
            'status': 'detected' if tumor_detected else 'not_detected',
            'confidence': confidence_score,
            'tumor_class': detected_class,
        })

    except Exception as e:
        logging.error(f"Prediction error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/download_report')
def download_report():
    result_path = request.args.get('result_path')
    tumor_status = request.args.get('status')
    confidence = request.args.get('confidence', 'N/A').replace('percent', '%')
    tumor_class = request.args.get('tumor_class', 'Unknown')

    buf = BytesIO()
    p = canvas.Canvas(buf, pagesize=letter)

    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Brain Tumor Analysis Report")
    p.setFont("Helvetica", 12)
    p.drawString(100, 720, f"Tumor Status : {tumor_status}")
    p.drawString(100, 700, f"Confidence   : {confidence}%")
    p.drawString(100, 680, f"Tumor Class  : {tumor_class}")

    if result_path:
        try:
            resp = http.get(result_path, timeout=15)
            resp.raise_for_status()
            img_buf = BytesIO(resp.content)
            p.drawString(100, 640, "Detection Result:")
            p.drawImage(ImageReader(img_buf), 100, 420, width=250, height=200)
        except Exception as e:
            logging.warning(f"Could not embed image in PDF: {e}")
            p.drawString(100, 620, "(Result image unavailable)")

    p.showPage()
    p.save()
    buf.seek(0)

    response = make_response(buf.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=brain_tumor_report.pdf'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
