package com.grupo8_uniandes.solventa.data.bff.mock

import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceInDto
import com.grupo8_uniandes.solventa.data.bff.dto.AssistanceOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimNoticeDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimReceiptDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimsDto
import com.grupo8_uniandes.solventa.data.bff.dto.DetailDto
import com.grupo8_uniandes.solventa.data.bff.dto.HomeDto
import com.grupo8_uniandes.solventa.data.bff.dto.IssuedDto
import com.grupo8_uniandes.solventa.data.bff.dto.MortgageInDto
import com.grupo8_uniandes.solventa.data.bff.dto.MortgageOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.NoticesDto
import com.grupo8_uniandes.solventa.data.bff.dto.OfferInDto
import com.grupo8_uniandes.solventa.data.bff.dto.OfferOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.PaymentDto
import com.grupo8_uniandes.solventa.data.bff.dto.PolicyCommandDto
import com.grupo8_uniandes.solventa.data.bff.dto.ProvidersDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushNoticeDto
import com.grupo8_uniandes.solventa.data.bff.dto.PushRegistrationDto
import com.grupo8_uniandes.solventa.data.bff.dto.RejectionDto
import com.grupo8_uniandes.solventa.data.bff.dto.RevokeDto
import com.grupo8_uniandes.solventa.data.bff.dto.SessionOutDto
import com.grupo8_uniandes.solventa.data.bff.dto.SignupDto
import com.grupo8_uniandes.solventa.data.bff.dto.WalletDto
import com.grupo8_uniandes.solventa.data.bff.fixture.PublishedSamples
import com.grupo8_uniandes.solventa.data.bff.mapping.decode
import com.grupo8_uniandes.solventa.data.bff.mapping.required
import com.grupo8_uniandes.solventa.data.bff.mapping.toDetail
import com.grupo8_uniandes.solventa.data.bff.mapping.toEntries
import com.grupo8_uniandes.solventa.data.bff.mapping.toHome
import com.grupo8_uniandes.solventa.data.bff.mapping.toNotice
import com.grupo8_uniandes.solventa.data.bff.mapping.toNotices
import com.grupo8_uniandes.solventa.data.bff.mapping.toOffer
import com.grupo8_uniandes.solventa.data.bff.mapping.toPayment
import com.grupo8_uniandes.solventa.data.bff.mapping.toPolicy
import com.grupo8_uniandes.solventa.data.bff.mapping.toPolicyOrNull
import com.grupo8_uniandes.solventa.data.bff.mapping.toProfile
import com.grupo8_uniandes.solventa.data.bff.mapping.toProviders
import com.grupo8_uniandes.solventa.data.bff.mapping.toQuote
import com.grupo8_uniandes.solventa.data.bff.mapping.toReceipt
import com.grupo8_uniandes.solventa.data.bff.mapping.toRecord
import com.grupo8_uniandes.solventa.data.bff.mapping.toRegistration
import com.grupo8_uniandes.solventa.data.bff.mapping.toRejection
import com.grupo8_uniandes.solventa.data.bff.mapping.toRequest
import com.grupo8_uniandes.solventa.data.bff.mapping.toResult
import com.grupo8_uniandes.solventa.data.bff.mapping.toRevocation
import com.grupo8_uniandes.solventa.data.bff.mapping.toRisk
import com.grupo8_uniandes.solventa.data.bff.mapping.toSummaries
import com.grupo8_uniandes.solventa.data.bff.mapping.toTokens
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRepository
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceResult
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.home.BffHome
import com.grupo8_uniandes.solventa.domain.bff.home.HomeBffRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssueRejection
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuedPolicy
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import com.grupo8_uniandes.solventa.domain.bff.mortgage.CreditProfile
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageQuote
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageRepository
import com.grupo8_uniandes.solventa.domain.bff.notice.NoticeRepository
import com.grupo8_uniandes.solventa.domain.bff.notice.ValidityNotice
import com.grupo8_uniandes.solventa.domain.bff.offer.DeviceRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.payment.AutomaticPayment
import com.grupo8_uniandes.solventa.domain.bff.payment.PaymentRepository
import com.grupo8_uniandes.solventa.domain.bff.policycommand.PolicyCommandRepository
import com.grupo8_uniandes.solventa.domain.bff.push.PushNotice
import com.grupo8_uniandes.solventa.domain.bff.push.PushRegistration
import com.grupo8_uniandes.solventa.domain.bff.push.PushRepository
import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import com.grupo8_uniandes.solventa.domain.bff.signup.ConsentRevocation
import com.grupo8_uniandes.solventa.domain.bff.signup.SignupRecord
import com.grupo8_uniandes.solventa.domain.bff.signup.SignupRepository
import kotlinx.serialization.SerializationException

