package com.grupo8_uniandes.solventa.domain.home

/**
 * One read of the customer's current situation. No network and no local database.
 */
fun interface HomeRepository {
    fun load(): HomeSituation
}
