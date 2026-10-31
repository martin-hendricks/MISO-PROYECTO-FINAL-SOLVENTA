package com.grupo8_uniandes.solventa.data.bff.remote

import android.content.Context
import com.grupo8_uniandes.solventa.data.bff.MobileBff
import com.grupo8_uniandes.solventa.data.session.TokenStore
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimHold
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.MemoryClaimHold
import com.grupo8_uniandes.solventa.domain.bff.home.HomeBffRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.InMemoryPolicyStore
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyMemory
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageRepository
import com.grupo8_uniandes.solventa.domain.bff.notice.NoticeRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.payment.PaymentRepository
import com.grupo8_uniandes.solventa.domain.bff.policycommand.PolicyCommandRepository
import com.grupo8_uniandes.solventa.domain.bff.push.PushRepository
import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository
import com.grupo8_uniandes.solventa.domain.bff.signup.SignupRepository

/**
 * One stand-in bag when the address is empty. One client and one token store when it is not.
 */
class BffRuntime private constructor(
    val session: MobileSessionRepository,
    val signup: SignupRepository,
    val offer: OfferRepository,
    val issuance: IssuanceRepository,
    val claim: ClaimRepository,
    val payment: PaymentRepository,
    val mortgage: MortgageRepository,
    val notices: NoticeRepository,
    val policyCommand: PolicyCommandRepository,
    val home: HomeBffRepository,
    val push: PushRepository,
    val assistance: AssistanceRepository,
    val memory: PolicyMemory,
    val claimHold: ClaimHold,
) {
    companion object {
        fun standIn(): BffRuntime {
            val bff = MobileBff()
            return BffRuntime(
                bff.session,
                bff.signup,
                bff.offer,
                bff.issuance,
                bff.claim,
                bff.payment,
                bff.mortgage,
                bff.notices,
                bff.policyCommand,
                bff.home,
                bff.push,
                bff.assistance,
                InMemoryPolicyStore(),
                MemoryClaimHold(),
            )
        }

        fun remote(context: Context, address: String): BffRuntime {
            val tokens = TokenStore(context)
            val cache = BffCache(context)
            val api = BffClients.open(address, tokens).api
            val gate = BffGate(api, cache)
            return BffRuntime(
                RemoteSessionRepository(api, tokens, gate),
                RemoteSignupRepository(api, gate),
                RemoteOfferRepository(api, gate),
                RemoteIssuanceRepository(api, gate, cache),
                RemoteClaimRepository(api, gate, cache),
                RemotePaymentRepository(api, gate),
                RemoteMortgageRepository(api, gate),
                RemoteNoticeRepository(api, gate),
                RemotePolicyCommandRepository(api, gate),
                RemoteHomeBffRepository(api, gate),
                RemotePushRepository(api, gate),
                RemoteAssistanceRepository(api, gate),
                BffPolicyMemory(cache),
                CachedClaimHold(cache),
            )
        }
    }
}
