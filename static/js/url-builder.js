// URL Builder page specific JavaScript

let currentEndpoint = 'random';

// Endpoint switching
document.querySelectorAll('.endpoint-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.endpoint-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentEndpoint = tab.dataset.endpoint;
        
        document.querySelectorAll('.endpoint-config').forEach(config => {
            config.style.display = config.dataset.endpoint === currentEndpoint ? 'block' : 'none';
        });
        
        updateURL();
    });
});

// Range value updates
['quality', 'blur', 'noise', 'pixelate', 'brightness', 'contrast', 'saturation', 'posterize', 'solarize', 'sharpen', 'halftone', 'vignette'].forEach(id => {
    const input = document.getElementById(id);
    const display = document.getElementById(id + '-value');
    
    input.addEventListener('input', () => {
        let value = input.value;
        if (['brightness', 'contrast', 'saturation', 'sharpen', 'vignette'].includes(id)) {
            value = (value / 100).toFixed(1);
        }
        display.textContent = value;
        updateURL();
    });
});

// Update URL on any input change
document.querySelectorAll('input, select').forEach(element => {
    element.addEventListener('change', updateURL);
    element.addEventListener('input', updateURL);
});

function updateURL() {
    let url = '';
    const params = [];
    let supportsFormat = true;
    
    // Build base URL based on endpoint
    switch(currentEndpoint) {
        case 'random': {
            const width = document.getElementById('width').value;
            const height = document.getElementById('height').value;
            const category = document.getElementById('category').value;
            const seed = document.getElementById('seed').value;
            const colorMatch = document.getElementById('random-color-match').value;
            url = `/${width}/${height}${category ? '/' + category : ''}`;
            if (seed) params.push(`seed=${encodeURIComponent(seed)}`);
            if (colorMatch && colorMatch !== '#3b82f6') params.push(`color=${encodeURIComponent(colorMatch.replace('#', ''))}`);
            break;
        }
            
        case 'id': {
            const id = document.getElementById('image-id').value;
            const idWidth = document.getElementById('id-width').value;
            const idHeight = document.getElementById('id-height').value;
            url = `/id/${id}/${idWidth}/${idHeight}`;
            break;
        }
            
        case 'ratio': {
            const ratio = document.getElementById('ratio').value;
            const ratioHeight = document.getElementById('ratio-height').value;
            const ratioCategory = document.getElementById('ratio-category').value;
            const ratioSeed = document.getElementById('ratio-seed').value;
            const ratioColor = document.getElementById('ratio-color-match').value;
            url = `/ratio/${ratio}/${ratioHeight}${ratioCategory ? '/' + ratioCategory : ''}`;
            if (ratioSeed) params.push(`seed=${encodeURIComponent(ratioSeed)}`);
            if (ratioColor && ratioColor !== '#3b82f6') params.push(`color=${encodeURIComponent(ratioColor.replace('#', ''))}`);
            break;
        }
            
        case 'preset': {
            const preset = document.getElementById('preset').value;
            const presetCategory = document.getElementById('preset-category').value;
            const presetSeed = document.getElementById('preset-seed').value;
            const presetColor = document.getElementById('preset-color-match').value;
            url = `/preset/${preset}${presetCategory ? '/' + presetCategory : ''}`;
            if (presetSeed) params.push(`seed=${encodeURIComponent(presetSeed)}`);
            if (presetColor && presetColor !== '#3b82f6') params.push(`color=${encodeURIComponent(presetColor.replace('#', ''))}`);
            break;
        }
            
        case 'solid': {
            const solidWidth = document.getElementById('solid-width').value;
            const solidHeight = document.getElementById('solid-height').value;
            const bgColor = document.getElementById('bg-color').value.replace('#', '');
            const fgColor = document.getElementById('fg-color').value.replace('#', '');
            const solidText = document.getElementById('solid-text').value;
            url = `/solid/${solidWidth}/${solidHeight}/${bgColor}/${fgColor}`;
            if (solidText) params.push(`text=${encodeURIComponent(solidText)}`);
            supportsFormat = false;
            break;
        }
            
        case 'color-match': {
            const matchColor = document.getElementById('match-color').value.replace('#', '');
            const matchWidth = document.getElementById('match-width').value;
            const matchHeight = document.getElementById('match-height').value;
            url = `/color/${matchColor}/${matchWidth}/${matchHeight}`;
            break;
        }
            
        case 'svg': {
            const svgWidth = document.getElementById('svg-width').value;
            const svgHeight = document.getElementById('svg-height').value;
            const svgBg = document.getElementById('svg-bg').value.replace('#', '');
            const svgFg = document.getElementById('svg-fg').value.replace('#', '');
            const svgText = document.getElementById('svg-text').value;
            url = `/svg/${svgWidth}/${svgHeight}`;
            params.push(`bg=${svgBg}`);
            params.push(`fg=${svgFg}`);
            if (svgText) params.push(`text=${encodeURIComponent(svgText)}`);
            supportsFormat = false;
            break;
        }
            
        case 'gradient': {
            const gradWidth = document.getElementById('grad-width').value;
            const gradHeight = document.getElementById('grad-height').value;
            const gradFrom = document.getElementById('grad-from').value.replace('#', '');
            const gradTo = document.getElementById('grad-to').value.replace('#', '');
            url = `/gradient/${gradWidth}x${gradHeight}/${gradFrom}/${gradTo}`;
            break;
        }
            
        case 'avatar': {
            const avatarSize = document.getElementById('avatar-size').value;
            const avatarName = document.getElementById('avatar-name').value;
            const avatarPalette = document.getElementById('avatar-palette').value;
            const avatarCircle = document.getElementById('avatar-circle').checked;
            const avatarSingle = document.getElementById('avatar-single').checked;
            const avatarBg = document.getElementById('avatar-bg').value;
            const avatarFg = document.getElementById('avatar-fg').value.replace('#', '');
            const avatarBorder = document.getElementById('avatar-border').value;
            const avatarBorderColor = document.getElementById('avatar-border-color').value.replace('#', '');
            url = `/avatar/${avatarSize}/${encodeURIComponent(avatarName)}`;
            if (avatarPalette && avatarPalette !== 'flatui') params.push(`palette=${avatarPalette}`);
            if (avatarCircle) params.push('circle=true');
            if (avatarSingle) params.push('single=true');
            if (avatarBorder > 0) {
                params.push(`border=${avatarBorder}`);
                params.push(`border_color=${avatarBorderColor}`);
            }
            // Only pass bg if user has explicitly changed it from default (#667eea)
            if (avatarBg && avatarBg !== '#667eea') params.push(`bg=${avatarBg.replace('#', '')}`);
            if (avatarFg && avatarFg !== 'ffffff') params.push(`fg=${avatarFg}`);
            supportsFormat = true;
            break;
        }
            
        case 'lucky': {
            const luckyCategory = document.getElementById('random-category').value;
            const luckyColor = document.getElementById('random-color').value;
            url = `/random/${luckyCategory}`;
            if (luckyColor && luckyColor !== '#3b82f6') params.push(`color=${encodeURIComponent(luckyColor.replace('#', ''))}`);
            supportsFormat = false;
            break;
        }
    }
    
    // Add format extension
    if (supportsFormat) {
        const format = document.getElementById('format').value;
        if (format !== 'jpeg') {
            url += `.${format}`;
        }
    }
    
    // Add query parameters
    if (document.getElementById('grayscale').checked) params.push('grayscale=true');
    if (document.getElementById('sepia').checked) params.push('sepia=true');
    if (document.getElementById('invert').checked) params.push('invert=true');
    if (document.getElementById('emboss').checked) params.push('emboss=true');
    if (document.getElementById('oil_painting').checked) params.push('oil_painting=true');
    if (document.getElementById('pencil_sketch').checked) params.push('pencil_sketch=true');
    if (document.getElementById('cartoon').checked) params.push('cartoon=true');
    if (document.getElementById('lqip').checked) params.push('lqip=true');
    if (document.getElementById('watermark').checked) params.push('watermark=true');
    if (document.getElementById('base64').checked) params.push('base64=true');
    
    const blur = document.getElementById('blur').value;
    if (blur > 0) params.push(`blur=${blur}`);
    
    const noise = document.getElementById('noise').value;
    if (noise > 0) params.push(`noise=${noise}`);
    
    const pixelate = document.getElementById('pixelate').value;
    if (pixelate > 0) params.push(`pixelate=${pixelate}`);
    
    const posterize = document.getElementById('posterize').value;
    if (posterize > 0) params.push(`posterize=${posterize}`);
    
    const solarize = document.getElementById('solarize').value;
    if (solarize > 0) params.push(`solarize=${solarize}`);
    
    const duotone = document.getElementById('duotone').value;
    if (duotone) params.push(`duotone=${encodeURIComponent(duotone)}`);
    
    const sharpen = document.getElementById('sharpen').value;
    if (sharpen > 0) params.push(`sharpen=${(sharpen/100).toFixed(1)}`);
    
    const halftone = document.getElementById('halftone').value;
    if (halftone > 0) params.push(`halftone=${halftone}`);
    
    const edges = document.getElementById('edges').value;
    if (edges) params.push(`edges=${edges}`);
    
    const vignette = document.getElementById('vignette').value;
    if (vignette > 0) params.push(`vignette=${(vignette/100).toFixed(1)}`);
    
    const quality = document.getElementById('quality').value;
    if (quality != 85) params.push(`quality=${quality}`);
    
    const fit = document.getElementById('fit').value;
    if (fit !== 'crop') params.push(`fit=${fit}`);
    
    const border = document.getElementById('border').value;
    if (border) params.push(`border=${encodeURIComponent(border)}`);
    
    const padding = document.getElementById('padding').value;
    if (padding > 0) params.push(`padding=${padding}`);
    
    const brightness = document.getElementById('brightness').value;
    if (brightness != 100) params.push(`brightness=${(brightness/100).toFixed(1)}`);
    
    const contrast = document.getElementById('contrast').value;
    if (contrast != 100) params.push(`contrast=${(contrast/100).toFixed(1)}`);
    
    const saturation = document.getElementById('saturation').value;
    if (saturation != 100) params.push(`saturation=${(saturation/100).toFixed(1)}`);
    
    const tint = document.getElementById('tint').value;
    if (tint && tint !== '#0ea5e9') params.push(`tint=${encodeURIComponent(tint.replace('#', ''))}`);
    
    const text = document.getElementById('text').value;
    if (text) params.push(`text=${encodeURIComponent(text)}`);
    
    // Combine URL and params
    if (params.length > 0) {
        url += '?' + params.join('&');
    }
    
    document.getElementById('url-output').innerHTML = `<div>${window.location.origin}${url}</div>`;
}

