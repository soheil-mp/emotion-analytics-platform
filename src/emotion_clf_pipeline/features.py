import logging
from collections import Counter

import nltk
import numpy as np
import pandas as pd
from nltk import pos_tag
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob


class POSFeatureExtractor:
    """Feature extractor for Part-of-Speech tagging."""

    def __init__(self):
        """Initialize POS feature extractor and download required NLTK data."""
        self._ensure_pos_resources()

    def _ensure_pos_resources(self):
        """Ensure required NLTK resources for POS tagging are available."""
        # Download NLTK data if not available (for Azure ML)
        required_resources = [
            ("punkt", "tokenizers/punkt"),
            ("punkt_tab", "tokenizers/punkt_tab"),
            ("averaged_perceptron_tagger", "taggers/averaged_perceptron_tagger"),
        ]

        for resource_name, resource_path in required_resources:
            try:
                nltk.data.find(resource_path)
                logging.info(f"✓ NLTK resource '{resource_name}' available")
            except LookupError:
                try:
                    logging.info(f"⬇ Downloading NLTK {resource_name}...")
                    nltk.download(resource_name, quiet=True)
                    logging.info(f"✅ Downloaded {resource_name}")
                except Exception as e:
                    logging.warning(f"⚠ Failed to download {resource_name}: {e}")

    def extract_features(self, text):
        """
        Extract part-of-speech features from text.

        Args:
            text (str): Input text to analyze

        Returns:
            list: List of POS features including normalized counts
        """
        if not text or pd.isna(text):
            return [0] * 10

        try:
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)

            # Count POS tags
            pos_counts = Counter(tag for word, tag in pos_tags)

            # Calculate features (normalized by total tokens)
            total = len(tokens) if tokens else 1
            features = [
                pos_counts.get("NN", 0) / total,  # Nouns
                pos_counts.get("NNS", 0) / total,  # Plural nouns
                pos_counts.get("VB", 0) / total,  # Verbs
                pos_counts.get("VBD", 0) / total,  # Past tense verbs
                pos_counts.get("JJ", 0) / total,  # Adjectives
                pos_counts.get("RB", 0) / total,  # Adverbs
                pos_counts.get("PRP", 0) / total,  # Personal pronouns
                pos_counts.get("IN", 0) / total,  # Prepositions
                pos_counts.get("DT", 0) / total,  # Determiners
                len(tokens) / 30,  # Text length (normalized)
            ]

            return features

        except Exception as e:
            logging.warning(f"⚠ POS analysis failed for text: {e}")
            return [0] * 10


class TextBlobFeatureExtractor:
    """Feature extractor for TextBlob sentiment analysis."""

    def extract_features(self, text):
        """
        Extract TextBlob sentiment features.

        Args:
            text (str): Input text to analyze

        Returns:
            list: List containing [polarity, subjectivity] scores
        """
        if not text or pd.isna(text):
            return [0, 0]

        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        return [polarity, subjectivity]


class VaderFeatureExtractor:
    """Feature extractor for VADER sentiment analysis."""

    def __init__(self):
        """Initialize VADER sentiment analyzer."""
        # Download NLTK data if not available (for Azure ML)
        self._ensure_vader_resources()
        self.analyzer = SentimentIntensityAnalyzer()

    def _ensure_vader_resources(self):
        """Ensure VADER lexicon is available."""
        try:
            nltk.data.find("vader_lexicon")
            logging.info("✓ VADER lexicon already available")
        except LookupError:
            try:
                logging.info("⬇ Downloading NLTK vader_lexicon...")
                nltk.download("vader_lexicon", quiet=True)
                logging.info("✅ Successfully downloaded vader_lexicon")
            except Exception as e:
                logging.error(f"❌ Failed to download vader_lexicon: {e}")
                raise RuntimeError(f"Cannot initialize VADER: {e}")

    def extract_features(self, text):
        """
        Extract VADER sentiment features.

        Args:
            text (str): Input text to analyze

        Returns:
            list: List containing [neg, neu, pos, compound] scores
        """
        if not text or pd.isna(text):
            return [0, 0, 0, 0]

        try:
            scores = self.analyzer.polarity_scores(text)
            features = [scores["neg"], scores["neu"], scores["pos"], scores["compound"]]
            return features
        except Exception as e:
            logging.warning(f"⚠ VADER analysis failed for text: {e}")
            return [0, 0, 0, 0]


