import React from 'react';
import { renderMarkdown } from '../utils/mdRenderer';

interface MarkdownBodyProps {
  content: string | null | undefined;
  className?: string;
}

export const MarkdownBody: React.FC<MarkdownBodyProps> = ({ content, className = '' }) => (
  <div
    className={`markdown-body ${className}`.trim()}
    dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
  />
);