function copyURL() {
    const url = document.getElementById('url-output').textContent;
    navigator.clipboard.writeText(url).then(() => {
        Toastify({
            text: i18n.get('notification.copied') || "URL copied to clipboard!",
            duration: 3000,
            gravity: "top",
            position: "center",
            offset: { x: 0, y: 60 },
            style: {
                background: "linear-gradient(to right, #0284c7, #0ea5e9)",
            }
        }).showToast();
    });
}

function openInNewTab() {
    const url = document.getElementById('url-output').textContent;
    window.open(url, '_blank');
}

function loadPreview() {
    let url = document.getElementById('url-output').textContent;
    const preview = document.getElementById('preview');
    const container = document.getElementById('preview-container');
    const sizeDisplay = document.getElementById('image-size');
    const fileSizeDisplay = document.getElementById('file-size');
    
    // Add cache-busting for random images (endpoints without seed or ID)
    const isRandom = currentEndpoint === 'random' || currentEndpoint === 'ratio' || currentEndpoint === 'preset';
    const hasSeed = url.includes('seed=');
    
    if (isRandom && !hasSeed) {
        // Add timestamp to prevent caching of random images
        const separator = url.includes('?') ? '&' : '?';
        url += `${separator}_t=${Date.now()}`;
    }
    
    // Show loading state
    sizeDisplay.textContent = 'Loading...';
    fileSizeDisplay.textContent = 'Loading...';
    
    // Create a new image to get dimensions
    const img = new Image();
    img.onload = function() {
        preview.src = url;
        container.classList.add('show');
        sizeDisplay.textContent = `${img.naturalWidth} × ${img.naturalHeight}px`;
        
        // Fetch to get file size
        fetch(url)
            .then(response => {
                const contentLength = response.headers.get('content-length');
                if (contentLength) {
                    const sizeKB = (parseInt(contentLength) / 1024).toFixed(2);
                    fileSizeDisplay.textContent = `${sizeKB} KB`;
                } else {
                    return response.blob().then(blob => {
                        const sizeKB = (blob.size / 1024).toFixed(2);
                        fileSizeDisplay.textContent = `${sizeKB} KB`;
                    });
                }
            })
            .catch(() => {
                fileSizeDisplay.textContent = 'Unknown';
            });
    };
    img.onerror = function() {
        sizeDisplay.textContent = 'Error loading';
        fileSizeDisplay.textContent = '-';
    };
    img.src = url;
}

