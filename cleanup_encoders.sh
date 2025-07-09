#!/bin/bash

# Cleanup script for corrupted encoder files
# Run this on your server to fix the "unknown" prediction issue

echo "🧹 Cleaning up potentially corrupted encoder files..."

# Define encoder paths
ENCODER_PATHS=(
    "models/encoders/emotion_encoder.pkl"
    "models/encoders/sub_emotion_encoder.pkl" 
    "models/encoders/intensity_encoder.pkl"
    "models/test_encoders/emotion_encoder.pkl"
    "models/test_encoders/sub_emotion_encoder.pkl"
)

# Remove encoder files
for encoder_path in "${ENCODER_PATHS[@]}"; do
    if [ -f "$encoder_path" ]; then
        echo "🗑️  Removing: $encoder_path"
        rm "$encoder_path"
        echo "✅ Removed: $encoder_path"
    else
        echo "⏭️  Not found: $encoder_path"
    fi
done

# Also clean up the baseline stats if it exists and is corrupted
if [ -f "models/baseline_stats.pkl" ]; then
    echo "🗑️  Removing potentially corrupted baseline_stats.pkl"
    rm "models/baseline_stats.pkl"
    echo "✅ Removed: models/baseline_stats.pkl"
fi

echo ""
echo "✅ Cleanup complete!"
echo "📋 Next steps:"
echo "   1. Restart your docker containers: docker-compose down && docker-compose up"
echo "   2. The missing files will be re-downloaded from Azure ML automatically"
echo "   3. If Azure ML sync fails, you may need to retrain or copy the encoder files manually"
echo ""
echo "🔍 Monitor logs for: '✅ Loaded [encoder_name] encoder from [path]'" 