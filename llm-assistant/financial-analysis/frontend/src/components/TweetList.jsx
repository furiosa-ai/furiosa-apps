import React from 'react';
import logoImage from '../assets/Symbol.png';

const TweetList = ({ queues, isProcessing, processingEnabled, onStartProcessing, onStopProcessing, requestsPerSecond, onRpsChange, completedCount }) => {
  const renderTweet = (tweet, status) => (
    <div key={`${status}-${tweet.id}`} className={`tweet-item ${status}`}>
      <div className="tweet-text">
        {tweet.text.substring(0, 120)}
        {tweet.text.length > 120 && '...'}
      </div>
      <div className={`tweet-status ${status}`}>
        {status === 'completed' && tweet.company && (
          <span className="tweet-result">
            {tweet.company === '????' ? '????' : `$${tweet.company}`} - {tweet.sentiment}
          </span>
        )}
        <div className="status-label">{status}</div>
      </div>
    </div>
  );

  return (
    <div className="left-panel">
      <div className="logo-section">
        <img src={logoImage} alt="logo" className="logo" />
      </div>

      <h1 className="sidebar-title">
        Financial Sentiment Analysis
      </h1>

      <p className="sidebar-subtitle">Real-time Processing with RNGD</p>

      <hr className="divider" />

      <div className="controls">
        <div className="control-group">
          <label className="section-label">Request Speed</label>
          <div className="slider-container">
            <input
              type="range"
              min="1"
              max="30"
              step="1"
              value={requestsPerSecond}
              onChange={(e) => onRpsChange(parseFloat(e.target.value))}
              onInput={(e) => onRpsChange(parseFloat(e.target.value))}
              disabled={false}
            />
            <div className="slider-marks">
              <span>-</span>
              <span>+</span>
            </div>
          </div>
        </div>

        <div className="control-group">
          {!processingEnabled ? (
            <button onClick={onStartProcessing}>
              Start Processing
            </button>
          ) : (
            <button onClick={onStopProcessing}>
              Stop Processing
            </button>
          )}
        </div>

        <div className="control-group">
          <div className="section-label">Active Requests</div>
          <div className="stat-value">{queues.processing.length}</div>
        </div>

        <div className="control-group">
          <div className="section-label">Completed</div>
          <div className="stat-value">{completedCount}</div>
        </div>

      </div>

    </div>
  );
};

export default TweetList;
