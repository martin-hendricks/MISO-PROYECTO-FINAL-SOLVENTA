package com.grupo8_uniandes.solventa.ui.shell

import android.app.Activity
import androidx.activity.OnBackPressedCallback
import androidx.activity.compose.LocalOnBackPressedDispatcherOwner
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.data.bff.remote.SessionUnauthorized
import com.grupo8_uniandes.solventa.di.startSolventaKoin
import org.koin.androidx.compose.koinViewModel
import org.koin.core.context.GlobalContext
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.data.consent.SharedPrefsConsentRepository
import com.grupo8_uniandes.solventa.data.profile.SharedPrefsSessionRepository
import com.grupo8_uniandes.solventa.data.region.SharedPrefsRegionRepository
import com.grupo8_uniandes.solventa.data.registration.SharedPrefsRegistrationRepository
import com.grupo8_uniandes.solventa.data.session.TokenStore
import com.grupo8_uniandes.solventa.domain.consent.ChangeDataTreatment
import com.grupo8_uniandes.solventa.domain.consent.ConsentState
import com.grupo8_uniandes.solventa.domain.region.RegionRepository
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository
import com.grupo8_uniandes.solventa.domain.registration.RegisterAccount
import com.grupo8_uniandes.solventa.domain.startup.PostSplashStep
import com.grupo8_uniandes.solventa.domain.startup.RestoreRemoteSession
import com.grupo8_uniandes.solventa.domain.startup.RestoredSession
import com.grupo8_uniandes.solventa.domain.startup.StartupSession
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.home.HomeViewModel
import com.grupo8_uniandes.solventa.navigation.CotizacionRoute
import com.grupo8_uniandes.solventa.navigation.Destination
import com.grupo8_uniandes.solventa.navigation.VerOfertaRoute
import com.grupo8_uniandes.solventa.navigation.CustomerNavHost
import com.grupo8_uniandes.solventa.navigation.EmisionEnCursoRoute
import com.grupo8_uniandes.solventa.navigation.InicioRoute
import com.grupo8_uniandes.solventa.navigation.PerfilRoute
import com.grupo8_uniandes.solventa.navigation.PolizaDetalleRoute
import com.grupo8_uniandes.solventa.navigation.PolizaEmitidaRoute
import com.grupo8_uniandes.solventa.navigation.SuscripcionRechazadaRoute
import com.grupo8_uniandes.solventa.navigation.PolizasRoute
import com.grupo8_uniandes.solventa.navigation.ShellMode
import com.grupo8_uniandes.solventa.navigation.SiniestroDetalleRoute
import com.grupo8_uniandes.solventa.navigation.SiniestrosRoute
import com.grupo8_uniandes.solventa.navigation.openDestination
import com.grupo8_uniandes.solventa.navigation.selectedDestination
import com.grupo8_uniandes.solventa.navigation.shellMode
import com.grupo8_uniandes.solventa.navigation.toSolventaRoute
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.components.SolventaFloatingAction
import com.grupo8_uniandes.solventa.ui.components.SolventaTopBar
import com.grupo8_uniandes.solventa.ui.consent.ConsentEffect
import com.grupo8_uniandes.solventa.ui.consent.ConsentScreen
import com.grupo8_uniandes.solventa.ui.consent.ConsentSurface
import com.grupo8_uniandes.solventa.ui.consent.ConsentViewModel
import com.grupo8_uniandes.solventa.ui.region.IdiomaRegionScreen
import com.grupo8_uniandes.solventa.ui.region.IdiomaRegionViewModel
import com.grupo8_uniandes.solventa.ui.region.RegionEffect
import com.grupo8_uniandes.solventa.ui.region.RegionSurface
import com.grupo8_uniandes.solventa.ui.region.findActivity
import com.grupo8_uniandes.solventa.ui.login.DeviceBiometricPrompt
import com.grupo8_uniandes.solventa.ui.login.LoginEffect
import com.grupo8_uniandes.solventa.ui.login.LoginScreen
import com.grupo8_uniandes.solventa.ui.login.LoginViewModel
import com.grupo8_uniandes.solventa.ui.registration.LivenessEffect
import com.grupo8_uniandes.solventa.ui.registration.LivenessScreen
import com.grupo8_uniandes.solventa.ui.registration.LivenessViewModel
import com.grupo8_uniandes.solventa.ui.registration.OnboardingEffect
import com.grupo8_uniandes.solventa.ui.registration.OnboardingScreen
import com.grupo8_uniandes.solventa.ui.registration.OnboardingViewModel

