package com.grupo8_uniandes.solventa.domain.bff

sealed interface StandInAnswer<out T> {
    data class Ready<T>(val value: T) : StandInAnswer<T>

    data object Failed : StandInAnswer<Nothing>

    data object Pending : StandInAnswer<Nothing>
}
