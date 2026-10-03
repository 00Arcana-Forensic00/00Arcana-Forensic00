// :core is its own Gradle build so it can be built and tested on any JVM, without the
// Android SDK. The Android app pulls it in as an included build (see ../settings.gradle.kts).
pluginManagement { repositories { gradlePluginPortal(); mavenCentral() } }
dependencyResolutionManagement { repositories { mavenCentral() } }
rootProject.name = "core"