@Composable
fun CustomerShell(
    startupSession: StartupSession = StartupSession.FirstUse,
    splashHoldMillis: Long = SplashHoldMillis,
    enterSignedInShell: Boolean = false,
    openOnboarding: Boolean = false,
    onboardingShowsStep: Boolean = true,
    openLiveness: Boolean = false,
    openConsent: Boolean = false,
    resumeProfile: Boolean = false,
    signedOut: Boolean = false,
    modifier: Modifier = Modifier,
) {
    if (signedOut) {
        LoginHost(modifier = modifier, onLeaveToAccount = null, showBack = false)
        return
    }
    if (enterSignedInShell) {
        SignedInShell(modifier = modifier, startOnProfile = resumeProfile)
        return
    }
    if (openOnboarding) {
        OnboardingHost(modifier = modifier, showStep = onboardingShowsStep)
        return
    }
    if (openLiveness) {
        LivenessHost(modifier = modifier)
        return
    }
    if (openConsent) {
        ConsentHost(modifier = modifier)
        return
    }

    val splashViewModel = remember(startupSession, splashHoldMillis) {
        SplashViewModel(session = startupSession, holdMillis = splashHoldMillis)
    }
    val splashState by splashViewModel.state.collectAsState()
    LaunchedEffect(splashViewModel) {
        splashViewModel.start()
    }
    if (splashState is SplashUiState.Showing) {
        SplashScreen(modifier = modifier)
        return
    }

    val step = (splashState as SplashUiState.Finished).step
    val context = LocalContext.current
    val repository = remember(context) {
        SharedPrefsRegionRepository(context.applicationContext)
    }
    val completed = repository.read().firstLaunchCompleted
    val registrationDone = remember(context) {
        SharedPrefsRegistrationRepository(context.applicationContext).read() != null
    }
    val livenessDone = remember(context) {
        SharedPrefsRegistrationRepository(context.applicationContext).livenessCompleted()
    }
    val consentOpen = remember(context) {
        SharedPrefsConsentRepository(context.applicationContext).read().state != ConsentState.NotGranted
    }
    when {
        step == PostSplashStep.LanguageAndRegion && !completed -> {
            FirstLaunchLanguage(repository = repository, modifier = modifier)
        }
        step == PostSplashStep.LanguageAndRegion && completed && !registrationDone -> {
            OnboardingHost(modifier = modifier)
        }
        step == PostSplashStep.LanguageAndRegion && completed && registrationDone && !livenessDone -> {
            LivenessHost(modifier = modifier)
        }
        step == PostSplashStep.LanguageAndRegion && completed && registrationDone && livenessDone && !consentOpen && !resumeProfile -> {
            ConsentHost(modifier = modifier)
        }
        step == PostSplashStep.Login ||
            (registrationDone && !SharedPrefsSessionRepository(context.applicationContext).isOpen()) -> {
            LoginHost(modifier = modifier, onLeaveToAccount = null)
        }
        else -> {
            RestoredSessionHost(modifier = modifier, startOnProfile = resumeProfile)
        }
    }
}

@Composable
private fun RestoredSessionHost(
    modifier: Modifier = Modifier,
    startOnProfile: Boolean,
) {
    val context = LocalContext.current
    startSolventaKoin(context)
    val restore = remember(context) {
        val tokens = TokenStore(context.applicationContext)
        val local = SharedPrefsSessionRepository(context.applicationContext)
        val remote = GlobalContext.get().get<MobileSessionRepository>()
        RestoreRemoteSession(
            storedRefreshToken = { tokens.read()?.refreshToken },
            clearStoredSession = { tokens.clear() },
            remote = remote,
            local = local,
        )
    }
    var restored by remember { mutableStateOf<RestoredSession?>(null) }
    LaunchedEffect(restore) {
        restored = restore()
    }
    when (restored) {
        null -> SplashScreen(modifier = modifier)
        RestoredSession.Login -> LoginHost(
            modifier = modifier,
            onLeaveToAccount = null,
            showBack = false,
        )
        RestoredSession.Local, RestoredSession.Home -> SignedInShell(
            modifier = modifier,
            startOnProfile = startOnProfile,
        )
    }
}

