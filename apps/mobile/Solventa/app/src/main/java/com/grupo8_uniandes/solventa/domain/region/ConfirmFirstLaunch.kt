package com.grupo8_uniandes.solventa.domain.region

class ConfirmFirstLaunch(
    private val repository: RegionRepository,
) {
    operator fun invoke(): RegionChoice = repository.confirmFirstLaunch()
}
