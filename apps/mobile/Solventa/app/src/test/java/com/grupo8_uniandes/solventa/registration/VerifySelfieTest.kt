package com.grupo8_uniandes.solventa.registration

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.signup.Liveness
import com.grupo8_uniandes.solventa.domain.bff.signup.LivenessCheck
import com.grupo8_uniandes.solventa.domain.bff.signup.LivenessRepository
import com.grupo8_uniandes.solventa.domain.bff.signup.RecordStep
import com.grupo8_uniandes.solventa.domain.bff.signup.SelfieOutcome
import com.grupo8_uniandes.solventa.domain.bff.signup.VerifySelfie
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class VerifySelfieTest {
    @Test
    fun givenAPassingCheckAndAStoredResult_whenVerified_thenPassed() = runBlocking {
        val repository = ScriptedLiveness(LivenessCheck.Passed, StandInAnswer.Ready(Liveness.OK))
        val outcome = VerifySelfie(repository).invoke(byteArrayOf(1))
        assertEquals(SelfieOutcome.Passed, outcome)
        assertEquals(1, repository.checks)
        assertEquals(1, repository.records)
    }

    @Test
    fun givenAFailedCheck_whenVerified_thenFailedAndNothingIsRecorded() = runBlocking {
        val repository = ScriptedLiveness(LivenessCheck.Failed, StandInAnswer.Ready(Liveness.OK))
        val outcome = VerifySelfie(repository).invoke(byteArrayOf(1))
        assertEquals(SelfieOutcome.Failed, outcome)
        assertEquals(0, repository.records)
    }

    @Test
    fun givenAnUnavailableCheck_whenVerified_thenUnavailableAtTheCheck() = runBlocking {
        val repository = ScriptedLiveness(LivenessCheck.Unavailable, StandInAnswer.Ready(Liveness.OK))
        val outcome = VerifySelfie(repository).invoke(byteArrayOf(1))
        assertEquals(SelfieOutcome.Unavailable(RecordStep.Check), outcome)
        assertEquals(0, repository.records)
    }

    @Test
    fun givenAPassingCheckAndAFailedRecord_whenVerified_thenUnavailableAtTheRecord() = runBlocking {
        val repository = ScriptedLiveness(LivenessCheck.Passed, StandInAnswer.Failed)
        val outcome = VerifySelfie(repository).invoke(byteArrayOf(1))
        assertEquals(SelfieOutcome.Unavailable(RecordStep.Record), outcome)
    }

    @Test
    fun givenARecordRetry_whenRetried_thenTheCheckIsNotCalledAgain() = runBlocking {
        val repository = ScriptedLiveness(LivenessCheck.Passed, StandInAnswer.Ready(Liveness.OK))
        val verify = VerifySelfie(repository)
        verify.retryRecord()
        assertEquals(0, repository.checks)
        assertEquals(1, repository.records)
        assertTrue(repository.recorded == Liveness.OK)
    }
}

internal class ScriptedLiveness(
    private val check: LivenessCheck,
    private val record: StandInAnswer<Liveness>,
) : LivenessRepository {
    var checks: Int = 0
    var records: Int = 0
    var lastPhoto: ByteArray? = null
    var recorded: Liveness? = null

    override suspend fun check(photo: ByteArray): LivenessCheck {
        checks += 1
        lastPhoto = photo
        return check
    }

    override suspend fun record(result: Liveness): StandInAnswer<Liveness> {
        records += 1
        recorded = result
        return record
    }
}
