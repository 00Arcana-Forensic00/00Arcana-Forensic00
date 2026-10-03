#!/usr/bin/env bash
# Installs the beta APK on a running emulator and drives it the way a tester would: open it,
# recover the sample page, seal it into a vault, check the custody log and open the plan.
# This is the shrunk release build, so it catches anything R8 broke that debug tests can't see.
# Along the way it saves store-ready screenshots (1080x1920, clean status bar) to $OUT.
#
#   tools/beta_smoke.sh path/to/app-play-beta.apk out-dir
set -euo pipefail

APK=$1
OUT=$2
PKG=com.arcanaforensics.arcalume.beta
mkdir -p "$OUT"

log() { echo "== $*"; }
fail() {
    echo "::error::beta smoke: $*"
    adb exec-out screencap -p > "$OUT/failure.png" || true
    dump > "$OUT/failure.xml" || true
    adb logcat -d | grep -E 'Arcalume|AndroidRuntime|OpenCV|FATAL' | tail -200 || true
    exit 1
}

dump() {
    for _ in 1 2 3 4 5; do
        if adb shell uiautomator dump /sdcard/ui.xml >/dev/null 2>&1; then
            adb exec-out cat /sdcard/ui.xml
            return 0
        fi
        sleep 1
    done
    return 1
}

# Prints "x y" for the centre of the first node whose text, description or hint is $1
# (exact match first, then substring). Prints nothing if it isn't on screen.
locate() {
    dump | python3 -c '
import re, sys, xml.etree.ElementTree as ET
want = sys.argv[1]
try:
    nodes = list(ET.fromstring(sys.stdin.read()).iter("node"))
except ET.ParseError:
    sys.exit(0)
def labels(n):
    return [n.get(k, "") for k in ("text", "content-desc", "hint")]
for exact in (True, False):
    for n in nodes:
        if any((l == want) if exact else (want in l) for l in labels(n)):
            x1, y1, x2, y2 = map(int, re.findall(r"\d+", n.get("bounds")))
            print((x1 + x2) // 2, (y1 + y2) // 2)
            sys.exit(0)
' "$1"
}

wait_for() {  # text, seconds
    local deadline=$((SECONDS + $2))
    while (( SECONDS < deadline )); do
        [[ -n "$(locate "$1")" ]] && return 0
        alive || fail "the app closed while waiting for \"$1\""
        sleep 2
    done
    return 1
}

scroll_down() { adb shell input swipe 540 1500 540 700 300; sleep 1; }
scroll_up()   { adb shell input swipe 540 600 540 1500 300; sleep 1; }
to_top()      { for _ in 1 2 3 4 5 6; do scroll_up; done; }

tap() {  # text; scrolls down to find it
    local xy
    for _ in 1 2 3 4 5 6 7 8; do
        xy=$(locate "$1")
        if [[ -n "$xy" ]]; then adb shell input tap $xy; sleep 1; return 0; fi
        scroll_down
    done
    return 1
}

tap_field() {  # n: taps the nth text field on screen (1-based)
    local xy
    xy=$(dump | python3 -c '
import re, sys, xml.etree.ElementTree as ET
fields = [n for n in ET.fromstring(sys.stdin.read()).iter("node") if n.get("class") == "android.widget.EditText"]
n = int(sys.argv[1])
if len(fields) >= n:
    x1, y1, x2, y2 = map(int, re.findall(r"\d+", fields[n - 1].get("bounds")))
    print((x1 + x2) // 2, (y1 + y2) // 2)
' "$1")
    [[ -n "$xy" ]] && adb shell input tap $xy && sleep 1
}

alive() { adb shell pidof "$PKG" >/dev/null 2>&1; }
shot() { sleep 1; adb exec-out screencap -p > "$OUT/$1.png"; log "screenshot $1"; }

log "screen 1080x1920 at 420 dpi, clean status bar"
adb shell wm size 1080x1920
adb shell wm density 420
adb shell settings put global sysui_demo_allowed 1
adb shell am broadcast -a com.android.systemui.demo -e command enter >/dev/null
adb shell am broadcast -a com.android.systemui.demo -e command clock -e hhmm 0930 >/dev/null
adb shell am broadcast -a com.android.systemui.demo -e command battery -e level 100 -e plugged false >/dev/null
adb shell am broadcast -a com.android.systemui.demo -e command network -e wifi show -e level 4 >/dev/null
adb shell am broadcast -a com.android.systemui.demo -e command notifications -e visible false >/dev/null

log "install $APK"
adb install -r "$APK"
adb logcat -c

log "launch"
adb shell am start -W -n "$PKG/com.arcanaforensics.arcalume.MainActivity" >/dev/null
wait_for "Try a sample page" 60 || fail "the start screen did not appear"
shot 01-start

log "recover the sample page"
tap "Try a sample page" || fail "could not tap the sample"
wait_for "What Arcalume found and did" 180 || fail "the sample was not recovered"
to_top
shot 02-recovered
tap "Show filled areas" || fail "no filled-areas switch"
to_top
shot 03-filled-areas
tap "What Arcalume found and did" >/dev/null || true
shot 04-findings

log "seal it into a vault (Argon2id and AES-GCM in the shrunk build)"
tap "Seal as evidence" || fail "no seal button"
wait_for "Repeat passphrase" 20 || fail "the seal dialog did not open"
tap "I understand that a forgotten passphrase" || fail "no acknowledgement box"
tap_field 1 || fail "no passphrase field"
adb shell input text "glare-proof-sample-page"
tap_field 2 || fail "no repeat field"
adb shell input text "glare-proof-sample-page"
adb shell input keyevent 66   # the keyboard's Done seals
if ! wait_for "Sealed" 15; then tap "Seal" || true; fi
wait_for "Sealed" 180 || fail "sealing did not finish"
shot 05-sealed
tap "Done" || fail "could not close the sealed dialog"

log "check the custody log"
tap "Vault" || fail "no Vault tab"
shot 06-vault
tap "Check the log" || fail "no log check"
wait_for "Chain intact" 60 || fail "the custody log check did not pass"
shot 07-log-checked

log "plan"
tap "Plan" || fail "no Plan tab"
wait_for "Pro, free for 180 more days" 10 || fail "the free Pro offer is not shown"
to_top
shot 08-plan

alive || fail "the app is not running at the end"
if adb logcat -d | grep -q "FATAL EXCEPTION"; then fail "a crash was logged"; fi
adb shell am broadcast -a com.android.systemui.demo -e command exit >/dev/null
log "beta smoke passed"