@Composable
private fun FirstLaunchLanguage(
    repository: RegionRepository,
    modifier: Modifier = Modifier,
) {
    val viewModel = remember(repository) {
        IdiomaRegionViewModel(repository = repository, surface = RegionSurface.FirstLaunch)
    }
    val state by viewModel.state.collectAsState()
    val activity = LocalContext.current.findActivity()
    LaunchedEffect(state.effect) {
        if (state.effect == RegionEffect.ContinueToOnboarding) {
            activity?.openOnboarding(showStep = true)
        }
    }
    IdiomaRegionScreen(
        draft = state.choice.draftRegion,
        onSelect = viewModel::select,
        onContinue = viewModel::confirm,
        modifier = modifier,
    )
}

@Composable
private fun OnboardingHost(
    modifier: Modifier = Modifier,
    showStep: Boolean = true,
) {
    val context = LocalContext.current
    val region = remember(context) {
        SharedPrefsRegionRepository(context.applicationContext).read().appliedRegion
    }
    startSolventaKoin(context)
    val session = remember {
        GlobalContext.get().get<MobileSessionRepository>()
    }
    val viewModel = remember(context, region, session) {
        OnboardingViewModel(
            RegisterAccount(SharedPrefsRegistrationRepository(context.applicationContext)),
            region,
            openRemoteSession = { email, password ->
                session.signIn(email, password) is StandInAnswer.Ready
            },
        )
    }
    val state by viewModel.state.collectAsState()
    val activity = LocalContext.current.findActivity()
    LaunchedEffect(state.effect) {
        if (state.effect == OnboardingEffect.ContinueToLiveness) {
            activity?.openLiveness()
        }
    }
    if (state.effect == OnboardingEffect.OpenLogin) {
        LoginHost(modifier = modifier, onLeaveToAccount = viewModel::dismissLogin)
    } else {
        OnboardingScreen(
            state = state,
            onGivenName = viewModel::onGivenName,
            onSurnames = viewModel::onSurnames,
            onEmail = viewModel::onEmail,
            onDocumentType = viewModel::onDocumentType,
            onDocumentNumber = viewModel::onDocumentNumber,
            onPassword = viewModel::onPassword,
            onPasswordConfirm = viewModel::onPasswordConfirm,
            onPhotoAttached = viewModel::attachPhoto,
            onPhotoDeclined = viewModel::photoDeclined,
            onContinue = viewModel::continuar,
            onExistingAccount = viewModel::yaTengoCuenta,
            showStep = showStep,
            modifier = modifier,
        )
    }
}

@Composable
internal fun SignedInShell(
    modifier: Modifier = Modifier,
    startOnProfile: Boolean = false,
    homeState: HomeUiState? = null,
) {
    val signedIn = true
    val navController = rememberNavController()
    val activity = LocalContext.current.findActivity()
    startSolventaKoin(LocalContext.current)
    DisposableEffect(activity) {
        val notify = {
            activity?.runOnUiThread { activity.signOutToLogin() }
            Unit
        }
        SessionUnauthorized.onUnauthorized = notify
        onDispose {
            if (SessionUnauthorized.onUnauthorized === notify) {
                SessionUnauthorized.onUnauthorized = null
            }
        }
    }
    val homeViewModel: HomeViewModel = koinViewModel()
    val collectedHome by homeViewModel.state.collectAsState()
    val homeStateResolved = homeState ?: collectedHome
    val entry by navController.currentBackStackEntryAsState()
    val start = if (startOnProfile) PerfilRoute else InicioRoute
    val route = entry?.toSolventaRoute() ?: start
    val mode = shellMode(route, signedIn)
    val selected = selectedDestination(route)
    val showBottomBar = mode == ShellMode.Root || mode == ShellMode.Nested

    val dispatcher = LocalOnBackPressedDispatcherOwner.current?.onBackPressedDispatcher
    val consumeBack = remember {
        object : OnBackPressedCallback(false) {
            override fun handleOnBackPressed() = Unit
        }
    }
    DisposableEffect(dispatcher) {
        dispatcher?.addCallback(consumeBack)
        onDispose { consumeBack.remove() }
    }
    SideEffect {
        consumeBack.remove()
        consumeBack.isEnabled = mode == ShellMode.Root || mode == ShellMode.Issuance
        dispatcher?.addCallback(consumeBack)
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = MaterialTheme.colorScheme.surface,
        topBar = {
            if (signedIn && mode != ShellMode.PreLogin && route != PolizaEmitidaRoute) {
                SolventaTopBar(
                    title = routeTitle(route),
                    showBack = mode == ShellMode.Nested,
                    onBack = { navController.popBackStack() },
                )
            }
        },
        bottomBar = {
            if (showBottomBar && selected != null) {
                SolventaBottomBar(
                    selected = selected,
                    onSelect = navController::openDestination,
                )
            }
        },
        floatingActionButton = {
            if (route == InicioRoute) {
                SolventaFloatingAction(
                    label = stringResource(R.string.action_report_claim),
                    icon = painterResource(R.drawable.add),
                    onClick = { navController.openDestination(Destination.Siniestros) },
                    containerColor = MaterialTheme.colorScheme.error,
                    contentColor = MaterialTheme.colorScheme.onError,
                )
            }
        },
    ) { padding ->
        val activity = LocalContext.current.findActivity()
        CustomerNavHost(
            navController = navController,
            homeState = homeStateResolved,
            contentPadding = padding,
            startDestination = start,
            onSignedOut = { activity?.signOutToLogin() },
            onInicioVisible = homeViewModel::refresh,
        )
    }
}

