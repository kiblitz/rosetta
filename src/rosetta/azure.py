import os
import random

import azure.cognitiveservices.speech as speechsdk


class Foundry:
    def __init__(self, voice_ids):
        self.foundry_api_key = os.environ.get("FOUNDRY_API_KEY")
        self.foundry_api_endpoint = os.environ.get("FOUNDRY_API_ENDPOINT")

        def _speech_synthesizer(voice_id):
            speech_config = speechsdk.SpeechConfig(
                subscription=self.foundry_api_key,
                endpoint=self.foundry_api_endpoint,
            )
            speech_config.speech_synthesis_voice_name = voice_id
            audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

            return speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config,
            )

        self.speech_synthesizers = {
            voice_id: _speech_synthesizer(voice_id) for voice_id in voice_ids
        }

    def speak(self, text, *, voice_id=None):
        voice_id = (
            voice_id
            if voice_id is not None
            else random.choice(list(self.speech_synthesizers))
        )
        return self.speech_synthesizers[voice_id].speak_text_async(text).get()

    def run(self):
        print("Enter some text >")
        text = input()
        speech_synthesis_result = self.speak(text)

        if (
            speech_synthesis_result.reason
            == speechsdk.ResultReason.SynthesizingAudioCompleted
        ):
            return
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            error_msg = "Speech synthesis canceled: {}".format(
                cancellation_details.reason
            )

            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    error_msg += "\nError details: {}".format(
                        cancellation_details.error_details
                    )
                    error_msg += "\nFOUNDRY_API_KEY: {}".format(self.foundry_api_key)
                    error_msg += "\nFOUNDRY_API_ENDPOINT: {}".format(
                        self.foundry_api_endpoint
                    )

            raise RuntimeError(error_msg)
