# AtmoGraph

**Supply Chain Ripple Effect Predictor**

AtmoGraph is a focused semiconductor supply-chain risk analysis project. The current project scope uses monthly UN Comtrade observations for electronic integrated circuits (HS 8542), enriched with semiconductor supplier and production-stage context from the ETO Semiconductor Supply Chain dataset.

See [`docs/PROJECT_SCOPE.md`](docs/PROJECT_SCOPE.md) for the project boundary, data choices, prediction target, architecture, team split, and mentor-approval item.

## First data-engineering step: validate ETO source tables

The ETO source is maintained by Georgetown CSET in [`georgetown-cset/eto-chip-explorer`](https://github.com/georgetown-cset/eto-chip-explorer). AtmoGraph pins the five CSV downloads to upstream commit [`98dcb78`](https://github.com/georgetown-cset/eto-chip-explorer/commit/98dcb7821ff96d723a2ca4ff0feed77e591b204e) so the same source snapshot can be retrieved again.

From the repository root, download the source CSVs and validate their schemas and cross-table IDs:

```bash
python scripts/validate_eto_data.py --download
```

The files are saved under `data/eto/` and are not intended to be committed. Existing files are preserved; pass `--overwrite` only when you deliberately want to replace them with the pinned upstream snapshot.

To validate files already downloaded:

```bash
python scripts/validate_eto_data.py
```

The command prints a JSON report and exits non-zero when required files, columns, IDs, references, years, or market-share values fail validation. Warnings identify source conditions that require care, including repeated identical provider rows. ETO market-share values are optional and rounded in the source; the validator does not enforce that supplier shares sum to 100%.

Run the offline unit tests with:

```bash
python -m unittest discover -s tests -v
```

The validator uses only the Python standard library. It does not synthesize records, fill missing trade values, or change the upstream CSVs.
