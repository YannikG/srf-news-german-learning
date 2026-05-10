import DOMPurify from 'dompurify';
import { marked } from 'marked';
import { stripMediaFromText } from '@/utils/stripMediaFromText';

let optionsApplied = false;

function ensureMarkedOptions(): void {
  if (optionsApplied) return;
  optionsApplied = true;
  marked.use({ gfm: true, breaks: true });
}

/** Renders Markdown to sanitized HTML (no scripts; media stripped in preprocessing). */
export function renderArticleMarkdown(markdown: string): string {
  ensureMarkedOptions();
  const cleaned = stripMediaFromText(markdown);
  const parsed = marked.parse(cleaned);
  if (typeof parsed !== 'string') {
    throw new Error('marked.parse returned non-string; async mode is not supported here');
  }
  return DOMPurify.sanitize(parsed, { USE_PROFILES: { html: true } });
}
