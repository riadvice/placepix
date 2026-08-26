// URL Builder page specific JavaScript

let currentEndpoint = 'random';

// Initialize endpoint switching - update for vertical sidebar
function initEndpointSidebar() {
    document.querySelectorAll('.endpoint-sidebar-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            // Remove active from all sidebar items
            document.querySelectorAll('.endpoint-sidebar-item').forEach(i => i.classList.remove('active'));
            // Add active to clicked item
            item.classList.add('active');
            // Update current endpoint
            currentEndpoint = item.dataset.endpoint;

            // Show/hide config sections with animation
            document.querySelectorAll('.endpoint-config').forEach(config => {
                if (config.dataset.endpoint === currentEndpoint) {
                    config.style.display = 'block';
                    // Small delay to allow display:block to take effect before adding active class
                    setTimeout(() => config.classList.add('active'), 10);
                } else {
                    config.classList.remove('active');
                    // Wait for transition to complete before hiding
                    setTimeout(() => {
                        if (!config.classList.contains('active')) {
                            config.style.display = 'none';
                        }
                    }, 300);
                }
            });

            updateURL();
        });
    });

    // Set initial active state based on currentEndpoint
    document.querySelectorAll('.endpoint-sidebar-item').forEach(item => {
        if (item.dataset.endpoint === currentEndpoint) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Show initial config section
    document.querySelectorAll('.endpoint-config').forEach(config => {
        if (config.dataset.endpoint === currentEndpoint) {
            config.style.display = 'block';
            config.classList.add('active');
        } else {
            config.style.display = 'none';
            config.classList.remove('active');
        }
    });
}

// Initialize sidebar after DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initEndpointSidebar);
} else {
    initEndpointSidebar();
}

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

// Size badge detection
function updateSizeBadge() {
    const preview = document.getElementById('preview');
    const sizeBadge = document.getElementById('size-badge');

    if (!preview.src || preview.naturalWidth === 0) {
        sizeBadge.style.display = 'none';
        return;
    }

    const displayedWidth = preview.clientWidth;
    const naturalWidth = preview.naturalWidth;

    // Show badge if image is scaled down significantly (>5% difference)
    if (naturalWidth > displayedWidth * 1.05) {
        sizeBadge.textContent = `Actual: ${preview.naturalWidth} × ${preview.naturalHeight}`;
        sizeBadge.style.display = 'block';
    } else {
        sizeBadge.style.display = 'none';
    }
}

// Update size badge when preview loads
const originalLoadPreview = loadPreview;
loadPreview = function() {
    originalLoadPreview();
    const preview = document.getElementById('preview');
    preview.onload = () => updateSizeBadge();
};

// Update size badge on window resize
window.addEventListener('resize', updateSizeBadge);

// Helper function to add optional category to URL
function addCategoryToUrl(baseUrl, category) {
    return category ? `${baseUrl}/${category}` : baseUrl;
}

// Helper function to add optional seed, color match, and orientation parameters
function addSeedAndColorParams(params, seed, colorMatch, defaultColor = '#3b82f6', orientation = '') {
    if (seed) params.push(`seed=${encodeURIComponent(seed)}`);
    if (colorMatch && colorMatch !== defaultColor) params.push(`color=${encodeURIComponent(colorMatch.replace('#', ''))}`);
    if (orientation) params.push(`orientation=${encodeURIComponent(orientation)}`);
}

// Endpoint URL builders
function buildRandomURL(params) {
    const width = document.getElementById('width').value;
    const height = document.getElementById('height').value;
    const category = document.getElementById('category').value;
    const seed = document.getElementById('seed').value;
    const colorMatch = document.getElementById('random-color-match').value;
    const orientation = document.getElementById('orientation').value;
    let url = addCategoryToUrl(`/${width}/${height}`, category);
    addSeedAndColorParams(params, seed, colorMatch, '#3b82f6', orientation);
    return url;
}

function buildIdURL(params) {
    const id = document.getElementById('image-id').value;
    const idWidth = document.getElementById('id-width').value;
    const idHeight = document.getElementById('id-height').value;
    return `/id/${id}/${idWidth}/${idHeight}`;
}

