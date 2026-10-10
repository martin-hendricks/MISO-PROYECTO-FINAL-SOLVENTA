package com.grupo8_uniandes.solventa.region

import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.RegionChoice
import com.grupo8_uniandes.solventa.domain.region.RegionRepository

class FakeRegionRepository(
    var choice: RegionChoice = RegionChoice(),
) : RegionRepository {
    override fun read(): RegionChoice = choice

    override fun stage(region: Region): RegionChoice {
        choice = choice.copy(draftRegion = region)
        return choice
    }

    override fun confirmFirstLaunch(): RegionChoice {
        choice = choice.copy(
            appliedRegion = choice.draftRegion,
            firstLaunchCompleted = true,
        )
        return choice
    }

    override fun confirmFromProfile(): RegionChoice {
        choice = choice.copy(appliedRegion = choice.draftRegion)
        return choice
    }
}
