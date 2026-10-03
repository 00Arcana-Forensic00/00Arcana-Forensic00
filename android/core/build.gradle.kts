plugins {
    kotlin("jvm") version "2.2.20"
    `java-library`
}

group = "com.arcanaforensics.arcalume"
version = "0.1.0"

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}
kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }

dependencies {
    // Argon2id and Ed25519 that behave the same on every Android version.
    api("org.bouncycastle:bcprov-jdk18on:1.86")
    // The engine is written against OpenCV's Java API. The Android app supplies the real
    // library (org.opencv:opencv AAR); on the JVM the openpnp build of the same API is
    // used for tests only, so it is never shipped.
    compileOnly("org.openpnp:opencv:4.9.0-0")
    testImplementation("org.openpnp:opencv:4.9.0-0")
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.11.4")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
    // Optional cross-language check: write artifacts for the Python suite to verify.
    systemProperty("fixtures", rootDir.resolve("src/test/resources/fixtures").absolutePath)
    System.getenv("ARCALUME_INTEROP_OUT")?.let { environment("ARCALUME_INTEROP_OUT", it) }
    testLogging { events("failed"); exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL }
}
