package com.grupo8_uniandes.solventa.data.home

import com.grupo8_uniandes.solventa.domain.home.HomeRepository
import com.grupo8_uniandes.solventa.domain.home.HomeSituation

/**
 * A real launch has no quotes, policies, or claims, and no origination.
 */
class EmptyHomeRepository : HomeRepository {
    override fun load(): HomeSituation = HomeSituation()
}
