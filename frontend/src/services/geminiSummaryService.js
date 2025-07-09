import axios from 'axios';

/**
 * Gemini Video Summary Service
 * Generates intelligent video summaries using Google's Gemini 2.0 Flash API
 * Updated for 2025 API specifications with enhanced error handling
 */
class GeminiSummaryService {
  constructor() {
    // HARDCODED FOR DEBUGGING - Remove in production!
    this.apiKey = "AIzaSyAeqDhrmHdtfnwg01qkFTUB0mcMcYZgV64";

    // Fallback to environment variables if hardcoded key is removed
    // this.apiKey = process.env.REACT_APP_GEMINI_API_KEY ||
    //               window.REACT_APP_GEMINI_API_KEY ||
    //               localStorage.getItem('gemini_api_key');

    // Updated to use Gemini 2.0 Flash (latest model as of 2025)
    this.baseURL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent';

    // Fallback models if primary fails
    this.fallbackModels = [
      'gemini-1.5-flash:generateContent',
      'gemini-1.5-pro:generateContent'
    ];

    // Log API key status for debugging (without exposing the key)
    if (this.apiKey && this.apiKey.trim() !== '') {
      console.log('✅ Gemini API key found');
    } else {
      console.warn('⚠️ Gemini API key not found - using fallback summaries');
    }
  }

  /**
   * Set API key dynamically (useful for Docker containers)
   * @param {string} apiKey - Gemini API key
   */
  setApiKey(apiKey) {
    if (apiKey && apiKey.trim() !== '') {
      this.apiKey = apiKey.trim();
      localStorage.setItem('gemini_api_key', this.apiKey);
      console.log('✅ Gemini API key updated');
    }
  }

  /**
   * Check if API key is available
   * @returns {boolean} - True if API key exists
   */
  hasApiKey() {
    return !!(this.apiKey && this.apiKey.trim() !== '');
  }

  /**
   * Generate a concise video summary using transcript and emotion data
   * @param {Object} analysisData - Video analysis data
   * @param {string} videoTitle - Title of the video
   * @returns {Promise<string>} - Generated summary (50-60 words)
   */
  async generateVideoSummary(analysisData, videoTitle = 'Video') {
    // Validate API key first
    if (!this.apiKey || this.apiKey.trim() === '') {
      console.warn('Gemini API key not found, using fallback summary');
      return this.generateFallbackSummary(analysisData, videoTitle);
    }

    try {
      // Extract key information from analysis data
      const transcriptText = this.extractTranscriptText(analysisData);
      const emotionSummary = this.extractEmotionSummary(analysisData);
      const duration = this.calculateDuration(analysisData);

      // Construct the prompt for Gemini
      const prompt = this.buildSummaryPrompt(transcriptText, emotionSummary, duration, videoTitle);

      // Try primary model first, then fallbacks
      let summary = await this.callGeminiAPI(this.baseURL, prompt);

      if (!summary) {
        // Try fallback models
        for (const fallbackModel of this.fallbackModels) {
          const fallbackURL = `https://generativelanguage.googleapis.com/v1beta/models/${fallbackModel}`;
          summary = await this.callGeminiAPI(fallbackURL, prompt);
          if (summary) break;
        }
      }

      if (summary) {
        return this.cleanAndTruncateSummary(summary);
      }

      throw new Error('All Gemini models failed to generate summary');

    } catch (error) {
      console.error('Gemini API Error:', error);

      // Enhanced fallback with error details
      return this.generateFallbackSummary(analysisData, videoTitle, error.message);
    }
  }

  /**
   * Call Gemini API with improved error handling and request structure
   */
  async callGeminiAPI(modelURL, prompt) {
    try {
      const response = await axios.post(
        `${modelURL}?key=${this.apiKey}`,
        {
          contents: [{
            parts: [{
              text: prompt
            }]
          }],
          generationConfig: {
            temperature: 0.8,         // Increased for more creative summaries
            topK: 50,                // Increased vocabulary range
            topP: 0.9,               // Better coherence
            maxOutputTokens: 150,    // Increased for proper summaries
            candidateCount: 1,
            stopSequences: []
          },
          safetySettings: [
            {
              category: 'HARM_CATEGORY_HARASSMENT',
              threshold: 'BLOCK_ONLY_HIGH'    // Less restrictive
            },
            {
              category: 'HARM_CATEGORY_HATE_SPEECH',
              threshold: 'BLOCK_ONLY_HIGH'    // Less restrictive
            },
            {
              category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
              threshold: 'BLOCK_ONLY_HIGH'
            },
            {
              category: 'HARM_CATEGORY_DANGEROUS_CONTENT',
              threshold: 'BLOCK_ONLY_HIGH'
            }
          ]
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
          timeout: 15000 // Increased timeout
        }
      );

      // Updated response parsing for 2025 API structure
      if (response.data?.candidates?.[0]?.content?.parts?.[0]?.text) {
        return response.data.candidates[0].content.parts[0].text.trim();
      }

      // Handle blocked content
      if (response.data?.candidates?.[0]?.finishReason === 'SAFETY') {
        console.warn('Content blocked by safety filters');
        return null;
      }

      // Handle other finish reasons
      if (response.data?.candidates?.[0]?.finishReason) {
        console.warn('Content generation stopped:', response.data.candidates[0].finishReason);
        return null;
      }

      return null;

    } catch (error) {
      // Enhanced error logging
      if (error.response) {
        console.error('Gemini API Response Error:', {
          status: error.response.status,
          statusText: error.response.statusText,
          data: error.response.data
        });

        // Handle specific API errors
        if (error.response.status === 400) {
          console.error('Bad request - check API key and request format');
        } else if (error.response.status === 403) {
          console.error('API key invalid or quota exceeded');
        } else if (error.response.status === 429) {
          console.error('Rate limit exceeded');
        }
      } else if (error.request) {
        console.error('Network error:', error.message);
      } else {
        console.error('Request setup error:', error.message);
      }

      return null;
    }
  }

