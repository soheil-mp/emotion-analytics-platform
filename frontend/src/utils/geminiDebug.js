import geminiSummaryService from '../services/geminiSummaryService';

/**
 * Debug utilities for Gemini Summary Service
 * Use these functions to test and debug the Gemini API integration
 */

/**
 * Test the Gemini API with sample data
 */
export const testGeminiAPI = async () => {
  console.log('🧪 Testing Gemini API...');

  const sampleAnalysisData = {
    title: 'Sample Video Test',
    transcript: [
      {
        text: 'Welcome to this engineering tutorial about robots.',
        start_time: 0,
        end_time: 3,
        emotion: 'neutral',
        confidence: 0.8
      },
      {
        text: 'Today we will explore how robots work and their applications.',
        start_time: 3,
        end_time: 7,
        emotion: 'happiness',
        confidence: 0.7
      },
      {
        text: 'Engineering robots requires understanding of mechanics and programming.',
        start_time: 7,
        end_time: 12,
        emotion: 'neutral',
        confidence: 0.9
      }
    ]
  };

  try {
    const summary = await geminiSummaryService.generateVideoSummary(
      sampleAnalysisData,
      'How Engineering Robots Works: Crash Course Engineering #33'
    );

    console.log('✅ Gemini API Test Result:', summary);
    console.log('📊 Summary Length:', summary.split(' ').length, 'words');

    return summary;
  } catch (error) {
    console.error('❌ Gemini API Test Failed:', error);
    throw error;
  }
};

/**
 * Check if Gemini API key is configured
 */
export const checkGeminiConfig = () => {
  const apiKey = process.env.REACT_APP_GEMINI_API_KEY;

  console.log('🔐 Checking Gemini Configuration...');
  console.log('API Key exists:', !!apiKey);
  console.log('API Key length:', apiKey ? apiKey.length : 0);
  console.log('API Key preview:', apiKey ? `${apiKey.substring(0, 10)}...` : 'Not found');

  if (!apiKey || apiKey.trim() === '' || apiKey === 'your_gemini_api_key_here') {
    console.warn('⚠️ Gemini API key not properly configured!');
    console.log('💡 To fix this:');
    console.log('1. Get API key from: https://makersuite.google.com/app/apikey');
    console.log('2. Create .env file in frontend folder');
    console.log('3. Add: REACT_APP_GEMINI_API_KEY=your_actual_key');
    console.log('4. Restart the development server');
    return false;
  }

  console.log('✅ Gemini API key appears to be configured');
  return true;
};

/**
 * Test different aspects of the summary service
 */
export const runFullDiagnostics = async () => {
  console.log('🔍 Running Full Gemini Diagnostics...');

  // Check configuration
  const configOK = checkGeminiConfig();

  if (!configOK) {
    console.log('❌ Configuration check failed - skipping API test');
    return;
  }

  // Test API
  try {
    await testGeminiAPI();
    console.log('✅ All diagnostics passed!');
  } catch (error) {
    console.error('❌ API test failed:', error.message);

    // Provide specific troubleshooting
    if (error.message.includes('403')) {
      console.log('💡 Troubleshooting: API key might be invalid or expired');
    } else if (error.message.includes('429')) {
      console.log('💡 Troubleshooting: Rate limit exceeded - try again later');
    } else if (error.message.includes('400')) {
      console.log('💡 Troubleshooting: Bad request - check API format');
    } else {
      console.log('💡 Troubleshooting: Check network connection and API key');
    }
  }
};

// Auto-run diagnostics in development
if (process.env.NODE_ENV === 'development') {
  setTimeout(() => {
    console.log('🚀 Auto-running Gemini diagnostics...');
    runFullDiagnostics();
  }, 2000);
}

const geminiDebugUtils = {
  testGeminiAPI,
  checkGeminiConfig,
  runFullDiagnostics
};

export default geminiDebugUtils;
