// Index page specific JavaScript

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const categorySelect = document.getElementById('upload-category');
const statusEl = document.getElementById('upload-status');

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  handleFiles(e.dataTransfer.files);
});
fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

async function handleFiles(files) {
  if (!files.length) return;
  statusEl.classList.remove('hidden');
  const uploadingText = i18n.get('upload.uploading') || 'Uploading {count} file(s)...';
  statusEl.textContent = uploadingText.replace('{count}', files.length);
  statusEl.className = 'mt-3 text-sm text-center font-medium text-stone-500';

  let uploaded = 0;
  const category = categorySelect.value;

  for (const file of files) {
    const formData = new FormData();
    formData.append('file', file);
    if (category) formData.append('category', category);

    try {
      const res = await fetch('/api/upload', { method: 'POST', body: formData });
      if (res.ok) uploaded++;
    } catch (err) {
      console.error('Upload failed:', err);
    }
  }

  const uploadedText = i18n.get('upload.uploaded') || 'Uploaded {uploaded}/{total} files. Reloading...';
  statusEl.textContent = uploadedText.replace('{uploaded}', uploaded).replace('{total}', files.length);
  statusEl.className = 'mt-3 text-sm text-center font-medium text-accent';
  setTimeout(() => location.reload(), 1000);
}