function buildRatioURL(params) {
    const ratio = document.getElementById('ratio').value;
    const ratioHeight = document.getElementById('ratio-height').value;
    const ratioCategory = document.getElementById('ratio-category').value;
    const ratioSeed = document.getElementById('ratio-seed').value;
    const ratioColor = document.getElementById('ratio-color-match').value;
    const orientation = document.getElementById('ratio-orientation').value;
    let url = addCategoryToUrl(`/ratio/${ratio}/${ratioHeight}`, ratioCategory);
    addSeedAndColorParams(params, ratioSeed, ratioColor, '#3b82f6', orientation);
    return url;
}

function buildPresetURL(params) {
    const preset = document.getElementById('preset').value;
    const presetCategory = document.getElementById('preset-category').value;
    const presetSeed = document.getElementById('preset-seed').value;
    const presetColor = document.getElementById('preset-color-match').value;
    const orientation = document.getElementById('preset-orientation').value;
    let url = addCategoryToUrl(`/preset/${preset}`, presetCategory);
    addSeedAndColorParams(params, presetSeed, presetColor, '#3b82f6', orientation);
    return url;
}

function buildSolidURL(params) {
    const solidWidth = document.getElementById('solid-width').value;
    const solidHeight = document.getElementById('solid-height').value;
    const bgColor = document.getElementById('bg-color').value.replace('#', '');
    const fgColor = document.getElementById('fg-color').value.replace('#', '');
    const solidText = document.getElementById('solid-text').value;
    let url = `/solid/${solidWidth}/${solidHeight}/${bgColor}/${fgColor}`;
    if (solidText) params.push(`text=${encodeURIComponent(solidText)}`);
    return { url, supportsFormat: false };
}

function buildColorMatchURL(params) {
    const matchColor = document.getElementById('match-color').value.replace('#', '');
    const matchWidth = document.getElementById('match-width').value;
    const matchHeight = document.getElementById('match-height').value;
    return `/color/${matchColor}/${matchWidth}/${matchHeight}`;
}

function buildSvgURL(params) {
    const svgWidth = document.getElementById('svg-width').value;
    const svgHeight = document.getElementById('svg-height').value;
    const svgBg = document.getElementById('svg-bg').value.replace('#', '');
    const svgFg = document.getElementById('svg-fg').value.replace('#', '');
    const svgText = document.getElementById('svg-text').value;
    let url = `/svg/${svgWidth}/${svgHeight}`;
    params.push(`bg=${svgBg}`);
    params.push(`fg=${svgFg}`);
    if (svgText) params.push(`text=${encodeURIComponent(svgText)}`);
    return { url, supportsFormat: false };
}

function buildGradientURL(params) {
    const gradWidth = document.getElementById('grad-width').value;
    const gradHeight = document.getElementById('grad-height').value;
    const gradFrom = document.getElementById('grad-from').value.replace('#', '');
    const gradTo = document.getElementById('grad-to').value.replace('#', '');
    return `/gradient/${gradWidth}x${gradHeight}/${gradFrom}/${gradTo}`;
}

function buildMockupURL(params) {
    const device = document.getElementById('mockup-device').value;
    const width = document.getElementById('mockup-width').value;
    const category = document.getElementById('mockup-category').value.trim();
    const addressBar = document.getElementById('mockup-url').value.trim();
    const seed = document.getElementById('mockup-seed').value.trim();
    const transparent = document.getElementById('mockup-transparent').checked;
    const background = document.getElementById('mockup-bg').value.replace('#', '');

    let url = `/mockup/${device}/${width}`;
    if (category) url += `/${encodeURIComponent(category)}`;
    if (seed) params.push(`seed=${encodeURIComponent(seed)}`);
    if (device.startsWith('browser') && addressBar && addressBar !== 'placepix.net') {
        params.push(`url=${encodeURIComponent(addressBar)}`);
    }
    if (!transparent) params.push(`background=${background}`);
    _pushOwnFormat(params, 'png');
    return { url, supportsFormat: false };
}

function buildSkeletonURL(params) {
    const preset = document.getElementById('skeleton-preset').value;
    const width = document.getElementById('skeleton-width').value;
    const height = document.getElementById('skeleton-height').value;
    const theme = document.getElementById('skeleton-theme').value;
    const radius = document.getElementById('skeleton-radius').value;
    const rows = document.getElementById('skeleton-rows').value;
    const cols = document.getElementById('skeleton-cols').value;

    const url = `/skeleton/${preset}/${width}/${height}`;
    if (theme !== 'light') params.push(`theme=${theme}`);
    if (radius != 8) params.push(`radius=${radius}`);
    if (rows > 0) params.push(`rows=${rows}`);
    if (cols > 0) params.push(`cols=${cols}`);
    _pushOwnFormat(params, 'png');
    return { url, supportsFormat: false };
}