enum class StandInMode { Success, Failure, Late }

class StandInControl(private val mode: StandInMode) {
    private var released = false

    fun release() {
        released = true
    }

    fun <T> ready(load: () -> T): StandInAnswer<T> {
        if (mode == StandInMode.Failure) return StandInAnswer.Failed
        if (mode == StandInMode.Late && !released) return StandInAnswer.Pending
        return try {
            StandInAnswer.Ready(load())
        } catch (_: SerializationException) {
            StandInAnswer.Failed
        }
    }
}

class MockMobileSessionRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
) : MobileSessionRepository {
    override fun signIn(correo: String, contrasena: String): StandInAnswer<SessionTokens> =
        control.ready { decode<SessionOutDto>(PublishedSamples.SESSION_OUT).let(::required).toTokens() }

    override fun refresh(refreshToken: String): StandInAnswer<SessionTokens> =
        control.ready { decode<SessionOutDto>(PublishedSamples.SESSION_OUT).let(::required).toTokens() }

    override fun signOut(): StandInAnswer<Unit> = control.ready { Unit }
}

class MockSignupRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
) : SignupRepository {
    override fun register(record: SignupRecord): StandInAnswer<SignupRecord> =
        control.ready { decode<SignupDto>(PublishedSamples.SIGNUP).let(::required).toRecord() }

    override fun revokeConsent(): StandInAnswer<ConsentRevocation> =
        control.ready { decode<RevokeDto>(PublishedSamples.REVOKE).let(::required).toRevocation() }
}

class MockOfferRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
) : OfferRepository {
    override fun quote(ramo: String, risk: DeviceRisk): StandInAnswer<FirmOffer> =
        control.ready { decode<OfferOutDto>(PublishedSamples.OFFER_OUT).let(::required).toOffer() }

    override fun requote(cotizacionId: String): StandInAnswer<FirmOffer> =
        control.ready { decode<OfferOutDto>(PublishedSamples.OFFER_OUT).let(::required).toOffer() }

    fun release() = control.release()
}

class MockIssuanceRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
) : IssuanceRepository {
    override fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> =
        control.ready { decode<IssuedDto>(PublishedSamples.ISSUED).let(::required).toPolicy() }

    override fun rejected(): StandInAnswer<IssueRejection> =
        control.ready { required(decode<RejectionDto>(PublishedSamples.REJECTION).let(::required).toRejection()) }

    override fun wallet(): StandInAnswer<List<WalletEntry>> =
        control.ready { decode<WalletDto>(PublishedSamples.WALLET).let(::required).toEntries() }

    override fun detail(numero: String): StandInAnswer<PolicyDetail> =
        control.ready { decode<DetailDto>(PublishedSamples.DETAIL).let(::required).toDetail() }
}

class MockClaimRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
    private val noticeJson: String = PublishedSamples.CLAIM_NOTICE,
) : ClaimRepository {
    override fun notify(notice: ClaimNotice): StandInAnswer<ClaimReceipt> =
        control.ready { decode<ClaimReceiptDto>(PublishedSamples.CLAIM_RECEIPT).let(::required).toReceipt() }

    override fun list(): StandInAnswer<List<ClaimSummary>> =
        control.ready { decode<ClaimsDto>(PublishedSamples.CLAIMS).let(::required).toSummaries() }

    fun readNotice(raw: String = noticeJson): ClaimNotice? = decode<ClaimNoticeDto>(raw)?.toNotice()
}

class MockPaymentRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
) : PaymentRepository {
    override fun read(): StandInAnswer<AutomaticPayment> =
        control.ready { decode<PaymentDto>(PublishedSamples.PAYMENT).let(::required).toPayment() }
}

class MockMortgageRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
) : MortgageRepository {
    override fun offer(profile: CreditProfile): StandInAnswer<MortgageQuote> = read(PublishedSamples.MORTGAGE_OUT)

    override fun degraded(): StandInAnswer<MortgageQuote> = read(PublishedSamples.MORTGAGE_DEGRADED)

    private fun read(raw: String) =
        control.ready { decode<MortgageOutDto>(raw).let(::required).toQuote() }
}

class MockNoticeRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
) : NoticeRepository {
    override fun list(): StandInAnswer<List<ValidityNotice>> =
        control.ready { decode<NoticesDto>(PublishedSamples.NOTICES).let(::required).toNotices() }
}

class MockPolicyCommandRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
) : PolicyCommandRepository {
    override fun renew(numero: String): StandInAnswer<IssuedPolicy> = command(PublishedSamples.RENEW)

    override fun modify(numero: String): StandInAnswer<IssuedPolicy> = command(PublishedSamples.RENEW)

    override fun cancel(numero: String, motivo: String?): StandInAnswer<IssuedPolicy> {
        val raw = if (motivo.isNullOrBlank()) PublishedSamples.CANCEL_NO_REASON else PublishedSamples.CANCEL
        return command(raw)
    }

    private fun command(raw: String): StandInAnswer<IssuedPolicy> =
        control.ready {
            val issued = decode<IssuedDto>(PublishedSamples.ISSUED).let(::required).toPolicy()
            val command = decode<PolicyCommandDto>(raw).let(::required)
            command.toPolicyOrNull(issued) ?: throw SerializationException("missing motivo")
        }
}

class MockHomeBffRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
) : HomeBffRepository {
    override fun load(): StandInAnswer<BffHome> =
        control.ready { decode<HomeDto>(PublishedSamples.HOME).let(::required).toHome() }
}

class MockPushRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
) : PushRepository {
    override fun register(registration: PushRegistration): StandInAnswer<PushRegistration> =
        control.ready { decode<PushRegistrationDto>(PublishedSamples.PUSH_REGISTRATION).let(::required).toRegistration() }

    override fun notice(): StandInAnswer<PushNotice> =
        control.ready { decode<PushNoticeDto>(PublishedSamples.PUSH_NOTICE).let(::required).toNotice() }
}

class MockAssistanceRepository(
    private val control: StandInControl = StandInControl(StandInMode.Success),
) : AssistanceRepository {
    override fun providers(): StandInAnswer<List<Provider>> =
        control.ready { decode<ProvidersDto>(PublishedSamples.PROVIDERS).let(::required).toProviders() }

    override fun request(body: AssistanceRequest): StandInAnswer<AssistanceResult> =
        control.ready { decode<AssistanceOutDto>(PublishedSamples.ASSISTANCE_OUT).let(::required).toResult() }
}

internal fun publishedOfferRequest() = decode<OfferInDto>(PublishedSamples.OFFER_IN).let(::required).toRisk()

internal fun publishedSignup() = decode<SignupDto>(PublishedSamples.SIGNUP).let(::required).toRecord()

internal fun publishedMortgageRequest() = decode<MortgageInDto>(PublishedSamples.MORTGAGE_IN).let(::required).toProfile()

internal fun publishedAssistanceRequest() = decode<AssistanceInDto>(PublishedSamples.ASSISTANCE_IN).let(::required).toRequest()
