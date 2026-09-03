/** Client-side photo compression before upload.
 *  Phone cameras produce 5-48MB images; the palm/vastu pipelines need far
 *  less. Decode via the browser (handles HEIC on iOS Safari), draw upright to
 *  a canvas capped at 1600px, export JPEG. Falls back to the original file if
 *  anything fails — the server normalizes again as the safety net. */
export async function compressImage(file: File, maxEdge = 1600,
                                    quality = 0.85): Promise<File> {
  try {
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, maxEdge / Math.max(bitmap.width, bitmap.height));
    const w = Math.max(1, Math.round(bitmap.width * scale));
    const h = Math.max(1, Math.round(bitmap.height * scale));
    const canvas = document.createElement("canvas");
    canvas.width = w; canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) return file;
    ctx.drawImage(bitmap, 0, 0, w, h);
    bitmap.close();
    const blob: Blob | null = await new Promise((res) =>
      canvas.toBlob(res, "image/jpeg", quality));
    if (!blob || blob.size === 0) return file;
    return new File([blob], file.name.replace(/\.[^.]+$/, "") + ".jpg",
                    { type: "image/jpeg" });
  } catch {
    return file; // server-side normalization is the backstop
  }
}
