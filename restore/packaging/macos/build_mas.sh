#!/usr/bin/env bash
# Package dist/store/Arcalume.app for Mac App Store upload. NOT YET RUN: needs an Apple
# Developer account and these in the keychain / environment:
#   MAS_APP_IDENTITY        "3rd Party Mac Developer Application: <Name> (<TEAMID>)" or "Apple Distribution: ..."
#   MAS_INSTALLER_IDENTITY  "3rd Party Mac Developer Installer: <Name> (<TEAMID>)"
#   MAS_PROVISIONING_PROFILE path to the .provisionprofile for com.arcanaforensics.arcalume
# Then upload the .pkg with Transporter or `xcrun altool --upload-app`.
set -euo pipefail
cd "$(dirname "$0")/../.."
APP="dist/store/Arcalume.app"
VERSION="$(grep -m1 '^version' pyproject.toml | cut -d'"' -f2)"
[ -d "$APP" ] || { echo "build first: python packaging/build.py --edition store"; exit 1; }
cp "$MAS_PROVISIONING_PROFILE" "$APP/Contents/embedded.provisionprofile"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $VERSION" "$APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :LSApplicationCategoryType string public.app-category.productivity" "$APP/Contents/Info.plist" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :ITSAppUsesNonExemptEncryption bool true" "$APP/Contents/Info.plist" 2>/dev/null || true
# Sign nested code first, then the bundle, with the sandbox entitlements.
find "$APP/Contents" \( -name "*.so" -o -name "*.dylib" \) -print0 | xargs -0 -I{} codesign --force --timestamp --options runtime --sign "$MAS_APP_IDENTITY" {}
codesign --force --timestamp --options runtime --entitlements packaging/macos/entitlements.mas.plist --sign "$MAS_APP_IDENTITY" "$APP"
productbuild --component "$APP" /Applications --sign "$MAS_INSTALLER_IDENTITY" "dist/Arcalume-$VERSION-mas.pkg"
echo "dist/Arcalume-$VERSION-mas.pkg"
