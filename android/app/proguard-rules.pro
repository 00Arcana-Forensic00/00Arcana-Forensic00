# OpenCV's Java classes are called from native code.
-keep class org.opencv.** { *; }
# BouncyCastle: only Argon2 and Ed25519 are used, directly; the rest may be removed.
-dontwarn org.bouncycastle.**
-dontwarn javax.naming.**
