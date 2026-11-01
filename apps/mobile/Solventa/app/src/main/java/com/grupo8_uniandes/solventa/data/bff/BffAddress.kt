package com.grupo8_uniandes.solventa.data.bff

/**
 * A non-blank Gradle address wins. Otherwise a non-blank `bff.baseUrl` is used.
 * Both blank means the stand-in. Debug never asks this; its address field is empty.
 */
object BffAddress {
    fun resolve(gradleUrl: String?, localUrl: String?): String {
        val fromGradle = gradleUrl?.trim().orEmpty()
        if (fromGradle.isNotBlank()) return fromGradle
        return localUrl?.trim().orEmpty()
    }

    fun allowsCleartext(url: String): Boolean = url.trim().startsWith("http://")
}
