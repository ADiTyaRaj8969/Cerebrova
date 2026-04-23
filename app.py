import base64
import datetime
import logging
import os
from io import BytesIO

from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, render_template, request
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from ultralytics import YOLO

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, static_folder='static', template_folder='templates')

base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'yolov8_weights', 'best.pt')
if not os.path.exists(model_path):
    raise RuntimeError(f'Model weights not found at {model_path}')
model = YOLO(model_path)
logging.info('YOLO model loaded.')

TUMOR_CLASSES = {'Glioma', 'Meningioma', 'Pituitary'}

BRAND_RED   = colors.HexColor('#9e1c1c')
LIGHT_RED   = colors.HexColor('#f5eaea')
DARK_GREY   = colors.HexColor('#333333')
MID_GREY    = colors.HexColor('#666666')
LIGHT_GREY  = colors.HexColor('#f0f0f0')
GREEN       = colors.HexColor('#2e7d32')
RED_ALERT   = colors.HexColor('#c62828')


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
        file_bytes = file.read()
        img = Image.open(BytesIO(file_bytes)).convert('RGB')

        results = model(img)

        # YOLO returns BGR numpy array — flip to RGB for PIL
        res_bgr = results[0].plot()
        result_img = Image.fromarray(res_bgr[:, :, ::-1])

        buf = BytesIO()
        result_img.save(buf, format='JPEG', quality=85)
        result_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

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
                if class_name in TUMOR_CLASSES and not tumor_detected:
                    tumor_detected = True
                    detected_class = class_name
                    confidence_score = int(conf * 100)
            if not tumor_detected:
                confidence_score = int(max_conf * 100)

        return jsonify({
            'result_image_b64': result_b64,
            'status': 'detected' if tumor_detected else 'not_detected',
            'confidence': confidence_score,
            'tumor_class': detected_class,
        })

    except Exception as e:
        logging.error(f'Prediction error: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/download_report', methods=['POST'])
