package com.grupo8_uniandes.solventa.region

import com.grupo8_uniandes.solventa.domain.region.ConfirmFirstLaunch
import com.grupo8_uniandes.solventa.domain.region.ConfirmFromProfile
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.RegionChoice
import com.grupo8_uniandes.solventa.domain.region.StageRegion
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ConfirmRegionTest {
    @Test
    fun givenUnknownTag_whenParsed_thenColombia() {
        assertEquals(Region.Colombia, Region.fromStored("es-AR"))
        assertEquals(Region.Colombia, Region.fromStored(null))
    }

    @Test
    fun givenKnownTag_whenParsed_thenThatRegion() {
        assertEquals(Region.Colombia, Region.fromStored("es-CO"))
        assertEquals(Region.Mexico, Region.fromStored("es-MX"))
        assertEquals(Region.Chile, Region.fromStored("es-CL"))
        assertEquals(Region.Peru, Region.fromStored("es-PE"))
    }

    @Test
    fun givenFreshChoice_whenRowStaged_thenDraftChangesAndAppliedStaysColombia() {
        val repository = FakeRegionRepository()
        val staged = StageRegion(repository)(Region.Mexico)

        assertEquals(Region.Mexico, staged.draftRegion)
        assertEquals(Region.Colombia, staged.appliedRegion)
        assertFalse(staged.firstLaunchCompleted)
    }

    @Test
    fun givenDraftMexico_whenContinuar_thenAppliedAndCompleted() {
        val repository = FakeRegionRepository(
            RegionChoice(appliedRegion = Region.Colombia, draftRegion = Region.Mexico),
        )

        val confirmed = ConfirmFirstLaunch(repository)()

        assertEquals(Region.Mexico, confirmed.appliedRegion)
        assertEquals(Region.Mexico, confirmed.draftRegion)
        assertTrue(confirmed.firstLaunchCompleted)
    }

    @Test
    fun givenCompletedChoice_whenListo_thenAppliedUpdatesAndCompletedStays() {
        val repository = FakeRegionRepository(
            RegionChoice(
                appliedRegion = Region.Colombia,
                draftRegion = Region.Chile,
                firstLaunchCompleted = true,
            ),
        )

        val confirmed = ConfirmFromProfile(repository)()

        assertEquals(Region.Chile, confirmed.appliedRegion)
        assertTrue(confirmed.firstLaunchCompleted)
    }

    @Test
    fun givenOpenFirstLaunch_whenListo_thenCompletedStaysFalse() {
        val repository = FakeRegionRepository(
            RegionChoice(draftRegion = Region.Peru, firstLaunchCompleted = false),
        )

        val confirmed = ConfirmFromProfile(repository)()

        assertEquals(Region.Peru, confirmed.appliedRegion)
        assertFalse(confirmed.firstLaunchCompleted)
    }

    @Test
    fun givenStagedDraft_whenDismissed_thenAppliedStays() {
        val repository = FakeRegionRepository()
        StageRegion(repository)(Region.Mexico)

        assertEquals(Region.Colombia, repository.read().appliedRegion)
        assertEquals(Region.Mexico, repository.read().draftRegion)
    }
}
