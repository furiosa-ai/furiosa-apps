import React, { useState, useEffect, useCallback } from 'react';
import TweetList from './components/TweetList';
import CurrentTweet from './components/CurrentTweet';
import SentimentChart from './components/SentimentChart';
import NPUMetrics from './components/NPUMetrics';

function App() {
  const [tweets, setTweets] = useState([]);
  const [currentTweet, setCurrentTweet] = useState(null);
  const [sentimentData, setSentimentData] = useState([]);
  const [npuMetrics, setNpuMetrics] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingEnabled, setProcessingEnabled] = useState(false);
  const [requestsPerSecond, setRequestsPerSecond] = useState(50.0);
  const [websocket, setWebsocket] = useState(null);
  const [completedCount, setCompletedCount] = useState(0);

  const connectWebSocket = useCallback(() => {
    // Use the same host as the current page
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('Connected to WebSocket');
      setWebsocket(ws);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'initial_state':
          // Full state on initial connection
          setTweets(message.data.tweets);
          setProcessingEnabled(message.data.processing_enabled);
          setRequestsPerSecond(message.data.requests_per_second);
          setIsProcessing(message.data.processing_enabled && message.data.tweets.some(t => t.status === 'processing'));
          setCompletedCount(message.data.tweets.filter(t => t.status === 'completed').length);
          break;

        case 'config_update':
          // Configuration changes only
          setProcessingEnabled(message.data.processing_enabled);
          setRequestsPerSecond(message.data.requests_per_second);
          setIsProcessing(message.data.processing_enabled && tweets.some(t => t.status === 'processing'));
          break;

        case 'tweet_update':
          // Single tweet status change
          const updatedTweet = message.data;
          setTweets(prevTweets => {
            const existingTweet = prevTweets.find(t => t.id === updatedTweet.id);

            let newTweets;
            if (existingTweet) {
              // Update existing tweet by merging data
              newTweets = prevTweets.map(t =>
                t.id === updatedTweet.id ? { ...t, ...updatedTweet } : t
              );
            } else {
              // Add new tweet
              newTweets = [...prevTweets, updatedTweet];
            }

            // Count completed tweets only if status changed to completed
            if (updatedTweet.status === 'completed' && existingTweet?.status !== 'completed') {
              setCompletedCount(prev => prev + 1);
            }
            return newTweets;
          });
          break;

        case 'tweets_removed':
          // Multiple tweets removed
          const removedIds = message.data.tweet_ids;
          setTweets(prevTweets =>
            prevTweets.filter(t => !removedIds.includes(t.id))
          );
          break;

        case 'tweets_cleared':
          // All tweets cleared (stop processing)
          setTweets([]);
          setCurrentTweet(null);
          break;

        case 'current_tweet':
          console.log('Received current_tweet:', message.data);
          setCurrentTweet(message.data);
          break;

        case 'sentiment_data':
          setSentimentData(prevData => [...prevData, message.data]);
          break;

        case 'npu_metrics':
          setNpuMetrics(message.data);
          break;

        default:
          console.log('Unknown message type:', message.type);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWebsocket(null);
      // Attempt to reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return ws;
  }, []);

  useEffect(() => {
    const ws = connectWebSocket();

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [connectWebSocket]);

  // Cleanup is now handled by backend with incremental updates

  const handleStartProcessing = () => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'start_processing'
      }));
      setSentimentData([]); // Clear previous data
      setCurrentTweet(null);
      setCompletedCount(0); // Reset completed counter
    }
  };

  const handleStopProcessing = () => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'stop_processing'
      }));
    }
  };

  const handleRpsChange = (newRps) => {
    setRequestsPerSecond(newRps);
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'set_rps',
        rps: newRps
      }));
    }
  };

  // Create queues from tweets array
  const queues = {
    pending: tweets.filter(t => t.status === 'pending' || t.status === 'queuing'),
    processing: tweets.filter(t => t.status === 'processing'),
    completed: tweets.filter(t => t.status === 'completed')
  };

  return (
    <div className="app">
      <TweetList
        queues={queues}
        isProcessing={isProcessing}
        processingEnabled={processingEnabled}
        onStartProcessing={handleStartProcessing}
        onStopProcessing={handleStopProcessing}
        requestsPerSecond={requestsPerSecond}
        onRpsChange={handleRpsChange}
        completedCount={completedCount}
      />

      <div className="center-panel">
        <div className="main-content">
          <div className="left-center">
            {/* Three Equal-Width Queues */}
            <div className="three-column-queues">
              {/* Pending Queue */}
              <div className="queue-section third-width">
                <div className="queue-header pending">
                  <span className="queue-title">Pending</span>
                  <span className="queue-count">({queues.pending.length})</span>
                </div>
                <div className="queue-list">
                  {queues.pending.map((tweet) => (
                    <div key={`pend-${tweet.id}`} className="tweet-item pending">
                      <div className="tweet-text">
                        {tweet.text.substring(0, 80)}
                        {tweet.text.length > 80 && '...'}
                      </div>
                    </div>
                  ))}
                  {queues.pending.length === 0 && (
                    <div className="queue-empty">No pending tweets</div>
                  )}
                </div>
              </div>

              {/* Processing Queue */}
              <div className="queue-section third-width">
                <div className="queue-header processing">
                  <span className="queue-title">Processing</span>
                  <span className="queue-count">({queues.processing.length})</span>
                </div>
                <div className="queue-list">
                  {queues.processing.map((tweet) => (
                    <div key={`proc-${tweet.id}`} className="tweet-item processing">
                      <div className="tweet-text">
                        {tweet.text.substring(0, 80)}
                        {tweet.text.length > 80 && '...'}
                      </div>
                    </div>
                  ))}
                  {queues.processing.length === 0 && (
                    <div className="queue-empty">No tweets processing</div>
                  )}
                </div>
              </div>

              {/* Completed Queue */}
              <div className="queue-section third-width">
                <div className="queue-header completed">
                  <span className="queue-title">Completed</span>
                </div>
                <div className="queue-list">
                  {queues.completed.map((tweet) => (
                    <div key={`comp-${tweet.id}`} className="tweet-item completed">
                      <div className="tweet-text">
                        {tweet.text.substring(0, 80)}
                        {tweet.text.length > 80 && '...'}
                      </div>
                      <div className="tweet-result">
                        <span className="company">{tweet.company === '????' ? '????' : `$${tweet.company}`}</span> - <span className={`sentiment-${tweet.sentiment}`}>{tweet.sentiment}</span>
                      </div>
                    </div>
                  ))}
                  {queues.completed.length === 0 && (
                    <div className="queue-empty">No completed tweets</div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="right-center">
            <div style={{ height: '100%', width: '100%', position: 'relative' }}>
              {/* Current Analysis at Top */}
              <CurrentTweet currentTweet={currentTweet} tweets={tweets} />

              {/* Sentiment Chart Below */}
              <SentimentChart sentimentData={sentimentData} />
            </div>

          </div>
        </div>

        <NPUMetrics metrics={npuMetrics} />
      </div>
    </div>
  );
}

export default App;
