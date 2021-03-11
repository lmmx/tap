from .summarise import summarise_in_chunks
from enum import Enum
from sys import stderr

__all__ = ["DocSummaryExportEnum"]

class DocumentSummaryExporter:
    """
    Base class (must be subclassed with `transform_document` method
    defined to initialise successfully).

    Upon initialisation, summarise the documents in chunks (using
    `tap.scrape.summarise.summarise_in_chunks`) determined by the
    token limit of the summarisation model (for Wav2Vec2: 1024 tokens).

    Write the generated summaries to files in the format specified in
    the `DocSummaryExportEnum` (e.g. "md" gives `MarkdownExport`,
    formatting the generated summaries as markdown).
    """
    def __init__(self, documents, to):
        chunk_seek = 0
        doc_sep = ". "
        print("Obtaining summaries...", file=stderr)
        summaries, chunk_sizes = summarise_in_chunks(documents)
        print("...Finished")
        self.zf_len = len(str(len(chunk_sizes))) # zfill to match number of chunks
        self.out_files = []
        for i, (summary, chunk_size) in enumerate(zip(summaries, chunk_sizes)):
            merge_doc = doc_sep.join(documents[chunk_seek: chunk_seek + chunk_size])
            export_content = self.transform_summary(summary=summary, document=merge_doc)
            chunk_seek += chunk_size
            output_filename = self.get_output_filename(i)
            if not to.exists():
                to.mkdir(parents=True)
            elif not to.is_dir():
                raise FileNotFoundError(f"{to=} is a file not a directory")
            out_file = to / output_filename
            with open(out_file, "w") as f:
                print(f"Writing file {i} to {output_filename}", file=stderr)
                f.write(export_content)
            self.out_files.append(out_file)

    def get_output_filename(self, i, prefix="", suffix=""):
        return f"{i:0{self.zf_len}d}.{self.ext}"

    def wire_post_hook(self, *args, **kwargs):
        pass # no post hook by default: return value is `None`

class PlainTextExport(DocumentSummaryExporter):
    """
    Export the summary and the document in a single text file, separated by a newline.
    """
    ext = "txt"
    def transform_summary(self, summary, document):
        sections = [f"Summary: {summary}\n", f"Full: {document}\n"]
        summary_file_string = "\n".join(sections)
        return summary_file_string


class MarkdownExport(DocumentSummaryExporter):
    ext = "md"
    def transform_summary(self, summary, document):
        md_summary, md_document = [
            "- " + original.strip(" ")
            for original in (summary, document)
        ]
        sections = ["# Summary", f"{md_summary}", "# Full", f"{md_document}\n"]
        summary_file_string = "\n\n".join(sections)
        return summary_file_string


class GitHubMarkdownExport(DocumentSummaryExporter):
    ext = "md"
    def transform_summary(self, summary, document):
        md_document = "- " + document.strip(" ")
        sections = [
            f"<details><summary>{summary}</summary>",
            "<p>",
            f"{md_document}",
            "</p>",
            "</details>"
        ]
        summary_file_string = "\n\n".join(sections)
        return summary_file_string


class LeverMmdExport(DocumentSummaryExporter):
    ext = "mmd"
    quill_template_name = "radio_transcript_summaries"
    multinode_detail = False
    def transform_summary(self, summary, document):
        # Simplified approximation of proper MMD format version of plaintext
        mmd_summary = "-?" + summary.strip(" ")
        doc_stripped = document.strip(" ")
        mmd_document = "-:" + (
            doc_stripped.replace(". ", "\n-")
            if self.multinode_detail
            else doc_stripped
        )
        sections = [f"{mmd_summary}", f"{mmd_document}\n"]
        summary_file_string = "\n".join(sections)
        return summary_file_string

    def wire_post_hook(self, single_file=False):
        if single_file:
            merged_output_filename = f"transcript_summaries.{self.ext}"
            merged_output_file = self.out_files[0].parent / merged_output_filename
            if merged_output_file.exists():
                # Overwrite existing file (blank it)
                with open(merged_output_file, "w") as f:
                    f.write("")
            with open(merged_output_file, "a") as fw:
                for out_file in self.out_files[:-1]:
                    with open(out_file, "r") as fr:
                        print(fr.read(), file=fw) # print puts newline between each
                with open(self.out_files[-1], "r") as fr:
                    print(fr.read(), file=fw, end="") # Don't double final newline
            wire_files = [merged_output_filename]
        else:
            wire_files = self.out_files
        wire_config = [
            "\n".join([
                f"-transmit⠶{wire_file}\n"
                f"-..template⠶{self.quill_template_name}\n"
            ])
            for wire_file in wire_files
        ]
        wire_string = "\n\n".join(wire_config)
        return wire_string

class DocSummaryExportEnum(Enum):
    txt = PlainTextExport
    md = MarkdownExport
    ghmd = GitHubMarkdownExport
    mmd = LeverMmdExport
