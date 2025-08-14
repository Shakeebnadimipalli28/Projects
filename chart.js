// This script renders pie charts for sentiment and emotion breakdown on completion page

document.addEventListener('DOMContentLoaded', () => {
  fetch('/api/analytics')
    .then(res => res.json())
    .then(data => {
      // Sentiment Chart
      const sentimentCtx = document.getElementById('sentimentChart').getContext('2d');
      new Chart(sentimentCtx, {
        type: 'pie',
        data: {
          labels: Object.keys(data.sentiment_counts),
          datasets: [{
            label: 'Sentiment Distribution',
            data: Object.values(data.sentiment_counts),
            backgroundColor: ['#3498db', '#e74c3c', '#95a5a6']
          }]
        }
      });
      // Emotion Chart
      const emotionCtx = document.getElementById('emotionChart').getContext('2d');
      new Chart(emotionCtx, {
        type: 'bar',
        data: {
          labels: Object.keys(data.emotion_counts),
          datasets: [{
            label: 'Facial Emotion Counts',
            data: Object.values(data.emotion_counts),
            backgroundColor: '#9b59b6'
          }]
        },
        options: {
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    });
});
