from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import logging
from ..share import device
from sys import stderr
from tqdm import tqdm

__all__ = ["summarise", "summarise_in_chunks"]

def get_tokeniser_and_model(model_to_load="sshleifer/distilbart-cnn-12-6"):
    tokeniser = AutoTokenizer.from_pretrained(model_to_load)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_to_load)
    return tokeniser, model

def summarise(text_to_summarise, tokeniser=None, model=None, tok_limit=1024, length_penalty=.5, n_beams=2):
    if None in (tokeniser, model):
        tokeniser, model = get_tokeniser_and_model()
    preamble = "summarize:"
    prompt = f"{preamble} {text_to_summarise}"
    input_ids = tokeniser(prompt, return_tensors="pt").to(device).input_ids  # Batch size 1
    outputs = model.to(device).generate(
        input_ids, max_length=tok_limit, length_penalty=length_penalty, num_beams=n_beams
    )
    return tokeniser.decode(*outputs, skip_special_tokens=True)

def summarise_in_chunks(doc_list, tok_limit=1024, length_penalty=.5, n_beams=2):
    doc_list = doc_list.copy() # Destroy a duplicate
    tokeniser, model = get_tokeniser_and_model()
    # Since docs are segmented on either noEnergy or quiet parts, separate by periods
    doc_sep = ". " # (by 'period' I mean 'full stop')
    toks_chunked = [] # List of tokenised texts within the limit
    working_text = [] # Texts go here while processing
    tokenised = []    # Sufficiently small tokenisations go here
    chunk_sizes = []
    n_docs = len(doc_list)
    preamble = "summarize:"
    while doc_list:
        doc = doc_list.pop(0)
        working_text.append(doc)
        to_tokenise = preamble + doc_sep.join(working_text)
        # Temporarily silence warnings: deliberately surpassing token max. length limit
        logger = logging.getLogger("transformers.tokenization_utils_base")
        lvl = logger.level # store original logger level
        logger.setLevel(logging.ERROR)
        freshly_tokenised = tokeniser(to_tokenise, return_tensors="pt").to(device)
        logger.setLevel(lvl) # return to original level
        if len(freshly_tokenised[0]) < tok_limit:
            tokenised = freshly_tokenised
        else:
            # Store the number of documents which gave the tokens in the previous chunk
            chunk_sizes.append(len(working_text) - 1)
            # Create a new working text from the document that pushed it over the limit
            working_text = working_text[-1:]
            # Store the last approved tokenisation that was within the limit
            #print(f"Storing a chunk of {len(tokenised[0])}")
            toks_chunked.append(tokenised)
            tokenised = []
            freshly_tokenised = []
    if len(tokenised): # Finish off any leftovers
        #print(working_text)
        chunk_sizes.append(len(working_text))
        toks_chunked.append(tokenised)
    if sum(chunk_sizes) != n_docs:
        # Repeat the while loop process one final time (more than likely will give
        # a bad summary due to being too short...)
        #
        # The working text must be tokenised to finish off
        to_tokenise = preamble + doc_sep.join(working_text)
        # Temporarily silence warnings: deliberately surpassing token max. length limit
        logger = logging.getLogger("transformers.tokenization_utils_base")
        lvl = logger.level # store original logger level
        logger.setLevel(logging.ERROR)
        freshly_tokenised = tokeniser(to_tokenise, return_tensors="pt").to(device)
        logger.setLevel(lvl) # return to original level
        if len(freshly_tokenised[0]) < tok_limit:
            tokenised = freshly_tokenised
        else:
            raise ValueError("Could not finish chunking the input list in one pass")
        #else:
        #    # Store the number of documents which gave the tokens in the previous chunk
        #    chunk_sizes.append(len(working_text) - 1)
        #    # Create a new working text from the document that pushed it over the limit
        #    working_text = working_text[-1:]
        #    # Store the last approved tokenisation that was within the limit
        #    #print(f"Storing a chunk of {len(tokenised[0])}")
        #    toks_chunked.append(tokenised)
        #    tokenised = []
        #    freshly_tokenised = []
        if len(tokenised): # Finish off any leftovers
            chunk_sizes.append(len(working_text))
            toks_chunked.append(tokenised)
        if sum(chunk_sizes) != n_docs:
            breakpoint()
            raise ValueError("Did not correctly chunk the input list")
    summaries = []
    for toks in tqdm(toks_chunked):
        model_outputs = model.to(device).generate(
            toks.input_ids, max_length=tok_limit, length_penalty=length_penalty,
            num_beams=n_beams
        )
        summary = tokeniser.decode(*model_outputs, skip_special_tokens=True)
        summaries.append(summary)
    return summaries, chunk_sizes
