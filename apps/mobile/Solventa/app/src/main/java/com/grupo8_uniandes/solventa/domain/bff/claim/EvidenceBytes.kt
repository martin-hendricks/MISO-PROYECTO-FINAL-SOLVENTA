package com.grupo8_uniandes.solventa.domain.bff.claim

object EvidenceBytes {
    private val files = linkedMapOf<String, ByteArray>()

    fun keep(nombre: String, bytes: ByteArray) {
        files[nombre] = bytes.copyOf()
    }

    fun read(nombre: String): ByteArray? = files[nombre]?.copyOf()

    fun drop(nombre: String) {
        files.remove(nombre)
    }

    fun clear() {
        files.clear()
    }
}

fun ClaimNotice.bytesMissing(): Boolean = adjuntos.any { file ->
    file.tamanoBytes > 0 && EvidenceBytes.read(file.nombre) == null
}

fun ClaimNotice.storedFiles(): List<ByteArray> = adjuntos.map { file ->
    EvidenceBytes.read(file.nombre) ?: ByteArray(0)
}
