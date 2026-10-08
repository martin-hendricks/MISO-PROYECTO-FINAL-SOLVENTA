package com.grupo8_uniandes.solventa.domain.region

data class RegionChoice(
    val appliedRegion: Region = Region.Colombia,
    val draftRegion: Region = Region.Colombia,
    val firstLaunchCompleted: Boolean = false,
)