function zoomImage() {
    const preview = document.getElementById('preview');
    const modal = document.getElementById('zoom-modal');
    const zoomImg = document.getElementById('zoom-image');
    const zoomSize = document.getElementById('zoom-size');
    const zoomFileSize = document.getElementById('zoom-file-size');
    
    zoomImg.src = preview.src;
    zoomSize.textContent = document.getElementById('image-size').textContent;
    zoomFileSize.textContent = document.getElementById('file-size').textContent;
    modal.classList.add('active');
}

function closeZoom() {
    const modal = document.getElementById('zoom-modal');
    modal.classList.remove('active');
}

// Close zoom on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeZoom();
    }
});

// Fetch and populate categories
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const data = await response.json();
        
        if (data.categories && data.categories.length > 0) {
            // Get all category select elements
            const selects = [
                document.getElementById('category'),
                document.getElementById('ratio-category'),
                document.getElementById('preset-category')
            ];
            
            // Populate each select
            selects.forEach(select => {
                // Keep the first "All categories" option
                const firstOption = select.options[0];
                select.innerHTML = '';
                select.appendChild(firstOption);
                
                // Add category options
                data.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category;
                    select.appendChild(option);
                });
            });
            
            console.log(`Loaded ${data.categories.length} categories:`, data.categories);
        }
    } catch (error) {
        console.error(i18n.get('console.load_categories_error') || 'Failed to load categories:', error);
    }
}

