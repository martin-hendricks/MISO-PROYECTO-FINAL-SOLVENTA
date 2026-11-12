package com.grupo8_uniandes.solventa.data.bff.remote

import com.grupo8_uniandes.solventa.data.bff.dto.AccountNameDto
import com.grupo8_uniandes.solventa.data.bff.dto.IdDto
import com.grupo8_uniandes.solventa.data.bff.dto.RenewalRequestDto
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
import com.grupo8_uniandes.solventa.data.bff.mapping.toAccepted
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
import com.grupo8_uniandes.solventa.data.bff.mapping.toParts
import com.grupo8_uniandes.solventa.data.bff.mapping.toResult
import com.grupo8_uniandes.solventa.data.bff.mapping.toRevocation
import com.grupo8_uniandes.solventa.data.bff.mapping.toSummaries
import com.grupo8_uniandes.solventa.data.bff.mapping.toTokens
import com.grupo8_uniandes.solventa.data.session.TokenStore
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.profile.AccountName
import com.grupo8_uniandes.solventa.domain.profile.AccountNameRepository
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRepository
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceResult
import com.grupo8_uniandes.solventa.domain.bff.assistance.Provider
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimDetail
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimReceipt
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimSummary
import com.grupo8_uniandes.solventa.domain.bff.claim.bytesMissing
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
import com.grupo8_uniandes.solventa.domain.bff.offer.AcceptedQuote
import com.grupo8_uniandes.solventa.domain.bff.offer.FirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.LineRisk
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteExplained
import com.grupo8_uniandes.solventa.domain.bff.policy.RenewalPreferenceRepository
import com.grupo8_uniandes.solventa.domain.bff.policy.RenewalSave
import com.grupo8_uniandes.solventa.domain.bff.payment.AutomaticPayment
import com.grupo8_uniandes.solventa.domain.bff.payment.PaymentRepository
import com.grupo8_uniandes.solventa.domain.bff.policycommand.PolicyCommandRepository
import com.grupo8_uniandes.solventa.data.bff.dto.PushTokenRetiroDto
import com.grupo8_uniandes.solventa.domain.bff.push.PushRegistration
import com.grupo8_uniandes.solventa.domain.bff.push.PushRepository
import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import com.grupo8_uniandes.solventa.domain.bff.signup.ConsentRevocation
import com.grupo8_uniandes.solventa.domain.bff.signup.SignupRecord
import com.grupo8_uniandes.solventa.domain.bff.signup.SignupRepository
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.decodeFromJsonElement
import retrofit2.HttpException
import java.io.IOException

class BffGate(private val api: MobileBffApi, private val cache: BffCache) {
    fun remember(accessToken: String) {
        cache.retainOwner(customerUid(accessToken))
    }

    fun forget() {
        cache.clear()
    }
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
            api.notify(pending.key, pending.notice.toParts())
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
        tokens.clear()
        val answer = try {
            StandInAnswer.Ready(api.signIn(SessionInDto(correo, contrasena)).toTokens())
        } catch (_: IOException) {
            StandInAnswer.Failed
        } catch (_: HttpException) {
            StandInAnswer.Failed
        } catch (_: SerializationException) {
            StandInAnswer.Failed
        }
        if (answer is StandInAnswer.Ready) {
            tokens.save(answer.value)
            gate.remember(answer.value.accessToken)
        }
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
        gate.forget()
        return answer
    }
}

