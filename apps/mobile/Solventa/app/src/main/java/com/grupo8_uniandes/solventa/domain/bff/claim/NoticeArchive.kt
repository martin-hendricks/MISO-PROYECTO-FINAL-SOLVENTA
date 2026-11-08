package com.grupo8_uniandes.solventa.domain.bff.claim

interface NoticeArchive {
    fun keep(key: String, notice: ClaimNotice, files: List<ByteArray>)

    fun clear()
}
