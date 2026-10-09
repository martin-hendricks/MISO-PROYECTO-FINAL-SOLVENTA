package com.grupo8_uniandes.solventa.consent

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.consent.ConsentPrefsFile
import com.grupo8_uniandes.solventa.data.consent.KeyConsentRecords
import com.grupo8_uniandes.solventa.data.consent.KeyConsentState
import com.grupo8_uniandes.solventa.data.consent.SharedPrefsConsentRepository
import com.grupo8_uniandes.solventa.data.consent.toWire
import com.grupo8_uniandes.solventa.domain.consent.ChangeDataTreatment
import com.grupo8_uniandes.solventa.domain.consent.ConsentAction
import com.grupo8_uniandes.solventa.domain.consent.ConsentRecord
import com.grupo8_uniandes.solventa.domain.consent.ConsentState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class SharedPrefsConsentRepositoryTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()
    private val repository = SharedPrefsConsentRepository(context)

    @Before
    fun clearStore() {
        context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
    }

    @Test
    fun givenEmptyStore_whenRead_thenNotGranted() {
        val snapshot = repository.read()

        assertEquals(ConsentState.NotGranted, snapshot.state)
        assertTrue(snapshot.records.isEmpty())
    }

    @Test
    fun givenGrant_whenRead_thenOneGrantLine() {
        ChangeDataTreatment(repository) { 1_710_000_000_000L }.grant()

        val prefs = context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE)
        assertEquals("granted", prefs.getString(KeyConsentState, null))
        assertEquals("GRANT|1710000000000|granted", prefs.getString(KeyConsentRecords, null))
        assertEquals(ConsentState.Granted, repository.read().state)
        assertEquals(1, repository.read().records.size)
        assertFalse(prefs.all.keys.any { it.contains("profil") })
    }

    @Test
    fun givenGrant_whenGrantAgain_thenLineStaysOne() {
        val change = ChangeDataTreatment(repository) { 1_710_000_000_000L }
        change.grant()
        change.grant()

        val records = context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE)
            .getString(KeyConsentRecords, null)
        assertEquals("GRANT|1710000000000|granted", records)
    }

    @Test
    fun givenNotGranted_whenRevokeAppended_thenStoreStaysEmpty() {
        repository.append(
            ConsentRecord(
                action = ConsentAction.Revoke,
                atMillis = 9L,
                resulting = ConsentState.Revoked,
            ),
        )

        assertEquals(ConsentState.NotGranted, repository.read().state)
        assertTrue(repository.read().records.isEmpty())
    }

    @Test
    fun givenRevokeThenGrant_whenRead_thenRevokeLineRemains() {
        ChangeDataTreatment(repository) { 1L }.grant()
        ChangeDataTreatment(repository) { 2L }.revoke()
        ChangeDataTreatment(repository) { 3L }.grant()

        val records = context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE)
            .getString(KeyConsentRecords, null)
        assertEquals(
            "GRANT|1|granted\nREVOKE|2|revoked\nGRANT|3|granted",
            records,
        )
        assertEquals(ConsentState.Granted, repository.read().state)
        assertEquals(setOf(KeyConsentState, KeyConsentRecords), prefsKeys())
    }

    @Test
    fun givenMalformedLines_whenRead_thenOnlyLegalRecordsRemain() {
        context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE)
            .edit()
            .putString(KeyConsentState, "other")
            .putString(
                KeyConsentRecords,
                "broken\nNOPE|1|granted\nGRANT|nope|granted\nGRANT|4|maybe\nGRANT|5|granted",
            )
            .commit()

        val snapshot = repository.read()

        assertEquals(ConsentState.NotGranted, snapshot.state)
        assertEquals(
            listOf(ConsentRecord(ConsentAction.Grant, 5L, ConsentState.Granted)),
            snapshot.records,
        )
        assertEquals("not_granted", ConsentState.NotGranted.toWire())
    }

    @Test
    fun givenGrantRecordWithRevokedResult_whenAppend_thenStoreStaysEmpty() {
        repository.append(
            ConsentRecord(
                action = ConsentAction.Grant,
                atMillis = 8L,
                resulting = ConsentState.Revoked,
            ),
        )

        assertTrue(repository.read().records.isEmpty())
    }

    private fun prefsKeys(): Set<String> {
        return context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE).all.keys
    }
}