internal fun customerUid(accessToken: String): String? {
    val parts = accessToken.split('.')
    if (parts.size < 2) return null
    val payload = android.util.Base64.decode(
        parts[1],
        android.util.Base64.URL_SAFE or android.util.Base64.NO_WRAP or android.util.Base64.NO_PADDING,
    )
    return org.json.JSONObject(String(payload)).optString("uid").ifBlank { null }
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
    override suspend fun quote(ramo: String, risk: LineRisk): StandInAnswer<FirmOffer> {
        gate.flush()
        return try {
            StandInAnswer.Ready(
                api.quote(newIdempotencyKey(), QuoteRequestDto(ramo, risk.toRequestElement())).toOffer(),
            )
        } catch (error: HttpException) {
            val detail = problemDetail(error.response()?.errorBody()?.string().orEmpty())
            if (error.code() == 422 && !detail.isNullOrBlank()) throw QuoteExplained(detail)
            StandInAnswer.Failed
        } catch (_: IOException) {
            StandInAnswer.Failed
        } catch (_: SerializationException) {
            StandInAnswer.Failed
        }
    }

    override suspend fun requote(cotizacionId: String): StandInAnswer<FirmOffer> =
        gate.call { api.requote(cotizacionId).toOffer() }

    override suspend fun accept(cotizacionId: String): StandInAnswer<AcceptedQuote> {
        val answer = gate.call { api.acceptQuote(newIdempotencyKey(), cotizacionId).toAccepted() }
        return when (answer) {
            is StandInAnswer.Ready -> if (answer.value.estado == "aceptada") answer else StandInAnswer.Failed
            is StandInAnswer.Rejected -> StandInAnswer.Failed
            else -> answer
        }
    }
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
            StandInAnswer.Failed
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
    override suspend fun notify(
        notice: ClaimNotice,
        idempotencyKey: String?,
    ): StandInAnswer<ClaimReceipt> {
        if (idempotencyKey == null && !gate.flush()) return StandInAnswer.Failed
        val key = idempotencyKey ?: newIdempotencyKey()
        if (notice.bytesMissing()) return StandInAnswer.Failed
        return try {
            val receipt = api.notify(key, notice.toParts()).toReceipt()
            if (cache.readClaim()?.key == key) cache.clearClaim()
            StandInAnswer.Ready(receipt)
        } catch (_: IOException) {
            cache.writeClaim(PendingClaim(key, notice))
            StandInAnswer.Failed
        } catch (error: HttpException) {
            if (error.code() == 422 || error.code() == 409) {
                StandInAnswer.Rejected(error.response()?.errorBody()?.string().orEmpty())
            } else {
                StandInAnswer.Failed
            }
        } catch (_: SerializationException) {
            StandInAnswer.Failed
        }
    }

    override suspend fun list(): StandInAnswer<List<ClaimSummary>> =
        gate.call { api.claims().toSummaries() }

    override suspend fun detail(id: String): StandInAnswer<ClaimDetail> {
        if (!gate.flush()) return StandInAnswer.Failed
        return try {
            StandInAnswer.Ready(api.claim(id).toDetail())
        } catch (_: IOException) {
            StandInAnswer.Failed
        } catch (error: HttpException) {
            if (error.code() == 404) StandInAnswer.Rejected("not_found") else StandInAnswer.Failed
        } catch (_: SerializationException) {
            StandInAnswer.Failed
        }
    }
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
    private val tokens: TokenStore,
) : HomeBffRepository {
    override suspend fun load(): StandInAnswer<BffHome> {
        if (tokens.read() == null) return StandInAnswer.Ready(emptyHome())
        return gate.call { api.home().toHome() }
    }
}

private fun emptyHome() = BffHome(
    ofertaVigente = null,
    poliza = null,
    siniestroEnCurso = null,
    hipotecario = null,
)

class RemotePushRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : PushRepository {
    override suspend fun register(registration: PushRegistration): StandInAnswer<PushRegistration> =
        gate.call {
            val response = api.registerPush(registration.toDto())
            if (!response.isSuccessful) throw HttpException(response)
            registration
        }

    override suspend fun unregister(token: String): StandInAnswer<Unit> =
        gate.call {
            val response = api.unregisterPush(PushTokenRetiroDto(token))
            if (!response.isSuccessful) throw HttpException(response)
        }
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

class RemoteAccountNameRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : AccountNameRepository {
    override suspend fun read(): StandInAnswer<AccountName> =
        gate.call { api.accountName().toAccountName() }

    override suspend fun save(nombre: String, apellidos: String): StandInAnswer<AccountName> =
        gate.call { api.saveAccountName(AccountNameDto(nombre, apellidos)).toAccountName() }
}

private fun AccountNameDto.toAccountName() = AccountName(nombre, apellidos)

class RemoteRenewalPreferenceRepository(
    private val api: MobileBffApi,
    private val gate: BffGate,
) : RenewalPreferenceRepository {
    override suspend fun save(numero: String, enabled: Boolean): RenewalSave {
        gate.flush()
        return try {
            val saved = api.preferences(numero, RenewalRequestDto(enabled))
            RenewalSave.Saved(saved.renovacionAutomatica)
        } catch (error: HttpException) {
            val detail = problemDetail(error.response()?.errorBody()?.string().orEmpty())
            if (error.code() == 404 || detail == "No existe") RenewalSave.Missing else RenewalSave.Failed
        } catch (_: IOException) {
            RenewalSave.Failed
        } catch (_: SerializationException) {
            RenewalSave.Failed
        }
    }
}

internal fun problemDetail(raw: String): String? = runCatching {
    val text = bffJson.parseToJsonElement(raw).jsonObject["detail"]?.jsonPrimitive?.content?.trim().orEmpty()
    text.ifBlank { null }
}.getOrNull()
