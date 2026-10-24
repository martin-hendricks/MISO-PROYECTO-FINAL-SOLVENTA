package com.grupo8_uniandes.solventa.data.bff.remote

import com.grupo8_uniandes.solventa.data.bff.dto.IdDto
import com.grupo8_uniandes.solventa.data.bff.dto.PolicyCommandDto
import com.grupo8_uniandes.solventa.data.bff.dto.PolicyVerbDto
import com.grupo8_uniandes.solventa.data.bff.dto.QuoteRequestDto
import com.grupo8_uniandes.solventa.data.bff.dto.RefreshInDto
import com.grupo8_uniandes.solventa.data.bff.dto.RejectionDto
import com.grupo8_uniandes.solventa.data.bff.dto.RevokeDto
import com.grupo8_uniandes.solventa.data.bff.dto.SessionInDto
import com.grupo8_uniandes.solventa.data.bff.mapping.bffJson
import com.grupo8_uniandes.solventa.data.bff.mapping.toDetail
import com.grupo8_uniandes.solventa.data.bff.mapping.toDto
import com.grupo8_uniandes.solventa.data.bff.mapping.toEntries
import com.grupo8_uniandes.solventa.data.bff.mapping.toHome
import com.grupo8_uniandes.solventa.data.bff.mapping.toNotices
import com.grupo8_uniandes.solventa.data.bff.mapping.toOffer
import com.grupo8_uniandes.solventa.data.bff.mapping.toPayment
import com.grupo8_uniandes.solventa.data.bff.mapping.toPolicy
import com.grupo8_uniandes.solventa.data.bff.mapping.toProviders
import com.grupo8_uniandes.solventa.data.bff.mapping.toQuote
import com.grupo8_uniandes.solventa.data.bff.mapping.toReceipt
import com.grupo8_uniandes.solventa.data.bff.mapping.toRecord
import com.grupo8_uniandes.solventa.data.bff.mapping.toRegistration
import com.grupo8_uniandes.solventa.data.bff.mapping.toRejection
import com.grupo8_uniandes.solventa.data.bff.mapping.toRequestElement
import com.grupo8_uniandes.solventa.data.bff.mapping.toNotice
import com.grupo8_uniandes.solventa.data.bff.mapping.toResult
import com.grupo8_uniandes.solventa.data.bff.mapping.toRevocation
import com.grupo8_uniandes.solventa.data.bff.mapping.toSummaries
import com.grupo8_uniandes.solventa.data.bff.mapping.toTokens
import com.grupo8_uniandes.solventa.data.session.TokenStore
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
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssueRejection
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuedPolicy
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import com.grupo8_uniandes.solventa.domain.bff.mortgage.CreditProfile
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageQuote
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageRepository
import com.grupo8_uniandes.solventa.domain.bff.notice.NoticeRepository
import com.grupo8_uniandes.solventa.domain.bff.notice.ValidityNotice
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.LineRisk
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
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.decodeFromJsonElement
import kotlinx.serialization.json.jsonPrimitive
import retrofit2.HttpException
import java.io.IOException

class BffGate(private val api: MobileBffApi, private val cache: BffCache) {
    suspend fun <T> call(block: suspend () -> T): StandInAnswer<T> {
        flush()
        return try {
            StandInAnswer.Ready(block())
        } catch (_: IOException) {
            StandInAnswer.Failed
        } catch (_: HttpException) {
            StandInAnswer.Failed
        } catch (_: SerializationException) {
            StandInAnswer.Failed
        }
    }

    /** Sends a queued claim once the host answers. Keeps it when the host is still unreachable. */
    suspend fun flush(): Boolean {
        val pending = cache.readClaim() ?: return true
        return try {
            api.notify(pending.key, pending.notice.toDto())
            cache.clearClaim()
            true
        } catch (_: IOException) {
            false
        } catch (_: HttpException) {
            cache.clearClaim()
            true
        }
    }
}

class RemoteSessionRepository(
    private val api: MobileBffApi,
    private val tokens: TokenStore,
    private val gate: BffGate,
) : MobileSessionRepository {
    override suspend fun signIn(correo: String, contrasena: String): StandInAnswer<SessionTokens> {
        val answer = gate.call { api.signIn(SessionInDto(correo, contrasena)).toTokens() }
        if (answer is StandInAnswer.Ready) tokens.save(answer.value)
        return answer
    }

    override suspend fun refresh(refreshToken: String): StandInAnswer<SessionTokens> {
        val answer = gate.call { api.refresh(RefreshInDto(refreshToken)).toTokens() }
        if (answer is StandInAnswer.Ready) tokens.save(answer.value)
        return answer
    }

    override suspend fun signOut(): StandInAnswer<Unit> {
        val answer = try {
            val response = api.signOut()
            if (response.isSuccessful) StandInAnswer.Ready(Unit) else StandInAnswer.Failed
        } catch (_: IOException) {
            StandInAnswer.Failed
        } catch (_: HttpException) {
            StandInAnswer.Failed
        }
        tokens.clear()
        return answer
    }
}

class RemoteSignupRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : SignupRepository {
    override suspend fun register(record: SignupRecord): StandInAnswer<SignupRecord> =
        gate.call { api.register(record.toDto()).toRecord() }

    override suspend fun revokeConsent(): StandInAnswer<ConsentRevocation> =
        gate.call { api.revoke(RevokeDto(false)).toRevocation() }
}

class RemoteOfferRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : OfferRepository {
    override suspend fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> =
        gate.call {
            api.quote(newIdempotencyKey(), QuoteRequestDto(ramo, risk.toRequestElement())).toOffer()
        }

