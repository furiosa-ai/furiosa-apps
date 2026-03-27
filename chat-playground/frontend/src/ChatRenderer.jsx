import React, { useLayoutEffect, useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'

// Helper function to detect RTL characters (Arabic, Hebrew)
const hasRTLChars = (text) => {
  if (!text) return false;
  const rtlRegex = /[\u0590-\u05FF\u0600-\u06FF\u0750-\u077F]/;
  return rtlRegex.test(text);
};

// Helper function to extract text content from React children (recursive)
const extractTextFromChildren = (children) => {
  if (typeof children === 'string') {
    return children;
  }
  if (Array.isArray(children)) {
    return children.map(extractTextFromChildren).join(' ');
  }
  if (children && typeof children === 'object' && children.props) {
    return extractTextFromChildren(children.props.children);
  }
  return '';
};

// Helper function to determine text direction for content
const getContentDirection = (children, isRTLMode) => {
  if (!isRTLMode) return 'ltr';
  const text = extractTextFromChildren(children);
  return hasRTLChars(text) ? 'rtl' : 'ltr';
};

export default function ChatRenderer({ messages, fontSize = 1, isRTL = false }) {
  const messageList = Object.values(messages).sort((a, b) => (b.gi || 0) - (a.gi || 0))
  const scrollContainerRef = useRef(null)
  const [isUserScrolling, setIsUserScrolling] = useState(false)
  const autoScrollingRef = useRef(false);


  // Detect if user has scrolled manually
  const handleScroll = () => {
    if (!scrollContainerRef.current) return
    if (autoScrollingRef.current) return;

    const container = scrollContainerRef.current
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
    console.log( container.scrollHeight - container.scrollTop - container.clientHeight )

    // If user is near bottom, re-enable auto-scroll
    if (isNearBottom) {
      setIsUserScrolling(false)
      console.log('set user scroll false')
    } else {
      setIsUserScrolling(true)
      console.log('set user scroll true')
    }
  }

  useLayoutEffect(() => {
    const el = scrollContainerRef.current;
    if (!el || isUserScrolling) return;

    autoScrollingRef.current = true;

    const delta = el.scrollHeight - (el.scrollTop + el.clientHeight);
    const behavior = delta < 1000 ? 'auto' : 'auto';

    requestAnimationFrame(() => {
      el.scrollTo({ top: el.scrollHeight , behavior });
      const clear = () => { autoScrollingRef.current = false; };
      el.addEventListener('scrollend', clear, { once: true });
    });

  }, [messages, isUserScrolling]);


  if (messageList.length === 0) {
    return (
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        style={{
        height: '100%',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        direction: isRTL ? 'rtl' : 'ltr'
      }} />
    )
  }

  // Show only the most recent message
  const latestMessage = messageList[0]

  return (
    <div
      ref={scrollContainerRef}
      onScroll={handleScroll}
      style={{
        height: '100%',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
        direction: isRTL ? 'rtl' : 'ltr'
      }}>
      <div style={{ marginBottom: '15px' }}>
        <div style={{
          background: '#2b2b2b',
          borderRadius: '1.5rem',
          padding: '12px 18px',
          display: 'inline-block',
          minWidth: 'min-content',
          maxWidth: '100%'
        }}>
          <div style={{ color: '#fff', margin: 0, fontSize: '1.1em', fontWeight: '600' }}>
            {latestMessage.user_message}
          </div>
        </div>
      </div>

      <div style={{ color: '#ccc', lineHeight: '1.6', fontSize: '14px', flex: 1, paddingBottom: '40px' }}>
        {/* Reasoning Box - Only show if there's reasoning content */}
        {latestMessage.reasoning_chunks && latestMessage.reasoning_chunks.length > 0 && (
          <div style={{
            marginBottom: '15px',
            padding: '12px 16px',
            borderLeft: '1px solid #666',
            display: 'inline-block',
            minWidth: 'fit-content',
            maxWidth: '100%'
          }}>
            <div style={{
              color: '#ccc',
              fontSize: `${fontSize*0.875}rem`,
              lineHeight: '1.6',
              fontFamily: 'monospace'
            }}>
              {latestMessage.reasoning_chunks.join('')}
            </div>
          </div>
        )}
        {/*
          remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex, rehypeRaw]} // keep both
            */}

        <ReactMarkdown
          remarkPlugins={[remarkGfm]}

          components={{
            // Style markdown elements for dark theme with intelligent RTL/LTR
            h1: ({node, children, ...props}) => {
              const direction = getContentDirection(children, isRTL);
              return <h1 style={{color: '#fff', fontSize: '1.5em', marginBottom: '0.5em', direction, textAlign: direction === 'rtl' ? 'right' : 'left'}} {...props}>{children}</h1>;
            },
            h2: ({node, children, ...props}) => {
              const direction = getContentDirection(children, isRTL);
              return <h2 style={{color: '#fff', fontSize: '1.3em', marginBottom: '0.5em', direction, textAlign: direction === 'rtl' ? 'right' : 'left'}} {...props}>{children}</h2>;
            },
            h3: ({node, children, ...props}) => {
              const direction = getContentDirection(children, isRTL);
              return <h3 style={{color: '#fff', fontSize: '1.1em', marginBottom: '0.5em', direction, textAlign: direction === 'rtl' ? 'right' : 'left'}} {...props}>{children}</h3>;
            },
            p: ({node, children, ...props}) => {
              const direction = getContentDirection(children, isRTL);
              return <p style={{color: '#ccc', marginBottom: '1em', fontSize: `${fontSize}rem`, lineHeight: '1.6', direction, textAlign: direction === 'rtl' ? 'right' : 'left'}} {...props}>{children}</p>;
            },
            // Code blocks should ALWAYS be LTR
            code: ({node, inline, ...props}) =>
              inline
                ? <code style={{background: '#333', padding: '2px 4px', borderRadius: '3px', color: '#fff', direction: 'ltr', unicodeBidi: 'embed'}} {...props} />
                : <code style={{background: '#222', padding: '1em', borderRadius: '6px', display: 'block', color: '#fff', overflowX: 'auto', direction: 'ltr', textAlign: 'left'}} {...props} />,
            pre: ({node, ...props}) => <pre style={{background: '#222', padding: '1em', borderRadius: '6px', overflowX: 'auto', direction: 'ltr', textAlign: 'left'}} {...props} />,
            strong: ({node, children, ...props}) => {
              const direction = getContentDirection(children, isRTL);
              return <strong style={{color: '#fff', direction}} {...props}>{children}</strong>;
            },
            em: ({node, children, ...props}) => {
              const direction = getContentDirection(children, isRTL);
              return <em style={{color: '#ddd', direction}} {...props}>{children}</em>;
            },
            ul: ({node, ...props}) => <ul style={{color: '#ccc', paddingLeft: isRTL ? '0' : '1.5em', paddingRight: isRTL ? '1.5em' : '0'}} {...props} />,
            ol: ({node, ...props}) => <ol style={{color: '#ccc', paddingLeft: isRTL ? '0' : '1.5em', paddingRight: isRTL ? '1.5em' : '0'}} {...props} />,
            li: ({node, children, ...props}) => {
              const direction = getContentDirection(children, isRTL);
              return <li style={{marginBottom: '0.5em', direction, textAlign: direction === 'rtl' ? 'right' : 'left'}} {...props}>{children}</li>;
            },
            blockquote: ({node, children, ...props}) => {
              const direction = getContentDirection(children, isRTL);
              const borderSide = direction === 'rtl' ? 'borderRight' : 'borderLeft';
              const paddingSide = direction === 'rtl' ? 'paddingRight' : 'paddingLeft';
              return <blockquote style={{[borderSide]: '4px solid #666', [paddingSide]: '1em', margin: '1em 0', fontStyle: 'italic', color: '#aaa', direction, textAlign: direction === 'rtl' ? 'right' : 'left'}} {...props}>{children}</blockquote>;
            },
            // URLs should always be LTR
            a: ({node, ...props}) => <a style={{color: '#66d9ff', direction: 'ltr', unicodeBidi: 'embed'}} {...props} />
          }}
        >
          {(latestMessage.chunks || []).join('')}
        </ReactMarkdown>
        {latestMessage.failed && (
          <div style={{ color: '#ff6666' }}>Error: {latestMessage.failed}</div>
        )}

        {/* Token usage display */}
        {(latestMessage.tokens_prompt || latestMessage.tokens_reasoning || latestMessage.tokens_response || latestMessage.tokens_total) && (
          <>
            <div style={{ height: '1em' }} />
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              fontSize: `${fontSize * 0.9}rem`,
              fontFamily: 'monospace'
            }}>
              {latestMessage.tokens_prompt && (
                <div>
                  <span style={{ color: '#76d6ff', fontFamily: 'monospace' }}>Tokens used for the prompt: </span>
                  <span style={{ color: '#fff', fontFamily: 'monospace' }}>{latestMessage.tokens_prompt}</span>
                </div>
              )}
              {latestMessage.tokens_reasoning && (
                <div>
                  <span style={{ color: '#76d6ff', fontFamily: 'monospace' }}>Tokens used for the reasoning: </span>
                  <span style={{ color: '#fff', fontFamily: 'monospace' }}>{latestMessage.tokens_reasoning}</span>
                </div>
              )}
              {latestMessage.tokens_response && (
                <div>
                  <span style={{ color: '#76d6ff', fontFamily: 'monospace' }}>Tokens used for the response: </span>
                  <span style={{ color: '#fff', fontFamily: 'monospace' }}>{latestMessage.tokens_response}</span>
                </div>
              )}
              {latestMessage.tokens_total && (
                <div>
                  <span style={{ color: '#76d6ff', fontFamily: 'monospace' }}>Total tokens: </span>
                  <span style={{ color: '#fff', fontFamily: 'monospace' }}>{latestMessage.tokens_total}</span>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
