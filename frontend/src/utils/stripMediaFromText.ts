/** Removes Markdown image syntax and HTML img tags (no images in UI). */
export function stripMediaFromText(text: string): string {
  return text.replace(/!\[[^\]]*]\([^)]+\)/g, '').replace(/<img\b[^>]*>/gi, '');
}
