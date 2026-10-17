package com.grupo8_uniandes.solventa.data.bff

import com.grupo8_uniandes.solventa.data.bff.mock.MockAssistanceRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockClaimRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockHomeBffRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockIssuanceRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockMobileSessionRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockMortgageRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockNoticeRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockOfferRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockPaymentRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockPolicyCommandRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockPushRepository
import com.grupo8_uniandes.solventa.data.bff.mock.MockSignupRepository

class MobileBff(
    val session: MockMobileSessionRepository = MockMobileSessionRepository(),
    val signup: MockSignupRepository = MockSignupRepository(),
    val offer: MockOfferRepository = MockOfferRepository(),
    val issuance: MockIssuanceRepository = MockIssuanceRepository(),
    val claim: MockClaimRepository = MockClaimRepository(),
    val payment: MockPaymentRepository = MockPaymentRepository(),
    val mortgage: MockMortgageRepository = MockMortgageRepository(),
    val notices: MockNoticeRepository = MockNoticeRepository(),
    val policyCommand: MockPolicyCommandRepository = MockPolicyCommandRepository(),
    val home: MockHomeBffRepository = MockHomeBffRepository(),
    val push: MockPushRepository = MockPushRepository(),
    val assistance: MockAssistanceRepository = MockAssistanceRepository(),
)
