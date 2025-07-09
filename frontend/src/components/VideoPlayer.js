import React, { useState, useRef, useEffect } from 'react';
import ReactPlayer from 'react-player';
import { Box, Typography, Paper } from '@mui/material';
import { useVideo } from '../VideoContext';

const VideoPlayer = ({ url, onProgress, onReady, currentTime }) => {
  const { isPlaying, setIsPlaying } = useVideo();
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState(false);
  const playerRef = useRef(null);

  // Seek to specific time when currentTime prop changes from outside
  useEffect(() => {
    if (playerRef.current && isReady && currentTime !== undefined) {
      const internalPlayerTime = playerRef.current.getCurrentTime();
      // Only seek if the difference is more than a small threshold (e.g., 1 second)
      // OR if the video is not currently playing (implying the seek is intentional)
      if (Math.abs(internalPlayerTime - currentTime) > 1 || !isPlaying) {
        playerRef.current.seekTo(currentTime, 'seconds');
      }
    }
  }, [currentTime, isReady, isPlaying]);

  const handleReady = () => {
    setIsReady(true);
    setError(false);
    if (onReady) {
      onReady();
    }
  };

  const handleError = (e) => {
    console.error('Video player error:', e);
    setError(true);
  };

  const handlePlay = () => {
    setIsPlaying(true);
  };

  const handlePause = () => {
    setIsPlaying(false);
  };

  return (
    <Box sx={{ width: '100%' }}>
      {url ? (
        <Box
          sx={{
            position: 'relative',
            paddingTop: '56.25%', // 16:9 aspect ratio
            backgroundColor: '#000',
            borderRadius: 1,
            overflow: 'hidden',
          }}
        >
          <ReactPlayer
            ref={playerRef}
            url={url}
            width="100%"
            height="100%"
            style={{ position: 'absolute', top: 0, left: 0 }}
            controls={true}
            onReady={handleReady}
            onError={handleError}
            onProgress={onProgress}
            onPlay={handlePlay}
            onPause={handlePause}
            config={{
              youtube: {
                playerVars: {
                  modestbranding: 1,
                  rel: 0,
                },
              },
            }}
          />
        </Box>
      ) : (
        <Paper
          elevation={0}
          sx={{
            bgcolor: 'grey.200',
            height: '300px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 1,
          }}
        >
          <Typography variant="body1" color="textSecondary">
            Enter a YouTube URL to play video
          </Typography>
        </Paper>
      )}

      {error && (
        <Typography variant="body2" color="error" sx={{ mt: 1 }}>
          Error loading video. Please check the URL and try again.
        </Typography>
      )}
    </Box>
  );
};

export default VideoPlayer;
