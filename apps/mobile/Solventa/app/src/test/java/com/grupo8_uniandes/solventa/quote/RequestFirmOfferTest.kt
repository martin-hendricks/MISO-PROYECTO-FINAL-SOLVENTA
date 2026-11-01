package com.grupo8_uniandes.solventa.quote

import com.grupo8_uniandes.solventa.data.bff.mock.MockOfferRepository
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.offer.ClimateRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.DeviceRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.LifeRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.LineRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.MortgageRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.PaymentsRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteAnswers
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteAttempt
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteInput
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteLine
import com.grupo8_uniandes.solventa.domain.bff.offer.RequestFirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.TravelRisk
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Test

class RequestFirmOfferTest {
    @Test
    fun givenPublishedAnswers_whenSubmitted_thenThePreparedPremiumReturns() {
        val repository = RecordingOfferRepository()
        val attempt = runBlocking { RequestFirmOffer(repository).submit(QuoteLine.Device, device()) }
        val ready = (attempt as QuoteAttempt.Answer).answer as StandInAnswer.Ready

        assertEquals("Protección de dispositivo", repository.lastRamo)
        assertEquals(DeviceRisk(2400000, "Pixel", false), repository.lastRisk)
        assertEquals(89000L, ready.value.prima)
        assertEquals("COT-1042", ready.value.cotizacionId)
        assertEquals("COP", ready.value.moneda)
    }

    @Test
    fun givenTheStandIn_whenThePublishedAnswersAreSent_thenItReturnsTheSample() {
        val attempt = runBlocking { RequestFirmOffer(MockOfferRepository()).submit(QuoteLine.Device, device()) }
        val ready = (attempt as QuoteAttempt.Answer).answer as StandInAnswer.Ready

        assertEquals(89000L, ready.value.prima)
        assertEquals("oferta_vigente", ready.value.estado)
        assertEquals("Protección de dispositivo", ready.value.ramo)
    }

    @Test
    fun givenTravelAnswers_whenSubmitted_thenThePreparedPremiumKeepsThatLine() {
        val repository = RecordingOfferRepository()
        val attempt = runBlocking {
            RequestFirmOffer(repository).submit(
                QuoteLine.Travel,
                QuoteAnswers(destination = "Bogotá", duration = "7"),
            )
        }
        val ready = (attempt as QuoteAttempt.Answer).answer as StandInAnswer.Ready

        assertEquals("Viaje", repository.lastRamo)
        assertEquals(TravelRisk("Bogotá", 7), repository.lastRisk)
        assertEquals(89000L, ready.value.prima)
        assertEquals("COT-1042", ready.value.cotizacionId)
    }

    @Test
    fun givenEachLine_whenAnswersAreCompleteOrMissing_thenTheRiskOrTheGapIsReturned() {
        val repository = RecordingOfferRepository()
        val request = RequestFirmOffer(repository)

        assertEquals(
            LifeRisk(5000000, 34),
            sent(request, repository, QuoteLine.Life, QuoteAnswers(sumInsured = "5000000", ageYears = "34")),
        )
        assertEquals(QuoteInput.SumInsured, gap(request, QuoteLine.Life, QuoteAnswers(ageYears = "34")))
        assertEquals(QuoteInput.AgeYears, gap(request, QuoteLine.Life, QuoteAnswers(sumInsured = "5000000", ageYears = " ")))

        assertEquals(
            ClimateRisk("lluvia", "BOG", 40),
            sent(request, repository, QuoteLine.Climate, QuoteAnswers(event = "lluvia", reference = "BOG", threshold = "40")),
        )
        assertEquals(
            ClimateRisk("lluvia", "", 40),
            sent(request, repository, QuoteLine.Climate, QuoteAnswers(event = "lluvia", threshold = "40")),
        )
        assertEquals(QuoteInput.Event, gap(request, QuoteLine.Climate, QuoteAnswers(reference = "BOG", threshold = "40")))
        assertEquals(QuoteInput.Threshold, gap(request, QuoteLine.Climate, QuoteAnswers(event = "lluvia", reference = "BOG", threshold = "0")))

        assertEquals(
            MortgageRisk(180000000, 240),
            sent(request, repository, QuoteLine.Mortgage, QuoteAnswers(creditValue = "180000000", creditTerm = "20")),
        )
        assertEquals(QuoteInput.CreditValue, gap(request, QuoteLine.Mortgage, QuoteAnswers(creditTerm = "240")))
        assertEquals(QuoteInput.CreditTerm, gap(request, QuoteLine.Mortgage, QuoteAnswers(creditValue = "180000000")))

        assertEquals(
            PaymentsRisk(350000, 12),
            sent(request, repository, QuoteLine.Payments, QuoteAnswers(installment = "350000", term = "12")),
        )
        assertEquals(QuoteInput.Installment, gap(request, QuoteLine.Payments, QuoteAnswers(term = "12")))
        assertEquals(QuoteInput.Term, gap(request, QuoteLine.Payments, QuoteAnswers(installment = "350000", term = "-1")))
    }

    @Test
    fun givenAMissingAnswer_whenSubmitted_thenTheRepositoryIsNotCalled() {
        val repository = RecordingOfferRepository()
        val request = RequestFirmOffer(repository)

        assertEquals(QuoteInput.Value, gap(request, device(value = "")))
        assertEquals(QuoteInput.Value, gap(request, device(value = "0")))
        assertEquals(QuoteInput.Value, gap(request, device(value = "-5")))
        assertEquals(QuoteInput.Value, gap(request, device(value = "12.5")))
        assertEquals(QuoteInput.Brand, gap(request, device(brand = "  ")))
        assertEquals(QuoteInput.Age, gap(request, device(older = null)))
        assertEquals(
            QuoteInput.Destination,
            gap(request, QuoteLine.Travel, QuoteAnswers(duration = "7")),
        )
        assertEquals(
            QuoteInput.Duration,
            gap(request, QuoteLine.Travel, QuoteAnswers(destination = "Bogotá", duration = "0")),
        )
        assertEquals(0, repository.quotes)
    }

    private fun sent(
        request: RequestFirmOffer,
        repository: RecordingOfferRepository,
        line: QuoteLine,
        answers: QuoteAnswers,
    ): LineRisk? {
        val attempt = runBlocking { request.submit(line, answers) }
        assertEquals(true, attempt is QuoteAttempt.Answer)
        return repository.lastRisk
    }

    private fun device(
        value: String = "2400000",
        brand: String = "Pixel",
        older: Boolean? = false,
    ) = QuoteAnswers(value = value, brand = brand, olderThan12Months = older)

    private fun gap(
        request: RequestFirmOffer,
        answers: QuoteAnswers,
    ) = gap(request, QuoteLine.Device, answers)

    private fun gap(
        request: RequestFirmOffer,
        line: QuoteLine,
        answers: QuoteAnswers,
    ) = runBlocking { (request.submit(line, answers) as QuoteAttempt.Gap).field }
}

private class RecordingOfferRepository : OfferRepository {
    var quotes: Int = 0
    var lastRamo: String? = null
    var lastRisk: LineRisk? = null

    override suspend fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> {
        quotes += 1
        lastRamo = ramo
        lastRisk = risk
        return StandInAnswer.Ready(
            FirmOffer(
                cotizacionId = "COT-1042",
                ramo = ramo,
                estado = "oferta_vigente",
                prima = 89000,
                moneda = "COP",
                venceEn = "2026-10-01",
            ),
        )
    }

    override suspend fun requote(cotizacionId: String): StandInAnswer<FirmOffer> =
        quote("", DeviceRisk(1, "x", false))
}
