# dex ⠶ tap

`tap` is an audio transcriber for web radio

## Usage

### Stream downloading

- **URL retrieval**

  For a given program, we can populate a `Stream` object with its
  URLs for the day's episode as:
  
  ```py
  from tap.scrape import load_stream
  stream = load_stream()
  ```
  
  - Currently this is defaulting to `bbc⠶r4⠶today`
  
  To get its URLs for the day before yesterday, pass the `ymd_ago` argument (a tuple):
  
  ```py
  load_stream(ymd_ago=(0,0,-2))
  ```
  ⇣
  ```STDOUT
  stream⠶1716 from episode⠶2021-02-08 of program⠶today on station⠶r4 on channel⠶bbc
  ```
  
  or pass the `ymd` argument [either a `datetime.date` or an integer tuple
  `(y,m,d)`] for an absolute date:
  
  ```py
  stream = load_stream(ymd=(2021,2,8))
  ```

- **URL download**

  (Optional) To handle or inspect a stream's URLs manually, `stream.stream_urls` is a generator
  which can be iterated over:
  
  ```py
  for u in stream.stream_urls:
      ... # handle the URL content here
  ```

  These URLs can then be downloaded ("pulled" asynchronously, without re-downloading
  any stream parts previously downloaded e.g. due to connection interruption).
  
  ```py
  stream.pull()
  ```
  
  (TODO)

### Catalogue exploration

The namespace of the channels provides an inventory, so running:

```py
from tap import tap.data.store.channels
```

and typing `channels.`<kbd>Tab</kbd> will enumerate the available channels
(i.e. those already stored).

For a given channel, tab completion (in future: command line tab completion)
will give the path to a _channel » station » program_, e.g.

```py
channels.bbc.r4.today
```

(TBC)

## Requirements

- Python 3
- Libraries: (none)
