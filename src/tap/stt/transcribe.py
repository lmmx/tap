from transformers import Wav2Vec2ForCTC, Wav2Vec2Tokenizer
import librosa
import torch
from glob import glob


def transcribe_audio_file(audio_file, model_to_load="facebook/wav2vec2-base-960h"):
    # load model and tokenizer
    tokenizer = Wav2Vec2Tokenizer.from_pretrained(model_to_load)
    model = Wav2Vec2ForCTC.from_pretrained(model_to_load)
    audio_input, _ = librosa.load(audio_file, sr=16000)
    tok = tokenizer(audio_input, return_tensors="pt")
    input_values = tok.input_values
    logits = model(input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = tokenizer.batch_decode(predicted_ids)[0]
    return transcription
