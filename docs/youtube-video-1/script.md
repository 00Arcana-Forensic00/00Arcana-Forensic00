## HOOK (0:00 to 0:16)

A deleted Word file. Two words in its metadata. And a killer who had evaded police for decades was caught.
[VISUAL: Floppy disk on a dark desk, slow push-in. Text on screen: "February 2005." AI still, documentary grade, no faces.]

Now a different case. Forensic software told a jury the number was eighty-four. The real number was one.
[VISUAL: Text on screen: "84". The digits collapse into "1". Hard cut to black.]

## SETUP (0:16 to 1:04)

Digital evidence can close a case in days. It can also sink one in an afternoon. The difference is whether you can prove it.
[VISUAL: Split screen. A case file stamped CLOSED on the left. The same file torn in half on the right. Title card with the channel name.]

By the end of this video, you'll know what makes digital evidence hold up. You'll know what a hash chain proves, and what it can't.
[VISUAL: Three text cards appear one at a time: "What holds up." "What a hash chain proves." "What it can't."]

You'll also get one question to ask every forensic tool before it touches a case. Here it is: what did you send?
[VISUAL: Text on screen, typing effect: "What did you send?" The cursor blinks.]

One disclosure. We make Arcana Forensics, the tool in this video. We'll say so whenever we talk about our own software.
[VISUAL: Lower third: "We make the tool in this video." The Arcana logo fades in and out.]

Every demo uses synthetic files. Use these methods only on systems you're authorized to examine.
[VISUAL: Terminal in dark mode. A folder named "src" holds five text files. Corner tag: "Synthetic evidence."]

## BLOCK 1: TWO CASES, ONE LESSON (1:04 to 3:28)

Start with the floppy disk. In February 2005, it arrived at a local TV station, sent by the man police had hunted for more than thirty years.
[VISUAL: Padded envelope on a mailroom counter. AI still, no faces. Caption: "Illustration."]

Investigators found a deleted Word file still on the disk. Its metadata held two clues: a user name, Dennis, and an organization, Christ Lutheran Church.
[VISUAL: Illustrated file-properties window, labeled "Illustration based on public reporting." Fields highlighted: "Last saved by: Dennis." "Organization: Christ Lutheran Church."]

A search of the church's website turned up its council president, Dennis Rader. He was arrested that same month.
[VISUAL: Website search illustration. The cursor lands on "council president". Text on screen: "Arrested: February 2005."]

Deleted often means hidden, not gone. And every file carries a hidden layer of its own history. That's metadata.
[VISUAL: Diagram of a document. The visible page sits on top. A hidden layer below is labeled "metadata: author, organization, timestamps."]

Metadata cuts both ways. The same hidden timestamps that point at a suspect can clear one. Good examiners read all of it, not just the parts that fit.
[VISUAL: Two arrows leave the same hidden layer. One points to "suspect." One points to "cleared."]

That's digital evidence doing its job. Now the other side.
[VISUAL: Wipe transition from warm light to cold blue.]

In 2011, during the Casey Anthony trial, a browser-history tool reported eighty-four visits to a page about chloroform. The tool's author found a bug while the trial was still going. His recheck put the count at one.
[VISUAL: Timeline graphic. "Tool output: 84." An arrow to "Author's recheck: 1." Caption: "Source: 2011 court reporting."]

A tool was wrong, and its number reached a courtroom. We're not here to retry that case. We're here for the lesson.
[VISUAL: Empty witness stand, AI still. Caption: "We take no position on the verdict."]

One more, from the physical world. In the 1995 Simpson trial, a criminalist spent days on the stand, and much of the questioning was about how evidence was collected and logged.
[VISUAL: Courtroom sketch-style illustration, no faces. Text on screen: "1995." Caption: "Source: trial coverage and transcripts."]

