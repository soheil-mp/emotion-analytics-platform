import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


class HuggingFaceTranslator:
    def __init__(self, source_language):
        """
        Initialize the translator with the source language

        Args:
            source_language (str): Either 'french' or 'spanish'
        """
        self.source_language = source_language.lower()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Model mapping for different language
        self.model_map = {
            "french": "helsinki-nlp/opus-mt-fr-en",
            "spanish": "helsinki-nlp/opus-mt-es-en",
        }

        if self.source_language not in self.model_map:
            raise ValueError(
                f"Unsupported language: {source_language}. Supported: french, spanish"
            )

        self.model_name = self.model_map[self.source_language]

        print(f"Loading translation model for {source_language} to English...")
        self._load_model()
        print("Translation model loaded successfully!")

    def _load_model(self):
        """Load the tokenizer and model"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

    def translate(self, text, max_length=512, num_beams=4):
        """
        Translate text from source language to English

        Args:
            text (str): Text to translate
            max_length (int): Maximum length of generated translation
            num_beams (int): Number of beams for beam search

        Returns:
            str: Translated text
        """
        if not text or not text.strip():
            return ""

        try:
            # Tokenize input text
            inputs = self.tokenizer(
                text, return_tensors="pt", padding=True, truncation=True, max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate translation
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    early_stopping=True,
                    do_sample=False,
                )

            # Decode the translation
            translation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return translation.strip()

        except Exception as e:
            print(f"Translation error for text '{text[:50]}...': {e}")
            return text

    def translate_batch(self, texts, batch_size=8, max_length=512, num_beams=4):
        """
        Translate a batch of texts for better efficiency

        Args:
            texts (list): List of texts to translate
            batch_size (int): Batch size for processing
            max_length (int): Maximum length of generated translation
            num_beams (int): Number of beams for beam search

        Returns:
            list: List of translated texts
        """
        if not texts:
            return []

        translations = []

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_translations = []

            try:
                # Tokenize batch
                inputs = self.tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512,
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Generate translations
                with torch.no_grad():
                    outputs = self.model.generate(
                        **inputs,
                        max_length=max_length,
                        num_beams=num_beams,
                        early_stopping=True,
                        do_sample=False,
                    )

                # Decode translations
                for output in outputs:
                    translation = self.tokenizer.decode(
                        output, skip_special_tokens=True
                    )
                    batch_translations.append(translation.strip())

                translations.extend(batch_translations)

            except Exception as e:
                print(f"Batch translation error: {e}")
                # Fallback to individual translation
                for text in batch_texts:
                    translations.append(self.translate(text, max_length, num_beams))

        return translations

    def translate_csv(
        self, input_csv_path, output_csv_path=None, text_column=None, batch_size=8
    ):
        """
        Translate text from a CSV file

        Args:
            input_csv_path (str): Path to input CSV file
            output_csv_path (str): Path to output CSV file (optional)
            text_column (str): Name of column containing text to translate (optional)
            batch_size (int): Batch size for processing

        Returns:
            str: Path to output CSV file
        """
        import csv
        import os

        if not os.path.exists(input_csv_path):
            raise FileNotFoundError(f"Input CSV file not found: {input_csv_path}")

        # Read CSV
        with open(input_csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = list(reader)

        if not rows:
            raise ValueError("CSV file is empty")

        # Auto-detect text column if not specified
        if text_column is None:
            possible_columns = [
                "text",
                "Text",
                "sentence",
                "Sentence",
                "content",
                "Content",
            ]
            for col in possible_columns:
                if col in rows[0]:
                    text_column = col
                    break

            if text_column is None:
                raise ValueError(
                    f"No text column found. Available columns: {list(rows[0].keys())}"
                )

        if text_column not in rows[0]:
            raise ValueError(f"Column '{text_column}' not found in CSV")

        # Generate output path if not provided
        if output_csv_path is None:
            base_name = os.path.splitext(input_csv_path)[0]
            output_csv_path = (
                f"{base_name}_translated_{self.source_language}_to_english.csv"
            )

        # Extract texts for batch translation
        texts = [row[text_column] for row in rows]

        print(
            f"Translating {len(texts)} texts from {self.source_language} to English..."
        )
        translations = self.translate_batch(texts, batch_size)

        # Write output CSV
        with open(output_csv_path, "w", newline="", encoding="utf-8") as file:
            fieldnames = list(rows[0].keys()) + ["english_translation"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()

            for row, translation in zip(rows, translations):
                row["english_translation"] = translation
                writer.writerow(row)

        print(f"Translation complete! Output saved to: {output_csv_path}")
        return output_csv_path
