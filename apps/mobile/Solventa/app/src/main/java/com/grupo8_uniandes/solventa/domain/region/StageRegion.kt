package com.grupo8_uniandes.solventa.domain.region

class StageRegion(
    private val repository: RegionRepository,
) {
    operator fun invoke(region: Region): RegionChoice = repository.stage(region)
}
