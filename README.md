# Cerebrova — AI Brain Tumor Detection

Cerebrova is a web application that detects brain tumors from MRI scans using a fine-tuned YOLOv8 model. Upload an MRI image and get instant results: tumor type, confidence score, annotated scan, and a downloadable PDF report.

---

## Features

- **Tumor Detection** — identifies Glioma, Meningioma, and Pituitary tumors
- **Confidence Score** — shows model confidence for each prediction
- **Annotated Output** — returns the MRI with bounding boxes drawn
- **PDF Report** — download a structured report of the analysis
- **Cloud Storage** — MRI uploads and results stored securely in Supabase
- **Tumor Info Pages** — descriptions of each tumor type for patient education

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| AI Model | YOLOv8 (Ultralytics) |
| Storage | Supabase |
| PDF Generation | ReportLab |
| Image Processing | Pillow, OpenCV |
| Server | Gunicorn |

---

## Project Structure

```
Cerebrova/
├── app.py                  # Flask application
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
    └── best.pt             # Trained model weights
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project with a storage bucket named `mri`

### Installation

```bash
git clone https://github.com/ADiTyaRaj8969/Cerebrova.git
cd Cerebrova
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root directory:

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

### Run Locally

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Deploying to Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → **New Web Service** → connect your repo
3. Render will auto-detect `render.yaml` — no manual config needed
4. Set the following environment variables in the Render dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
5. Click **Deploy**

> The model weights (`yolov8_weights/best.pt`) are included in the repo so no extra setup is needed.

---

## API

### `POST /predict`

Upload an MRI image for analysis.

**Request:** `multipart/form-data` with field `image`

**Response:**
```json
{
  "result_path": "https://...",
  "status": "detected",
  "confidence": 92,
  "tumor_class": "Glioma"
}
```

### `GET /download_report`

Returns a PDF report. Query params: `result_path`, `status`, `confidence`, `tumor_class`

---

## Model

The YOLOv8 model (`yolov8_weights/best.pt`) was trained on a labeled brain MRI dataset with four classes:

| Class | Description |
|---|---|
| Glioma | Tumor arising from glial cells |
| Meningioma | Tumor in the meninges (brain lining) |
| Pituitary | Tumor in the pituitary gland |
| No Tumor | Healthy scan |

---

## License

This project is for educational and research purposes.
