document.addEventListener('DOMContentLoaded', function () {

    // ── Neural network background ────────────────────────────────────────────
    function createNeuralNetwork() {
        const container = document.getElementById('neuralNetwork');
        if (!container) return;
        const width = window.innerWidth;
        const height = window.innerHeight;
        const nodes = [];

        for (let i = 0; i < 25; i++) {
            const node = document.createElement('div');
            node.classList.add('node');
            const size = Math.random() * 15 + 5;
            node.style.width  = `${size}px`;
            node.style.height = `${size}px`;
            node.style.left   = `${Math.random() * width}px`;
            node.style.top    = `${Math.random() * height}px`;
            node.dataset.dx   = (Math.random() - 0.5) * 0.2;
            node.dataset.dy   = (Math.random() - 0.5) * 0.2;
            container.appendChild(node);
            nodes.push(node);
        }

        for (let i = 0; i < 40; i++) {
            const n1 = nodes[Math.floor(Math.random() * nodes.length)];
            const n2 = nodes[Math.floor(Math.random() * nodes.length)];
            if (n1 === n2) continue;
            const x1 = parseFloat(n1.style.left) + parseFloat(n1.style.width)  / 2;
            const y1 = parseFloat(n1.style.top)  + parseFloat(n1.style.height) / 2;
            const x2 = parseFloat(n2.style.left) + parseFloat(n2.style.width)  / 2;
            const y2 = parseFloat(n2.style.top)  + parseFloat(n2.style.height) / 2;
            const dx = x2 - x1, dy = y2 - y1;
            const conn = document.createElement('div');
            conn.classList.add('connection');
            conn.style.width     = `${Math.sqrt(dx * dx + dy * dy)}px`;
            conn.style.height    = `${Math.random() + 0.5}px`;
            conn.style.left      = `${x1}px`;
            conn.style.top       = `${y1}px`;
            conn.style.transform = `rotate(${Math.atan2(dy, dx) * 180 / Math.PI}deg)`;
            container.appendChild(conn);
        }

        (function animate() {
            nodes.forEach(node => {
                let x = parseFloat(node.style.left), y = parseFloat(node.style.top);
                let dx = parseFloat(node.dataset.dx),  dy = parseFloat(node.dataset.dy);
                x += dx; y += dy;
                if (x < 0 || x > width)  node.dataset.dx = -dx;
                if (y < 0 || y > height) node.dataset.dy = -dy;
                node.style.left = `${x}px`;
                node.style.top  = `${y}px`;
            });
            requestAnimationFrame(animate);
        })();
    }

    window.addEventListener('load', createNeuralNetwork);

    // ── DOM refs ─────────────────────────────────────────────────────────────
    const fileInput           = document.getElementById('fileInput');
    const previewContainer    = document.getElementById('previewContainer');
    const imagePreview        = document.getElementById('imagePreview');
    const submitBtn           = document.getElementById('submitBtn');
    const resultBox           = document.getElementById('resultBox');
    const detectionImage      = document.getElementById('detectionImage');
    const detectionResultText = document.getElementById('detectionResultText');
    const confidenceValue     = document.getElementById('confidenceValue');
    const downloadBtn         = document.getElementById('downloadReportBtn');
    const sidebar             = document.getElementById('sidebar');
    const overlay             = document.getElementById('overlay');

    // Stores the last result for PDF download
    let _lastResult = {};

    // ── Sidebar ──────────────────────────────────────────────────────────────
    function toggleSidebar() {
        sidebar && sidebar.classList.toggle('active');
        overlay && overlay.classList.toggle('active');
    }
    document.getElementById('instructionsBtn')?.addEventListener('click', toggleSidebar);
    document.getElementById('closeBtn')?.addEventListener('click', toggleSidebar);
    overlay?.addEventListener('click', toggleSidebar);

    // ── File input preview ───────────────────────────────────────────────────
    fileInput?.addEventListener('change', function () {
        const label = document.querySelector('.file-input-label');
        if (this.files.length > 0) {
            const reader = new FileReader();
            reader.onload = e => {
                if (imagePreview)     imagePreview.src = e.target.result;
                if (previewContainer) previewContainer.classList.add('active');
                if (submitBtn)        submitBtn.disabled = false;
                if (resultBox)        resultBox.classList.remove('active');
            };
            reader.readAsDataURL(this.files[0]);
            if (label) label.innerHTML = `
                <i class="fas fa-check-circle" style="color:#4CAF50"></i>
                <p>${this.files[0].name}</p>
                <span>Click to change file</span>`;
        } else {
            if (previewContainer) previewContainer.classList.remove('active');
            if (submitBtn)        submitBtn.disabled = true;
            if (label) label.innerHTML = `
                <i class="fas fa-file-medical"></i>
                <p>Click to upload MRI image</p>
                <span>Supports JPG, JPEG or PNG formats</span>`;
        }
    });

    // ── Form submit → /predict ───────────────────────────────────────────────
    document.getElementById('uploadForm')?.addEventListener('submit', function (e) {
        e.preventDefault();

        if (submitBtn) { submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...'; submitBtn.disabled = true; }
        if (detectionResultText) detectionResultText.textContent = 'Processing MRI scan… this may take a few seconds.';
        if (resultBox) { resultBox.classList.add('active'); resultBox.scrollIntoView({ behavior: 'smooth', block: 'center' }); }

        fetch('/predict', { method: 'POST', body: new FormData(this) })
            .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
            .then(data => {
                if (submitBtn) { submitBtn.innerHTML = 'Analyze Scan'; submitBtn.disabled = false; }

                if (data.error) {
                    if (detectionResultText) detectionResultText.textContent = `Error: ${data.error}`;
                    return;
                }

                // Show annotated image from base64
                if (detectionImage) {
                    detectionImage.src = `data:image/jpeg;base64,${data.result_image_b64}`;
                    detectionImage.style.display = 'block';
                }

                // Result text
                if (detectionResultText) {
                    if (data.status === 'detected') {
                        const cls = data.tumor_class !== 'None' ? data.tumor_class + ' tumour' : 'tumour';
                        detectionResultText.textContent =
                            `Our AI detected a potential ${cls} with ${data.confidence}% confidence. ` +
                            `The highlighted areas indicate regions of concern. ` +
                            `Please consult a qualified radiologist for a definitive diagnosis.`;
                    } else {
                        detectionResultText.textContent =
                            `No tumour was detected in this scan (confidence: ${data.confidence}%). ` +
                            `This result does not substitute a professional medical evaluation.`;
                    }
                }

                if (confidenceValue) confidenceValue.textContent = `${data.confidence}%`;

                // Store result for PDF download
                _lastResult = {
                    status:           data.status,
                    confidence:       data.confidence,
                    tumor_class:      data.tumor_class,
                    result_image_b64: data.result_image_b64,
                };

                if (downloadBtn) downloadBtn.style.display = 'inline-block';
            })
            .catch(err => {
                if (detectionResultText) detectionResultText.textContent = `An error occurred: ${err.message}`;
                if (submitBtn) { submitBtn.innerHTML = 'Analyze Scan'; submitBtn.disabled = false; }
            });
    });

    // ── Download report → POST /download_report ──────────────────────────────
    downloadBtn?.addEventListener('click', function (e) {
        e.preventDefault();
        if (!_lastResult.status) return;

        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/download_report';

        Object.entries(_lastResult).forEach(([k, v]) => {
            const inp = document.createElement('input');
            inp.type = 'hidden';
            inp.name = k;
            inp.value = v;
            form.appendChild(inp);
        });

        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    });

    // ── Learn more modal → /tumor_descriptions ───────────────────────────────
    const tumorModal              = document.getElementById('tumorModal');
    const tumorDescContainer      = document.getElementById('tumorDescriptionsContainer');

    document.getElementById('learnMoreBtn')?.addEventListener('click', () => {
        fetch('/tumor_descriptions')
            .then(r => r.text())
            .then(html => {
                if (tumorDescContainer) tumorDescContainer.innerHTML = html;
                if (tumorModal) tumorModal.style.display = 'block';
            })
            .catch(err => console.error('Failed to load tumor descriptions:', err));
    });

    document.getElementById('closeModal')?.addEventListener('click', () => {
        if (tumorModal) tumorModal.style.display = 'none';
    });

    window.addEventListener('click', e => {
        if (e.target === tumorModal) tumorModal.style.display = 'none';
    });
});
