import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS } from 'chart.js/auto';

const NPUMetrics = ({ metrics }) => {
  // Keep last 20 data points for each metric
  const [historicalData, setHistoricalData] = useState({
    throughput: Array(20).fill(0),
    efficiency: Array(20).fill(0),
    power: Array(20).fill(0),
    temperature: Array(20).fill(25)
  });

  useEffect(() => {
    if (!metrics) return;

    // Update historical data with new metrics
    setHistoricalData(prev => ({
      throughput: [...prev.throughput.slice(1), metrics.throughput],
      efficiency: [...prev.efficiency.slice(1), metrics.efficiency],
      power: [...prev.power.slice(1), metrics.power],
      temperature: [...prev.temperature.slice(1), metrics.temperature]
    }));
  }, [metrics]);

  const defaultMetrics = {
    throughput: 0,
    efficiency: 0,
    power: 0,
    temperature: 25
  };

  const currentMetrics = metrics || defaultMetrics;

  // Chart configurations matching ref_frontend
  const chartOptions = {
    responsive: false,
    plugins: {
      legend: { display: false },
      tooltip: { enabled: false },
      customCanvasBackgroundColor: {
        color: '#000',
      }
    },
    animation: false,
    stacked: false,
    scales: {
      x: { display: false, border: { display: false } },
      y: { border: { display: false }, beginAtZero: true, position: 'left' }
    }
  };

  const chartDataThroughput = {
    labels: historicalData.throughput.map(() => ""),
    datasets: [
      { data: historicalData.throughput, borderColor: '#70e697', yAxisID: 'y', pointStyle: false },
    ]
  };

  const chartDataEfficiency = {
    labels: historicalData.efficiency.map(() => ""),
    datasets: [
      { data: historicalData.efficiency, borderColor: '#cdbbff', yAxisID: 'y', pointStyle: false },
    ]
  };

  const chartDataPower = {
    labels: historicalData.power.map(() => ""),
    datasets: [
      { data: historicalData.power, borderColor: '#fec2a0', yAxisID: 'y', pointStyle: false },
    ]
  };

  const chartDataTemperature = {
    labels: historicalData.temperature.map(() => ""),
    datasets: [
      { data: historicalData.temperature, borderColor: '#fffa82', yAxisID: 'y', pointStyle: false },
    ]
  };

  return (
    <div className="npu-metrics">
      <div className="metric-card">
        <div className="metric-header">Throughput</div>
        <div className="metric-chart">
          <Line data={chartDataThroughput} options={chartOptions} />
        </div>
        <div className="metric-detail">
          <span className="metric-value metric-green">{currentMetrics.throughput}</span>
          <span className="metric-unit">token/s</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-header">Efficiency</div>
        <div className="metric-chart">
          <Line data={chartDataEfficiency} options={chartOptions} />
        </div>
        <div className="metric-detail">
          <span className="metric-value metric-purple">{currentMetrics.efficiency.toFixed(2)}</span>
          <span className="metric-unit">tok/s/W</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-header">Power</div>
        <div className="metric-chart">
          <Line data={chartDataPower} options={chartOptions} />
        </div>
        <div className="metric-detail">
          <span className="metric-value metric-orange">{currentMetrics.power}</span>
          <span className="metric-unit">watt</span>
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-header">Temperature</div>
        <div className="metric-chart">
          <Line data={chartDataTemperature} options={chartOptions} />
        </div>
        <div className="metric-detail">
          <span className="metric-value metric-yellow">{currentMetrics.temperature}</span>
          <span className="metric-unit">°C</span>
        </div>
      </div>
    </div>
  );
};

export default NPUMetrics;