@Composable
private fun routeTitle(route: Any): String = when (route) {
    is CotizacionRoute -> stringResource(R.string.quote_step_title)
    is VerOfertaRoute -> stringResource(R.string.offer_title)
    is PolizaDetalleRoute -> stringResource(R.string.policy_detail_title)
    is SiniestroDetalleRoute -> stringResource(R.string.destination_siniestros)
    is EmisionEnCursoRoute -> stringResource(R.string.issuing_title)
    PolizaEmitidaRoute -> stringResource(R.string.issued_title)
    SuscripcionRechazadaRoute -> stringResource(R.string.rejection_title)
    PolizasRoute -> stringResource(R.string.destination_polizas)
    SiniestrosRoute -> stringResource(R.string.destination_siniestros)
    PerfilRoute -> stringResource(R.string.destination_perfil)
    else -> stringResource(R.string.destination_inicio)
}

@Composable
private fun LoginHost(
    modifier: Modifier = Modifier,
    onLeaveToAccount: (() -> Unit)?,
    showBack: Boolean = true,
) {
    val context = LocalContext.current
    startSolventaKoin(context)
    val viewModel: LoginViewModel = koinViewModel()
    val state by viewModel.state.collectAsState()
    val activity = LocalContext.current.findActivity()
    val registration = remember(context) {
        SharedPrefsRegistrationRepository(context.applicationContext)
    }
    val biometricPrompt = remember(activity) {
        val host = activity ?: return@remember null
        DeviceBiometricPrompt(
            activity = host,
            title = host.getString(R.string.login_biometric_title),
            negativeButtonText = host.getString(R.string.action_secondary),
        )
    }
    val unlockEnabled = registration.biometricPromptOffered()
    val deviceCanAuthenticate = biometricPrompt?.available() == true
    val offerBiometric = unlockEnabled && deviceCanAuthenticate && !state.biometricFallback
    LaunchedEffect(state.effect) {
        if (state.effect == LoginEffect.OpenHome || state.effect == LoginEffect.ConfirmBiometric) {
            activity?.openHomeAfterOnboarding()
            viewModel.consumeEffect()
        }
    }
    LoginScreen(
        email = state.email,
        password = state.password,
        failure = state.failure,
        onEmail = viewModel::onEmail,
        onPassword = viewModel::onPassword,
        onIngresar = viewModel::ingresar,
        onBiometric = { biometricPrompt?.authenticate(viewModel::onDeviceUnlock) },
        biometricEnabled = true,
        biometricFallback = !offerBiometric,
        confirmBiometric = false,
        onAcceptBiometric = viewModel::acceptBiometric,
        onDeclineBiometric = viewModel::declineBiometric,
        onBack = { onLeaveToAccount?.invoke() },
        showBack = showBack,
        onCreateAccount = {
            if (onLeaveToAccount != null) {
                onLeaveToAccount()
            } else {
                activity?.openOnboarding()
            }
        },
        modifier = modifier,
    )
}

