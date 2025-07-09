import os
from datetime import timedelta

from pytubefix import YouTube  # noqa: E402


class Transcript:
    def get_input_type(self):
        """Get input type choice from user"""
        while True:
            input_choice = (
                input("Choose input type (youtube/video/csv): ").strip().lower()
            )
            if input_choice in ["youtube", "video", "csv"]:
                return input_choice
            print("Invalid choice. Please enter youtube, video, or csv.")

    def __init__(self):
        self.choice = None
        self.language = None
        self.translate_to_english = False
        self.input_type = None

        # Initialize settings
        self.initialize_settings()

    def initialize_settings(self):
        """Initialize or re-initialize all settings"""
        # Get input type choice
        self.input_type = self.get_input_type()

        # For CSV
        if self.input_type != "csv":
            # Get transcription service choice
            while True:
                choice = (
                    input("Choose transcription service (whisper/assembly): ")
                    .strip()
                    .lower()
                )
                if choice in ["whisper", "assembly"]:
                    self.choice = choice
                    break
                print("Invalid choice. Please enter whisper or assembly.")

        # Get language choice
        while True:
            lang_choice = (
                input("Choose language (english/french/spanish): ").strip().lower()
            )
            if lang_choice in ["english", "french", "spanish"]:
                self.language = lang_choice
                break
            print("Invalid choice. Please enter english, french, or spanish.")

        # Auto-translate for French/Spanish
        if self.language != "english":
            self.translate_to_english = True
            print("Will translate to English using Hugging Face models")

        print(f"Input type: {self.input_type}")
        if self.input_type != "csv":
            print(f"You chose {self.choice} for {self.language}")
        else:
            print(f"Processing CSV in {self.language}")

    def verify_youtube_link(self):
        """Get YouTube URL from user, verify it exists, and confirm with user"""
        while True:
            url = input("Enter YouTube URL: ").strip()
            if not url:
                print("Please enter a valid URL.")
                continue

            try:
                print("Checking URL...")
                yt = YouTube(url)
                title = yt.title
                duration = str(timedelta(seconds=yt.length))

                print("\nVideo found:")
                print(f"Title: {title}")
                print(f"Duration: {duration}")

                while True:
                    confirm = (
                        input("Is this the correct video? (yes/no): ").strip().lower()
                    )
                    if confirm in ["yes", "y"]:
                        return yt
                    elif confirm in ["no", "n"]:
                        break
                    print("Please enter yes or no.")

                # If user said no, ask if they want to try another URL
                retry = input("Try another URL? (yes/no): ").strip().lower()
                if retry in ["no", "n"]:
                    return None

            except Exception as e:
                print(f"Error: Could not access YouTube video - {e}")
                retry = input("Try another URL? (yes/no): ").strip().lower()
                if retry in ["no", "n"]:
                    return None

    def download_youtube_audio(self, yt_object=None):
        """Download audio from YouTube video"""
        import os

        from pytubefix import YouTube  # noqa: E402

        if yt_object is None:
            # Default behavior for backward compatibility
            yt = YouTube("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        else:
            yt = yt_object

        try:
            # extract only audio
            video = yt.streams.filter(only_audio=True).first()
            if video is None:
                print("Error: No audio stream found for this video")
                return None

            # set destination to save file
            destination = os.path.join("data", "transcript")
            if not os.path.exists(destination):
                os.makedirs(destination)
                print(f"Created directory: {destination}")

            # download the file
            print("Downloading audio...")
            out_file = video.download(output_path=destination)
            print(f"Downloaded to: {out_file}")

            # save the file
            base, ext = os.path.splitext(out_file)
            new_file = base + ".mp3"

            # Check if file exists before renaming
            if not os.path.exists(out_file):
                print(f"Error: Downloaded file not found at {out_file}")
                return None

            # Rename to .mp3
            os.rename(out_file, new_file)
            print(f"Renamed to: {new_file}")

            # Verify the final file exists
            if not os.path.exists(new_file):
                print(f"Error: Final audio file not found at {new_file}")
                return None

            print(f"Audio file ready: {new_file}")
            return new_file

        except Exception as e:
            print(f"Error downloading audio: {e}")
            return None

    def get_video_file_path(self):
        """Get video file path from user and verify it exists"""
        while True:
            file_path = input("Enter the path to your video file: ").strip()

            # Remove quotes if user wrapped path in quotes
            file_path = file_path.strip("\"'")

            if not file_path:
                print("Please enter a valid file path.")
                continue

            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                retry = input("Try another path? (yes/no): ").strip().lower()
                if retry in ["no", "n"]:
                    return None
                continue

            # Check if it's a video file (basic extension check)
            video_extensions = [
                ".mp4",
                ".avi",
                ".mov",
                ".mkv",
                ".wmv",
                ".flv",
                ".webm",
                ".m4v",
            ]
            file_ext = os.path.splitext(file_path)[1].lower()

            if file_ext not in video_extensions:
                print(f"Warning: {file_ext} might not be a supported video format.")
                confirm = input("Continue anyway? (yes/no): ").strip().lower()
                if confirm not in ["yes", "y"]:
                    continue

            return file_path

    def convert_video_to_audio(self, video_path):
        """Convert video file to audio using ffmpeg"""
        try:
            import subprocess

            # Set destination
            destination = os.path.join("data", "transcript")
            if not os.path.exists(destination):
                os.makedirs(destination)

            # Generate output filename
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            audio_path = os.path.join(destination, f"{base_name}.mp3")

            # Use ffmpeg to extract audio
            command = [
                "ffmpeg",
                "-i",
                video_path,
                "-vn",
                "-acodec",
                "mp3",
                "-ab",
                "192k",
                "-ar",
                "44100",
                "-y",
                audio_path,
            ]

            print("Converting video to audio...")
            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Error converting video: {result.stderr}")
                return None

            print(f"Audio extracted to: {audio_path}")
            return audio_path

        except FileNotFoundError:
            print(
                "Error: ffmpeg not found. Please install ffmpeg to convert video files."
            )
            return None
        except Exception as e:
            print(f"Error converting video: {e}")
            return None

    def get_csv_file_path(self):
        """Get CSV file path from user and verify it exists"""
        while True:
            file_path = input("Enter the path to your CSV file: ").strip()

            # Remove quotes if user wrapped path in quotes
            file_path = file_path.strip("\"'")

            if not file_path:
                print("Please enter a valid file path.")
                continue

            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                retry = input("Try another path? (yes/no): ").strip().lower()
                if retry in ["no", "n"]:
                    return None
                continue

            # Check if it's a CSV file
            if not file_path.lower().endswith(".csv"):
                print("Warning: File doesn't have .csv extension.")
                confirm = input("Continue anyway? (yes/no): ").strip().lower()
                if confirm not in ["yes", "y"]:
                    continue

            return file_path

    def process_csv_translation(self, csv_path):
        """Process CSV file for translation"""
        if not self.translate_to_english:
            print(
                "No translation needed for English text or translation not requested."
            )
            return

        try:
            from translator import HuggingFaceTranslator

            print("Initializing translator...")
            translator = HuggingFaceTranslator(self.language)
            print("Translator ready!")

            # Use the translator's CSV method
            output_path = translator.translate_csv(csv_path)
            print(f"Translation complete! Output saved to: {output_path}")

        except Exception as e:
            print(f"Error processing CSV: {e}")

    def seconds_to_hms(self, seconds):
        from datetime import timedelta

        return str(timedelta(seconds=int(seconds)))

    def get_whisper_language_code(self):
        """Get Whisper language code from user selection"""
        lang_map = {"english": "en", "french": "fr", "spanish": "es"}
        return lang_map.get(self.language, "en")

    def get_assemblyai_language_code(self):
        """Get AssemblyAI language code from user selection"""
        lang_map = {"english": "en", "french": "fr", "spanish": "es"}
        return lang_map.get(self.language, "en")

    def check_ffmpeg_availability(self):
        """Check if ffmpeg is available for Whisper"""
        try:
            import subprocess

            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def whisper_model(self, audio_file_path):
        import csv
        import os

        import whisper  # noqa: E402

        # Check if ffmpeg is available
        if not self.check_ffmpeg_availability():
            print("\n❌ ERROR: ffmpeg is required for Whisper but not found!")
            return

        model_type = "medium"
        output_dir = os.path.join("data", "transcript")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Use the full path that was returned by download_youtube_audio
        audio_path = audio_file_path

        # Set output filename
        if self.language == "english":
            output_filename = "transcript_english.csv"
        else:
            output_filename = f"transcript_{self.language}_to_english.csv"

        output_path = os.path.join(output_dir, output_filename)

        # Load the Whisper model
        print("Loading Whisper model...")
        model = whisper.load_model(model_type)
        print(f"Processing audio file: {audio_path}")

        # Verify the file exists and get its size
        if not os.path.exists(audio_path):
            print(f"Error: Audio file not found at {audio_path}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Directory contents of {os.path.dirname(audio_path)}:")
            try:
                for item in os.listdir(os.path.dirname(audio_path)):
                    print(f"  {item}")
            except Exception as e:
                print(f"  Could not list directory: {e}")
            return

        # Check if file is empty
        file_size = os.path.getsize(audio_path)
        print(f"Audio file size: {file_size} bytes")
        if file_size == 0:
            print("Error: Audio file is empty")
            return

        print(f"Transcribing file: {audio_path} in {self.language}")

        # Transcribe the MP3 file with specified language
        try:
            language_code = self.get_whisper_language_code()
            print(f"Using language code: {language_code}")

            result = model.transcribe(audio_path, language=language_code)

            # Check if transcription result is valid
            if not result or "segments" not in result:
                print("Error: No transcription result or segments found")
                return

            print(f"Transcription completed. Found {len(result['segments'])} segments")

            # Initialize translator if needed
            translator = None
            if self.translate_to_english:
                from translator import HuggingFaceTranslator

                print("Initializing translator...")
                translator = HuggingFaceTranslator(self.language)
                print("Translator ready!")

            # Save the transcription as a CSV file
            with open(output_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write header based on language
                if self.language == "english":
                    writer.writerow(["Start (HH:MM:SS)", "End (HH:MM:SS)", "Sentence"])
                else:
                    # For non-English
                    writer.writerow(
                        [
                            "Start (HH:MM:SS)",
                            "End (HH:MM:SS)",
                            "Sentence",
                            f"Text_{self.language}",
                        ]
                    )

                # Write transcription text (split into sentences)
                for i, segment in enumerate(result["segments"]):
                    start_hms = self.seconds_to_hms(segment["start"])
                    end_hms = self.seconds_to_hms(segment["end"])
                    original_text = segment["text"].strip()

                    print(
                        f"Processing segment {i+1}/{len(result['segments'])}: "
                        f"{original_text[:50]}..."
                    )

                    if self.translate_to_english and translator:
                        print(f"Translating: {original_text[:50]}...")
                        try:
                            translated_text = translator.translate(original_text)
                            writer.writerow(
                                [start_hms, end_hms, translated_text, original_text]
                            )
                        except Exception as e:
                            print(f"Translation error for segment {i+1}: {e}")
                            # Write original text if translation fails
                            writer.writerow(
                                [start_hms, end_hms, original_text, original_text]
                            )
                    else:
                        writer.writerow([start_hms, end_hms, original_text])

            print(f"Transcription saved to {output_path}")

            # Only remove audio file if it was downloaded from YouTube
            if self.input_type in ["youtube"]:
                try:
                    os.remove(audio_path)
                    print(f"Cleaned up audio file: {audio_path}")
                except Exception as e:
                    print(f"Warning: Could not remove audio file: {e}")

        except Exception as e:
            print(f"Transcription error: {e}")
            if "ffmpeg" in str(e).lower() or "file specified" in str(e).lower():
                print("\n❌ This looks like an ffmpeg issue!")
            import traceback

            print("Full error traceback:")
            traceback.print_exc()

    def transcribe_audio_with_assemblyai(self, audio_file_path):
        import csv
        import os
        from datetime import timedelta

        import assemblyai as aai  # noqa: E402

        # Basic setup
        aai.settings.api_key = "fb2df8accbcb4f38ba02666862cd6216"

        # Setup paths
        output_dir = os.path.join("data", "transcript")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Set output filename
        if self.language == "english":
            output_filename = "transcript_english.csv"
        else:
            output_filename = f"transcript_{self.language}_to_english.csv"

        output_path = os.path.join(output_dir, output_filename)
        print(f"Starting transcription in {self.language}...")

        # Verify the audio file exists
        if not os.path.exists(audio_file_path):
            print(f"Error: Audio file not found at {audio_file_path}")
            return

        # Create transcriber with language configuration
        config = aai.TranscriptionConfig(
            language_code=self.get_assemblyai_language_code()
        )
        transcriber = aai.Transcriber(config=config)

        try:
            transcript = transcriber.transcribe(audio_file_path)

            def format_time(seconds):
                td = timedelta(seconds=seconds)
                # Format as H:MM:SS (removes microseconds)
                return str(td).split(".")[0]

            # Initialize translator if needed
            translator = None
            if self.translate_to_english:
                from translator import HuggingFaceTranslator

                print("Initializing translator...")
                translator = HuggingFaceTranslator(self.language)
                print("Translator ready!")

            # Save to CSV
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                if self.translate_to_english:
                    writer.writerow(
                        [
                            "Sentence Number",
                            f"Original ({self.language.title()})",
                            "Text",
                            "Start Time",
                            "End Time",
                        ]
                    )
                else:
                    writer.writerow(
                        ["Sentence Number", "Text", "Start Time", "End Time"]
                    )

                sentences = transcript.get_sentences()
                print(f"Found {len(sentences)} sentences")

                for i, sentence in enumerate(sentences, 1):
                    start_time_sec = round(sentence.start / 1000, 2)
                    end_time_sec = round(sentence.end / 1000, 2)
                    start_time_str = format_time(start_time_sec)
                    end_time_str = format_time(end_time_sec)

                    original_text = sentence.text

                    if self.translate_to_english and translator:
                        print(f"Translating sentence {i}: {original_text[:50]}...")
                        try:
                            translated_text = translator.translate(original_text)
                            writer.writerow(
                                [
                                    i,
                                    original_text,
                                    translated_text,
                                    start_time_str,
                                    end_time_str,
                                ]
                            )
                        except Exception as e:
                            print(f"Translation error for sentence {i}: {e}")
                            writer.writerow(
                                [
                                    i,
                                    original_text,
                                    original_text,
                                    start_time_str,
                                    end_time_str,
                                ]
                            )
                    else:
                        writer.writerow(
                            [i, original_text, start_time_str, end_time_str]
                        )

                    print(f"Sentence {i} saved")

            print(f"Done! Check {output_path} for the output.")

            # Only remove audio file if we created it
            if self.input_type in ["youtube"]:
                try:
                    os.remove(audio_file_path)
                    print(f"Cleaned up audio file: {audio_file_path}")
                except Exception as e:
                    print(f"Warning: Could not remove audio file: {e}")

        except Exception as e:
            print(f"AssemblyAI transcription error: {e}")
            import traceback

            print("Full error traceback:")
            traceback.print_exc()

    def process(self):
        """Main processing method that handles different input types"""
        while True:  # Loop to allow going back to input type selection
            try:
                if self.input_type == "youtube":
                    # Get and verify YouTube URL
                    yt_object = self.verify_youtube_link()
                    if yt_object is None:
                        print("YouTube URL verification failed.")
                        # Go back to input type selection and re-initialize all settings
                        self.initialize_settings()
                        continue

                    # Download audio
                    audio_file_path = self.download_youtube_audio(yt_object)
                    if audio_file_path is None:
                        print("Failed to download audio from YouTube.")
                        # Go back to input type selection and re-initialize all settings
                        self.initialize_settings()
                        continue

                    print(f"Downloaded audio file: {audio_file_path}")

                    # Transcribe
                    if self.choice == "whisper":
                        self.whisper_model(audio_file_path)
                    elif self.choice == "assembly":
                        self.transcribe_audio_with_assemblyai(audio_file_path)
                    break  # Success, exit the loop

                elif self.input_type == "video":
                    # Get video file path
                    video_path = self.get_video_file_path()
                    if video_path is None:
                        print("No valid video file provided.")
                        # Go back to input type selection and re-initialize all settings
                        self.initialize_settings()
                        continue

                    # Convert to audio
                    audio_file_path = self.convert_video_to_audio(video_path)
                    if audio_file_path is None:
                        print("Failed to convert video to audio.")
                        # Go back to input type selection and re-initialize all settings
                        self.initialize_settings()
                        continue

                    print(f"Audio extracted: {audio_file_path}")

                    # Transcribe
                    if self.choice == "whisper":
                        self.whisper_model(audio_file_path)
                    elif self.choice == "assembly":
                        self.transcribe_audio_with_assemblyai(audio_file_path)
                    break  # Success, exit the loop

                elif self.input_type == "csv":
                    # Get CSV file path
                    csv_path = self.get_csv_file_path()
                    if csv_path is None:
                        print("No valid CSV file provided.")
                        # Go back to input type selection and re-initialize all settings
                        self.initialize_settings()
                        continue

                    # Process CSV for translation
                    self.process_csv_translation(csv_path)
                    break  # Success, exit the loop

            except Exception as e:
                print(f"Error in pipeline: {e}")
                import traceback

                print("Full error traceback:")
                traceback.print_exc()

                retry = (
                    input("Try again with different settings? (yes/no): ")
                    .strip()
                    .lower()
                )
                if retry in ["yes", "y"]:
                    # Re-initialize all settings when retrying
                    self.initialize_settings()
                    continue
                else:
                    break


if __name__ == "__main__":
    transcript = Transcript()
    transcript.process()
