import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';

interface Props {
  content: string;
}

export default function MarkdownRenderer({ content }: Props) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeHighlight]}
      components={{
        pre: ({ children, ...props }) => (
          <pre style={{ background: '#f6f8fa', padding: 12, borderRadius: 6, overflow: 'auto', fontSize: 13 }} {...props}>
            {children}
          </pre>
        ),
        code: ({ children, className, ...props }) => {
          const isInline = !className;
          if (isInline) {
            return <code style={{ background: '#f0f0f0', padding: '2px 6px', borderRadius: 3, fontSize: 13 }} {...props}>{children}</code>;
          }
          return <code className={className} {...props}>{children}</code>;
        },
        table: ({ children, ...props }) => (
          <table style={{ borderCollapse: 'collapse', width: '100%', margin: '8px 0' }} {...props}>{children}</table>
        ),
        th: ({ children, ...props }) => (
          <th style={{ border: '1px solid #d9d9d9', padding: '6px 12px', background: '#fafafa' }} {...props}>{children}</th>
        ),
        td: ({ children, ...props }) => (
          <td style={{ border: '1px solid #d9d9d9', padding: '6px 12px' }} {...props}>{children}</td>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
