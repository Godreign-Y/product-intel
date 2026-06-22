function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatInline(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>');
}

function isSectionTitle(line: string): boolean {
  const t = line.trim();
  return (
    t.length > 0 &&
    t.length < 48 &&
    /^[A-Z][A-Za-z0-9\s&]+$/.test(t) &&
    !t.includes(':') &&
    !t.startsWith('|')
  );
}

/** Render markdown-like report text into structured HTML for UI surfaces */
export const renderMarkdown = (text: string | null | undefined): string => {
  if (!text) return '';

  const codeBlocks: string[] = [];
  let src = text.replace(/`{2,3}(\w*)\n?([\s\S]*?)`{2,3}/g, (_, lang: string, code: string) => {
    const idx = codeBlocks.length;
    const formatted = escapeHtml(code.trim())
      .replace(/\s*-->\s*/g, '\n  → ')
      .replace(/\n/g, '<br/>');
    codeBlocks.push(
      `<pre class="md-pre"><code class="md-code-block${lang ? ` language-${lang}` : ''}">${formatted}</code></pre>`
    );
    return `\n__CODE_${idx}__\n`;
  });

  const lines = src.split('\n');
  const parts: string[] = [];
  let listBuf: string[] = [];
  let tableBuf: string[] = [];

  const flushList = () => {
    if (listBuf.length) {
      parts.push(`<ul class="md-ul">${listBuf.map((l) => `<li class="md-li">${formatInline(l)}</li>`).join('')}</ul>`);
      listBuf = [];
    }
  };

  const flushTable = () => {
    if (tableBuf.length) {
      parts.push(parseTable(tableBuf));
      tableBuf = [];
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      flushList();
      flushTable();
      continue;
    }

    const codeMatch = line.match(/^__CODE_(\d+)__$/);
    if (codeMatch) {
      flushList();
      flushTable();
      parts.push(codeBlocks[Number(codeMatch[1])]);
      continue;
    }

    if (line.startsWith('|') && line.endsWith('|')) {
      flushList();
      tableBuf.push(line);
      continue;
    }

    flushTable();

    if (/^#\s+/.test(line)) {
      flushList();
      parts.push(`<h1 class="md-h1">${formatInline(line.replace(/^#\s+/, ''))}</h1>`);
    } else if (/^##\s+/.test(line)) {
      flushList();
      parts.push(`<h2 class="md-h2">${formatInline(line.replace(/^##\s+/, ''))}</h2>`);
    } else if (/^###\s+/.test(line)) {
      flushList();
      parts.push(`<h3 class="md-h3">${formatInline(line.replace(/^###\s+/, ''))}</h3>`);
    } else if (isSectionTitle(line)) {
      flushList();
      parts.push(`<h2 class="md-h2">${formatInline(line)}</h2>`);
    } else if (/^\s*[\*\-]\s+/.test(line)) {
      listBuf.push(line.replace(/^\s*[\*\-]\s+/, ''));
    } else if (/^[A-Za-z][^:]{0,44}:\s/.test(line)) {
      flushList();
      const colon = line.indexOf(':');
      parts.push(
        `<div class="md-kv"><span class="md-kv-label">${escapeHtml(line.slice(0, colon))}</span><span class="md-kv-value">${formatInline(line.slice(colon + 1).trim())}</span></div>`
      );
    } else {
      flushList();
      parts.push(`<p class="md-p">${formatInline(line)}</p>`);
    }
  }

  flushList();
  flushTable();

  return `<div class="md-content">${parts.join('')}</div>`;
};

function parseTable(lines: string[]): string {
  const rows = lines.filter((l) => l.trim() && !l.includes('---'));
  if (!rows.length) return '';

  const parseRow = (line: string) =>
    line
      .split('|')
      .map((c) => c.trim())
      .filter((c) => c !== '');

  const header = parseRow(rows[0]);
  const body = rows.slice(1).map(parseRow);

  const thead = `<thead><tr>${header.map((c) => `<th>${formatInline(c)}</th>`).join('')}</tr></thead>`;
  const tbody = `<tbody>${body.map((r) => `<tr>${r.map((c) => `<td>${formatInline(c)}</td>`).join('')}</tr>`).join('')}</tbody>`;
  return `<div class="md-table-wrap"><table class="md-table">${thead}${tbody}</table></div>`;
}
