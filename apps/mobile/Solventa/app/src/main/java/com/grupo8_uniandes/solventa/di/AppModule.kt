package com.grupo8_uniandes.solventa.di

import android.content.Context
import com.grupo8_uniandes.solventa.BuildConfig
import com.grupo8_uniandes.solventa.data.bff.remote.BffRuntime
import com.grupo8_uniandes.solventa.data.claim.ClaimReplay
import com.grupo8_uniandes.solventa.data.claim.DeviceRenewal
import com.grupo8_uniandes.solventa.data.claim.EncryptedNoticeStore
import com.grupo8_uniandes.solventa.data.claim.PlatformLocator
import com.grupo8_uniandes.solventa.data.consent.SharedPrefsConsentRepository
import com.grupo8_uniandes.solventa.data.home.StandInHomeRepository
import com.grupo8_uniandes.solventa.data.profile.AndroidDevicePermissionReader
import com.grupo8_uniandes.solventa.data.profile.SharedPrefsSessionRepository
import com.grupo8_uniandes.solventa.data.region.SharedPrefsRegionRepository
import com.grupo8_uniandes.solventa.data.registration.SharedPrefsRegistrationRepository
import com.grupo8_uniandes.solventa.domain.bff.assistance.AssistanceRepository
import com.grupo8_uniandes.solventa.claim.AvisoSiniestroViewModel
import com.grupo8_uniandes.solventa.claim.ParametricoViewModel
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimHold
import com.grupo8_uniandes.solventa.domain.bff.claim.DeviceLocator
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimRepository
import com.grupo8_uniandes.solventa.domain.bff.claim.LocalRenewal
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticeArchive
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.PoliciesInForce
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenParametricPayment
import com.grupo8_uniandes.solventa.domain.bff.home.HomeBffRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.AcceptOffer
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyMemory
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageRepository
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ProfilingConsentRepository
import com.grupo8_uniandes.solventa.domain.bff.notice.NoticeRepository
import com.grupo8_uniandes.solventa.domain.bff.notice.OpenValidityNotice
import com.grupo8_uniandes.solventa.domain.bff.offer.OfferRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.RequestFirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.ShowFirmOffer
import com.grupo8_uniandes.solventa.domain.bff.payment.PaymentRepository
import com.grupo8_uniandes.solventa.domain.bff.policy.RenewalPreferenceRepository
import com.grupo8_uniandes.solventa.domain.bff.policy.SaveRenewalPreference
import com.grupo8_uniandes.solventa.domain.bff.policycommand.PolicyCommandRepository
import com.grupo8_uniandes.solventa.issuance.ConfirmacionTarjetaViewModel
import com.grupo8_uniandes.solventa.policy.RenewalChoiceViewModel
import com.google.firebase.FirebaseApp
import com.grupo8_uniandes.solventa.domain.bff.push.PushRepository
import com.grupo8_uniandes.solventa.domain.push.PushOptIn
import com.grupo8_uniandes.solventa.domain.push.PushToken
import com.grupo8_uniandes.solventa.push.FirebasePushToken
import com.grupo8_uniandes.solventa.push.NoPushToken
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository
import com.grupo8_uniandes.solventa.domain.bff.signup.SignupRepository
import com.grupo8_uniandes.solventa.domain.consent.ConsentRepository
import com.grupo8_uniandes.solventa.domain.home.HomeRepository
import com.grupo8_uniandes.solventa.domain.home.LoadInicio
import com.grupo8_uniandes.solventa.domain.login.SignIn
import com.grupo8_uniandes.solventa.domain.profile.DevicePermissionReader
import com.grupo8_uniandes.solventa.domain.profile.AccountNameRepository
import com.grupo8_uniandes.solventa.domain.profile.LoadProfile
import com.grupo8_uniandes.solventa.domain.profile.PublishStoredName
import com.grupo8_uniandes.solventa.domain.profile.SessionRepository
import com.grupo8_uniandes.solventa.domain.profile.SignOut
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.RegionRepository
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import com.grupo8_uniandes.solventa.claim.ClaimsPhase
import com.grupo8_uniandes.solventa.claim.SiniestroDetalleViewModel
import com.grupo8_uniandes.solventa.claim.SiniestrosViewModel
import com.grupo8_uniandes.solventa.home.HomeViewModel
import com.grupo8_uniandes.solventa.mortgage.MortgageOfferViewModel
import com.grupo8_uniandes.solventa.offer.OfferViewModel
import com.grupo8_uniandes.solventa.policy.AvisoVigenciaViewModel
import com.grupo8_uniandes.solventa.policy.PolizaDetalleViewModel
import com.grupo8_uniandes.solventa.policy.IssuanceViewModel
import com.grupo8_uniandes.solventa.policy.PolizasViewModel
import com.grupo8_uniandes.solventa.quote.QuoteViewModel
import com.grupo8_uniandes.solventa.ui.login.BiometricGate
import com.grupo8_uniandes.solventa.ui.login.DisableBiometric
import com.grupo8_uniandes.solventa.ui.login.EnableBiometric
import com.grupo8_uniandes.solventa.ui.login.LoginViewModel
import com.grupo8_uniandes.solventa.ui.login.RememberBiometricLogin
import com.grupo8_uniandes.solventa.ui.login.RemoteSessionOpener
import com.grupo8_uniandes.solventa.ui.login.StoredBiometricLogin
import com.grupo8_uniandes.solventa.ui.shell.ProfileViewModel
import org.koin.android.ext.koin.androidContext
import org.koin.core.context.GlobalContext
import org.koin.core.parameter.parametersOf
import org.koin.core.context.startKoin
import org.koin.core.module.dsl.viewModel
import org.koin.dsl.module