def download_report():
    status      = request.form.get('status', 'unknown')
    confidence  = request.form.get('confidence', 'N/A')
    tumor_class = request.form.get('tumor_class', 'Unknown')
    image_b64   = request.form.get('result_image_b64', '')

    buf = BytesIO()
    p = canvas.Canvas(buf, pagesize=letter)
    W, H = letter

    # ── Header bar ──────────────────────────────────────────────────────────
    p.setFillColor(BRAND_RED)
    p.rect(0, H - 80, W, 80, fill=True, stroke=False)

    p.setFillColor(colors.white)
    p.setFont('Helvetica-Bold', 22)
    p.drawString(40, H - 45, 'Cerebrova')
    p.setFont('Helvetica', 11)
    p.drawString(40, H - 65, 'AI-Powered Brain Tumour Detection')

    report_id = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    p.setFont('Helvetica', 9)
    p.drawRightString(W - 40, H - 45, f'Report ID: {report_id}')
    p.drawRightString(W - 40, H - 60, datetime.datetime.now().strftime('%d %B %Y  %H:%M'))

    # ── Section: Detection Summary ───────────────────────────────────────────
    y = H - 115
    p.setFillColor(DARK_GREY)
    p.setFont('Helvetica-Bold', 13)
    p.drawString(40, y, 'Detection Summary')
    p.setStrokeColor(BRAND_RED)
    p.setLineWidth(1.5)
    p.line(40, y - 6, W - 40, y - 6)

    # Status badge
    y -= 30
    detected = (status == 'detected')
    badge_color = RED_ALERT if detected else GREEN
    badge_label = 'TUMOUR DETECTED' if detected else 'NO TUMOUR DETECTED'

    p.setFillColor(badge_color)
    p.roundRect(40, y - 6, 200, 24, 5, fill=True, stroke=False)
    p.setFillColor(colors.white)
    p.setFont('Helvetica-Bold', 11)
    p.drawString(50, y + 4, badge_label)

    # Result details table
    y -= 45
    rows = [
        ('Tumour Status', 'Detected' if detected else 'Not Detected'),
        ('Tumour Type',   tumor_class if detected else '—'),
        ('Confidence',    f'{confidence}%'),
    ]

    p.setFont('Helvetica', 10)
    row_h = 26
    for i, (label, value) in enumerate(rows):
        row_y = y - i * row_h
        # Alternating row background
        if i % 2 == 0:
            p.setFillColor(LIGHT_GREY)
            p.rect(40, row_y - 8, W - 80, row_h, fill=True, stroke=False)
        p.setFillColor(MID_GREY)
        p.setFont('Helvetica-Bold', 10)
        p.drawString(52, row_y + 4, label)
        p.setFillColor(DARK_GREY)
        p.setFont('Helvetica', 10)
        p.drawString(240, row_y + 4, value)

    # ── Section: Annotated MRI ───────────────────────────────────────────────
    y -= (len(rows) * row_h) + 30
    p.setFillColor(DARK_GREY)
    p.setFont('Helvetica-Bold', 13)
    p.drawString(40, y, 'Annotated MRI Scan')
    p.setStrokeColor(BRAND_RED)
    p.setLineWidth(1.5)
    p.line(40, y - 6, W - 40, y - 6)

    y -= 20
    if image_b64:
        try:
            img_bytes = base64.b64decode(image_b64)
            img_buf = BytesIO(img_bytes)
            img_w, img_h = 3.5 * inch, 3.0 * inch
            img_x = (W - img_w) / 2
            p.drawImage(ImageReader(img_buf), img_x, y - img_h, width=img_w, height=img_h,
                        preserveAspectRatio=True, mask='auto')
            # Border around image
            p.setStrokeColor(LIGHT_GREY)
            p.setLineWidth(1)
            p.rect(img_x, y - img_h, img_w, img_h, fill=False, stroke=True)
            y -= img_h + 15
        except Exception as e:
            logging.warning(f'Could not embed image in PDF: {e}')
            p.setFont('Helvetica-Oblique', 10)
            p.setFillColor(MID_GREY)
            p.drawString(40, y - 20, '(Result image unavailable)')
            y -= 40
    else:
        p.setFont('Helvetica-Oblique', 10)
        p.setFillColor(MID_GREY)
        p.drawString(40, y - 20, '(No image provided)')
        y -= 40

    # ── Medical Disclaimer ───────────────────────────────────────────────────
    y -= 20
    p.setFillColor(LIGHT_RED)
    p.rect(40, y - 50, W - 80, 60, fill=True, stroke=False)
    p.setStrokeColor(BRAND_RED)
    p.setLineWidth(0.8)
    p.rect(40, y - 50, W - 80, 60, fill=False, stroke=True)

    p.setFillColor(BRAND_RED)
    p.setFont('Helvetica-Bold', 9)
    p.drawString(52, y + 2, 'Medical Disclaimer')
    p.setFillColor(DARK_GREY)
    p.setFont('Helvetica', 8)
    disclaimer = (
        'This report is generated by an AI system and is intended for research and educational purposes only. '
        'It does not constitute a medical diagnosis. Always consult a qualified radiologist or physician '
        'for clinical interpretation and treatment decisions.'
    )
    # Word-wrap disclaimer
    words = disclaimer.split()
    line, lines = '', []
    for w in words:
        test = f'{line} {w}'.strip()
        if p.stringWidth(test, 'Helvetica', 8) < W - 120:
            line = test
        else:
            lines.append(line)
            line = w
    lines.append(line)
    for j, ln in enumerate(lines):
        p.drawString(52, y - 12 - j * 12, ln)

    # ── Footer ───────────────────────────────────────────────────────────────
    p.setFillColor(BRAND_RED)
    p.rect(0, 0, W, 28, fill=True, stroke=False)
    p.setFillColor(colors.white)
    p.setFont('Helvetica', 8)
    p.drawString(40, 10, 'Cerebrova Diagnostics  |  AI Brain Tumour Detection  |  For professional use only')
    p.drawRightString(W - 40, 10, 'Page 1 of 1')

    p.showPage()
    p.save()
    buf.seek(0)

    response = make_response(buf.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=cerebrova_report_{report_id}.pdf'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
