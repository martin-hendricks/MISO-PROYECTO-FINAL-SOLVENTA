package com.grupo8_uniandes.solventa.consent

import com.grupo8_uniandes.solventa.domain.consent.ChangeDataTreatment
import com.grupo8_uniandes.solventa.domain.consent.ConsentAction
import com.grupo8_uniandes.solventa.domain.consent.ConsentRecord
import com.grupo8_uniandes.solventa.domain.consent.ConsentRepository
import com.grupo8_uniandes.solventa.domain.consent.ConsentSnapshot
import com.grupo8_uniandes.solventa.domain.consent.ConsentState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ChangeDataTreatmentTest {
    @Test
    fun givenNotGranted_whenGrant_thenOneGrantAtTheInjectedClock() {
        val repository = RecordingConsentRepository()
        val change = ChangeDataTreatment(repository) { 1_710_000_000_000L }

        val result = change.grant()

        assertEquals(ConsentState.Granted, result.state)
        assertEquals(1, result.records.size)
        assertEquals(ConsentAction.Grant, result.records.single().action)
        assertEquals(1_710_000_000_000L, result.records.single().atMillis)
        assertEquals(ConsentState.Granted, result.records.single().resulting)
        assertEquals("unset", repository.profiling)
    }

    @Test
    fun givenGranted_whenGrantAgain_thenNoSecondLine() {
        val repository = RecordingConsentRepository()
        val change = ChangeDataTreatment(repository) { 1_710_000_000_000L }
        change.grant()

        val again = change.grant()

        assertEquals(1, again.records.size)
        assertEquals(ConsentState.Granted, again.state)
    }

    @Test
    fun givenNotGranted_whenRevoke_thenNothingIsWritten() {
        val repository = RecordingConsentRepository()
        val change = ChangeDataTreatment(repository) { 5L }

        val result = change.revoke()

        assertEquals(ConsentState.NotGranted, result.state)
        assertTrue(result.records.isEmpty())
        assertEquals("unset", repository.profiling)
    }

    @Test
    fun givenGranted_whenRevoke_thenOneRevokeLine() {
        val repository = RecordingConsentRepository()
        val change = ChangeDataTreatment(repository) { 1_710_000_000_000L }
        change.grant()

        val revoked = ChangeDataTreatment(repository) { 1_710_000_000_500L }.revoke()

        assertEquals(ConsentState.Revoked, revoked.state)
        assertEquals(ConsentAction.Revoke, revoked.records.last().action)
        assertEquals(1_710_000_000_500L, revoked.records.last().atMillis)
        assertEquals(ConsentState.Revoked, revoked.records.last().resulting)
    }

    @Test
    fun givenRevoked_whenGrant_thenEarlierRevokeStays() {
        val repository = RecordingConsentRepository()
        ChangeDataTreatment(repository) { 1L }.grant()
        ChangeDataTreatment(repository) { 2L }.revoke()

        val again = ChangeDataTreatment(repository) { 3L }.grant()

        assertEquals(ConsentState.Granted, again.state)
        assertEquals(3, again.records.size)
        assertEquals(ConsentAction.Revoke, again.records[1].action)
        assertEquals(ConsentAction.Grant, again.records[2].action)
        assertEquals("unset", repository.profiling)
    }

    @Test
    fun givenRevoked_whenRevoke_thenNoNewLine() {
        val repository = RecordingConsentRepository()
        ChangeDataTreatment(repository) { 1L }.grant()
        ChangeDataTreatment(repository) { 2L }.revoke()

        val again = ChangeDataTreatment(repository) { 3L }.revoke()

        assertEquals(2, again.records.size)
        assertEquals(ConsentState.Revoked, again.state)
    }
}

private class RecordingConsentRepository : ConsentRepository {
    var snapshot = ConsentSnapshot()
    var profiling = "unset"

    override fun read(): ConsentSnapshot = snapshot

    override fun append(record: ConsentRecord) {
        snapshot = ConsentSnapshot(
            state = record.resulting,
            records = snapshot.records + record,
        )
    }
}
