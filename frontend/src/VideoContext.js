import React, { createContext, useContext, useState, useEffect } from 'react';
import { analyzeVideo } from './api';
import { processEmotionData, timeStringToSeconds } from './utils';

// Create context
const VideoContext = createContext();

// Hook to use video context
export const useVideo = () => {
  return useContext(VideoContext);
};

// Provider component
export const VideoProvider = ({ children }) => {
  const [videoUrl, setVideoUrl] = useState('');
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [videoHistory, setVideoHistory] = useState([]);
  const [fullAnalysisStorage, setFullAnalysisStorage] = useState({});

  // Convert API response data to internal format (time strings to seconds)
  const normalizeTranscriptData = (data) => {
    if (!data || !data.transcript) return data;

    const normalizedTranscript = data.transcript.map(item => ({
      ...item,
      start_time: typeof item.start_time === 'string' ? timeStringToSeconds(item.start_time) : item.start_time,
      end_time: typeof item.end_time === 'string' ? timeStringToSeconds(item.end_time) : item.end_time,
      // Also handle legacy 'start' and 'end' properties
      start: typeof item.start === 'string' ? timeStringToSeconds(item.start) : item.start,
      end: typeof item.end === 'string' ? timeStringToSeconds(item.end) : item.end,
    }));

    return {
      ...data,
      transcript: normalizedTranscript
    };
  };

  // Load existing history and analysis data from localStorage on component mount
  useEffect(() => {
    try {
      // Load video history
      const storedHistory = localStorage.getItem('videoAnalysisHistory');
      if (storedHistory) {
        setVideoHistory(JSON.parse(storedHistory));
      }

      // Load full analysis data cache
      const storedAnalysisData = localStorage.getItem('videoFullAnalysisData');
      if (storedAnalysisData) {
        setFullAnalysisStorage(JSON.parse(storedAnalysisData));
      }
    } catch (error) {
      console.error("Error loading data from localStorage:", error);
    }
  }, []);

  // Save full analysis data to localStorage
  const saveFullAnalysisToStorage = (videoId, data) => {
    try {
      // Make sure the transcript array always exists and has more than one sentence
      const safeData = {
        ...data,
        transcript: Array.isArray(data.transcript) ? data.transcript : []
      };

      const updatedStorage = {
        ...fullAnalysisStorage,
        [videoId]: safeData
      };

      setFullAnalysisStorage(updatedStorage);
      localStorage.setItem('videoFullAnalysisData', JSON.stringify(updatedStorage));
    } catch (error) {
      console.error("Error saving full analysis data to localStorage:", error);
    }
  };

  // Process video URL and get analysis
  const processVideo = async (url) => {
    if (!url) return;

    setVideoUrl(url);
    setIsLoading(true);
    setError(null);    try {
      // Real API call
      const result = await analyzeVideo(url);

      // Normalize time data from API response (convert time strings to seconds)
      const normalizedResult = normalizeTranscriptData(result);

      // Ensure result always has a transcript array
      const safeResult = {
        ...normalizedResult,
        transcript: Array.isArray(normalizedResult.transcript) ? normalizedResult.transcript : []
      };

      setAnalysisData(safeResult);

      // Store the full analysis data in storage
      saveFullAnalysisToStorage(safeResult.videoId, safeResult);

      // Add to history
      setVideoHistory(prev => {
        // Check if video with same URL already exists
        const existingVideoIndex = prev.findIndex(video => video.url.trim() === url.trim());

        // If it exists, remove it so we can add updated version to top
        const filteredHistory = existingVideoIndex >= 0
          ? [...prev.slice(0, existingVideoIndex), ...prev.slice(existingVideoIndex + 1)]
          : prev;

        const newHistory = [
          {
            id: result.videoId,
            title: result.title || 'Untitled Video',
            url: url,
            date: new Date().toISOString().split('T')[0],
            emotions: processEmotionData(result).emotionDistribution,
          },
          ...filteredHistory
        ];

        // Keep only the most recent 10 videos
        const updatedHistory = newHistory.slice(0, 10);

        // Save history to localStorage
        try {
          localStorage.setItem('videoAnalysisHistory', JSON.stringify(updatedHistory));
        } catch (error) {
          console.error("Error saving history to localStorage:", error);
        }

        return updatedHistory;
      });

    } catch (err) {
      console.error('Error processing video:', err);
      setError(err.message || 'Failed to process video');
    } finally {
      setIsLoading(false);
    }
  };

  // Load a video from history
  const loadFromHistory = (historyItem) => {
    setVideoUrl(historyItem.url);
    setIsLoading(true);

    setTimeout(() => {      // Check if we have full analysis data for this video
      if (fullAnalysisStorage[historyItem.id]) {
        // Use stored full analysis data, ensuring transcript property is handled properly
        const storedData = fullAnalysisStorage[historyItem.id];

        // Normalize time data in case it was stored in string format
        const normalizedData = normalizeTranscriptData(storedData);

        // Validate transcript data - make sure it has the required structure
        if (!normalizedData.transcript || !Array.isArray(normalizedData.transcript) || normalizedData.transcript.length === 0) {
          console.warn("Stored transcript is missing or empty, creating fallback");
          normalizedData.transcript = [{
            sentence: "Transcript data couldn't be loaded properly.",
            start_time: 1,
            end_time: 3,
            emotion: Object.keys(historyItem.emotions)[0] || "neutral",
            sub_emotion: "neutral",
            intensity: "moderate"
          }];
        }

        // Log the transcript for debugging
        console.log(`Loading transcript with ${normalizedData.transcript.length} sentences`);

        setAnalysisData(normalizedData);
      } else {
        // Fallback to basic data if full analysis isn't available
        setAnalysisData({
          videoId: historyItem.id,
          title: historyItem.title,
          transcript: [
            {
              sentence: "Historic data for this video is not available.",
              start_time: 1,
              end_time: 3,
              emotion: Object.keys(historyItem.emotions)[0] || "neutral",
              sub_emotion: "neutral",
              intensity: "moderate"
            }
          ]
        });
      }

      setIsLoading(false);
    }, 500);
  };

  // Get current emotion based on timestamp
  const getCurrentEmotion = () => {
    // Validate analysis data structure first
    if (!analysisData) {
      return null;
    }

    // Validate transcript data
    const transcript = analysisData.transcript;
    if (!transcript || !Array.isArray(transcript) || transcript.length === 0) {
      console.warn("Invalid or empty transcript in getCurrentEmotion");
      return null;
    }

    // Find the current emotion based on timestamp
    const current = transcript.find(
      item => item && typeof item === 'object' &&
             typeof item.start_time !== 'undefined' &&
             typeof item.end_time !== 'undefined' &&
             currentTime >= item.start_time && currentTime <= item.end_time
    );

    return current || null;
  };

  // Remove a video from history
  const removeFromHistory = (videoId) => {
    setVideoHistory(prev => {
      const updatedHistory = prev.filter(video => video.id !== videoId);

      // Save updated history to localStorage
      try {
        localStorage.setItem('videoAnalysisHistory', JSON.stringify(updatedHistory));
      } catch (error) {
        console.error("Error saving history to localStorage:", error);
      }

      return updatedHistory;
    });

    // Also remove from full analysis storage if it exists
    if (fullAnalysisStorage[videoId]) {
      const updatedStorage = { ...fullAnalysisStorage };
      delete updatedStorage[videoId];

      setFullAnalysisStorage(updatedStorage);
      try {
        localStorage.setItem('videoFullAnalysisData', JSON.stringify(updatedStorage));
      } catch (error) {
        console.error("Error updating analysis storage in localStorage:", error);
      }
    }
  };

  // Value to be provided by the context
  const value = {
    videoUrl,
    currentTime,
    setCurrentTime,
    isPlaying,
    setIsPlaying,
    isLoading,
    error,
    analysisData,
    videoHistory,
    processVideo,
    loadFromHistory,
    removeFromHistory,
    getCurrentEmotion,
  };

  return (
    <VideoContext.Provider value={value}>
      {children}
    </VideoContext.Provider>
  );
};

export default VideoContext;
