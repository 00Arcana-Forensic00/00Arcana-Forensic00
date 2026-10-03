pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "Arcalume"

// The recovery engine, vault, ledger and licensing: plain Kotlin/JVM, testable without
// the Android SDK (cd core && gradle test). Substituted for com.arcanaforensics.arcalume:core.
includeBuild("core")
include(":app")
