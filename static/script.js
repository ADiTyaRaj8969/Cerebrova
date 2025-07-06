// Create neural network background with smooth movement
        function createNeuralNetwork() {
            const container = document.getElementById('neuralNetwork');
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
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        }
        
        // Event listeners
        instructionsBtn.addEventListener('click', toggleSidebar);
        closeBtn.addEventListener('click', toggleSidebar);
        overlay.addEventListener('click', toggleSidebar);
        
        // File input handling and preview
        fileInput.addEventListener('change', function(e) {
            const label = document.querySelector('.file-input-label');
            
            if (this.files.length > 0) {
                const file = this.files[0];
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    // Update preview
                    imagePreview.src = e.target.result;
                    previewContainer.classList.add('active');
                    
                    // Enable submit button
                    submitBtn.disabled = false;
                    
                    // Hide any previous results
                    resultBox.classList.remove('active');
                }
                
                reader.readAsDataURL(file);
                
                // Update label
                label.innerHTML = `
                    <i class="fas fa-check-circle" style="color: #4CAF50;"></i>
                    <p>${file.name}</p>
                    <span>Click to change file</span>
                `;
            } else {
                // Reset if no file selected
                previewContainer.classList.remove('active');
                submitBtn.disabled = true;
                label.innerHTML = `
                    <i class="fas fa-file-medical"></i>
                    <p>Click to upload MRI image</p>
                    <span>Supports JPG, JPEG or PNG formats</span>
                `;
            }
        });
        
        // Handle form submission
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            // Show loading state
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
            submitBtn.disabled = true;
            detectionResultText.textContent = "Processing MRI scan... This may take a few seconds.";
        });
        
        // Check if we have a result to show on page load
        window.addEventListener('load', function() {
            const urlParams = new URLSearchParams(window.location.search);
            const resultPath = urlParams.get('result');
            const tumorStatus = urlParams.get('status');
            const confidence = urlParams.get('confidence');
            // const extractedText = urlParams.get('extracted_text');
            const confidenceValueElement = document.getElementById('confidenceValue');
            // const extractedTextElement = document.getElementById('extractedText');
            const detectionResultText = document.getElementById('detectionResultText');
            const tumorClass = urlParams.get('tumor_class');

            if (resultPath) {
                // Show the result box
                resultBox.classList.add('active');

                // Set the detection image - add cache busting parameter
                detectionImage.src = resultPath + '?t=' + Date.now();

                // Set the extracted text
                // extractedTextElement.textContent = extractedText;

                // Set the detection result text
                if (tumorStatus === 'detected') {
                    if (tumorClass !== 'None') {
                        detectionResultText.textContent = "Our AI has detected a potential " + tumorClass + " tumor with " + confidence + "% confidence. The highlighted areas in the image indicate regions of concern. Please consult with a medical professional for a comprehensive diagnosis and treatment plan.";
                    } else {
                        detectionResultText.textContent = "Our AI has detected a potential tumor with " + confidence + "% confidence. The highlighted areas in the image indicate regions of concern. Please consult with a medical professional for a comprehensive diagnosis and treatment plan.";
                    }
                } else {
                    detectionResultText.textContent = "No tumor detected.";
                }
                
                // Scroll to results
                resultBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }

            // Set confidence value
            if (confidenceValueElement) {
                confidenceValueElement.textContent = confidence;
            }
        });
