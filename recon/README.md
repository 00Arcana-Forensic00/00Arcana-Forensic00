# arcana-recon

Repair photographed or scanned document pages damaged by lighting, map their
block layout and reading order, and seal the result in an ARCN v1 vault blob
that the Rust `arcana-vault` crate can also open.

Everything here is classical image processing (OpenCV + NumPy). There is no
machine-learning model in this package.

## Quick start

```sh
cd recon
pip install -e '.[test]'
export ARCANA_VAULT_PASSWORD='at least twelve characters'

arcana-recon synth ./samples                  # synthetic damaged test pages
arcana-recon process ./samples --out ./vault  # repair + seal a file or folder
arcana-recon extract ./vault/synthetic_damaged.png.arcv
pytest
```

`process` writes two files per input, and nothing unencrypted:

| File | Contents |
|---|---|
| `<name>.arcv` | The repaired page as PNG, sealed: `ARCN \| 0x01 \| salt(16) \| nonce(12) \| AES-256-GCM ciphertext+tag` |
| `<name>.json` | Report: source SHA-256, clipped pixel counts, every filled region, layout blocks in reading order, SHA-256 of the sealed PNG. Plaintext; contains the source file name and page geometry but no pixels and no key material. |

Existing outputs are never overwritten. `extract` needs only the passphrase,
in any process, and checks the unsealed PNG against the report's hash.

## Pipeline

1. **Ingest.** 50 MB ceiling, magic-byte allow-list (PNG, JPEG, TIFF, BMP,
   WebP), PNG dimensions checked before decoding (pixel-bomb guard), decode
   from the same in-memory bytes that were hashed. Colour, alpha and 16-bit
   input become 8-bit grayscale.
2. **Triage.** Pixels ≥ 250 or ≤ 5 are *clipped*. A morphological opening
   keeps only blobs larger than a text stroke, so dark ink and clean white
   paper are not reported as damage.
3. **Repair.**
   - *Illumination flattening*: divide by a smooth background estimate. This
     is what actually recovers text in soft shadows and uneven light.
   - *Glare halo stretch*: around each glare spot, stretch local contrast so
     washed-out but unclipped ink becomes dark again.
   - *Telea inpainting* of the clipped glare core. This hides the blown-out
     spot; it does **not** restore the characters that were under it.
   - Clipped-black regions are reported but left alone unless
     `--fill-shadow` is given, because they are often redaction bars,
     figures or scan borders.
4. **Layout.** Otsu binarization, dilation into blocks, then a recursive
   XY-cut reading order that finishes one column before starting the next.
5. **Seal.** Passphrase-derived key (100,000 rounds of SHA-256, same as the
   Rust crate), fresh salt and nonce per file.

## What is real and what is not

| Claim in the design notes | Status here |
|---|---|
| Detect glare and shadow damage | **Real.** Clipped regions, with coordinates, in the report. |
| Recover text in shadows / uneven light | **Real** when the pixels are dimmed, not clipped. The synthetic test goes from 0.19 to 0.99 F1 on the shadowed column. |
| Recover text under blown-out glare | **Not possible from one image.** Clipped pixels hold no data; inpainting fills them smoothly. A test asserts this. Multi-frame fusion (glare moves between shots) could do it; not implemented. |
| "Generative inpainting", font priors, VLM grafting | **Not implemented.** Would invent content, which needs careful labelling in a forensic setting. |
| Multi-column reading order | **Real** for column layouts via XY-cut. The naive (y, x) sort from the drafts interleaves columns; a test shows both. |
| GNN / semantic layout (footnote links, schematic wires, cross-column tables) | **Not implemented.** Layout is geometry only. |
| AES-256-GCM vault | **Real**, interoperable with `crates/arcana-vault` (shared test vectors run in both test suites). |
| Chain of custody | Source and output SHA-256 in the report. Not yet written to the `arcana-custody` ledger. |

## Fixed from the pasted drafts

- `os.path.splitext(base_name)][0]` syntax error in the high-speed draft.
- A draft returned the encryption key (`ephemeral_key_hex_escrow`) in its output.
- The key lived only in memory, so vaults could only be opened by the same
  process; the extractor guessed the file name and needed the in-memory ledger.
- The "magic-number check" only checked `len(bytes) >= 4`.
- Every pixel ≤ 5 was inpainted, which erases dark text on a clean scan, and
  every pixel ≥ 250 was inpainted, which on white paper means the whole page.
- The vault format did not match the repository's existing ARCN v1 format.
- Worker threads could write to the same output name; names are now assigned
  up front and files opened with `O_EXCL`.

## Limits

- The key stretch is pure Python and holds the GIL, so large batches are
  bound by it (~0.1 s per file) even though OpenCV work runs in parallel.
- Flattening treats dark areas larger than about 4% of the page (big photos)
  as background and washes them out.
- XY-cut assumes column gutters are wider than paragraph gaps; tables whose
  column gaps exceed their row gaps are read column by column.
