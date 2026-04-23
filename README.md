# Cerebrova — AI Brain Tumour Detection

Cerebrova is a web application that detects brain tumours from MRI scans using a fine-tuned YOLOv8n model. Upload an MRI image and get instant results — tumour type, confidence score, annotated scan, and a downloadable PDF report. No cloud storage, no sign-up required.

> **Live demo:** https://cerebrova-lk7q.onrender.com

---

## Features

- **Tumour Detection** — identifies Glioma, Meningioma, and Pituitary tumours
- **Confidence Score** — model confidence displayed for every prediction
- **Annotated MRI** — result image returned with bounding boxes overlaid
- **PDF Report** — professionally formatted report with embedded scan and findings
- **Tumour Info** — in-app descriptions of each tumour type
- **Privacy first** — images are processed in memory and never stored anywhere

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| AI Model | YOLOv8n (Ultralytics) |
| PDF Generation | ReportLab |
| Image Processing | Pillow, OpenCV |
| Server | Gunicorn |
| Hosting | Render |

---

## Project Structure

```
Cerebrova/
├── app.py                  # Flask application & routes
├── requirements.txt
├── gunicorn.conf.py        # Gunicorn server config
├── render.yaml             # Render deployment config
├── static/
│   ├── style.css
│   ├── script.js
│   ├── favicon.ico
│   └── icons8-brain-*.png
├── templates/
│   ├── index.html
│   └── tumor_descriptions.html
└── yolov8_weights/
    └── best.pt             # Trained YOLOv8n weights
```

---

## Run Locally

```bash
git clone https://github.com/ADiTyaRaj8969/Cerebrova.git
cd Cerebrova
pip install -r requirements.txt
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

No environment variables or API keys needed.

---

## Deploy to Render

1. Go to [render.com](https://render.com) → **New + → Web Service**
2. Connect your GitHub account and select **ADiTyaRaj8969/Cerebrova**
3. Render auto-detects `render.yaml` — no manual configuration needed
4. Click **Deploy Web Service**

No environment variables to set. The model weights are included in the repo.

> Free tier note: the instance spins down after inactivity. The first request after sleep may take ~50 seconds to respond.

---

## API

### `POST /predict`

Analyse an uploaded MRI image.

**Request:** `multipart/form-data` with field `image` (JPG or PNG)

**Response:**
```json
{
  "status": "detected",
  "confidence": 91,
  "tumor_class": "Glioma",
  "result_image_b64": "<base64-encoded JPEG>"
}
```

### `POST /download_report`

Generate and download a PDF report.

**Request:** `application/x-www-form-urlencoded`

| Field | Description |
|---|---|
| `status` | `detected` or `not_detected` |
| `confidence` | confidence score (integer) |
| `tumor_class` | tumour type string |
| `result_image_b64` | base64-encoded result image |

---

## Model

The YOLOv8n model was trained on a labelled brain MRI dataset with four classes:

| Class | Description |
|---|---|
| Glioma | Tumour arising from glial cells |
| Meningioma | Tumour in the meninges (brain lining) |
| Pituitary | Tumour in the pituitary gland |
| No Tumour | Healthy scan |

---

## Author

**Aditya Raj**

---

## License

This project is for educational and research purposes only. Not intended for clinical use.
