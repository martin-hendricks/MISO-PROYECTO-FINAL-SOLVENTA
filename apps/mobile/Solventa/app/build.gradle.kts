import org.gradle.testing.jacoco.plugins.JacocoTaskExtension
import java.util.Properties

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
        versionCode = (findProperty("versionCode") as String?)?.toIntOrNull() ?: 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        buildConfigField("String", "BFF_BASE_URL", "\"\"")
        manifestPlaceholders["usesCleartextTraffic"] = "false"
    }

    buildTypes {
        debug {
            enableUnitTestCoverage = true
        }
        create("remote") {
            initWith(getByName("debug"))
            matchingFallbacks += listOf("debug")
            isDebuggable = true
            val address = remoteBffAddress()
            buildConfigField("String", "BFF_BASE_URL", address.asBuildConfigString())
            manifestPlaceholders["usesCleartextTraffic"] = address.startsWith("http://").toString()
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
        buildConfig = true
    }
    installation {
        timeOutInMs = 10 * 60 * 1000
    }
    testOptions {
        unitTests.isIncludeAndroidResources = true
        unitTests.all {
            it.extensions.configure<JacocoTaskExtension> {
                isIncludeNoLocationClasses = true
                excludes = listOf("jdk.internal.*")
            }
        }
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.biometric)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.koin.android)
    implementation(libs.koin.androidx.compose)
    implementation(libs.retrofit)
    implementation(libs.okhttp)
    implementation(libs.retrofit.kotlinx.serialization)
    testImplementation(libs.junit)
    testImplementation(libs.robolectric)
    testImplementation(libs.koin.test)
    testImplementation(libs.koin.test.junit4)
    testImplementation(libs.mockwebserver)
    testImplementation(libs.kotlinx.coroutines.test)
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

// Same files as `ignore` in the repo codecov.yml. Codecov reads this filtered
// report.xml, so a file left in only one list makes the two percentages diverge.
val unitTestCoverageExcludedSources = setOf(
    "MainActivity.kt",
    "CustomerShell.kt",
    "SplashScreen.kt",
    "IdiomaRegionScreen.kt",
    "IdiomaRegionSheet.kt",
    "PerfilScreen.kt",
    "SolventaApp.kt",
)

val filterDebugUnitTestCoverageReport = tasks.register<ExcludeJacocoSources>("filterDebugUnitTestCoverageReport") {
    report.set(layout.buildDirectory.file("reports/coverage/test/debug/report.xml"))
    excludedSources.set(unitTestCoverageExcludedSources)
    dependsOn("createDebugUnitTestCoverageReport")
}

tasks.matching { it.name == "createDebugUnitTestCoverageReport" }.configureEach {
    finalizedBy(filterDebugUnitTestCoverageReport)
}

// Same order as BffAddress.resolve. Debug never reads this file: its address field stays empty.
private fun Project.remoteBffAddress(): String {
    val fromGradle = (findProperty("bffBaseUrl") as String?).orEmpty().trim()
    if (fromGradle.isNotBlank()) return fromGradle
    val file = rootProject.file("local.properties")
    if (!file.exists()) return ""
    val properties = Properties()
    file.inputStream().use(properties::load)
    return properties.getProperty("bff.baseUrl").orEmpty().trim()
}

private fun String.asBuildConfigString(): String =
    "\"" + replace("\\", "\\\\").replace("\"", "\\\"") + "\""