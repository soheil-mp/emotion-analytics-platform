/**
 * Gemini API Setup Utility for Docker Containers
 * Helps users configure Gemini API access in containerized environments
 */

import geminiSummaryService from '../services/geminiSummaryService';

class GeminiSetup {
  constructor() {
    this.apiKeyPattern = /^AIza[0-9A-Za-z-_]{35}$/;
  }

  /**
   * Check if Gemini is configured and working
   * @returns {Promise<Object>} Status object with configuration details
   */
  async checkConfiguration() {
    const hasApiKey = geminiSummaryService.hasApiKey();

    if (!hasApiKey) {
      return {
        configured: false,
        status: 'missing_api_key',
        message: 'Gemini API key not found. Add REACT_APP_GEMINI_API_KEY environment variable.',
        instructions: this.getSetupInstructions()
      };
    }

    // Test API key validity (quick test)
    try {
      const testSummary = await geminiSummaryService.generateVideoSummary(
        { transcript: [{ text: 'test', emotion: 'neutral', confidence: 0.8 }] },
        'Test Video'
      );

      if (testSummary.includes('💡 Tip: Add REACT_APP_GEMINI_API_KEY')) {
        return {
          configured: false,
          status: 'invalid_api_key',
          message: 'API key found but appears invalid',
          instructions: this.getSetupInstructions()
        };
      }

      return {
        configured: true,
        status: 'working',
        message: 'Gemini API is configured and working',
        apiKeyPresent: true
      };

    } catch (error) {
      return {
        configured: false,
        status: 'api_error',
        message: `API test failed: ${error.message}`,
        instructions: this.getSetupInstructions()
      };
    }
  }

  /**
   * Validate API key format
   * @param {string} apiKey - API key to validate
   * @returns {boolean} True if format is valid
   */
  validateApiKey(apiKey) {
    return this.apiKeyPattern.test(apiKey);
  }

  /**
   * Set up Gemini API key dynamically
   * @param {string} apiKey - Gemini API key
   * @returns {Object} Setup result
   */
  setupApiKey(apiKey) {
    if (!apiKey || apiKey.trim() === '') {
      return {
        success: false,
        message: 'API key cannot be empty'
      };
    }

    const trimmedKey = apiKey.trim();

    if (!this.validateApiKey(trimmedKey)) {
      return {
        success: false,
        message: 'Invalid API key format. Should start with "AIza" and be 39 characters long.'
      };
    }

    try {
      geminiSummaryService.setApiKey(trimmedKey);
      return {
        success: true,
        message: 'Gemini API key configured successfully'
      };
    } catch (error) {
      return {
        success: false,
        message: `Failed to set API key: ${error.message}`
      };
    }
  }

  /**
   * Get setup instructions for different environments
   * @returns {Object} Instructions for various deployment types
   */
  getSetupInstructions() {
    return {
      docker: {
        title: 'Docker Container Setup',
        steps: [
          '1. Get a Gemini API key from Google AI Studio: https://makersuite.google.com/app/apikey',
          '2. Stop your Docker containers',
          '3. Create a .env file in your project root with: REACT_APP_GEMINI_API_KEY=your_api_key',
          '4. Add environment variables to docker-compose.yml:',
          '   frontend:',
          '     environment:',
          '       - REACT_APP_GEMINI_API_KEY=${REACT_APP_GEMINI_API_KEY}',
          '5. Rebuild and restart containers: docker-compose up --build'
        ],
        alternative: 'Or use the runtime setup below to configure without rebuilding'
      },
      runtime: {
        title: 'Runtime Configuration (Temporary)',
        description: 'Configure API key without rebuilding containers. Settings will persist until container restart.',
        note: 'This is a temporary solution. For permanent setup, use the Docker environment method above.'
      },
      local: {
        title: 'Local Development',
        steps: [
          '1. Create a .env file in your frontend directory',
          '2. Add: REACT_APP_GEMINI_API_KEY=your_api_key',
          '3. Restart your development server'
        ]
      }
    };
  }

  /**
   * Get user-friendly status message
   * @param {string} status - Status code
   * @returns {string} Human-readable message
   */
  getStatusMessage(status) {
    const messages = {
      missing_api_key: '⚠️ Gemini API key not configured - using basic summaries',
      invalid_api_key: '❌ Invalid API key - check format and permissions',
      api_error: '🔄 API connection issues - check network and quota',
      working: '✅ Gemini AI summaries fully operational'
    };

    return messages[status] || '❓ Unknown configuration status';
  }

  /**
   * Create a setup notification for the UI
   * @returns {Object} Notification object
   */
  async createSetupNotification() {
    const config = await this.checkConfiguration();

    if (config.configured) {
      return null; // No notification needed
    }

    return {
      type: 'info',
      title: 'Enhanced AI Summaries Available',
      message: config.message,
      action: {
        text: 'Configure Gemini API',
        onClick: () => this.showSetupDialog()
      },
      persistent: true
    };
  }

  /**
   * Show setup dialog (to be implemented in UI component)
   */
  showSetupDialog() {
    // This would trigger a modal/dialog in the UI
    // Implementation depends on your UI framework
    console.log('Setup dialog should be shown');

    // For now, log instructions
    const instructions = this.getSetupInstructions();
    console.group('🔧 Gemini API Setup Instructions');
    console.log('Docker Setup:', instructions.docker);
    console.log('Runtime Setup:', instructions.runtime);
    console.groupEnd();
  }
}

// Create singleton instance
const geminiSetup = new GeminiSetup();

// Auto-check configuration on load (in development)
if (process.env.NODE_ENV === 'development') {
  geminiSetup.checkConfiguration().then(config => {
    console.log('🤖 Gemini Configuration:', config);
  });
}

export default geminiSetup;