class EmolexFeatureExtractor:
    """Feature extractor for EmoLex emotion lexicon."""

    def __init__(self, lexicon_path):
        """
        Initialize EmoLex feature extractor.

        Args:
            lexicon_path (str): Path to the EmoLex lexicon file
        """
        # Ensure NLTK tokenizer is available
        self._ensure_tokenizer_resources()

        self.EMOTIONS = [
            "anger",
            "anticipation",
            "disgust",
            "fear",
            "joy",
            "sadness",
            "surprise",
            "trust",
        ]
        self.SENTIMENTS = ["negative", "positive"]

        # Load lexicon if path is provided
        if lexicon_path:
            self.lexicon = self._load_lexicon(lexicon_path)
        else:
            self.lexicon = {}
            logging.warning("⚠ No EmoLex lexicon path provided")

    def _ensure_tokenizer_resources(self):
        """Ensure NLTK tokenizer resources are available."""
        try:
            nltk.data.find("tokenizers/punkt")
            logging.info("✓ NLTK punkt tokenizer available")
        except LookupError:
            try:
                logging.info("⬇ Downloading NLTK punkt...")
                nltk.download("punkt", quiet=True)
                logging.info("✅ Downloaded punkt")
            except Exception as e:
                logging.warning(f"⚠ Failed to download punkt: {e}")

    def _load_lexicon(self, lexicon_path):
        """Load and parse the NRC Emotion Lexicon."""
        lexicon = {}

        try:
            with open(lexicon_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("#"):
                        continue

                    parts = line.strip().split("\t")
                    if len(parts) == 3:
                        word, emotion, flag = parts

                        if word not in lexicon:
                            lexicon[word] = {
                                e: 0 for e in self.EMOTIONS + self.SENTIMENTS
                            }

                        if int(flag) == 1:
                            lexicon[word][emotion] = 1

            logging.info(f"✅ Loaded EmoLex lexicon with {len(lexicon)} words")
        except Exception as e:
            logging.error(f"❌ Failed to load EmoLex lexicon: {e}")

        return lexicon

    def extract_features(self, text):
        """
        Extract emotion features using EmoLex.

        Args:
            text (str): Input text to analyze

        Returns:
            numpy.ndarray: Array of emotion features
        """
        if not text or pd.isna(text):
            return np.zeros(2 * len(self.EMOTIONS) + len(self.SENTIMENTS) + 3)

        if not self.lexicon:
            # Return zeros if no lexicon is available
            return np.zeros(2 * len(self.EMOTIONS) + len(self.SENTIMENTS) + 3)

        try:
            # Tokenize and lowercase
            tokens = word_tokenize(text.lower())
            total_words = len(tokens)

            if total_words == 0:
                return np.zeros(2 * len(self.EMOTIONS) + len(self.SENTIMENTS) + 3)

            # Initialize counters
            emotion_counts = {emotion: 0 for emotion in self.EMOTIONS}
            sentiment_counts = {sentiment: 0 for sentiment in self.SENTIMENTS}

            # Count emotion words
            for token in tokens:
                if token in self.lexicon:
                    for emotion in self.EMOTIONS:
                        emotion_counts[emotion] += self.lexicon[token][emotion]
                    for sentiment in self.SENTIMENTS:
                        sentiment_counts[sentiment] += self.lexicon[token][sentiment]

            # Calculate densities
            emotion_densities = {
                emotion: count / total_words
                for emotion, count in emotion_counts.items()
            }

            # Calculate additional metrics
            emotion_diversity = sum(1 for count in emotion_counts.values() if count > 0)
            dominant_emotion_score = (
                max(emotion_densities.values()) if emotion_densities else 0
            )
            total_emotion_words = sum(emotion_counts.values())
            total_sentiment_words = sum(sentiment_counts.values())
            emotion_sentiment_ratio = (
                total_emotion_words / total_sentiment_words
                if total_sentiment_words > 0
                else 0
            )

            # Construct feature vector
            features = []
            features.extend([emotion_counts[emotion] for emotion in self.EMOTIONS])
            features.extend([emotion_densities[emotion] for emotion in self.EMOTIONS])
            features.extend(
                [sentiment_counts[sentiment] for sentiment in self.SENTIMENTS]
            )
            features.append(emotion_diversity)
            features.append(dominant_emotion_score)
            features.append(emotion_sentiment_ratio)

            return np.array(features, dtype=np.float32)

        except Exception as e:
            logging.warning(f"⚠ EmoLex analysis failed for text: {e}")
            return np.zeros(2 * len(self.EMOTIONS) + len(self.SENTIMENTS) + 3)


class FeatureExtractor:
    """
    A comprehensive feature extraction class for text analysis.

    This class provides methods to extract various linguistic and emotional
    features from text, including emotion lexicon features, part-of-speech
    features, sentiment features, and TF-IDF features.

    Attributes:
        vader (SentimentIntensityAnalyzer): VADER sentiment analyzer instance
        EMOTIONS (list): List of emotions tracked by EmoLex
        SENTIMENTS (list): List of sentiment categories
        emolex_lexicon (dict): Loaded EmoLex lexicon
        tfidf_vectorizer (TfidfVectorizer): TF-IDF vectorizer instance
    """

    def __init__(self, feature_config=None, lexicon_path=None):
        """Initialize the FeatureExtractor with necessary components."""
        # Ensure NLTK resources are available first
        self._ensure_nltk_resources()

        # Use provided feature_config, or a specific default (all on) if None
        if feature_config is None:
            self.feature_config = {
                "pos": True,
                "textblob": True,
                "vader": True,
                "tfidf": True,
                "emolex": True,
            }
        else:
            self.feature_config = feature_config

        # Initialize components based on feature configuration
        self.vader = (
            SentimentIntensityAnalyzer()
            if self.feature_config.get("vader", True)
            else None
        )
        self.EMOTIONS = [
            "anger",
            "anticipation",
            "disgust",
            "fear",
            "joy",
            "sadness",
            "surprise",
            "trust",
        ]
        self.SENTIMENTS = ["negative", "positive"]
        self.emolex_lexicon = (
            self._load_emolex_lexicon(lexicon_path)
            if self.feature_config.get("emolex", True) and lexicon_path
            else None
        )
        self.tfidf_vectorizer = None  # Will be initialized when fit is called

        # Define output columns that will be used for labels
        self.output_columns = ["emotion", "sub_emotion", "intensity"]

        # Initialize feature extractors based on configuration
        if self.feature_config.get("pos", True):
            self.pos_extractor = POSFeatureExtractor()
        if self.feature_config.get("textblob", True):
            self.textblob_extractor = TextBlobFeatureExtractor()
        if self.feature_config.get("vader", True):
            self.vader_extractor = VaderFeatureExtractor()
        if self.feature_config.get("emolex", True) and lexicon_path:
            self.emolex_extractor = EmolexFeatureExtractor(lexicon_path)

    def _ensure_nltk_resources(self):
        """
        Ensure all required NLTK resources are available.

        This method downloads missing NLTK data in a robust way,
        suitable for Azure ML and other cloud environments.
        """
        required_resources = [
            ("punkt", "tokenizers/punkt"),
            ("punkt_tab", "tokenizers/punkt_tab"),
            ("averaged_perceptron_tagger", "taggers/averaged_perceptron_tagger"),
            ("vader_lexicon", "vader_lexicon"),
            ("stopwords", "corpora/stopwords"),
        ]

        for resource_name, resource_path in required_resources:
            try:
                # Try to find the resource first
                if resource_path:
                    nltk.data.find(resource_path)
                else:
                    # For some resources, just try to download
                    raise LookupError(f"Downloading {resource_name}")

                logging.info(f"✓ NLTK resource '{resource_name}' available")

            except LookupError:
                try:
                    logging.info(f"⬇ Downloading NLTK resource '{resource_name}'...")
                    nltk.download(resource_name, quiet=True)
                    logging.info(f"✅ Downloaded '{resource_name}'")

                except Exception as e:
                    logging.warning(f"⚠ Failed to download '{resource_name}': {e}")
                    # Continue - some resources might be optional

    def _load_emolex_lexicon(self, lexicon_path):
        """
        Load and parse the NRC Emotion Lexicon.

        Args:
            lexicon_path (str): Path to the EmoLex lexicon file

        Returns:
            dict: Dictionary mapping words to their emotion and sentiment scores

        Note:
            The lexicon file should be in the NRC Emotion Lexicon format with
            tab-separated values:
            word    emotion    flag
        """
        lexicon = {}

        with open(lexicon_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("#"):
                    continue

                parts = line.strip().split("\t")
                if len(parts) == 3:
                    word, emotion, flag = parts

                    if word not in lexicon:
                        lexicon[word] = {e: 0 for e in self.EMOTIONS + self.SENTIMENTS}

                    if int(flag) == 1:
                        lexicon[word][emotion] = 1

        # print(f"Loaded EmoLex lexicon with {len(lexicon)} words")
        return lexicon

    def extract_emolex_features(self, text):
        """
        Extract emotion features from text using the EmoLex lexicon.

        Args:
            text (str): Input text to analyze

        Returns:
            numpy.ndarray: Array of emotion features including:
                - Raw emotion counts
                - Emotion densities
                - Sentiment counts
                - Emotion diversity
                - Dominant emotion score
                - Emotion-sentiment ratio
        """
        # Tokenize and lowercase
        tokens = word_tokenize(text.lower())
        total_words = len(tokens)

        if total_words == 0:
            return np.zeros(2 * len(self.EMOTIONS) + len(self.SENTIMENTS) + 2)

        # Initialize counters
        emotion_counts = {emotion: 0 for emotion in self.EMOTIONS}
        sentiment_counts = {sentiment: 0 for sentiment in self.SENTIMENTS}

        # Count emotion words
        for token in tokens:
            if token in self.emolex_lexicon:
                for emotion in self.EMOTIONS:
                    emotion_counts[emotion] += self.emolex_lexicon[token][emotion]
                for sentiment in self.SENTIMENTS:
                    sentiment_counts[sentiment] += self.emolex_lexicon[token][sentiment]

        # Calculate densities
        emotion_densities = {
            emotion: count / total_words for emotion, count in emotion_counts.items()
        }

        # Calculate number of distinct emotions present
        emotion_diversity = sum(1 for count in emotion_counts.values() if count > 0)

        # Find dominant emotion (the one with highest density)
        dominant_emotion_score = (
            max(emotion_densities.values()) if emotion_densities else 0
        )

        # Calculate emotion to sentiment ratio
        total_emotion_words = sum(emotion_counts.values())
        total_sentiment_words = sum(sentiment_counts.values())
        emotion_sentiment_ratio = (
            total_emotion_words / total_sentiment_words
            if total_sentiment_words > 0
            else 0
        )

        # Construct feature vector
        features = []
        features.extend(
            [emotion_counts[emotion] for emotion in self.EMOTIONS]
        )  # Raw counts
        features.extend(
            [emotion_densities[emotion] for emotion in self.EMOTIONS]
        )  # Densities
        features.extend(
            [sentiment_counts[sentiment] for sentiment in self.SENTIMENTS]
        )  # Sentiment counts
        features.append(emotion_diversity)  # Diversity
        features.append(dominant_emotion_score)  # Dominant emotion intensity
        features.append(emotion_sentiment_ratio)  # Emotion-sentiment ratio

        return np.array(features, dtype=np.float32)

    def get_emolex_feature_names(self):
        """
        Get names of the extracted features for interpretability.

        Returns:
            list: List of feature names in the same order as they appear in
            the feature vector
        """
        feature_names = []

        # Emotion counts
        feature_names.extend([f"emolex_{emotion}_count" for emotion in self.EMOTIONS])

        # Emotion densities
        feature_names.extend([f"emolex_{emotion}_density" for emotion in self.EMOTIONS])

        # Sentiment counts
        feature_names.extend(
            [f"emolex_{sentiment}_count" for sentiment in self.SENTIMENTS]
        )

        # Additional metrics
        feature_names.append("emolex_emotion_diversity")
        feature_names.append("emolex_dominant_emotion_score")
        feature_names.append("emolex_emotion_sentiment_ratio")

        return feature_names

    def extract_pos_features(self, text):
        """
        Extract part-of-speech features from text.

        Args:
            text (str): Input text to analyze

        Returns:
            list: List of POS features including normalized counts of:
                - Nouns (NN)
                - Plural nouns (NNS)
                - Verbs (VB)
                - Past tense verbs (VBD)
                - Adjectives (JJ)
                - Adverbs (RB)
                - Personal pronouns (PRP)
                - Prepositions (IN)
                - Determiners (DT)
                - Text length (normalized)
        """
        if not text or pd.isna(text):
            return [0] * 10  # Return zeros for empty text

        tokens = word_tokenize(text)
        pos_tags = pos_tag(tokens)

        # Count POS tags
        pos_counts = Counter(tag for word, tag in pos_tags)

        # Calculate features (normalized by total tokens)
        total = len(tokens) if tokens else 1
        features = [
            pos_counts.get("NN", 0) / total,  # Nouns
            pos_counts.get("NNS", 0) / total,  # Plural nouns
            pos_counts.get("VB", 0) / total,  # Verbs
            pos_counts.get("VBD", 0) / total,  # Past tense verbs
            pos_counts.get("JJ", 0) / total,  # Adjectives
            pos_counts.get("RB", 0) / total,  # Adverbs
            pos_counts.get("PRP", 0) / total,  # Personal pronouns
            pos_counts.get("IN", 0) / total,  # Prepositions
            pos_counts.get("DT", 0) / total,  # Determiners
            len(tokens) / 30,  # Text length (normalized)
        ]

        return features

    def extract_textblob_sentiment(self, text):
        """
        Extract TextBlob sentiment features.

        Args:
            text (str): Input text to analyze

        Returns:
            list: List containing [polarity, subjectivity] scores
                - polarity: float between -1.0 and 1.0
                - subjectivity: float between 0.0 and 1.0
        """
        if not text or pd.isna(text):
            return [0, 0]

        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        return [polarity, subjectivity]

    def extract_vader_sentiment(self, text):
        """
        Extract VADER sentiment features.

        Args:
            text (str): Input text to analyze

        Returns:
            list: List containing [neg, neu, pos, compound] scores
                - neg: negative sentiment score
                - neu: neutral sentiment score
                - pos: positive sentiment score
                - compound: normalized compound score
        """
        if not text or pd.isna(text):
            return [0, 0, 0, 0]

        scores = self.vader.polarity_scores(text)
        features = [scores["neg"], scores["neu"], scores["pos"], scores["compound"]]

        return features

    def fit_tfidf(self, texts):
        """
        Fit the TF-IDF vectorizer on the provided texts.

        Args:
            texts (list): List of text documents to fit the vectorizer on

        Note:
            This method must be called before using extract_tfidf_features
        """
        self.tfidf_vectorizer = TfidfVectorizer(max_features=100)
        self.tfidf_vectorizer.fit(texts)

    def extract_tfidf_features(self, text):
        """
        Extract TF-IDF features using pre-trained vectorizer.

        Args:
            text (str): Input text to analyze

        Returns:
            numpy.ndarray: Array of TF-IDF features

        Raises:
            ValueError: If fit_tfidf() has not been called yet
        """
        if not text or pd.isna(text):
            return np.zeros(100)

        if self.tfidf_vectorizer is None:
            raise ValueError("TF-IDF vectorizer not fitted. Call fit_tfidf() first.")

        features = self.tfidf_vectorizer.transform([text]).toarray()[0]
        return features

    def extract_all_features(self, text, expected_dim=None):
        """
        Extract all features for a given text based on the feature configuration.
        Pad or truncate features if expected_dim is provided.

        Args:
            text (str): Input text to analyze
            expected_dim (int, optional): The dimension the output features should have.
                                       If None, uses the natural dimension of enabled
                                       features.

        Returns:
            numpy.ndarray: Combined array of all features, padded/truncated to
            expected_dim if provided.
        """
        features_list = []

        if self.feature_config.get("pos", True):
            features_list.extend(self.extract_pos_features(text))

        if self.feature_config.get("textblob", True):
            features_list.extend(self.extract_textblob_sentiment(text))

        if self.feature_config.get("vader", True):
            features_list.extend(self.extract_vader_sentiment(text))

        if self.feature_config.get("tfidf", True):
            # Ensure TF-IDF vectorizer is fitted, especially if called outside
            if self.tfidf_vectorizer is None:
                # Fallback: return zeros for TF-IDF part if not fitted,
                # or fit with dummy if appropriate For prediction, it should
                # have been fit during setup of CustomPredictor. However, if
                # CustomPredictor.predict fits it on the fly, that's different.
                # Let's assume for now if it's None, it means 0 features for
                # this part for a single text.
                num_tfidf_features = (
                    100  # Default expected, should align with get_feature_dim
                )
                if (
                    hasattr(self, "_actual_tfidf_dim")
                    and self._actual_tfidf_dim is not None
                ):
                    num_tfidf_features = self._actual_tfidf_dim
                features_list.extend(np.zeros(num_tfidf_features))
            else:
                features_list.extend(self.extract_tfidf_features(text))

        if self.feature_config.get("emolex", True):
            if self.emolex_lexicon is None:
                # Fallback: Emolex needs lexicon. If none, zero features.
                num_emolex_features = (8 * 2) + 2 + 3
                features_list.extend(np.zeros(num_emolex_features))
            else:
                features_list.extend(self.extract_emolex_features(text))

        actual_features = np.array(features_list, dtype=np.float32)

        if expected_dim is not None:
            current_dim = len(actual_features)
            if current_dim < expected_dim:
                padded_features = np.zeros(expected_dim, dtype=np.float32)
                padded_features[:current_dim] = actual_features
                return padded_features
            elif current_dim > expected_dim:
                return actual_features[:expected_dim]
            # else current_dim == expected_dim, return as is

        return actual_features

    def get_feature_dim(self, expected_dim_from_model=None):
        """
        Calculate the total dimension of all features.
        If expected_dim_from_model is provided, it might influence calculations for
        uninitialized parts (like TF-IDF). However, this function should primarily
        reflect the natural dimension based on config. The padding/truncation should
        ideally happen in extract_all_features.

        Returns:
            int: Total dimension of all enabled features based on current configuration.
        """
        total_dim = 0
        if self.feature_config.get("pos", True):
            total_dim += 10
        if self.feature_config.get("textblob", True):
            total_dim += 2
        if self.feature_config.get("vader", True):
            total_dim += 4
        if self.feature_config.get("emolex", True):
            if self.emolex_lexicon is not None:  # Only add if lexicon loaded
                total_dim += (8 * 2) + 2 + 3  # 21 total EmoLex features
            # else: if emolex is True but lexicon is None, it will produce zeros
            # but occupy space if expected.

        if self.feature_config.get("tfidf", True):
            if self.tfidf_vectorizer is not None and hasattr(
                self.tfidf_vectorizer, "max_features"
            ):
                # Use max_features if vectorizer is initialized, as this is the
                # intended fixed dimension
                self._actual_tfidf_dim = self.tfidf_vectorizer.max_features
                total_dim += self._actual_tfidf_dim
            elif self.tfidf_vectorizer is not None and hasattr(
                self.tfidf_vectorizer, "get_feature_names_out"
            ):
                # Fallback if max_features isn't directly on the instance but
                # vocab is there This case should ideally be avoided by consistent
                # TfidfVectorizer setup
                self._actual_tfidf_dim = len(
                    self.tfidf_vectorizer.get_feature_names_out()
                )
                total_dim += self._actual_tfidf_dim
            else:
                # If TF-IDF is enabled in config but vectorizer not set or lacks
                # max_features info, assume default. This should align with
                # TfidfVectorizer(max_features=100) default in fit_tfidf
                self._actual_tfidf_dim = 100
                total_dim += self._actual_tfidf_dim
        else:
            self._actual_tfidf_dim = None  # Explicitly set to None if tfidf is False

        return total_dim
