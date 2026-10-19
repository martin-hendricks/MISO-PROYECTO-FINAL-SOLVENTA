package com.grupo8_uniandes.solventa.region

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.region.KeyAppliedRegion
import com.grupo8_uniandes.solventa.data.region.KeyDraftRegion
import com.grupo8_uniandes.solventa.data.region.KeyFirstLaunchCompleted
import com.grupo8_uniandes.solventa.data.region.RegionPrefsFile
import com.grupo8_uniandes.solventa.data.region.SharedPrefsRegionRepository
import com.grupo8_uniandes.solventa.data.region.readAppliedLanguageTag
import com.grupo8_uniandes.solventa.domain.region.Region
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class SharedPrefsRegionRepositoryTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()
    private val repository = SharedPrefsRegionRepository(context)

    @Before
    fun clearPrefs() {
        prefs().edit().clear().commit()
    }

    @Test
    fun givenEmptyFile_whenRead_thenColombiaAndNotCompleted() {
        val choice = repository.read()

        assertEquals(Region.Colombia, choice.appliedRegion)
        assertEquals(Region.Colombia, choice.draftRegion)
        assertFalse(choice.firstLaunchCompleted)
        assertEquals("es-CO", readAppliedLanguageTag(context))
    }

    @Test
    fun givenUnknownTags_whenRead_thenColombia() {
        prefs().edit()
            .putString(KeyAppliedRegion, "es-AR")
            .putString(KeyDraftRegion, "en-US")
            .commit()

        val choice = repository.read()

        assertEquals(Region.Colombia, choice.appliedRegion)
        assertEquals(Region.Colombia, choice.draftRegion)
    }

    @Test
    fun givenRowStaged_whenReadBack_thenOnlyDraftChanges() {
        val staged = repository.stage(Region.Mexico)

        assertEquals(Region.Mexico, staged.draftRegion)
        assertEquals(Region.Colombia, staged.appliedRegion)
        assertFalse(staged.firstLaunchCompleted)
        assertEquals("es-MX", prefs().getString(KeyDraftRegion, null))
        assertEquals("es-CO", prefs().getString(KeyAppliedRegion, null))
    }

    @Test
    fun givenDraft_whenContinuar_thenAppliedAndCompletedAreStored() {
        repository.stage(Region.Chile)

        val confirmed = repository.confirmFirstLaunch()

        assertEquals(Region.Chile, confirmed.appliedRegion)
        assertTrue(confirmed.firstLaunchCompleted)
        assertEquals("es-CL", readAppliedLanguageTag(context))
        assertTrue(prefs().getBoolean(KeyFirstLaunchCompleted, false))
    }

    @Test
    fun givenCompletedChoice_whenListo_thenAppliedChangesAndCompletionStays() {
        repository.stage(Region.Peru)
        repository.confirmFirstLaunch()
        repository.stage(Region.Mexico)

        val confirmed = repository.confirmFromProfile()

        assertEquals(Region.Mexico, confirmed.appliedRegion)
        assertEquals(Region.Mexico, confirmed.draftRegion)
        assertTrue(confirmed.firstLaunchCompleted)
    }

    private fun prefs() = context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE)
}