  /**
   * Extract readable text from transcript data
   */
  extractTranscriptText(analysisData) {
    if (!analysisData?.transcript || !Array.isArray(analysisData.transcript)) {
      return '';
    }

    return analysisData.transcript
      .map(segment => {
        const text = segment.text || segment.sentence || segment.content || '';
        return text.trim();
      })
      .filter(text => text.length > 0)
      .join(' ')
      .substring(0, 1500); // Limit to prevent token overflow
  }

  /**
   * Extract sophisticated emotion summary statistics
   */
  extractEmotionSummary(analysisData) {
    if (!analysisData?.transcript) return 'Visual emotion analysis enabled';

    // Count emotions with confidence weighting
    const emotionCounts = {};
    const emotionConfidences = {};
    let totalSegments = 0;

    analysisData.transcript.forEach(segment => {
      const emotion = segment.emotion || segment.primary_emotion || 'neutral';
      const confidence = segment.confidence || 0.7;

      emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
      emotionConfidences[emotion] = (emotionConfidences[emotion] || []).concat(confidence);
      totalSegments++;
    });

    // Calculate weighted emotion scores
    const emotionScores = Object.entries(emotionCounts).map(([emotion, count]) => {
      const avgConfidence = emotionConfidences[emotion].reduce((a, b) => a + b, 0) / emotionConfidences[emotion].length;
      const percentage = ((count / totalSegments) * 100).toFixed(0);
      return { emotion, count, percentage, avgConfidence };
    }).sort((a, b) => b.count - a.count);

    // Create rich emotional narrative
    const primary = emotionScores[0];
    const secondary = emotionScores[1];

    if (!primary) return 'Emotion detection in progress';

    let narrative = `${primary.emotion} dominates (${primary.percentage}%)`;

    if (secondary && secondary.count > totalSegments * 0.15) {
      narrative += `, with ${secondary.emotion} moments (${secondary.percentage}%)`;
    }

    // Add emotional intensity description
    const avgOverallConfidence = Object.values(emotionConfidences)
      .flat()
      .reduce((a, b) => a + b, 0) / Object.values(emotionConfidences).flat().length;

    const intensityDesc = avgOverallConfidence > 0.8 ? 'high emotional clarity' :
                         avgOverallConfidence > 0.6 ? 'moderate emotional expression' :
                         'subtle emotional nuances';

    return `${totalSegments} segments analyzed with ${intensityDesc}. ${narrative}`;
  }

  /**
   * Calculate video duration
   */
  calculateDuration(analysisData) {
    if (!analysisData?.transcript) return 0;

    const totalDuration = analysisData.transcript.reduce((sum, segment) => {
      const start = segment.start_time || segment.start || 0;
      const end = segment.end_time || segment.end || start;
      return sum + (end - start);
    }, 0);

    return Math.round(totalDuration);
  }

  /**
   * Build the prompt for Gemini API with enhanced instructions
   */
  buildSummaryPrompt(transcriptText, emotionSummary, duration, videoTitle) {
    const hasTranscript = transcriptText && transcriptText.length > 10;
    const durationMinutes = Math.round(duration / 60);

    if (!hasTranscript) {
      // Enhanced prompt for emotion-only analysis
      return `Create a professional video summary in exactly 45-55 words.

VIDEO DETAILS:
Title: "${videoTitle}"
Duration: ${durationMinutes > 0 ? `${durationMinutes} minute(s)` : `${duration} seconds`}
Analysis: ${emotionSummary}

REQUIREMENTS:
- Write a natural, engaging summary
- Focus on what viewers will experience
- Use active voice and clear language
- Start with "This video" or "The video"
- End with proper punctuation

Write only the summary, no additional text:`;
    }

    // Enhanced prompt for transcript + emotion analysis
    return `Create a professional video summary in exactly 45-55 words.

VIDEO DETAILS:
Title: "${videoTitle}"
Duration: ${durationMinutes > 0 ? `${durationMinutes} minute(s)` : `${duration} seconds`}

CONTENT:
${transcriptText}

EMOTIONAL ANALYSIS:
${emotionSummary}

REQUIREMENTS:
- Capture the main topic and key insights
- Mention the emotional tone/journey
- Use engaging, accessible language
- Write in active voice
- Be accurate to the content
- Start naturally (avoid "This video..." if content flows better without it)

Write only the summary, no additional text:`;
  }

