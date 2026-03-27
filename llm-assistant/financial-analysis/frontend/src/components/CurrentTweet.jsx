import React, { useState, useEffect, useRef } from 'react';

const CurrentTweet = ({ currentTweet }) => {
  const [displayTweet, setDisplayTweet] = useState(null);
  const [displayText, setDisplayText] = useState('');
  const [textIndex, setTextIndex] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);
  const typingTimeoutRef = useRef(null);

  // Copy currentTweet to displayTweet when ready to animate
  useEffect(() => {
    if (!displayTweet && currentTweet && !isAnimating) {
      setDisplayTweet(currentTweet);
    }
  }, [currentTweet, displayTweet, isAnimating]);

  // Animate displayTweet when it's set
  useEffect(() => {
    if (!displayTweet) {
      setIsAnimating(false);
      return;
    }

    setIsAnimating(true);

    // Clear any existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Start typing animation
    setDisplayText('');
    setTextIndex(0);
    setShowResults(false);

    const text = displayTweet.text;
    const words = text.split(' ');
    let wordIndex = 0;

    const typeNextWord = () => {
      const currentText = words.slice(0, wordIndex + 1).join(' ');
      setDisplayText(currentText);
      setTextIndex(currentText.length);
      wordIndex++;

      if (wordIndex < words.length) {
        typingTimeoutRef.current = setTimeout(typeNextWord, 50);
      } else {
        // Typing finished, show results
        setTimeout(() => {
          setShowResults(true);
          // After 5 seconds, clear displayTweet to start cycle again
          setTimeout(() => {
            setDisplayTweet(null);
            setIsAnimating(false);
          }, 5000);
        }, 500);
      }
    };

    // Start typing immediately
    typeNextWord();

    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, [displayTweet]);


  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return '#00aa00';
      case 'negative': return '#aa0000';
      case 'neutral': return '#888';
      case 'not_detected': return '#f59e0b';
      default: return '#888';
    }
  };

  if (!displayTweet) {
    return (
      <div className="current-tweet-section">
        <div className="section-label">Latest Analysis</div>
        <div className="current-tweet-card">
          <div className="tweet-content">
            Waiting for processing to start...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="current-tweet-section">
      <div className="section-label">Latest Analysis</div>
      <div className="current-tweet-card">
        <div className="tweet-content">
          {displayText}
          {textIndex < (displayTweet?.text?.length || 0) && (
            <span style={{ opacity: 0.5 }}>|</span>
          )}
        </div>

        {showResults && displayTweet && (
          <div className="tweet-analysis">
            <div className="analysis-item">
              <div className="analysis-label">Company</div>
              <div className="analysis-value" style={{ color: '#61dafb' }}>
                {displayTweet.company === '????' ? '????' : `$${displayTweet.company}`}
              </div>
            </div>

            <div className="analysis-item">
              <div className="analysis-label">Sentiment</div>
              <div
                className="analysis-value"
                style={{ color: getSentimentColor(displayTweet.sentiment) }}
              >
                {displayTweet.sentiment.toUpperCase()}
              </div>
            </div>

            <div className="analysis-item">
              <div className="analysis-label">Confidence</div>
              <div className="analysis-value" style={{ color: '#fff' }}>
                {displayTweet.sentiment === 'not_detected' ? 'N/A' : `${Math.round(displayTweet.confidence * 100)}%`}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CurrentTweet;
