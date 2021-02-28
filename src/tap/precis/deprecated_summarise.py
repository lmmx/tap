from transformers import pipeline
from transformers import AutoTokenizer, AutoModelWithLMHead
from transformers import T5Tokenizer, T5ForConditionalGeneration
from transformers import LongformerTokenizer, EncoderDecoderModel
from ..share import device

def get_tokeniser_and_model(model_to_load="t5-large"):
    #tokeniser = T5Tokenizer.from_pretrained(model_to_load)
    tokeniser = AutoTokenizer.from_pretrained(model_to_load)
    #model = T5ForConditionalGeneration.from_pretrained(model_to_load)
    model = AutoModelWithLMHead.from_pretrained(model_to_load)
    return tokeniser, model

def summarise(text_to_summarise, tokeniser=None, model=None, max_length=500, length_penalty=.5, n_beams=2):
    if not (tokeniser or model):
        tokeniser, model = get_tokeniser_and_model()
    preamble = "summarize"
    prompt = f"{preamble}: {text_to_summarise}"
    input_ids = tokeniser(prompt, return_tensors="pt").to(device)  # Batch size 1
    outputs = model(input_ids, max_length=max_length, length_penalty=length_penalty, num_beams=n_beams).to(device)
    return tokeniser.decode(**outputs)

def summarise_distilbart_pipeline(text_to_summarise):
    summariser = pipeline("summarization", device=0)
    summary = summariser(text_to_summarise)[0]['summary_text']
    return summary

def summarise_longformer(long_text_to_summarise):
    model_to_load = "patrickvonplaten/longformer2roberta-cnn_dailymail-fp16"
    tok_to_load = "allenai/longformer-base-4096"
    tokeniser = LongformerTokenizer.from_pretrained(tok_to_load)
    model = EncoderDecoderModel.from_pretrained(model_to_load)
    input_ids = tokeniser(long_text_to_summarise, return_tensors="pt").input_ids#.to(device).input_ids
    outputs = model.generate(input_ids)#.to(device)
    summary = tokeniser.decode(outputs[0], skip_special_tokens=True)
    return summary
