// CivicFix: free in-browser CLIP image classification (no AI requests to the backend).
// The browser downloads ONNX weights on first use; later visits may use its cache.
const btn = document.getElementById('classifyBtn');
const status = document.getElementById('aiStatus');
const categories = [
  ['Pothole', 'a photo of a pothole or hole in the road'],
  ['Garbage', 'a photo of a pile of trash and litter on the street'],
  ['Broken Streetlight', 'a photo of a broken streetlight lamp'],
  ['Water Leakage', 'a photo of a burst water pipe leaking on the street'],
  ['Damaged Road', 'a photo of a badly damaged cracked road surface'],
  ['Other', 'a photo of a different civic infrastructure problem'],
];
let modelPromise;

function getModel() {
  if (!modelPromise) {
    modelPromise = (async () => {
      const { pipeline, env } = await import('https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1');
      env.allowLocalModels = false;
      return pipeline('zero-shot-image-classification', 'Xenova/clip-vit-base-patch32', {
        device: 'wasm',
        dtype: 'q8',
        progress_callback: event => {
          if (event.status === 'progress' && event.progress !== undefined) {
            status.textContent = `Downloading AI model: ${Math.round(event.progress)}% (first run only)…`;
          }
        },
      });
    })().catch(error => { modelPromise = null; throw error; });
  }
  return modelPromise;
}

btn.addEventListener('click', async () => {
  const file = document.getElementById('photo').files[0];
  if (!file) { status.textContent = 'Please upload a photo first.'; return; }
  if (!file.type.startsWith('image/')) { status.textContent = 'Please select an image file.'; return; }
  btn.disabled = true;
  status.textContent = 'Preparing on-device AI (first run downloads the model)…';
  let url;
  try {
    const classifier = await getModel();
    url = URL.createObjectURL(file);
    status.textContent = 'Analyzing your image on this device…';
    const results = await classifier(url, categories.map(item => item[1]));
    const top = results[0];
    const chosen = categories.find(item => item[1] === top.label);
    if (!chosen || chosen[0] === 'Other' || top.score < 0.25) {
      status.textContent = 'No clear suggestion. Please choose the correct category manually.';
    } else {
      document.getElementById('category').value = chosen[0];
      status.textContent = `Suggested: ${chosen[0]} (${Math.round(top.score * 100)}% relative model score). Please verify before submitting.`;
    }
  } catch (error) {
    console.error('Browser AI error:', error);
    status.textContent = 'On-device AI unavailable: ' + (error?.message || 'model could not load') + '. Select a category manually.';
  } finally {
    if (url) URL.revokeObjectURL(url);
    btn.disabled = false;
  }
});
