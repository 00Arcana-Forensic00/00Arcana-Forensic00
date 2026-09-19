mitchell5584dm@penguin:~/arcana-forensics$ cargo run -p arcana-acquire -- .
warning: use of deprecated associated function `aes_gcm::aead::hybrid_array::Array::<T, U>::from_slice`: use `TryFrom` instead
 --> arcana-vault/src/lib.rs:7:33
  |
7 |     let key = Key::<Aes256Gcm>::from_slice(&key_bytes);
  |                                 ^^^^^^^^^^
  |
  = note: `#[warn(deprecated)]` on by default

warning: use of deprecated associated function `aes_gcm::aead::hybrid_array::Array::<T, U>::from_slice`: use `TryFrom` instead
  --> arcana-vault/src/lib.rs:12:24
   |
12 |     let nonce = Nonce::from_slice(&nonce_bytes);
   |                        ^^^^^^^^^^

warning: `arcana-vault` (lib) generated 2 warnings
   Compiling arcana-acquire v0.1.0 (/home/mitchell5584dm/arcana-forensics/arcana-acquire)
warning: unused import: `Write`
 --> arcana-acquire/src/main.rs:3:27
  |
3 | use std::io::{self, Read, Write};
  |                           ^^^^^
  |
  = note: `#[warn(unused_imports)]` on by default

warning: constant `DORMANT_THRESHOLD_SECS` is never used
  --> arcana-acquire/src/main.rs:11:7
   |
11 | const DORMANT_THRESHOLD_SECS: u64 = 30 * 24 * 3600; 
   |       ^^^^^^^^^^^^^^^^^^^^^^
   |
   = note: `#[warn(dead_code)]` on by default

warning: multiple variants are never constructed
  --> arcana-acquire/src/main.rs:19:5
   |
15 | enum ArtifactType {
   |      ------------ variants in this enum
...
19 |     ZipCompressed,
   |     ^^^^^^^^^^^^^
20 |     SevenZipPack,
   |     ^^^^^^^^^^^^
21 |     GzipCompressed,
   |     ^^^^^^^^^^^^^^
22 |     PdfDocument,
23 |     WordDocument,
   |     ^^^^^^^^^^^^
24 |     ExcelSpreadsheet,
   |     ^^^^^^^^^^^^^^^^
...
27 |     GifImage,
   |     ^^^^^^^^
28 |     ShellScript,
   |     ^^^^^^^^^^^
29 |     PythonScript,
   |     ^^^^^^^^^^^^
   |
   = note: `ArtifactType` has derived impls for the traits `Clone` and `Debug`, but these are intentionally ignored during dead code analysis

warning: field `extension` is never read
  --> arcana-acquire/src/main.rs:37:5
   |
34 | struct ForensicJob {
   |        ----------- field in this struct
...
37 |     extension: String,
   |     ^^^^^^^^^

warning: `arcana-acquire` (bin "arcana-acquire") generated 4 warnings (run `cargo fix --bin "arcana-acquire"` to apply 1 suggestion)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 1.29s
     Running `target/debug/arcana-acquire .`
--- Arcana Forensics Workspace Execution Pipeline ---

--- Automated Chain of Custody Audit Sealed ---
RECORD TARGET: unallocated_space.dat
TIMESTAMP    : 1789820163 (Unix Epoch)
SHA-256 HASH : e26507f3ae108f668383d71873df38829f669cf3214db731a8bed3381c3e3166
VAULT SIZE   : 100 encrypted bytes

--- Automated Chain of Custody Audit Sealed ---
RECORD TARGET: Cargo.toml
TIMESTAMP    : 1789820163 (Unix Epoch)
SHA-256 HASH : 8ef5aed359d84db411d1126e3133b637b9c4aafc1d995c66c5ce7e03bf359bd9
VAULT SIZE   : 121 encrypted bytes
STATUS       : Write-locked with zero cloud exposure.
-----------------------------------------------

[💎 Premium DB] Connecting to synchronized corporate relational ledger...

--- Automated Chain of Custody Audit Sealed ---
RECORD TARGET: .gitignore
TIMESTAMP    : 1789820163 (Unix Epoch)
SHA-256 HASH : 379420c738d349e5b430729b2928bf13449309fd4ac7ab6346714c19fa8531b9
VAULT SIZE   : 71 encrypted bytes
STATUS       : Write-locked with zero cloud exposure.
-----------------------------------------------
STATUS       : Write-locked with zero cloud exposure.
-----------------------------------------------

[💎 Premium DB] Connecting to synchronized corporate relational ledger...

[💎 Premium DB] Connecting to synchronized corporate relational ledger...
[💎 Premium DB] SUCCESS: Relational entry committed safely via rusqlite.
[💎 Premium DB] SUCCESS: Relational entry committed safely via rusqlite.
[💎 Premium DB] SUCCESS: Relational entry committed safely via rusqlite.

--- Automated Chain of Custody Audit Sealed ---
RECORD TARGET: release.yml.bak
TIMESTAMP    : 1789820163 (Unix Epoch)
SHA-256 HASH : 09e3741d279351296d07a780285b5b068b446cf0e3a0ffceda1ab22ccdb04528
VAULT SIZE   : 1516 encrypted bytes
STATUS       : Write-locked with zero cloud exposure.
-----------------------------------------------

[💎 Premium DB] Connecting to synchronized corporate relational ledger...
[💎 Premium DB] SUCCESS: Relational entry committed safely via rusqlite.

--- Automated Chain of Custody Audit Sealed ---
RECORD TARGET: PostgreSQL DDL Blueprint.sql
TIMESTAMP    : 1789820163 (Unix Epoch)
SHA-256 HASH : 07af83b8a980d34b3dadbd7ca625afa10cc3b2330d7c8355ad3d3add398b75b7
VAULT SIZE   : 2081 encrypted bytes
STATUS       : Write-locked with zero cloud exposure.
-----------------------------------------------

[💎 Premium DB] Connecting to synchronized corporate relational ledger...
[💎 Premium DB] SUCCESS: Relational entry committed safely via rusqlite.

--- Automated Chain of Custody Audit Sealed ---
RECORD TARGET: Cargo.lock
TIMESTAMP    : 1789820163 (Unix Epoch)
SHA-256 HASH : 4abb9199859a494ded6808e3c15a429a3e625a34063be9596bbeffa38436525b
VAULT SIZE   : 11403 encrypted bytes
STATUS       : Write-locked with zero cloud exposure.
-----------------------------------------------

[💎 Premium DB] Connecting to synchronized corporate relational ledger...
[💎 Premium DB] SUCCESS: Relational entry committed safely via rusqlite.
