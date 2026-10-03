"""Video glare removal, checked against ground truth built from a known clean page."""
import os

import cv2
import numpy as np
import pytest
from conftest import FAST_KDF, PW
from arcana_restore import pipeline, video, imaging

W, H = 960, 700


def make_base():
    rng = np.random.default_rng(7)
    page = np.full((H - 80, W - 80, 3), 215, np.uint8)
    page = np.clip(page + rng.normal(0, 6, page.shape), 0, 255).astype(np.uint8)   # paper grain: gives features
    words = ["EVIDENCE", "CUSTODY", "LEDGER", "SEALED", "ORIGINAL", "RECEIPT", "TOTAL 482.17", "WITNESS"]
    for row in range(13):
        cv2.putText(page, f"{words[row % 8]} {row*37+11} {words[(row*3) % 8]}", (30, 50 + row * 44),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.95, (35, 35, 35), 2, cv2.LINE_AA)
    cv2.rectangle(page, (560, 60), (800, 200), (60, 60, 160), 3)
    return page


def make_video(path, n=14, glare=True, seed=3):
    base = make_base()
    rng = np.random.default_rng(seed)
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 10, (W, H))
    if not out.isOpened():
        pytest.skip("OpenCV build cannot write MJPG video")
    mats, frames = [], []
    for i in range(n):
        ang, sc = rng.uniform(-3, 3), rng.uniform(0.97, 1.03)
        M = cv2.getRotationMatrix2D((W / 2, H / 2), ang, sc)
        M[:, 2] += (rng.uniform(-20, 20), rng.uniform(-15, 15)) + np.array([40, 40])
        H3 = np.vstack([M, [0, 0, 1]])
        fr = cv2.warpPerspective(base, H3, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=(120, 120, 120))
        if glare:
            cx, cy = int(80 + 800 * (i / (n - 1))), int(250 + 120 * np.sin(i))
            cv2.ellipse(fr, (cx, cy), (70, 55), 0, 0, 360, (255, 255, 255), -1)
        fr = np.clip(fr + rng.normal(0, 2, fr.shape), 0, 255).astype(np.uint8)
        out.write(fr); mats.append(H3); frames.append(fr)
    out.release()
    return base, mats, frames


@pytest.fixture
def glare_video(tmp_path):
    p = str(tmp_path / "scene.avi")
    base, mats, frames = make_video(p)
    return p, base, mats, frames


def test_container_detection():
    assert video.video_kind(b"\x1a\x45\xdf\xa3" + b"0" * 20) == ".webm"
    assert video.video_kind(b"\x00\x00\x00\x18ftypmp42" + b"0" * 20) == ".mp4"
    assert video.video_kind(b"RIFF\x00\x00\x00\x00AVI LIST") == ".avi"
    assert video.video_kind(b"\x89PNG\r\n\x1a\n" + b"0" * 20) is None


def test_glare_is_recovered_from_other_frames(glare_video):
    p, base, mats, _ = glare_video
    data = open(p, "rb").read()
    frames, _ = video.read_frames(data, video.VideoConfig())
    img, replaced, rep = video.composite(frames, imaging.RepairConfig(), video.VideoConfig())
    assert rep["frames_used"] >= 8 and rep["composite_replaced_fraction"] > 0.01
    # ground truth: the clean page seen from the reference frame's viewpoint
    gt = cv2.warpPerspective(base, mats[rep["reference_frame"]], (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=(120, 120, 120))
    ref = frames[rep["reference_frame"]]
    glare = replaced > 0
    assert glare.sum() > 3000
    before = np.abs(ref.astype(int) - gt.astype(int))[glare].mean()
    after = np.abs(img.astype(int) - gt.astype(int))[glare].mean()
    assert before > 25 and after < 8 and after < before / 4, (before, after)   # real content came back
    clean = ~cv2.dilate(replaced, np.ones((9, 9), np.uint8)).astype(bool)
    assert (img[clean] == ref[clean]).all()                         # every clean pixel is exactly as captured


def test_end_to_end_video_seal_and_extract(glare_video, tmp_path, monkeypatch):
    import tempfile
    scratch = tmp_path / "scratch"; scratch.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(scratch))        # watch exactly where the decoder copies to
    p, *_ = glare_video
    vd = str(tmp_path / "v")
    (r,) = pipeline.process_batch([p], vd, PW, 1, kdf=FAST_KDF)
    assert r.ok, r.error
    assert r.report["source_kind"] == "video" and r.report["status"] == "repaired"
    out = pipeline.extract(r.vault_path, PW, str(tmp_path / "o"))
    orig = [x for x in out if ".original." in x][0]
    assert orig.endswith(".avi") and open(orig, "rb").read() == open(p, "rb").read()   # video kept byte-identical
    restored = cv2.imread([x for x in out if ".restored." in x][0])
    assert restored is not None and restored.shape[:2] == (H, W)
    # no frame-copy of the evidence is left behind in the temp dir
    assert os.listdir(scratch) == []


