class Transcript:
    def __init__(self):
        self.choice = None
        while True:
            choice = input("Choose one (whisper/assembly): ").strip().lower()
            if choice in ["whisper", "assembly"]:
                self.choice = choice
                break
            print("Invalid choice. Please enter whisper or assembly.")
        print(f"You chose {self.choice}!")

    def download_youtube_audio(self):
        # importing packages
        import os

        from pytubefix import YouTube

        # url input from youtube
        yt = YouTube("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # extract only audio
        video = yt.streams.filter(only_audio=True).first()

        # set destination to save file
        destination = os.path.join("data", "transcript")
        if not os.path.exists(destination):
            os.makedirs(destination)

        # download the file
        out_file = video.download(output_path=destination)

        # save the file
        base, ext = os.path.splitext(out_file)
        new_file = base + ".mp3"
        os.rename(out_file, new_file)
        return new_file  # Return full path instead of just basename

    def seconds_to_hms(self, seconds):
        from datetime import timedelta

        return str(timedelta(seconds=int(seconds)))

    def whisper_model(self, audio_file_path):
        import csv
        import os

        import whisper

        model_type = "medium"
        output_dir = os.path.join("data", "transcript")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Use the full path that was returned by download_youtube_audio
        audio_path = audio_file_path

        output_path = os.path.join(output_dir, "transcript.csv")

        # Load the Whisper model
        print("Loading Whisper model...")
        model = whisper.load_model(model_type)
        print(f"Processing audio file: {audio_path}")

        # Verify the file exists
        if not os.path.exists(audio_path):
            print(f"Error: Audio file not found at {audio_path}")
            return

        print(f"Transcribing file: {audio_path}")

        # Transcribe the MP3 file
        try:
            result = model.transcribe(audio_path)

            # Save the transcription as a CSV file
            with open(output_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow(["Start (HH:MM:SS)", "End (HH:MM:SS)", "Sentence"])

                # Write transcription text (split into sentences)
                for segment in result["segments"]:
                    start_hms = self.seconds_to_hms(segment["start"])
                    end_hms = self.seconds_to_hms(segment["end"])
                    writer.writerow([start_hms, end_hms, segment["text"].strip()])

            print(f"Transcription saved to {output_path}")
            os.remove(audio_path)
        except Exception as e:
            print(f"Transcription error: {e}")

    def transcribe_audio_with_assemblyai(self, audio_file_path):
        import csv
        import os
        from datetime import timedelta

        import assemblyai as aai

        # Basic setup
        aai.settings.api_key = "fb2df8accbcb4f38ba02666862cd6216"

        # Setup paths
        output_dir = os.path.join("data", "transcript")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_path = os.path.join(output_dir, "transcript.csv")
        print("Starting transcription...")

        # Create transcriber and process file
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file_path)

        def format_time(seconds):
            td = timedelta(seconds=seconds)
            # Format as H:MM:SS (removes microseconds)
            return str(td).split(".")[0]

        # Save to CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Sentence Number", "Text", "Start Time", "End Time"])

            for i, sentence in enumerate(transcript.get_sentences(), 1):
                start_time_sec = round(sentence.start / 1000, 2)
                end_time_sec = round(sentence.end / 1000, 2)
                start_time_str = format_time(start_time_sec)
                end_time_str = format_time(end_time_sec)
                writer.writerow([i, sentence.text, start_time_str, end_time_str])
                print(f"Sentence {i} saved")
        print(f"Done! Check {output_path} for the output.")
        os.remove(audio_file_path)

    def process(self):
        try:
            audio_file_path = self.download_youtube_audio()
            print(f"Downloaded audio file: {audio_file_path}")

            if self.choice == "whisper":
                self.whisper_model(audio_file_path)
            elif self.choice == "assembly":
                self.transcribe_audio_with_assemblyai(audio_file_path)
        except Exception as e:
            print(f"Error in pipeline: {e}")


if __name__ == "__main__":
    transcript = Transcript()
    transcript.process()
