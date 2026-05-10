import { describe, expect, it } from 'vitest';
import { renderArticleMarkdown } from './renderArticleMarkdown';

describe('renderArticleMarkdown', () => {
  it('renders headings and does not emit raw script tags', () => {
    const html = renderArticleMarkdown('## Titel\n\nHallo **du**.');
    expect(html).toContain('Titel');
    expect(html).toContain('<strong>');
    expect(html).not.toMatch(/<script/i);
  });

  it('strips markdown image syntax before render (no image URL in output)', () => {
    const html = renderArticleMarkdown('Text ![](x.png) end.');
    expect(html).not.toContain('x.png');
    expect(html).toMatch(/Text\s+end/);
  });
});
