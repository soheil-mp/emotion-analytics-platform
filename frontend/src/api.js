import axios from 'axios';

// Dynamically determine API base URL
const getApiBaseUrl = () => {
  // If environment variable is set, use it
  // if (process.env.REACT_APP_API_BASE_URL) {
  //   console.log('Using environment API URL:', process.env.REACT_APP_API_BASE_URL);
  //   return process.env.REACT_APP_API_BASE_URL;
  // }

  // Otherwise, dynamically construct based on current window location
  const { protocol, hostname, port } = window.location;

  console.log('Window location details:', { protocol, hostname, port });

  // If running on localhost, use localhost:3120
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    const url = 'http://localhost:3120';
    console.log('Using localhost API URL:', url);
    return url;
  }

  // Otherwise, use the same hostname with port 3120
  const url = `${protocol}//${hostname}:3120`;
  console.log('Using dynamic API URL:', url);
  return url;
};

const API_BASE_URL = getApiBaseUrl();
console.log('Final API_BASE_URL:', API_BASE_URL);

// Submit a YouTube video URL for analysis
export const analyzeVideo = async (youtubeUrl) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/predict`, {
      url: youtubeUrl
    });
    return response.data;
  } catch (error) {
    console.error('Error analyzing video:', error);
    throw error;
  }
};

// Get analysis results for a specific video
export const getVideoAnalysis = async (videoId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/analysis/${videoId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching analysis:', error);
    throw error;
  }
};

// Submit feedback for emotion predictions
export const saveFeedback = async (feedbackData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/save-feedback`, feedbackData);
    return response.data;
  } catch (error) {
    console.error('Error saving feedback:', error);
    throw error;
  }
};
