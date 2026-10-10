package com.grupo8_uniandes.solventa.ui.shell

import android.app.Activity
import androidx.activity.OnBackPressedCallback
import androidx.activity.compose.LocalOnBackPressedDispatcherOwner
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.data.region.SharedPrefsRegionRepository
import com.grupo8_uniandes.solventa.data.registration.SharedPrefsRegistrationRepository
import com.grupo8_uniandes.solventa.domain.region.RegionRepository
import com.grupo8_uniandes.solventa.domain.registration.RegisterAccount
import com.grupo8_uniandes.solventa.domain.startup.PostSplashStep
import com.grupo8_uniandes.solventa.domain.startup.StartupSession
import com.grupo8_uniandes.solventa.home.HomeViewModel
import com.grupo8_uniandes.solventa.navigation.CotizacionRoute
import com.grupo8_uniandes.solventa.navigation.CustomerNavHost
import com.grupo8_uniandes.solventa.navigation.EmisionEnCursoRoute
import com.grupo8_uniandes.solventa.navigation.InicioRoute
import com.grupo8_uniandes.solventa.navigation.PerfilRoute
import com.grupo8_uniandes.solventa.navigation.PolizaDetalleRoute
import com.grupo8_uniandes.solventa.navigation.PolizaEmitidaRoute
import com.grupo8_uniandes.solventa.navigation.PolizasRoute
import com.grupo8_uniandes.solventa.navigation.ShellMode
import com.grupo8_uniandes.solventa.navigation.SiniestrosRoute
import com.grupo8_uniandes.solventa.navigation.openDestination
import com.grupo8_uniandes.solventa.navigation.selectedDestination
import com.grupo8_uniandes.solventa.navigation.shellMode
import com.grupo8_uniandes.solventa.navigation.toSolventaRoute
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.components.SolventaTopBar
import com.grupo8_uniandes.solventa.ui.region.IdiomaRegionScreen
import com.grupo8_uniandes.solventa.ui.region.IdiomaRegionViewModel
import com.grupo8_uniandes.solventa.ui.region.RegionEffect
import com.grupo8_uniandes.solventa.ui.region.RegionSurface
import com.grupo8_uniandes.solventa.ui.region.findActivity
import com.grupo8_uniandes.solventa.ui.registration.LoginPlaceholder
import com.grupo8_uniandes.solventa.ui.registration.OnboardingEffect
import com.grupo8_uniandes.solventa.ui.registration.OnboardingScreen
import com.grupo8_uniandes.solventa.ui.registration.OnboardingViewModel

@Composable
fun CustomerShell(
    startupSession: StartupSession = StartupSession.FirstUse,
    splashHoldMillis: Long = SplashHoldMillis,
    enterSignedInShell: Boolean = false,
    openOnboarding: Boolean = false,
    resumeProfile: Boolean = false,
    modifier: Modifier = Modifier,
) {
    if (enterSignedInShell) {
        SignedInShell(modifier = modifier, startOnProfile = resumeProfile)
        return
    }
    if (openOnboarding) {
        OnboardingHost(modifier = modifier)
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
    when {
        step == PostSplashStep.LanguageAndRegion && !completed -> {
            FirstLaunchLanguage(repository = repository, modifier = modifier)
        }
        step == PostSplashStep.LanguageAndRegion && completed && !registrationDone -> {
            OnboardingHost(modifier = modifier)
        }
        else -> {
            SignedInShell(modifier = modifier, startOnProfile = resumeProfile)
        }
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
            activity?.openOnboarding()
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
private fun OnboardingHost(modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val viewModel = remember(context) {
        OnboardingViewModel(
            RegisterAccount(SharedPrefsRegistrationRepository(context.applicationContext)),
        )
    }
    val state by viewModel.state.collectAsState()
    val activity = LocalContext.current.findActivity()
    LaunchedEffect(state.effect) {
        if (state.effect == OnboardingEffect.ContinueToHome) {
            activity?.openHomeAfterOnboarding()
        }
    }
    if (state.effect == OnboardingEffect.OpenLogin) {
        LoginPlaceholder(modifier = modifier)
    } else {
        OnboardingScreen(
            state = state,
            onGivenName = viewModel::onGivenName,
            onSurnames = viewModel::onSurnames,
            onEmail = viewModel::onEmail,
            onDocumentType = viewModel::onDocumentType,
            onDocumentNumber = viewModel::onDocumentNumber,
            onPassword = viewModel::onPassword,
            onPhotoAttached = viewModel::attachPhoto,
            onPhotoDeclined = viewModel::photoDeclined,
            onContinue = viewModel::continuar,
            onExistingAccount = viewModel::yaTengoCuenta,
            modifier = modifier,
        )
    }
}

@Composable
private fun SignedInShell(
    modifier: Modifier = Modifier,
    startOnProfile: Boolean = false,
) {
    val signedIn = true
    val navController = rememberNavController()
    val homeViewModel: HomeViewModel = viewModel()
    val homeState by homeViewModel.state.collectAsState()
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
            if (signedIn && mode != ShellMode.PreLogin) {
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
    ) { padding ->
        CustomerNavHost(
            navController = navController,
            homeState = homeState,
            contentPadding = padding,
            startDestination = start,
        )
    }
}

@Composable
private fun routeTitle(route: Any): String = when (route) {
    CotizacionRoute -> stringResource(R.string.quote_title)
    is PolizaDetalleRoute -> stringResource(R.string.policy_detail_title)
    EmisionEnCursoRoute -> stringResource(R.string.issuing_title)
    PolizaEmitidaRoute -> stringResource(R.string.issued_title)
    PolizasRoute -> stringResource(R.string.destination_polizas)
    SiniestrosRoute -> stringResource(R.string.destination_siniestros)
    PerfilRoute -> stringResource(R.string.destination_perfil)
    else -> stringResource(R.string.destination_inicio)
}

internal fun Activity.openOnboarding() {
    intent.putExtra(MainActivity.EXTRA_OPEN_ONBOARDING, true)
    recreate()
}

internal fun Activity.openHomeAfterOnboarding() {
    intent.putExtra(MainActivity.EXTRA_OPEN_HOME, true)
    recreate()
}

internal fun Activity.resumeProfileAfterLocaleChange() {
    intent.putExtra(MainActivity.EXTRA_RESUME_PROFILE, true)
    recreate()
}
