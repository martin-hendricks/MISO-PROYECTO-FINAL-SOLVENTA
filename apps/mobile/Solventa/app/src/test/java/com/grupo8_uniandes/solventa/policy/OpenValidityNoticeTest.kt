package com.grupo8_uniandes.solventa.policy

import com.grupo8_uniandes.solventa.data.bff.dto.PushNoticeDto
import com.grupo8_uniandes.solventa.data.bff.fixture.PublishedSamples
import com.grupo8_uniandes.solventa.data.bff.mapping.decode
import com.grupo8_uniandes.solventa.data.bff.mapping.toNotice
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.notice.NoticeRepository
import com.grupo8_uniandes.solventa.domain.bff.notice.OpenValidityNotice
import com.grupo8_uniandes.solventa.domain.bff.notice.ValidityKind
import com.grupo8_uniandes.solventa.domain.bff.notice.ValidityNotice
import com.grupo8_uniandes.solventa.domain.bff.push.PushDestination
import com.grupo8_uniandes.solventa.domain.bff.push.PushNotice
import com.grupo8_uniandes.solventa.domain.bff.push.PushType
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class OpenValidityNoticeTest {
    private val notices = OpenValidityNotice(SampleNotices())

    @Before
    fun main() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun reset() {
        Dispatchers.resetMain()
    }

    @Test
    fun givenAPolicyAboutToExpire_whenTheNoticeOpens_thenTheBannerNamesTheSevenDays() = runBlocking {
        val reading = notices.openExpiry()

        assertNotNull(reading)
        assertEquals(ValidityKind.EXPIRY, reading!!.kind)
        assertEquals(OpenValidityNotice.POLICY, reading.poliza)
        assertEquals(OpenValidityNotice.EXPIRY_BANNER, reading.banner)
        assertFalse(reading.banner.contains("2027-03-12"))
        assertNull(OpenValidityNotice(SampleNotices(emptyList())).openExpiry())
        assertNull(OpenValidityNotice(FailedNotices()).openExpiry())
        assertNull(
            OpenValidityNotice(
                SampleNotices(listOf(ValidityNotice("renovacion", OpenValidityNotice.POLICY, null, "vigente"))),
            ).openExpiry(),
        )
        assertNull(
            OpenValidityNotice(
                SampleNotices(listOf(ValidityNotice("vencimiento", "POL-9", "2027-03-12", null))),
            ).openExpiry(),
        )
    }

    @Test
    fun givenARenewalInForce_whenTheNoticeOpens_thenTheBannerNamesTheDate() = runBlocking {
        val reading = notices.openRenewal()

        assertNotNull(reading)
        assertEquals(ValidityKind.RENEWAL, reading!!.kind)
        assertEquals(OpenValidityNotice.RENEWAL_BANNER, reading.banner)
        assertNotNull(
            OpenValidityNotice(
                SampleNotices(
                    listOf(
                        ValidityNotice("vencimiento", OpenValidityNotice.POLICY, "2027-03-12", null),
                        ValidityNotice("renovacion", OpenValidityNotice.POLICY, null, "vigente"),
                    ),
                ),
            ).openRenewal(),
        )
        assertNull(
            OpenValidityNotice(
                SampleNotices(
                    listOf(ValidityNotice("renovacion", OpenValidityNotice.POLICY, null, "pendiente")),
                ),
            ).openRenewal(),
        )
        assertNull(
            OpenValidityNotice(
                SampleNotices(
                    listOf(ValidityNotice("renovacion", "POL-9", null, "vigente")),
                ),
            ).openRenewal(),
        )
    }

    @Test
    fun givenAVigenciaPush_whenItIsOpened_thenTheMatchingReadingIsReturned() = runBlocking {
        val published = decode<PushNoticeDto>(PublishedSamples.PUSH_NOTICE)!!.toNotice()
        val expiry = notices.open(published)
        val renewal = notices.open(
            PushNotice(
                tipo = PushType.RENOVACION,
                titulo = "Renovación vigente",
                cuerpo = "Hasta 12 mar 2028",
                destino = PushDestination.AVISO_RENOVACION,
                poliza = OpenValidityNotice.POLICY,
            ),
        )
        val viewModel = AvisoVigenciaViewModel(notices)
        var requested: com.grupo8_uniandes.solventa.domain.bff.notice.ValidityReading? = null

        assertEquals(PushDestination.AVISO_VENCIMIENTO, published.destino)
        assertEquals(ValidityKind.EXPIRY, expiry!!.kind)
        assertEquals(ValidityKind.RENEWAL, renewal!!.kind)
        assertNull(notices.open(published.copy(destino = PushDestination.DETALLE_SINIESTRO)))
        assertNull(notices.open(published.copy(poliza = "POL-9")))
        viewModel.loadExpiry()
        assertEquals(expiry, viewModel.reading.value)
        viewModel.loadRenewal()
        assertEquals(renewal, viewModel.reading.value)
        viewModel.openPush(published)
        assertEquals(expiry, viewModel.reading.value)
        viewModel.requestExpiry(OpenValidityNotice.POLICY) { requested = it }
        assertEquals(expiry, requested)
        var other: com.grupo8_uniandes.solventa.domain.bff.notice.ValidityReading? = expiry
        viewModel.requestExpiry("POL-9") { other = it }
        assertNull(other)
        var missing: com.grupo8_uniandes.solventa.domain.bff.notice.ValidityReading? = expiry
        AvisoVigenciaViewModel(OpenValidityNotice(FailedNotices())).requestExpiry(OpenValidityNotice.POLICY) {
            missing = it
        }
        assertNull(missing)
    }

    private class SampleNotices(
        private val notices: List<ValidityNotice> = listOf(
            ValidityNotice("vencimiento", OpenValidityNotice.POLICY, "2027-03-12", null),
            ValidityNotice("renovacion", OpenValidityNotice.POLICY, null, "vigente"),
        ),
    ) : NoticeRepository {
        override suspend fun list(): StandInAnswer<List<ValidityNotice>> = StandInAnswer.Ready(notices)
    }

    private class FailedNotices : NoticeRepository {
        override suspend fun list(): StandInAnswer<List<ValidityNotice>> = StandInAnswer.Failed
    }
}
