package com.grupo8_uniandes.solventa.domain.region

class ConfirmFromProfile(
    private val repository: RegionRepository,
) {
    operator fun invoke(): RegionChoice = repository.confirmFromProfile()
}