Again, no position on the verdict. The point is the pattern. Challenges to evidence often start with handling, not content. Who touched it? Where was it? How do you know?
[VISUAL: Three questions appear one at a time: "Who touched it?" "Where was it?" "How do you know?"]

The evidence isn't just the file. It's everything between the file and the courtroom.
[VISUAL: Animated path: Device, Tool, Copy, Report, Courtroom. Each link lights up in turn.]

This isn't only about murder. Fraud, stalking, insider theft and breach response all run on the same idea.
[VISUAL: Four case folders labeled Fraud, Stalking, Insider theft and Breach response.]

In the physical world, that path is a paper form. Everyone who handles the evidence bag signs and dates it. That's chain of custody.
[VISUAL: Evidence bag with a signature table, AI still. Text on screen: "Chain of custody."]

Digital evidence needs the same thing. But now every hand is software. So how does software sign for evidence?
[VISUAL: A pen signing a form morphs into a line of code, then into a 64-character hash.]

## BLOCK 2: THE TOOL IS A LINK (3:28 to 6:03)

But before the answer, an uncomfortable thought. In the eighty-four case, the file was fine. The tool was the weak link.
[VISUAL: The chain graphic again. The "Tool" link pulses red.]

So ask any forensic tool one question. What did you send?
[VISUAL: Text on screen, large: "What did you send?" One beat of silence.]

Ask the follow-ups too. Where does it write? What does it log? Can you read the log without the tool?
[VISUAL: Four question cards stack on screen, one at a time.]

We asked it about our own software. So we searched our source code for anything that opens a network connection.
[VISUAL: Terminal: a search for network terms across the source tree. The cursor returns to the prompt with no output.]

We found nothing. No web client, no sockets, no telemetry code. That's for the free Community Edition source, which you can read yourself.
[VISUAL: The dependency list scrolls: sha2, aes-gcm, rusqlite, clap, walkdir. Highlight: no network crates. Caption: "Community Edition, MIT licensed."]

So the tool has no code to call out. Your operating system still can, so isolate the machine too.
[VISUAL: A laptop with its cable unplugged. A second icon shows operating system services with arrows leaving. Text on screen: "The tool is not the machine."]

Now the part that builds trust. We audited our own first version, and it was ugly.
[VISUAL: The audit file on screen, its top line highlighted.]

It didn't build. Its acquire command was a disk wiper. The vault demo reused a nonce. Custody logging was a print statement.
[VISUAL: A four-line list appears line by line. Each line is struck through in turn.]

The wiper is gone for good. The tool now reads your source and never writes to it.
[VISUAL: Code diff with the destructive lines in red, deleted. Text on screen: "Acquisition only."]

One scope note. This tool copies files from a folder. It isn't a disk imager. If you need a bit-for-bit image of a drive, that's a different job and a different tool.
[VISUAL: Two icons: a folder of files, and a whole drive. Text on screen: "Files, not drives."]

Here's a real run. Five files and one symlink, on synthetic data. One command.
[VISUAL: Terminal showing a folder tree of five text files and a symlink arrow. Typing effect: the acquire command with path, out, operator and case id.]

It seals five files and skips one. The output says so: acquired five, skipped one, ledger events seven.
[VISUAL: Output line highlighted: "acquired 5 file(s), skipped 1, ledger events 7, chain_ok=true".]

The skipped file is the symlink. A symlink can point anywhere. Follow it, and you copy files that were never evidence.
[VISUAL: Animated arrow leaving the evidence folder toward a system folder, stamped red.]

Every file gets a SHA-256 fingerprint. A sealed copy goes into the vault, named after that fingerprint.
[VISUAL: A file turns into a 64-character hash, then into a vault file with the same name.]

Here's the detail most write-ups skip. The seal is AES-256-GCM, with a fresh random nonce for every file.
[VISUAL: Blob layout diagram: magic, version, salt, nonce, ciphertext plus tag. The nonce segment pulses.]