fun appModule(baseUrl: String = BuildConfig.BFF_BASE_URL) = module {
    val address = baseUrl.trim().trimEnd('/').removeSuffix("/movil")
    single {
        if (address.isBlank()) BffRuntime.standIn() else BffRuntime.remote(androidContext(), address)
    }
    single<MobileSessionRepository> { get<BffRuntime>().session }
    single<SignupRepository> { get<BffRuntime>().signup }
    single<OfferRepository> { get<BffRuntime>().offer }
    single<IssuanceRepository> { get<BffRuntime>().issuance }
    single<RenewalPreferenceRepository> { get<BffRuntime>().renewal }
    single { SaveRenewalPreference(get()) }
    single<PolicyMemory> { get<BffRuntime>().memory }
    single { AcceptOffer(get()) }
    single<ClaimRepository> { get<BffRuntime>().claim }
    single<ClaimHold> { get<BffRuntime>().claimHold }
    single { EncryptedNoticeStore(androidContext(), "solventa-clave-1") }
    single<NoticeArchive> { get<EncryptedNoticeStore>() }
    single { ClaimReplay(get(), get()) }
    single<LocalRenewal> { DeviceRenewal(androidContext()) }
    single { OpenClaimNotice(get(), get(), get()) }
    single { OpenParametricPayment(get()) }
    single<PaymentRepository> { get<BffRuntime>().payment }
    single<MortgageRepository> { get<BffRuntime>().mortgage }
    single<ProfilingConsentRepository> { get<BffRuntime>().profilingConsent }
    single<NoticeRepository> { get<BffRuntime>().notices }
    single { OpenValidityNotice(get()) }
    single<PolicyCommandRepository> { get<BffRuntime>().policyCommand }
    single<HomeBffRepository> { get<BffRuntime>().home }
    single<PushRepository> { get<BffRuntime>().push }
    single<PushToken> {
        val context = androidContext()
        if (FirebaseApp.getApps(context).isEmpty()) NoPushToken() else FirebasePushToken(context)
    }
    single { PushOptIn(get(), get()) }
    single<AssistanceRepository> { get<BffRuntime>().assistance }
    single<HomeRepository> { StandInHomeRepository(get()) }
    single { LoadInicio(get()) }
    single { RequestFirmOffer(get()) }
    single { ShowFirmOffer(get()) }
    single { SignIn(get()) }
    single {
        SignOut(
            get<SessionRepository>(),
            get<MobileSessionRepository>(),
            get<PushRepository>(),
            get<PushToken>(),
            get<PushOptIn>(),
        )
    }
    factory { (originationActive: Boolean) ->
        LoadProfile(get(), get(), get(), get(), get(), originationActive)
    }
    single<RegistrationRepository> { SharedPrefsRegistrationRepository(androidContext()) }
    single<AccountNameRepository> { get<BffRuntime>().accountName }
    single { PublishStoredName(get(), get()) }
    single<RegionRepository> { SharedPrefsRegionRepository(androidContext()) }
    single<ConsentRepository> { SharedPrefsConsentRepository(androidContext()) }
    single<SessionRepository> { SharedPrefsSessionRepository(androidContext()) }
    single<DevicePermissionReader> { AndroidDevicePermissionReader(androidContext()) }
    viewModel { HomeViewModel(get()) }
    viewModel { MortgageOfferViewModel(get()) }
    viewModel {
        val registration = get<RegistrationRepository>()
        val session = get<MobileSessionRepository>()
        LoginViewModel(
            signIn = get(),
            biometricEnabled = BiometricGate(registration::biometricUnlockEnabled),
            enableBiometric = EnableBiometric(registration::enableBiometricUnlock),
            disableBiometric = DisableBiometric { registration.setBiometricUnlock(false) },
            openRemoteSession = RemoteSessionOpener { email, password ->
                session.signIn(email, password) is StandInAnswer.Ready
            },
            storedBiometricLogin = StoredBiometricLogin(registration::biometricLogin),
            rememberBiometricLogin = RememberBiometricLogin(registration::rememberBiometricLogin),
        )
    }
    factory { (originationActive: Boolean) ->
        ProfileViewModel(get { parametersOf(originationActive) }, get())
    }
    viewModel { (contextId: String) -> QuoteViewModel(get(), contextId) }
    viewModel { (cotizacionId: String, region: Region) ->
        OfferViewModel(get(), cotizacionId, region)
    }
    viewModel { PolizasViewModel(get(), get()) }
    viewModel { (numero: String) -> PolizaDetalleViewModel(get(), numero, get(), get()) }
    viewModel { (offerId: String) -> IssuanceViewModel(get(), offerId) }
    viewModel { (offerId: String, prima: Long, moneda: String) ->
        ConfirmacionTarjetaViewModel(prima, moneda, offerId, get())
    }
    viewModel { (numero: String) -> RenewalChoiceViewModel(numero, get()) }
    viewModel { SiniestrosViewModel(get()) }
    viewModel { (claimId: String) -> SiniestroDetalleViewModel(get(), claimId) }
    single { PoliciesInForce(get()) }
    single<DeviceLocator> { PlatformLocator(androidContext()) }
    viewModel { AvisoSiniestroViewModel(get(), get(), get()) }
    viewModel { ParametricoViewModel(get(), get(), get()) }
    viewModel { AvisoVigenciaViewModel(get()) }
}

fun startSolventaKoin(context: Context) {
    if (GlobalContext.getOrNull() != null) return
    startKoin {
        androidContext(context.applicationContext)
        modules(appModule())
    }
}