// These endpoints default to PNG rather than JPEG, so they carry ?format= instead
// of the shared extension the photo endpoints use. 'jpeg' is the select's own
// default rather than a deliberate choice, so it is left off the URL.
function _pushOwnFormat(params, defaultFormat) {
    const format = document.getElementById('format').value;
    if (format && format !== defaultFormat && format !== 'jpeg') {
        params.push(`format=${format}`);
    }
}

// The mockup and wireframe endpoints render their own pixels, so the shared
// photo filters do not apply to them.
function endpointTakesFilters() {
    return currentEndpoint !== 'mockup' && currentEndpoint !== 'skeleton';
}

function toggleAvatarType() {
    const avatarType = document.getElementById('avatar-type').value;
    const letterControls = document.querySelector('.avatar-letter-controls');
    const multiavatarControls = document.querySelector('.avatar-multiavatar-controls');
    if (letterControls) letterControls.style.display = avatarType === 'letter' ? 'block' : 'none';
    if (multiavatarControls) multiavatarControls.style.display = avatarType === 'multiavatar' ? 'block' : 'none';
    updateURL();
}

function _pushMultiavatarParams(params) {
    params.push('type=multiavatar');
    const avatarEnv = document.getElementById('avatar-env').checked;
    if (!avatarEnv) params.push('env=false');
    const avatarPart = document.getElementById('avatar-part').value.trim();
    const avatarTheme = document.getElementById('avatar-theme').value.trim();
    if (avatarPart) params.push(`part=${encodeURIComponent(avatarPart)}`);
    if (avatarTheme) params.push(`theme=${encodeURIComponent(avatarTheme)}`);
}

function _pushLetterAvatarParams(params) {
    const avatarPalette = document.getElementById('avatar-palette').value;
    const avatarCircle = document.getElementById('avatar-circle').checked;
    const avatarSingle = document.getElementById('avatar-single').checked;
    const avatarBg = document.getElementById('avatar-bg').value;
    const avatarFg = document.getElementById('avatar-fg').value.replace('#', '');
    const avatarBorder = document.getElementById('avatar-border').value;
    const avatarBorderColor = document.getElementById('avatar-border-color').value.replace('#', '');
    
    if (avatarPalette && avatarPalette !== 'flatui') params.push(`palette=${avatarPalette}`);
    if (avatarCircle) params.push('circle=true');
    if (avatarSingle) params.push('single=true');
    if (avatarBorder > 0) {
        params.push(`border=${avatarBorder}`);
        params.push(`border_color=${avatarBorderColor}`);
    }
    if (avatarBg && avatarBg !== '#667eea') params.push(`bg=${avatarBg.replace('#', '')}`);
    if (avatarFg && avatarFg !== 'ffffff') params.push(`fg=${avatarFg}`);
}

function buildAvatarURL(params) {
    const avatarType = document.getElementById('avatar-type').value;
    const avatarSize = document.getElementById('avatar-size').value;
    const avatarName = document.getElementById('avatar-name').value;
    const url = `/avatar/${avatarSize}/${encodeURIComponent(avatarName)}`;
    
    if (avatarType === 'multiavatar') {
        _pushMultiavatarParams(params);
        return { url, supportsFormat: false };
    }
    
    _pushLetterAvatarParams(params);
    return { url, supportsFormat: true };
}

function buildLuckyURL(params) {
    const luckyCategory = document.getElementById('random-category').value;
    const luckyColor = document.getElementById('random-color').value;
    const url = `/random/${luckyCategory}`;
    if (luckyColor && luckyColor !== '#3b82f6') params.push(`color=${encodeURIComponent(luckyColor.replace('#', ''))}`);
    return { url, supportsFormat: false };
}

