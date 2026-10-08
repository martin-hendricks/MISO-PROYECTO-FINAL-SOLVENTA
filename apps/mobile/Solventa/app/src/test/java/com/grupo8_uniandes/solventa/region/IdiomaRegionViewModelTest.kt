package com.grupo8_uniandes.solventa.region

import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.RegionChoice
import com.grupo8_uniandes.solventa.ui.region.IdiomaRegionViewModel
import com.grupo8_uniandes.solventa.ui.region.RegionEffect
import com.grupo8_uniandes.solventa.ui.region.RegionSurface
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class IdiomaRegionViewModelTest {
    @Test
    fun givenFirstLaunch_whenOpened_thenColombiaIsHighlighted() {
        val repository = FakeRegionRepository()
        val viewModel = IdiomaRegionViewModel(repository, RegionSurface.FirstLaunch)

        assertEquals(Region.Colombia, viewModel.state.value.choice.draftRegion)
        assertEquals(Region.Colombia, viewModel.state.value.choice.appliedRegion)
    }

    @Test
    fun givenFirstLaunch_whenRowTapped_thenDraftChangesAndNothingIsApplied() {
        val repository = FakeRegionRepository()
        val viewModel = IdiomaRegionViewModel(repository, RegionSurface.FirstLaunch)

        viewModel.select(Region.Mexico)

        assertEquals(Region.Mexico, repository.choice.draftRegion)
        assertEquals(Region.Colombia, repository.choice.appliedRegion)
        assertNull(viewModel.state.value.effect)
    }

    @Test
    fun givenFirstLaunch_whenContinuar_thenOnboardingHandoff() {
        val repository = FakeRegionRepository()
        val viewModel = IdiomaRegionViewModel(repository, RegionSurface.FirstLaunch)

        viewModel.select(Region.Mexico)
        viewModel.confirm()

        assertEquals(Region.Mexico, repository.choice.appliedRegion)
        assertTrue(repository.choice.firstLaunchCompleted)
        assertEquals(RegionEffect.ContinueToHome, viewModel.state.value.effect)
    }

    @Test
    fun givenProfile_whenOpened_thenAppliedRegionIsHighlighted() {
        val repository = FakeRegionRepository(
            RegionChoice(
                appliedRegion = Region.Colombia,
                draftRegion = Region.Mexico,
                firstLaunchCompleted = true,
            ),
        )
        val viewModel = IdiomaRegionViewModel(repository, RegionSurface.Profile)

        assertEquals(Region.Colombia, viewModel.state.value.choice.draftRegion)
        assertEquals(Region.Colombia, viewModel.state.value.choice.appliedRegion)
    }

    @Test
    fun givenProfile_whenListo_thenSheetClosesWithoutClearingCompletion() {
        val repository = FakeRegionRepository(
            RegionChoice(firstLaunchCompleted = true),
        )
        val viewModel = IdiomaRegionViewModel(repository, RegionSurface.Profile)

        viewModel.select(Region.Chile)
        viewModel.confirm()

        assertEquals(Region.Chile, repository.choice.appliedRegion)
        assertTrue(repository.choice.firstLaunchCompleted)
        assertEquals(RegionEffect.CloseSheet, viewModel.state.value.effect)
    }

    @Test
    fun givenProfile_whenDismissed_thenAppliedRegionIsUnchanged() {
        val repository = FakeRegionRepository(
            RegionChoice(firstLaunchCompleted = true),
        )
        val viewModel = IdiomaRegionViewModel(repository, RegionSurface.Profile)

        viewModel.select(Region.Peru)
        viewModel.dismiss()

        assertEquals(Region.Colombia, repository.choice.appliedRegion)
        assertEquals(Region.Peru, repository.choice.draftRegion)
        assertTrue(repository.choice.firstLaunchCompleted)
        assertEquals(RegionEffect.CloseSheet, viewModel.state.value.effect)
    }
}
