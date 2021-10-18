from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import librosa
import torch
from glob import glob


def transcribe_audio_file(
    audio_file,
    #model_to_load="facebook/wav2vec2-base-960h",
    #model_to_load="facebook/wav2vec2-large-960h-lv60-self",
    model_to_load="facebook/wav2vec2-large-robust-ft-libri-960h",
):
    # load model and tokenizer
    #print(f"Using {model_to_load}")
    processor = Wav2Vec2Processor.from_pretrained(model_to_load)
    model = Wav2Vec2ForCTC.from_pretrained(model_to_load)
    sr = 16000
    audio_input, _ = librosa.load(audio_file, sr=sr)
    proc = processor(audio_input, return_tensors="pt", padding="longest", sampling_rate=sr)
    input_values = proc.input_values
    logits = model(input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]
    return transcription
