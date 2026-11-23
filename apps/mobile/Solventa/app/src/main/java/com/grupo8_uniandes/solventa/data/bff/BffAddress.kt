package com.grupo8_uniandes.solventa.data.bff

/**
 * A non-blank Gradle address wins. Otherwise a non-blank `bff.baseUrl` is used.
 * Both blank means the debug stand-in (published samples). The remote build is the
 * cross-channel check: `./gradlew :app:installRemote -PbffBaseUrl=http://10.0.2.2:8007`.
 */
object BffAddress {
    fun resolve(gradleUrl: String?, localUrl: String?): String {
        val fromGradle = gradleUrl?.trim().orEmpty()
        if (fromGradle.isNotBlank()) return fromGradle
        return localUrl?.trim().orEmpty()
    }

    fun allowsCleartext(url: String): Boolean = url.trim().startsWith("http://")
}
