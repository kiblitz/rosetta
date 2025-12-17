import os
import random

import azure.cognitiveservices.speech as speechsdk


class Foundry:
    def __init__(self, voice_ids=[]):
        self.foundry_api_key = os.environ.get("FOUNDRY_API_KEY")
        self.foundry_api_endpoint = os.environ.get("FOUNDRY_API_ENDPOINT")
        self.speech_synthesizers = {}
        self.update_speech_synthesizer(voice_ids)
        self.speech_synthesizer_for_generic_ops = self._speech_synthesizer(None)
        self.voice_id_list = None

    def update_speech_synthesizer(self, voice_ids):
        self.speech_synthesizers |= {
            voice_id: self._speech_synthesizer(voice_id) for voice_id in voice_ids
        }

    def _speech_synthesizer(self, voice_id):
        speech_config = speechsdk.SpeechConfig(
            subscription=self.foundry_api_key,
            endpoint=self.foundry_api_endpoint,
        )
        if voice_id is not None:
            speech_config.speech_synthesis_voice_name = voice_id
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

        return speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

    def get_voice_id_list(self, use_cache=True):
        if use_cache and self.voice_id_list is not None:
            return self.voice_id_list

        speech_synthesis_result = (
            self.speech_synthesizer_for_generic_ops.get_voices_async().get()
        )
        if (
            speech_synthesis_result is not None
            and speech_synthesis_result.reason
            == speechsdk.ResultReason.VoicesListRetrieved
        ):
            self.voice_id_list = [
                voice.short_name for voice in speech_synthesis_result.voices
            ]
            return self.voice_id_list

        error_msg = self._foundry_speech_synthesis_result_error_msg(
            speech_synthesis_result
        )
        raise RuntimeError(error_msg)

    def speak(self, text, *, voice_id=None):
        voice_id = (
            voice_id
            if voice_id is not None
            else random.choice(list(self.speech_synthesizers))
        )
        speech_synthesis_result = (
            self.speech_synthesizers[voice_id].speak_text_async(text).get()
        )

        if (
            speech_synthesis_result is not None
            and speech_synthesis_result.reason
            == speechsdk.ResultReason.SynthesizingAudioCompleted
        ):
            return

        error_msg = self._foundry_speech_synthesis_result_error_msg(
            speech_synthesis_result
        )

        raise RuntimeError(error_msg)

    def _foundry_speech_synthesis_result_error_msg(self, result):
        if result is None:
            error_msg = "Speech synthesis result is null"
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            error_msg = "Speech synthesis canceled: {}".format(
                cancellation_details.reason
            )

            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    error_msg += "\nError details: {}".format(
                        cancellation_details.error_details
                    )
        else:
            error_msg = "Speech synthesis error with reason: {}".format(result.reason)

        error_msg += "\n" + self._foundry_api_msg()
        return error_msg

    def _foundry_api_msg(self):
        msg = "FOUNDRY_API_KEY: {}".format(self.foundry_api_key)
        msg += "\nFOUNDRY_API_ENDPOINT: {}".format(self.foundry_api_endpoint)
        return msg