internal fun Activity.openLiveness() {
    intent.putExtra(MainActivity.EXTRA_OPEN_LIVENESS, true)
    intent.removeExtra(MainActivity.EXTRA_OPEN_ONBOARDING)
    recreate()
}

@Composable
private fun LivenessHost(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val region = remember(context) {
        SharedPrefsRegionRepository(context.applicationContext).read().appliedRegion
    }
    val repository = remember(context) {
        SharedPrefsRegistrationRepository(context.applicationContext)
    }
    val viewModel = remember(repository, region) {
        LivenessViewModel(repository, region)
    }
    val state by viewModel.state.collectAsState()
    val activity = LocalContext.current.findActivity()
    LaunchedEffect(state.effect) {
        if (state.effect == LivenessEffect.OpenConsent) {
            activity?.openConsent()
        }
    }
    if (state.effect == LivenessEffect.OpenLogin) {
        LoginHost(modifier = modifier, onLeaveToAccount = viewModel::dismissLogin)
    } else {
        LivenessScreen(
            state = state,
            onGivenName = viewModel::onGivenName,
            onSurnames = viewModel::onSurnames,
            onEmail = viewModel::onEmail,
            onDocumentType = viewModel::onDocumentType,
            onDocumentNumber = viewModel::onDocumentNumber,
            onPassword = viewModel::onPassword,
            onContinue = viewModel::continuar,
            onExistingAccount = viewModel::yaTengoCuenta,
            modifier = modifier,
        )
    }
}

internal fun Activity.openOnboarding(showStep: Boolean = false) {
    intent.putExtra(MainActivity.EXTRA_OPEN_ONBOARDING, true)
    intent.putExtra(MainActivity.EXTRA_ONBOARDING_STEP, showStep)
    intent.removeExtra(MainActivity.EXTRA_OPEN_LIVENESS)
    intent.removeExtra(MainActivity.EXTRA_OPEN_CONSENT)
    intent.removeExtra(MainActivity.EXTRA_SIGNED_OUT)
    recreate()
}

@Composable
private fun ConsentHost(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val repository = remember(context) {
        SharedPrefsConsentRepository(context.applicationContext)
    }
    val viewModel = remember(repository) {
        ConsentViewModel(
            change = ChangeDataTreatment(repository) { System.currentTimeMillis() },
            initial = repository.read(),
            surface = ConsentSurface.Alta,
        )
    }
    val state by viewModel.state.collectAsState()
    val activity = LocalContext.current.findActivity()
    LaunchedEffect(state.effect) {
        if (state.effect == ConsentEffect.OpenHome) {
            activity?.openHomeAfterOnboarding()
        }
    }
    ConsentScreen(
        switchOn = state.switchOn,
        confirmEnabled = state.confirmEnabled,
        onSwitch = viewModel::onSwitch,
        onConfirm = viewModel::confirm,
        onBack = {
            viewModel.back()
            activity?.openOnboarding(showStep = true)
        },
        modifier = modifier,
    )
}

internal fun Activity.openConsent() {
    intent.putExtra(MainActivity.EXTRA_OPEN_CONSENT, true)
    recreate()
}

internal fun Activity.openHomeAfterOnboarding() {
    SharedPrefsSessionRepository(this).open()
    intent.putExtra(MainActivity.EXTRA_OPEN_HOME, true)
    intent.removeExtra(MainActivity.EXTRA_SIGNED_OUT)
    recreate()
}

internal fun Activity.resumeProfileAfterLocaleChange() {
    intent.putExtra(MainActivity.EXTRA_RESUME_PROFILE, true)
    recreate()
}

internal fun Activity.signOutToLogin() {
    SharedPrefsSessionRepository(this).close()
    intent.putExtra(MainActivity.EXTRA_SIGNED_OUT, true)
    intent.removeExtra(MainActivity.EXTRA_ENTER_SIGNED_IN_SHELL)
    intent.removeExtra(MainActivity.EXTRA_OPEN_HOME)
    intent.removeExtra(MainActivity.EXTRA_RESUME_PROFILE)
    recreate()
}
