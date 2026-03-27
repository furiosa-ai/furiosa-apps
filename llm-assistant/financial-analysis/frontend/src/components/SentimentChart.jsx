import React, { useRef, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const SentimentChart = ({ sentimentData }) => {
  const chartRef = useRef();

  // Process sentiment data to get company stats
  const processChartData = () => {
    const companyStats = {};

    sentimentData.forEach(item => {
      if (!item.company || item.company === '????' || item.sentiment === 'not_detected') {
        return;
      }

      if (!companyStats[item.company]) {
        companyStats[item.company] = { positive: 0, negative: 0, total: 0 };
      }

      companyStats[item.company].total++;
      if (item.sentiment === 'positive') {
        companyStats[item.company].positive++;
      } else if (item.sentiment === 'negative') {
        companyStats[item.company].negative++;
      }
    });

    // Convert to chart format with centered bars
    const companies = Object.keys(companyStats);
    const positiveData = [];
    const negativeData = [];

    companies.forEach(company => {
      const stats = companyStats[company];
      const positivePercent = stats.total > 0 ? (stats.positive / stats.total) * 100 : 0;
      const negativePercent = stats.total > 0 ? (stats.negative / stats.total) * 100 : 0;

      positiveData.push(positivePercent);
      negativeData.push(-negativePercent); // Negative values for left side
    });

    return {
      labels: companies,
      datasets: [
        {
          label: 'Negative',
          data: negativeData,
          backgroundColor: '#ff4444',
          borderColor: '#ff4444',
          borderWidth: 1,
          stack: 'sentiment'
        },
        {
          label: 'Positive',
          data: positiveData,
          backgroundColor: '#00aa00',
          borderColor: '#00aa00',
          borderWidth: 1,
          stack: 'sentiment'
        },
      ],
    };
  };

  const options = {
    indexAxis: 'y', // This makes it horizontal
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        stacked: true,
        min: -100,
        max: 100,
        display: false, // Hide x-axis completely
        grid: {
          display: false,
        },
      },
      y: {
        stacked: true,
        ticks: {
          color: '#fff', // Keep company names visible
        },
        grid: {
          display: false, // Hide grid lines
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const value = Math.abs(context.raw);
            const sentiment = context.raw >= 0 ? 'Positive' : 'Negative';
            return `${sentiment}: ${value.toFixed(1)}%`;
          }
        }
      }
    },
    interaction: {
      intersect: false,
      mode: 'index',
    },
  };

  const chartData = processChartData();

  // Calculate dynamic height based on number of companies
  const baseHeight = 30; // Height per bar
  const minHeight = 80; // Minimum chart height for single items
  const padding = 60; // Space for legend, labels, etc.
  // For single item, use smaller calculation
  const calculatedHeight = chartData.labels.length === 1
    ? minHeight
    : Math.max(minHeight, chartData.labels.length * baseHeight + padding);

  return (
    <div className="sentiment-chart-section">
      <div className="section-label">Company Sentiment Distribution</div>
      <div className="metric-chart" style={{ height: `${calculatedHeight}px`, position: 'relative' }}>
        {chartData.labels.length > 0 ? (
          <Bar ref={chartRef} data={chartData} options={options} />
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#888',
            fontSize: '14px'
          }}>
            No detected sentiment data available yet
          </div>
        )}
      </div>
    </div>
  );
};

export default SentimentChart;
