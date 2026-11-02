"""Command-line interface for paths, model contracts and explicit batch inference."""

import argparse
import contextlib
import csv
import json
import logging
import sys
from pathlib import Path

from ._version import __version__
from .models import ModelError, create_model_manifest, inspect_model, list_models, load_model
from .paths import paths_info


@contextlib.contextmanager
def _diagnostics_to_stderr():
    """Keep JSON stdout usable even if the library initialized logging earlier."""
    streams = []
    for name, logger in logging.Logger.manager.loggerDict.copy().items():
        if name.startswith("geonormml") and isinstance(logger, logging.Logger):
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    streams.append((handler, handler.stream))
                    handler.stream = sys.stderr
    try:
        with contextlib.redirect_stdout(sys.stderr):
            yield
    finally:
        for handler, stream in streams:
            handler.stream = stream


def _dispatch(args):
    if args.command == "paths":
        return paths_info()
    if args.command == "models":
        return {"models": list_models(args.directory)}
    if args.command == "inspect":
        return inspect_model(args.model, verify=not args.metadata_only)
    if args.command == "example":
        from .examples import create_example

        return create_example(args.output)
    if args.command == "manifest":
        metadata = json.loads(args.metadata.read_text(encoding="utf-8-sig"))
        return {"manifest": str(create_model_manifest(args.model_file, metadata, output=args.output))}
    if args.command == "predict":
        import pandas as pd

        model = load_model(args.model, trusted=args.trust_model)
        output = args.output.expanduser().resolve()
        if output.exists():
            raise FileExistsError(f"Output already exists; choose a new file: {output}")
        with args.input.expanduser().open(encoding="utf-8-sig", newline="") as stream:
            header = next(csv.reader(stream), [])
        if not header or len(set(header)) != len(header) or any(not name for name in header):
            raise ModelError("invalid_input", "CSV requires a nonempty, unique header")
        # Preserve lexical IDs (001 and NA). The input contract parses only its
        # numeric feature columns; blank numeric measurements remain missing.
        frame = pd.read_csv(args.input.expanduser(), dtype=object, keep_default_na=False)
        predictions = model.predict(frame, id_column=args.id_column)
        text = predictions.to_csv(index=False)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8", newline="") as stream:
            stream.write(text)
        return {
            "output": str(output),
            "rows": len(predictions),
            "predicted": int(predictions.status.eq("predicted").sum()),
            "rejected": int(predictions.status.eq("rejected").sum()),
            **predictions.attrs,
        }
    raise ModelError("invalid_command", "Unknown command")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("paths", help="Show portable paths without creating directories")
    models = commands.add_parser("models", help="List model manifests without deserializing them")
    models.add_argument("--directory", type=Path)
    inspect = commands.add_parser("inspect", help="Verify a manifest, bytes and dependency versions without loading")
    inspect.add_argument("model")
    inspect.add_argument("--metadata-only", action="store_true")
    example = commands.add_parser("example", help="Create an explicitly synthetic runnable example in a new directory")
    example.add_argument("--output", type=Path, required=True)
    manifest = commands.add_parser("manifest", help="Attach a known training contract to an existing artifact")
    manifest.add_argument("--model-file", type=Path, required=True)
    manifest.add_argument("--metadata", type=Path, required=True)
    manifest.add_argument("--output", type=Path)
    predict = commands.add_parser("predict", help="Predict a CSV with a trusted model and explicit input contract")
    predict.add_argument("--model", required=True)
    predict.add_argument("--input", type=Path, required=True)
    predict.add_argument("--output", type=Path, required=True)
    predict.add_argument("--id-column")
    predict.add_argument("--trust-model", action="store_true", help="Acknowledge that this model's source is trusted")
    args = parser.parse_args(argv)
    try:
        with _diagnostics_to_stderr():
            result = _dispatch(args)
        print(json.dumps({"ok": True, **result}, allow_nan=False))
        return 0
    except ModelError as error:
        payload = error.to_dict()
    except (OSError, ValueError, TypeError) as error:
        payload = {"code": "invalid_request", "message": str(error)}
    print(json.dumps({"ok": False, "error": payload}), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