def test_unalignable_video_falls_back_to_single_frame(tmp_path):
    p = str(tmp_path / "cuts.avi")
    out = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(*"MJPG"), 10, (320, 240))
    if not out.isOpened():
        pytest.skip("no MJPG writer")
    rng = np.random.default_rng(0)
    for _ in range(8):                      # unrelated random frames: nothing to align
        out.write(rng.integers(0, 255, (240, 320, 3), dtype=np.uint8))
    out.release()
    frames, _ = video.read_frames(open(p, "rb").read(), video.VideoConfig())
    img, replaced, rep = video.composite(frames, imaging.RepairConfig(), video.VideoConfig())
    assert "video_fallback" in rep and not replaced.any()


def test_no_repair_flag_keeps_single_sharpest_frame(glare_video, tmp_path):
    p, *_ = glare_video
    cfg = imaging.RepairConfig(repair=False)
    (r,) = pipeline.process_batch([p], str(tmp_path / "v"), PW, 1, cfg, FAST_KDF)
    assert r.ok and r.report["frames_used"] == 1 and r.report["status"] == "detected_not_repaired"


@pytest.mark.parametrize("bad", [b"\x00\x00\x00\x18ftypmp42" + b"junk" * 50, b"\x1a\x45\xdf\xa3" + b"junk" * 50])
def test_corrupt_video_is_rejected_cleanly(bad, tmp_path):
    f = tmp_path / "x.mp4"; f.write_bytes(bad)
    (r,) = pipeline.process_batch([str(f)], str(tmp_path / "v"), PW, 1, kdf=FAST_KDF)
    assert not r.ok and ("video" in r.error.lower() or "frames" in r.error.lower())


def test_friendly_message_for_other_file_types(tmp_path):
    f = tmp_path / "doc.pdf"; f.write_bytes(b"%PDF-1.7 hello")
    (r,) = pipeline.process_batch([str(f)], str(tmp_path / "v"), PW, 1, kdf=FAST_KDF)
    assert not r.ok and "photo or screenshot" in r.error and "short video" in r.error


def test_oversized_video_rejected():
    with pytest.raises(imaging.ImageError, match="250 MiB"):
        video.read_frames(b"\x1a\x45\xdf\xa3" + b"0" * (video.MAX_VIDEO_BYTES + 1), video.VideoConfig())


def test_webm_and_mp4_containers_decode(tmp_path):
    base = make_base()
    for ext, codec in ((".webm", "VP80"), (".mp4", "mp4v")):
        p = str(tmp_path / f"t{ext}")
        out = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(*codec), 10, (W, H))
        if not out.isOpened():
            continue                                             # this OpenCV build cannot write the codec
        for i in range(8):
            f = np.full((H, W, 3), 120, np.uint8)
            f[40:40 + base.shape[0], 40:40 + base.shape[1]] = base
            out.write(np.roll(f, i * 3, axis=1))
        out.release()
        data = open(p, "rb").read()
        assert video.video_kind(data) == ext
        frames, _ = video.read_frames(data, video.VideoConfig())
        assert len(frames) >= 6


@pytest.mark.parametrize("brand", [b"heic", b"heix", b"mif1", b"avif"])
def test_iphone_heic_and_avif_are_images_not_video(brand, tmp_path):
    data = b"\x00\x00\x00\x18ftyp" + brand + b"\x00" * 64
    assert video.video_kind(data) is None                       # not mistaken for MP4
    f = tmp_path / "IMG_0001.heic"; f.write_bytes(data)
    (r,) = pipeline.process_batch([str(f)], str(tmp_path / "v"), PW, 1, kdf=FAST_KDF)
    assert not r.ok and "HEIC" in r.error and "JPEG" in r.error   # clear next step for the user


def test_real_mp4_brands_still_video():
    for brand in (b"isom", b"mp42", b"avc1", b"qt  ", b"M4V "):
        assert video.video_kind(b"\x00\x00\x00\x18ftyp" + brand + b"\x00" * 20) == ".mp4"
