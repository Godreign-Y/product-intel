// Convert markdown-like headers and tables in AI text to basic HTML elements
export const renderMarkdown = (text: string | null | undefined): string => {
  if (!text) return '';
  let processed = text
    .replace(/### (.*)/g, '<h4>$1</h4>')
    .replace(/## (.*)/g, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
    
  // Handle list items
  processed = processed.replace(/^\s*[\*\-]\s+(.*)/gm, '<li>$1</li>');
  
  // Wrap consecutive list items
  const lines = processed.split('\n');
  let inList = false;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('<li>') && !inList) {
      lines[i] = '<ul>' + lines[i];
      inList = true;
    } else if (!lines[i].startsWith('<li>') && inList) {
      lines[i - 1] = lines[i - 1] + '</ul>';
      inList = false;
    }
  }
  if (inList) lines[lines.length - 1] = lines[lines.length - 1] + '</ul>';
  
  // Parse tables
  let inTable = false;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].startsWith('|') && lines[i].endsWith('|')) {
      const cells = lines[i].split('|').map(c => c.trim()).filter(c => c !== '');
      
      // Check if header line or separator
      if (lines[i].includes('---')) {
        lines[i] = ''; // skip separator
        continue;
      }
      
      const isHeader = (i > 0 && lines[i-1].includes('---')) || (i === 0 && lines[i+1]?.includes('---'));
      const cellTag = isHeader ? 'th' : 'td';
      
      let rowContent = `<tr>${cells.map(c => `<${cellTag}>${c}</${cellTag}>`).join('')}</tr>`;
      
      if (!inTable) {
        rowContent = `<table><thead>${rowContent}</thead><tbody>`;
        inTable = true;
      }
      lines[i] = rowContent;
    } else if (inTable) {
      lines[i-1] = lines[i-1] + '</tbody></table>';
      inTable = false;
    }
  }
  
  return lines.join('\n');
};
