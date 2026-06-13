// Client-side avatar processing: downscale + center-crop to a square JPEG data
// URL so the payload stays small (the backend stores it inline and caps size).

export async function fileToAvatarDataUrl(
  file: File,
  size = 256,
  quality = 0.85,
): Promise<string> {
  const bitmap = await createImageBitmap(file);
  try {
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Canvas is not supported on this device.");

    // Cover: scale so the image fills the square, then center-crop the overflow.
    const scale = Math.max(size / bitmap.width, size / bitmap.height);
    const w = bitmap.width * scale;
    const h = bitmap.height * scale;
    ctx.drawImage(bitmap, (size - w) / 2, (size - h) / 2, w, h);
    return canvas.toDataURL("image/jpeg", quality);
  } finally {
    bitmap.close();
  }
}
