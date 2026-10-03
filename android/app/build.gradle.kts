plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.arcanaforensics.arcalume"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.arcanaforensics.arcalume"
        minSdk = 26
        targetSdk = 36
        // CI numbers beta builds so each one installs over the last.
        versionCode = providers.environmentVariable("ARCALUME_VERSION_CODE").orNull?.toInt() ?: 1
        versionName = "0.1.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    // play: sold on Google Play, Pro through Play Billing.
    // direct: for sideloading and stores without Play Billing, Pro through an offline license key.
    flavorDimensions += "store"
    productFlavors {
        create("play") { dimension = "store" }
        create("direct") {
            dimension = "store"
            applicationIdSuffix = ".direct"
            versionNameSuffix = "-direct"
        }
    }

    signingConfigs {
        // Beta builds only. CI passes a stable keystore so updates install over each other;
        // without one (a local build) the debug key is used. Store uploads use a separate
        // upload key that never touches this repository (android/store/SUBMISSION.md).
        create("beta") {
            val keystore = providers.environmentVariable("ARCALUME_BETA_KEYSTORE").orNull
            if (keystore != null) {
                storeFile = file(keystore)
                storePassword = providers.environmentVariable("ARCALUME_BETA_PASSWORD").get()
                keyAlias = "beta"
                keyPassword = providers.environmentVariable("ARCALUME_BETA_PASSWORD").get()
            } else {
                initWith(getByName("debug"))
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            // Signing is configured in CI from secrets (see android/store/SUBMISSION.md);
            // unsigned release builds are still produced for inspection.
        }
        // A release build (shrunk and optimized, not debuggable) for testers to sideload. Its own
        // package id and home-screen name let it sit next to the store version.
        create("beta") {
            initWith(getByName("release"))
            applicationIdSuffix = ".beta"
            versionNameSuffix = "-beta"
            signingConfig = signingConfigs.getByName("beta")
            matchingFallbacks += "release"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    packaging {
        resources.excludes += setOf("META-INF/versions/9/OSGI-INF/MANIFEST.MF", "META-INF/{AL2.0,LGPL2.1}")
    }
    testOptions {
        unitTests.isIncludeAndroidResources = true
    }
    lint {
        abortOnError = true
        warningsAsErrors = false
        checkReleaseBuilds = true
    }
}

kotlin {
    compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) }
}

dependencies {
    implementation("com.arcanaforensics.arcalume:core")
    implementation(libs.opencv)

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.graphics)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.compose.material.icons)
    implementation(libs.camerax.core)
    implementation(libs.camerax.camera2)
    implementation(libs.camerax.lifecycle)
    implementation(libs.camerax.view)
    "playImplementation"(libs.billing)
    debugImplementation(libs.compose.ui.tooling)
    debugImplementation(libs.compose.ui.test.manifest)

    testImplementation(libs.junit)
    testImplementation(libs.robolectric)
    testImplementation(libs.androidx.test.core)
    testImplementation(libs.androidx.test.ext.junit)
    testImplementation(platform(libs.compose.bom))
    testImplementation(libs.compose.ui.test.junit4)

    androidTestImplementation(libs.androidx.test.ext.junit)
    androidTestImplementation(libs.androidx.test.runner)
    androidTestImplementation(libs.espresso.core)
    androidTestImplementation(libs.espresso.accessibility)
    androidTestImplementation(platform(libs.compose.bom))
    androidTestImplementation(libs.compose.ui.test.junit4)
    androidTestImplementation(libs.compose.ui.test.accessibility)
}