function updateURL() {
    let url = '';
    const params = [];
    let supportsFormat = true;

    // Build base URL based on endpoint using refactored functions
    switch(currentEndpoint) {
        case 'random':
            url = buildRandomURL(params);
            break;
        case 'id':
            url = buildIdURL(params);
            break;
        case 'ratio':
            url = buildRatioURL(params);
            break;
        case 'preset':
            url = buildPresetURL(params);
            break;
        case 'solid':
            const solidResult = buildSolidURL(params);
            url = solidResult.url;
            supportsFormat = solidResult.supportsFormat;
            break;
        case 'color-match':
            url = buildColorMatchURL(params);
            break;
        case 'svg':
            const svgResult = buildSvgURL(params);
            url = svgResult.url;
            supportsFormat = svgResult.supportsFormat;
            break;
        case 'gradient':
            url = buildGradientURL(params);
            break;
        case 'mockup':
            const mockupResult = buildMockupURL(params);
            url = mockupResult.url;
            supportsFormat = mockupResult.supportsFormat;
            break;
        case 'skeleton':
            const skeletonResult = buildSkeletonURL(params);
            url = skeletonResult.url;
            supportsFormat = skeletonResult.supportsFormat;
            break;
        case 'avatar':
            const avatarResult = buildAvatarURL(params);
            url = avatarResult.url;
            supportsFormat = avatarResult.supportsFormat;
            break;
        case 'lucky':
            const luckyResult = buildLuckyURL(params);
            url = luckyResult.url;
            supportsFormat = luckyResult.supportsFormat;
            break;
    }
    
    // Add format extension
    if (supportsFormat) {
        const format = document.getElementById('format').value;
        if (format !== 'jpeg') {
            url += `.${format}`;
        }
    }
    
    // Add query parameters
    if (!endpointTakesFilters()) {
        if (params.length > 0) url += '?' + params.join('&');
        document.getElementById('url-output').innerHTML = `<div>${window.location.origin}${url}</div>`;
        return;
    }

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

    const scrimMode = document.getElementById('scrim-mode').value;
    const scrimOpacity = document.getElementById('scrim-opacity').value;
    if (scrimMode && scrimOpacity > 0) {
        const amount = parseFloat((scrimOpacity / 100).toFixed(2));
        params.push(`scrim=${scrimMode === 'dark' ? amount : `${scrimMode}:${amount}`}`);
    }
    
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
    const isRandom = ['random', 'ratio', 'preset', 'mockup'].includes(currentEndpoint);
    const hasSeed = url.includes('seed=');
    
    if (isRandom && !hasSeed) {
        // Add timestamp to prevent caching of random images
        const separator = url.includes('?') ? '&' : '?';
        url += `${separator}_t=${Date.now()}`;
    }
    
    // Show loading state
    container.classList.add('loading');
    sizeDisplay.textContent = 'Loading...';
    fileSizeDisplay.textContent = 'Loading...';

    // Create a new image to get dimensions
    const img = new Image();
    img.onload = function() {
        preview.src = url;
        container.classList.remove('loading');
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
        container.classList.remove('loading');
        sizeDisplay.textContent = 'Error loading';
        fileSizeDisplay.textContent = '-';
    };
    img.src = url;
}

function zoomImage() {
    const container = document.getElementById('preview-container');
    if (container.classList.contains('loading')) return;

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

    // Generate QR code using qrcode library
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
    // Don't trigger shortcuts if user is typing in an input field
    const activeElement = document.activeElement;
    if (activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.tagName === 'SELECT' ||
        activeElement.isContentEditable
    )) {
        return;
    }

    // Ctrl/Cmd + P: Preview
    if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        const zoomModal = document.getElementById('zoom-modal');
        if (zoomModal && zoomModal.classList.contains('active')) return;
        e.preventDefault();
        e.stopPropagation();
        loadPreview();
    }

    // Ctrl/Cmd + U: Copy URL
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        e.stopPropagation();
        copyURL();
    }

    // Ctrl/Cmd + Q: Show QR Code
    if ((e.ctrlKey || e.metaKey) && e.key === 'q') {
        e.preventDefault();
        e.stopPropagation();
        showQRCode();
    }

    // Ctrl/Cmd + D: Toggle Dark Mode
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        e.stopPropagation();
        toggleTheme();
    }
});

// Scrim opacity readout
const scrimOpacityInput = document.getElementById('scrim-opacity');
if (scrimOpacityInput) {
    scrimOpacityInput.addEventListener('input', () => {
        document.getElementById('scrim-value').textContent = scrimOpacityInput.value;
    });
}

// Avatar type toggle
document.getElementById('avatar-type').addEventListener('change', toggleAvatarType);

// Initialize
loadTheme();
loadCategories();
toggleAvatarType();
updateURL();