In GCM, reuse a nonce and two ciphertexts leak the XOR of their plaintexts. It can even expose the authentication key, which lets someone forge data that still verifies. That was the bug in our first demo. It's fixed.
[VISUAL: Two bit strings XOR into a third. A forged blob is stamped "valid", then the stamp cracks.]

Flip one byte in a sealed file and verify refuses it. The error says authentication failed: wrong passphrase or corrupted vault.
[VISUAL: Hex editor with the last byte highlighted. Terminal: "error: authentication failed (wrong passphrase or corrupted vault)".]

## BLOCK 3: THE LEDGER (6:03 to 7:36)

Sealed files are half the story. The other half is the ledger: the tool's signature on the paper form. And this is where it gets interesting.
[VISUAL: The vault folder slides left. A table slides in from the right.]

Every action becomes a line. Case open, one line per sealed file, then the manifest.
[VISUAL: Seven-row table: case-open, five ingest-seal rows, manifest-write.]

And every line carries the operator's name. Accountability isn't a footnote. It's a column.
[VISUAL: The operator column highlighted in the ledger table. Value: "analyst01".]

The ledger is a plain SQLite file. Any examiner can open it with free tools and check the math. No black box.
[VISUAL: The ledger file opened in a free database viewer.]

Each line holds a timestamp, the operator, the action, the path, and the file's hash. And one more thing: the hash of the line before it.
[VISUAL: Row 3's hash flies into row 4's "previous hash" cell. Column labels appear.]

The line's own hash is SHA-256 over all of that. The very first line points at sixty-four zeros.
[VISUAL: Formula on screen: SHA-256(time | operator | action | path | file hash | previous hash). Row 1 shows a string of zeros.]

Change anything in a line and its hash changes. That breaks the next line, and the next. Like dominoes.
[VISUAL: Domino animation. The first domino turns red and the rest fall in sequence.]

Watch it work. We change line four, so the path says file nine instead of file four.
[VISUAL: Terminal showing the one-line database update. A row highlights and the path cell changes.]

Then we run verify. Ledger events, three. Chain okay, false. Verification failed.
[VISUAL: Output: "manifest files=5, ledger events=3, chain_ok=false", then "error: verification failed" in red, with exit code 1.]

Three means it checked three lines and stopped. It points at the exact line where the chain broke.
[VISUAL: Ledger table. Rows 1 to 3 get green checks. Row 4 is red. Rows 5 to 7 are grayed out.]

One more detail. The last line records the hash of the manifest itself. So the list of evidence is pinned to the chain too.
[VISUAL: Row 7 highlighted: "manifest-write, manifest.json". Its hash field glows.]

## BLOCK 4: WHERE THE LEDGER CAN LIE (7:36 to 9:58)

That's the good news. Most people stop here. Don't.
[VISUAL: Text on screen: "Most people stop here." The text flickers.]

Now do it like someone who knows what they're doing. Edit line four, then recompute every hash from line four down.
[VISUAL: A short Python loop on screen. Hashes cascade down the table and settle.]

It takes about ten lines of code. Anyone with write access to the file can do it.
[VISUAL: Code editor zoom, line numbers 1 to 10 highlighted.]

Run verify again. Events, seven. Chain okay, true. Exit code zero.
[VISUAL: Output in green. Freeze frame. A red circle draws around "chain_ok=true".]

The ledger now says file nine. The manifest still says file four. And the tool says everything is fine.
[VISUAL: Side by side: ledger row "file9.txt" and manifest "file4.txt", with the green verify line between them.]

Here's what that means. A hash chain proves the lines agree with each other. It doesn't prove who wrote them, or when.
[VISUAL: Card: "Lines agree with each other: yes. Written by whom: unknown. Written when: unknown."]

Here's the insider point. Tamper-evident is not tamper-proof. The edit that fails is the careless one. The edit that passes is the careful one.
[VISUAL: Two stamps side by side: "Careless edit: caught." "Careful edit: passes."]

