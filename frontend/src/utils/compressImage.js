import imageCompression from 'browser-image-compression';

/**
 * Compress an image file before upload.
 * 
 * Default options:
 * - maxSizeMB: 1        → target ≤ 1 MB output
 * - maxWidthOrHeight: 1920  → resize long edge to 1920 px
 * - useWebWorker: true   → non-blocking compression
 * - fileType: 'image/jpeg' → convert HEIC/PNG → JPEG for smaller size
 * 
 * @param {File} file - The original image File object
 * @param {Object} [opts] - Override default compression options
 * @returns {Promise<File>} Compressed File object
 */
export default async function compressImage(file, opts = {}) {
  // Skip compression for non-image files (e.g. PDF)
  if (!file.type.startsWith('image/')) {
    return file;
  }

  const options = {
    maxSizeMB: 1,
    maxWidthOrHeight: 1920,
    useWebWorker: true,
    fileType: 'image/jpeg',
    initialQuality: 0.8,
    ...opts,
  };

  try {
    const compressed = await imageCompression(file, options);

    // Log compression result for debugging
    const originalMB = (file.size / (1024 * 1024)).toFixed(2);
    const compressedMB = (compressed.size / (1024 * 1024)).toFixed(2);
    const ratio = ((1 - compressed.size / file.size) * 100).toFixed(0);
    console.log(
      `[compressImage] ${file.name}: ${originalMB}MB → ${compressedMB}MB (−${ratio}%)`
    );

    // Ensure the result is a File with a proper filename.
    // browser-image-compression may return a Blob (especially via web workers)
    // without a name, causing backend file-type validation to fail.
    if (!compressed.name || compressed.name === 'blob') {
      const ext = options.fileType === 'image/jpeg' ? '.jpg'
        : options.fileType === 'image/png' ? '.png'
        : options.fileType === 'image/webp' ? '.webp'
        : '.jpg';
      const safeName = (file.name || 'image').replace(/\.[^.]+$/, '') + ext;
      return new File([compressed], safeName, { type: compressed.type || options.fileType });
    }

    return compressed;
  } catch (err) {
    // If compression fails, return the original file so upload still works
    console.warn('[compressImage] Compression failed, using original file:', err);
    return file;
  }
}