    override suspend fun requote(cotizacionId: String): StandInAnswer<FirmOffer> =
        gate.call { api.requote(cotizacionId).toOffer() }
}

class RemoteIssuanceRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
    private val cache: BffCache,
) : IssuanceRepository {
    override suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy> =
        readAcceptance(cotizacionId).let { parsed ->
            when (parsed) {
                is Acceptance.Issued -> StandInAnswer.Ready(parsed.policy)
                is Acceptance.Rejected -> StandInAnswer.Failed
                null -> StandInAnswer.Failed
            }
        }

    override suspend fun rejected(): StandInAnswer<IssueRejection> =
        when (val parsed = readAcceptance("")) {
            is Acceptance.Rejected -> StandInAnswer.Ready(parsed.rejection)
            else -> StandInAnswer.Failed
        }

    override suspend fun wallet(): StandInAnswer<List<WalletEntry>> =
        try {
            gate.flush()
            val entries = api.wallet().toEntries()
            cache.writeWallet(entries)
            StandInAnswer.Ready(entries)
        } catch (_: IOException) {
            StandInAnswer.Ready(cache.readWallet().orEmpty())
        } catch (_: HttpException) {
            StandInAnswer.Failed
        } catch (_: SerializationException) {
            StandInAnswer.Failed
        }

    override suspend fun detail(numero: String): StandInAnswer<PolicyDetail> =
        gate.call { api.detail(numero).toDetail() }

    private suspend fun readAcceptance(cotizacionId: String): Acceptance? =
        try {
            gate.flush()
            api.accept(newIdempotencyKey(), IdDto(cotizacionId)).toAcceptance()
        } catch (_: IOException) {
            null
        } catch (_: HttpException) {
            null
        } catch (_: SerializationException) {
            null
        }
}

private sealed interface Acceptance {
    data class Issued(val policy: IssuedPolicy) : Acceptance
    data class Rejected(val rejection: IssueRejection) : Acceptance
}

private fun JsonElement.toAcceptance(): Acceptance {
    val estado = (this as? JsonObject)?.get("estado")?.jsonPrimitive?.content
    if (estado == "rechazada") {
        val dto = bffJson.decodeFromJsonElement(RejectionDto.serializer(), this)
        return Acceptance.Rejected(IssueRejection(dto.estado, dto.motivo))
    }
    return Acceptance.Issued(
        bffJson.decodeFromJsonElement(
            com.grupo8_uniandes.solventa.data.bff.dto.IssuedDto.serializer(),
            this,
        ).toPolicy(),
    )
}

class RemoteClaimRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
    private val cache: BffCache,
) : ClaimRepository {
    override suspend fun notify(notice: ClaimNotice): StandInAnswer<ClaimReceipt> {
        if (!gate.flush()) return StandInAnswer.Failed
        val key = newIdempotencyKey()
        return try {
            StandInAnswer.Ready(api.notify(key, notice.toDto()).toReceipt())
        } catch (_: IOException) {
            cache.writeClaim(PendingClaim(key, notice))
            StandInAnswer.Failed
        } catch (_: HttpException) {
            StandInAnswer.Failed
        } catch (_: SerializationException) {
            StandInAnswer.Failed
        }
    }

    override suspend fun list(): StandInAnswer<List<ClaimSummary>> =
        gate.call { api.claims().toSummaries() }
}

class RemotePaymentRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : PaymentRepository {
    override suspend fun read(): StandInAnswer<AutomaticPayment> =
        gate.call { api.payment().toPayment() }
}

class RemoteMortgageRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : MortgageRepository {
    override suspend fun offer(profile: CreditProfile): StandInAnswer<MortgageQuote> =
        gate.call { api.mortgage(profile.toDto()).toQuote() }

    override suspend fun degraded(): StandInAnswer<MortgageQuote> =
        gate.call { api.mortgage(CreditProfile(0, 0, false).toDto()).toQuote() }
}

class RemoteNoticeRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : NoticeRepository {
    override suspend fun list(): StandInAnswer<List<ValidityNotice>> =
        gate.call { api.notices().toNotices() }
}

class RemotePolicyCommandRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : PolicyCommandRepository {
    override suspend fun renew(numero: String): StandInAnswer<IssuedPolicy> =
        command(numero, PolicyVerbDto.renovar, null, null)

    override suspend fun modify(numero: String): StandInAnswer<IssuedPolicy> =
        command(numero, PolicyVerbDto.modificar, null, null)

    override suspend fun cancel(numero: String, motivo: String?): StandInAnswer<IssuedPolicy> =
        command(numero, PolicyVerbDto.cancelar, motivo, newIdempotencyKey())

    private suspend fun command(
        numero: String,
        verbo: PolicyVerbDto,
        motivo: String?,
        key: String?,
    ): StandInAnswer<IssuedPolicy> = gate.call {
        api.cycle(numero, key, PolicyCommandDto(numero, verbo, motivo)).toPolicy()
    }
}

class RemoteHomeBffRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : HomeBffRepository {
    override suspend fun load(): StandInAnswer<BffHome> = gate.call { api.home().toHome() }
}

class RemotePushRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : PushRepository {
    override suspend fun register(registration: PushRegistration): StandInAnswer<PushRegistration> =
        gate.call { api.registerPush(registration.toDto()).toRegistration() }

    override suspend fun notice(): StandInAnswer<PushNotice> =
        gate.call { api.pushNotice().toNotice() }
}

class RemoteAssistanceRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : AssistanceRepository {
    override suspend fun providers(): StandInAnswer<List<Provider>> =
        gate.call { api.providers().toProviders() }

    override suspend fun request(body: AssistanceRequest): StandInAnswer<AssistanceResult> =
        gate.call { api.assistance(body.toDto()).toResult() }
}
