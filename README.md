# dex ⠶ tap

`tap` is an audio transcriber for web radio

## Usage

### Download execution

For a given program, we can get its URLs for the day's show as:

```py
from tap.scrape import get_program_urls
get_program_urls()
```

- Currently this is defaulting to `bbc⠶r4⠶today`

To get its URLs for yesterday, pass the `ymd_ago` argument (a tuple):

```py
urls = get_program_urls(ymd_ago=(0,0,-1))
```

or pass the `ymd` argument [either a `datetime.date` or an integer tuple
`(y,m,d)`] for an absolute date:

```py
urls = get_program_urls(ymd=(2021,2,8))
```

These URLs can then be passed to the async scraper

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
