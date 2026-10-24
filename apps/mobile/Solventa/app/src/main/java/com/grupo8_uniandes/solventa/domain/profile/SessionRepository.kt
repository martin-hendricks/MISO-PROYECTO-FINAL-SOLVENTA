package com.grupo8_uniandes.solventa.domain.profile

interface SessionRepository {
    fun isOpen(): Boolean

    fun close()

    fun open()
}