  /**
   * Clean and ensure summary is within word limit
   */
  cleanAndTruncateSummary(summary) {
    // Remove any unwanted formatting or AI response prefixes
    let cleaned = summary
      .replace(/^(Summary:|Video Summary:|Here's a summary:|Compelling Summary:|Here's the summary:|The summary:|Analysis:)/i, '')
      .replace(/^(This video|The video|In this video)/i, (match) => match) // Keep natural openings
      .replace(/\*\*/g, '') // Remove markdown bold
      .replace(/\*/g, '') // Remove markdown italic
      .replace(/#{1,6}\s*/g, '') // Remove markdown headers
      .replace(/\n+/g, ' ') // Replace newlines with spaces
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();

    // Remove common AI-generated phrases that sound robotic
    cleaned = cleaned
      .replace(/^(Here's a|This is a|I've created a|Below is a)/i, '')
      .replace(/(summary|analysis) of the video:?/gi, '')
      .trim();

    // Ensure proper sentence structure
    if (cleaned && !cleaned.match(/^[A-Z]/)) {
      cleaned = cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
    }

    // Split into words and truncate if necessary
    const words = cleaned.split(/\s+/).filter(word => word.length > 0);
    if (words.length > 65) {
      cleaned = words.slice(0, 32).join(' ') + '...';
    }

    // Ensure it ends with proper punctuation
    if (cleaned && !cleaned.match(/[.!?]$/)) {
      cleaned += '.';
    }

    return cleaned;
  }

  /**
   * Generate a sophisticated fallback summary when API fails
   */
  generateFallbackSummary(analysisData, videoTitle, errorMessage = '') {
    const transcriptLength = analysisData?.transcript?.length || 0;
    const duration = this.calculateDuration(analysisData);
    const durationMinutes = Math.round(duration / 60);

    // Enhanced error logging for debugging
    if (errorMessage) {
      console.warn('Gemini API failed:', errorMessage);
    }

    if (transcriptLength === 0) {
      const timeText = durationMinutes > 0 ? `${durationMinutes}-minute` : `${Math.round(duration)}-second`;
      return `This ${timeText} "${videoTitle}" presents visual content with advanced emotion detection analysis, revealing expressions and patterns through AI-powered technology.`;
    }

    // Analyze emotion patterns for more intelligent fallback
    const emotionCounts = {};
    let totalConfidence = 0;

    analysisData.transcript?.forEach(segment => {
      const emotion = segment.emotion || segment.primary_emotion || 'neutral';
      const confidence = segment.confidence || 0.7;
      emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
      totalConfidence += confidence;
    });

    const avgConfidence = (totalConfidence / transcriptLength).toFixed(1);
    const emotionEntries = Object.entries(emotionCounts).sort(([,a], [,b]) => b - a);
    const dominantEmotion = emotionEntries[0]?.[0] || 'neutral';
    const secondaryEmotion = emotionEntries[1]?.[0];

    // Create more sophisticated emotional description
    let emotionalJourney = dominantEmotion;
    if (secondaryEmotion && emotionCounts[secondaryEmotion] > transcriptLength * 0.2) {
      emotionalJourney = `${dominantEmotion} with ${secondaryEmotion} undertones`;
    }

    const timeText = durationMinutes > 0 ? `${durationMinutes}-minute` : `${Math.round(duration)}-second`;

    // Try to extract some content keywords for better fallback
    let contentHint = '';
    if (analysisData.transcript && analysisData.transcript.length > 0) {
      const firstFewSegments = analysisData.transcript.slice(0, 3);
      const words = firstFewSegments
        .map(segment => segment.text || segment.sentence || '')
        .join(' ')
        .toLowerCase()
        .split(/\s+/)
        .filter(word => word.length > 4 && !['video', 'this', 'that', 'with', 'from', 'they', 'have', 'will', 'been'].includes(word));

      if (words.length > 0) {
        const keyWord = words[0];
        contentHint = ` exploring ${keyWord}-related content`;
      }
    }

    return `This ${timeText} "${videoTitle}"${contentHint} contains ${transcriptLength} analyzed segments with ${emotionalJourney} patterns and ${avgConfidence} confidence analysis.`;
  }
}

const geminiSummaryService = new GeminiSummaryService();
export default geminiSummaryService;