// QR Code Generation
function showQRCode() {
    const url = document.getElementById('url-output').textContent;
    const modal = document.getElementById('qr-modal');
    const canvas = document.getElementById('qr-canvas');

    // Clear previous QR code
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Generate real QR code using qrcode library
    QRCode.toCanvas(canvas, url, {
        width: 256,
        margin: 2,
        color: {
            dark: '#1c1917',
            light: '#ffffff'
        }
    }, function(error) {
        if (error) {
            console.error(error);
            Toastify({
                text: i18n.get('notification.qr_error') || "Failed to generate QR code",
                duration: 3000,
                gravity: "top",
                position: "center",
                offset: { x: 0, y: 60 },
                style: {
                    background: "linear-gradient(to right, #dc2626, #ef4444)",
                }
            }).showToast();
        }
    });

    modal.classList.add('active');
}

function closeQRModal(event) {
    if (event) {
        event.stopPropagation();
    }
    document.getElementById('qr-modal').classList.remove('active');
}

// Keyboard Shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + P: Preview
    if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        loadPreview();
    }
    
    // Ctrl/Cmd + U: Copy URL
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        copyURL();
    }
    
    // Ctrl/Cmd + Q: Show QR Code
    if ((e.ctrlKey || e.metaKey) && e.key === 'q') {
        e.preventDefault();
        showQRCode();
    }
    
    // Ctrl/Cmd + D: Toggle Dark Mode
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        toggleTheme();
    }
});

// Initialize
loadTheme();
loadCategories();
updateURL();
