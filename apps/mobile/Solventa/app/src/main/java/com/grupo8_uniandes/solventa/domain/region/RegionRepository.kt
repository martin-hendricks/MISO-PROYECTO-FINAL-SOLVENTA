package com.grupo8_uniandes.solventa.domain.region

interface RegionRepository {
    fun read(): RegionChoice

    fun stage(region: Region): RegionChoice

    fun confirmFirstLaunch(): RegionChoice

    fun confirmFromProfile(): RegionChoice
}
