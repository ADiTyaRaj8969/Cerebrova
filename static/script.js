document.addEventListener('DOMContentLoaded', function() {
    // Create neural network background with smooth movement
    function createNeuralNetwork() {
        const container = document.getElementById('neuralNetwork');
        if (!container) return; // Exit if container not found
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        // Create nodes with random movement
        const nodeCount = 25;
        const nodes = [];
        
        for (let i = 0; i < nodeCount; i++) {
            const node = document.createElement('div');
            node.classList.add('node');
            
            const size = Math.random() * 15 + 5;
            const x = Math.random() * width;
            const y = Math.random() * height;
            
            node.style.width = `${size}px`;
            node.style.height = `${size}px`;
            node.style.left = `${x}px`;
            node.style.top = `${y}px`;
            
            // Set random movement direction
            node.dataset.dx = (Math.random() - 0.5) * 0.2;
            node.dataset.dy = (Math.random() - 0.5) * 0.2;
            
            container.appendChild(node);
            nodes.push(node);
        }
        
        // Create connections
        const connectionCount = 40;
        
        for (let i = 0; i < connectionCount; i++) {
            const node1 = nodes[Math.floor(Math.random() * nodes.length)];
            const node2 = nodes[Math.floor(Math.random() * nodes.length)];
            
            if (node1 === node2) continue;
            
            const x1 = parseFloat(node1.style.left) + parseFloat(node1.style.width)/2;
            const y1 = parseFloat(node1.style.top) + parseFloat(node1.style.height)/2;
            const x2 = parseFloat(node2.style.left) + parseFloat(node2.style.width)/2;
            const y2 = parseFloat(node2.style.top) + parseFloat(node2.style.height)/2;
            
            const dx = x2 - x1;
            const dy = y2 - y1;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            const connection = document.createElement('div');
            connection.classList.add('connection');
            
            connection.style.width = `${distance}px`;
            connection.style.height = `${Math.random() * 1 + 0.5}px`;
            connection.style.left = `${x1}px`;
            connection.style.top = `${y1}px`;
            
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;
            connection.style.transform = `rotate(${angle}deg)`;
            
            container.appendChild(connection);
        }
        
        // Animate the neural network smoothly
        function animateNeuralNetwork() {
            nodes.forEach(node => {
                let x = parseFloat(node.style.left);
                let y = parseFloat(node.style.top);
                const dx = parseFloat(node.dataset.dx);
                const dy = parseFloat(node.dataset.dy);
                
                // Update position
                x += dx;
                y += dy;
                
                // Bounce off edges
                if (x < 0 || x > width) node.dataset.dx = -dx;
                if (y < 0 || y > height) node.dataset.dy = -dy;
                
                node.style.left = `${x}px`;
                node.style.top = `${y}px`;
            });
            
            requestAnimationFrame(animateNeuralNetwork);
        }
        
        animateNeuralNetwork();
    }
    
    // Initialize neural network on load
    window.addEventListener('load', createNeuralNetwork);
    
    // DOM elements
    const fileInput = document.getElementById('fileInput');
    const previewContainer = document.getElementById('previewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const submitBtn = document.getElementById('submitBtn');
    const resultBox = document.getElementById('resultBox');
    const predictionResult = document.getElementById('predictionResult');
    const detectionImage = document.getElementById('detectionImage');
    const detectionResultText = document.getElementById('detectionResultText');
    const sidebar = document.getElementById('sidebar');
    const closeBtn = document.getElementById('closeBtn');
    const instructionsBtn = document.getElementById('instructionsBtn');
    const overlay = document.getElementById('overlay');
    
    // Toggle sidebar
    function toggleSidebar() {
        if (sidebar && overlay) {
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        }
    }
    
    // Event listeners
    if (instructionsBtn) instructionsBtn.addEventListener('click', toggleSidebar);
    if (closeBtn) closeBtn.addEventListener('click', toggleSidebar);
    if (overlay) overlay.addEventListener('click', toggleSidebar);
    
    // File input handling and preview
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const label = document.querySelector('.file-input-label');
            
            if (this.files.length > 0) {
                const file = this.files[0];
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    // Update preview
                    if (imagePreview) imagePreview.src = e.target.result;
                    if (previewContainer) previewContainer.classList.add('active');
                    
                    // Enable submit button
                    if (submitBtn) submitBtn.disabled = false;
                    
                    // Hide any previous results
                    if (resultBox) resultBox.classList.remove('active');
                }
                
                reader.readAsDataURL(file);
                
                // Update label
                if (label) {
                    label.innerHTML = `
                        <i class="fas fa-check-circle" style="color: #4CAF50;"></i>
                        <p>${file.name}</p>
                        <span>Click to change file</span>
                    `;
                }
            } else {
                // Reset if no file selected
                if (previewContainer) previewContainer.classList.remove('active');
                if (submitBtn) submitBtn.disabled = true;
                if (label) {
                    label.innerHTML = `
                        <i class="fas fa-file-medical"></i>
                        <p>Click to upload MRI image</p>
                        <span>Supports JPG, JPEG or PNG formats</span>
                    `;
                }
            }
        });
    }
    
    // Handle form submission with Fetch API
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default form submission

            // Show loading state
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
                submitBtn.disabled = true;
            }
            if (detectionResultText) {
                detectionResultText.textContent = "Processing MRI scan... This may take a few seconds.";
            }
            if (resultBox) {
                resultBox.classList.add('active');
                resultBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }

            const formData = new FormData(this);

            fetch('/predict', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading state
                if (submitBtn) {
                    submitBtn.innerHTML = 'Analyze Scan';
                    submitBtn.disabled = false;
                }

                if (data.error) {
                    if (detectionResultText) detectionResultText.textContent = data.error;
                    return;
                }

                // Update result display
                if (detectionImage) {
                    detectionImage.src = data.result_path + '?t=' + Date.now(); // Add cache buster
                }

                if (detectionResultText) {
                    if (data.status === 'detected') {
                        if (data.tumor_class && data.tumor_class !== 'None') {
                            detectionResultText.textContent = "Our AI has detected a potential " + data.tumor_class + " tumor with " + data.confidence + "% confidence. The highlighted areas in the image indicate regions of concern. Please consult with a medical professional for a comprehensive diagnosis and treatment plan.";
                        } else {
                            detectionResultText.textContent = "Our AI has detected a potential tumor with " + data.confidence + "% confidence. The highlighted areas in the image indicate regions of concern. Please consult with a medical professional for a comprehensive diagnosis and treatment plan.";
                        }
                    } else {
                        detectionResultText.textContent = "No tumor detected.";
                    }
                }

                const confidenceValueElement = document.getElementById('confidenceValue');
                if (confidenceValueElement) {
                    confidenceValueElement.textContent = data.confidence;
                }

                // Update download link
                const downloadBtn = document.getElementById('downloadReportBtn');
                if (downloadBtn) {
                    const reportUrl = new URL(window.location.origin + '/download_report');
                    reportUrl.searchParams.set('result_path', data.result_path);
                    reportUrl.searchParams.set('status', data.status);
                    reportUrl.searchParams.set('confidence', data.confidence);
                    reportUrl.searchParams.set('tumor_class', data.tumor_class);
                    reportUrl.searchParams.set('extracted_text', data.extracted_text);
                    downloadBtn.href = reportUrl.toString();
                    downloadBtn.style.display = 'inline-block';
                }

                if(detectionImage) {
                    detectionImage.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                if (detectionResultText) detectionResultText.textContent = 'An error occurred during analysis.';
                // Hide loading state
                if (submitBtn) {
                    submitBtn.innerHTML = 'Analyze Scan';
                    submitBtn.disabled = false;
                }
            });
        });
    }
    
    // Remove the page load result check as it's now handled by fetch

    // Handle "Learn More" modal
    const learnMoreBtn = document.getElementById('learnMoreBtn');
    const tumorModal = document.getElementById('tumorModal');
    const closeModal = document.getElementById('closeModal');
    const tumorDescriptionsContainer = document.getElementById('tumorDescriptionsContainer');

    if (learnMoreBtn) {
        learnMoreBtn.addEventListener('click', () => {
            fetch('/tumor_descriptions')
                .then(response => response.text())
                .then(html => {
                    if (tumorDescriptionsContainer) {
                        tumorDescriptionsContainer.innerHTML = html;
                    }
                    if (tumorModal) {
                        tumorModal.style.display = 'block';
                    }
                })
                .catch(error => console.error('Error fetching tumor descriptions:', error));
        });
    }

    if (closeModal) {
        closeModal.addEventListener('click', () => {
            if (tumorModal) {
                tumorModal.style.display = 'none';
            }
        });
    }

    window.addEventListener('click', (event) => {
        if (event.target == tumorModal) {
            tumorModal.style.display = 'none';
        }
    });
});
