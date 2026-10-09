plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.grupo8_uniandes.solventa"
    compileSdk {
        version = release(37)
    }

    defaultConfig {
        applicationId = "com.grupo8_uniandes.solventa"
        minSdk = 24
        targetSdk = 37
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        debug {
            enableUnitTestCoverage = true
        }
        release {
            optimization {
                enable = false
            }
        }
    }
    testCoverage {
        jacocoVersion = libs.versions.jacoco.get()
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    buildFeatures {
        compose = true
    }
    testOptions {
        unitTests.isIncludeAndroidResources = true
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    testImplementation(libs.junit)
    testImplementation(libs.robolectric)
    testImplementation(platform(libs.androidx.compose.bom))
    testImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.navigation.testing)
    androidTestImplementation(libs.androidx.junit)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
    debugImplementation(libs.androidx.compose.ui.tooling)
}

// The activity, splash, and signed-in shell run on a device. Robolectric covers the
// language screen, the Profile sheet, and the preferences store in this report.
val unitTestCoverageExcludedSources = setOf(
    "MainActivity.kt",
    "CustomerShell.kt",
    "SplashScreen.kt",
)

val filterDebugUnitTestCoverageReport = tasks.register<ExcludeJacocoSources>("filterDebugUnitTestCoverageReport") {
    report.set(layout.buildDirectory.file("reports/coverage/test/debug/report.xml"))
    excludedSources.set(unitTestCoverageExcludedSources)
    dependsOn("createDebugUnitTestCoverageReport")
}

tasks.matching { it.name == "createDebugUnitTestCoverageReport" }.configureEach {
    finalizedBy(filterDebugUnitTestCoverageReport)
}