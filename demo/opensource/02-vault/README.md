# Open source — vault

Blob layout: `ARCN | version:u8=1 | salt:16 | nonce:12 | ciphertext||tag`

Seal `plaintext/secret.txt` with `demo/scripts/seal_demo.py`.