And when comes from the machine clock. Set the clock back, rebuild the chain, and every line looks honest.
[VISUAL: Clock hands spin backward while the timestamp column rewrites itself.]

So a local chain can't carry the whole weight. Three habits close most of the gap.
[VISUAL: Text cards numbered 1, 2 and 3.]

One. Verify with the passphrase, every time. Without it, verify checks the chain and nothing else. The tool even prints a note saying so.
[VISUAL: Two terminals side by side. Left: the note about passing a password to unseal and re-hash vault blobs. Right: the same command with the passphrase set. No note, and every file re-hashed.]

Two. Write the last hash somewhere you don't control. It's sixty-four characters. Put it on the intake form, email it to counsel, or get it stamped by an outside timestamp authority.
[VISUAL: A 64-character hash on an intake form. An email draft. A stamp icon labeled "RFC 3161."]

Rebuild the chain later and that final hash changes. The outside copy becomes your witness. It only counts if it was made before anyone could touch the ledger.
[VISUAL: Two hashes side by side, mismatched, with the differing characters highlighted.]

Free public services like OpenTimestamps can do this stamping for you. The standard behind timestamp authorities is called RFC 3161. Either one gives you a witness you don't have to run yourself.
[VISUAL: Two cards: "OpenTimestamps" and "RFC 3161 timestamp authority." Caption: "Public standards, not our product."]

But even a perfect outside stamp has a limit. It proves your ledger existed by that time. It can't prove the evidence was clean before the ledger began.
[VISUAL: Timeline with a stamp marker at "T". A dotted line before it is labeled "Unknown."]

Three. Cross-check the ledger against the manifest. Today, that's a manual step. We know it should be automatic.
[VISUAL: Text on screen: "Ledger vs manifest: manual today."]

## BLOCK 5: WHAT IT WON'T DO (9:58 to 11:36)

Now the part nobody puts in the brochure. What this tool does not do.
[VISUAL: Text on screen: "Not in the brochure."]

It doesn't wipe disks. It doesn't upload evidence. It doesn't need a network.
[VISUAL: Three icons, each crossed out in turn.]

It isn't an expert opinion. A printed ledger line isn't a court-ready exhibit on its own.
[VISUAL: A printed ledger page with a stamp: "Not an expert opinion."]

And here's a limit we'll say out loud. Today, key stretching is one hundred thousand rounds of SHA-256. Argon2id is the planned upgrade.
[VISUAL: The source comment about swapping in Argon2id, highlighted on screen.]

Until then, your passphrase is the weak point. The tool demands twelve characters. Use far more.
[VISUAL: A passphrase field. The error message appears: "passphrase must be at least 12 characters".]

Why say all this? Because every claim about a forensic tool should be checkable. Read the source, build it, run it air-gapped.
[VISUAL: Repository file list: LICENSE, SECURITY.md, crates. An MIT badge.]

If you work cases, ask every vendor the same three questions. What did you send? What do you log? What can't you prove? A good answer includes limits.
[VISUAL: Three question cards stack on screen, each one lighting up in turn.]

Arcana Forensics Community Edition is free and MIT licensed. Start free. Upgrade when your cases do. Link in the description.
[VISUAL: End card: arcana-forensics.com, the logo, and "Start free."]

Here's your Monday checklist. Write down exactly what each tool does with your evidence. Verify with the passphrase. And record the final hash somewhere outside the case.
[VISUAL: A checklist card with three items, each ticking off.]

But there's one thing no ledger can see. Everything here starts when acquisition starts. What happens to a file before line one?
[VISUAL: The ledger table with a blank row zero fading in above row one. Text on screen: "Line zero."]

Next video: how a case can be damaged before the chain even begins. And the one habit that catches it.
[VISUAL: End screen with a next-video card and a subscribe button. Working title: "Line Zero."]
