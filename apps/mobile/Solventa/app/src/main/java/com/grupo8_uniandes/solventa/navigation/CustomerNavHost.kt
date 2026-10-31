package com.grupo8_uniandes.solventa.navigation

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.PaddingValues
import androidx.core.content.ContextCompat
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import com.grupo8_uniandes.solventa.data.region.SharedPrefsRegionRepository
import com.grupo8_uniandes.solventa.di.startSolventaKoin
import com.grupo8_uniandes.solventa.claim.ClaimsPhase
import com.grupo8_uniandes.solventa.claim.SiniestrosViewModel
import com.grupo8_uniandes.solventa.offer.OfferViewModel
import com.grupo8_uniandes.solventa.policy.IssuanceUi
import com.grupo8_uniandes.solventa.policy.IssuanceViewModel
import com.grupo8_uniandes.solventa.policy.PolizaDetalleViewModel
import com.grupo8_uniandes.solventa.policy.PolizasViewModel
import com.grupo8_uniandes.solventa.quote.QuoteViewModel
import org.koin.androidx.compose.koinViewModel
import org.koin.core.parameter.parametersOf
import androidx.navigation.NavBackStackEntry
import androidx.navigation.NavDestination.Companion.hasRoute
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.toRoute
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ShowMortgageOffer
import com.grupo8_uniandes.solventa.ui.shell.CotizacionScreen
import com.grupo8_uniandes.solventa.ui.shell.OfertaHipotecarioScreen
import com.grupo8_uniandes.solventa.ui.shell.EmisionEnCursoScreen
import com.grupo8_uniandes.solventa.ui.shell.VerOfertaScreen
import com.grupo8_uniandes.solventa.ui.shell.InicioScreen
import com.grupo8_uniandes.solventa.ui.shell.PerfilScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizaDetalleScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizaEmitidaScreen
import com.grupo8_uniandes.solventa.ui.shell.SuscripcionRechazadaScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizasScreen
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenAssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenProviderCatalog
import com.grupo8_uniandes.solventa.domain.bff.claim.ProviderCatalog
import com.grupo8_uniandes.solventa.ui.shell.AsistenciaSitioScreen
import com.grupo8_uniandes.solventa.ui.shell.MapaPrestadoresScreen
import com.grupo8_uniandes.solventa.ui.shell.SiniestroDetalleScreen
import com.grupo8_uniandes.solventa.ui.shell.SiniestrosScreen

@Composable
fun CustomerNavHost(
    navController: NavHostController,
    homeState: HomeUiState,
    contentPadding: PaddingValues,
    modifier: Modifier = Modifier,
    startDestination: Any = InicioRoute,
    originationActive: Boolean = false,
    onSignedOut: () -> Unit = {},
    onInicioVisible: () -> Unit = {},
) {
    startSolventaKoin(LocalContext.current)
    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier.padding(contentPadding),
    ) {
        composable<InicioRoute> {
            LaunchedEffect(Unit) { onInicioVisible() }
            InicioScreen(
                state = homeState,
                onNewQuote = { navController.navigate(CotizacionRoute()) },
                onOpenOffer = { offerId -> navController.navigate(VerOfertaRoute(offerId)) },
                onAcceptOffer = { offerId -> navController.navigate(EmisionEnCursoRoute(offerId)) },
                onOpenPolicy = { policyId ->
                    navController.openParentThen(PolizasRoute, PolizaDetalleRoute(policyId))
                },
                onOpenClaim = { claimId ->
                    navController.openParentThen(SiniestrosRoute, SiniestroDetalleRoute(claimId))
                },
                onOpenMortgage = { navController.navigate(OfertaHipotecarioRoute) },
            )
        }
        composable<OfertaHipotecarioRoute> {
            val context = LocalContext.current
            val region = remember(context) {
                SharedPrefsRegionRepository(context.applicationContext).read().appliedRegion
            }
            val offer = remember(region) { ShowMortgageOffer(region).show() }
            OfertaHipotecarioScreen(
                offer = offer,
                onAccept = { navController.navigate(EmisionEnCursoRoute()) },
                onReviewLater = { navController.popBackStack() },
            )
        }
        composable<VerOfertaRoute> { entry ->
            val route = entry.toRoute<VerOfertaRoute>()
            val context = LocalContext.current
            val region = remember(context) {
                SharedPrefsRegionRepository(context.applicationContext).read().appliedRegion
            }
            val viewModel: OfferViewModel = koinViewModel { parametersOf(route.cotizacionId, region) }
            val state by viewModel.state.collectAsState()
            VerOfertaScreen(
                state = state,
                onAccept = { offerId -> navController.navigate(EmisionEnCursoRoute(offerId)) },
                onQuoteAgain = { navController.navigate(CotizacionRoute(route.cotizacionId)) },
                onDecline = { navController.popBackStack() },
            )
        }
        composable<CotizacionRoute> { entry ->
            val route = entry.toRoute<CotizacionRoute>()
            val context = LocalContext.current
            val region = remember(context) {
                SharedPrefsRegionRepository(context.applicationContext).read().appliedRegion
            }
            val viewModel: QuoteViewModel = koinViewModel { parametersOf(route.cotizacionId) }
            val state by viewModel.state.collectAsState()
            LaunchedEffect(state.readyId) {
                val readyId = state.readyId ?: return@LaunchedEffect
                viewModel.consumeReady()
                navController.navigate(VerOfertaRoute(readyId))
            }
            CotizacionScreen(
                state = state,
                onMenu = viewModel::onMenu,
                onLine = viewModel::onLine,
                onValueChange = viewModel::onValue,
                onBrandChange = viewModel::onBrand,
                onAge = viewModel::onAge,
                onText = viewModel::onText,
                onCotizar = viewModel::cotizar,
                onCancel = {
                    viewModel.cancel()
                    navController.popBackStack()
                },
                region = region,
            )
        }
        composable<PolizasRoute> {
            val viewModel: PolizasViewModel = koinViewModel()
            val state by viewModel.state.collectAsState()
            LaunchedEffect(Unit) { viewModel.refresh() }
            PolizasScreen(
                policies = state.policies,
                phase = state.phase,
                notice = state.notice,
                onOpenPolicy = { numero -> navController.navigate(PolizaDetalleRoute(numero)) },
                onNewQuote = { navController.navigate(CotizacionRoute()) },
            )
        }
        composable<PolizaDetalleRoute> { entry ->
            val route = entry.toRoute<PolizaDetalleRoute>()
            val viewModel: PolizaDetalleViewModel = koinViewModel { parametersOf(route.policyId) }
            val state by viewModel.state.collectAsState()
            PolizaDetalleScreen(
                state = state,
            )
        }
        composable<SiniestrosRoute> {
            val viewModel: SiniestrosViewModel = koinViewModel()
            val state by viewModel.state.collectAsState()
            val context = LocalContext.current
            val locationPermission = rememberLauncherForActivityResult(
                ActivityResultContracts.RequestPermission(),
            ) { granted ->
                if (granted) navController.navigate(MapaPrestadoresRoute)
            }
            LaunchedEffect(Unit) { viewModel.refresh() }
            SiniestrosScreen(
                claims = state.claims,
                failed = state.phase == ClaimsPhase.Failed,
                onOpenClaim = viewModel::openClaim,
                onOpenCatalog = {
                    val granted = ContextCompat.checkSelfPermission(
                        context,
                        Manifest.permission.ACCESS_FINE_LOCATION,
                    ) == PackageManager.PERMISSION_GRANTED
                    if (granted) {
                        navController.navigate(MapaPrestadoresRoute)
                    } else {
                        locationPermission.launch(Manifest.permission.ACCESS_FINE_LOCATION)
                    }
                },
            )
        }
        composable<MapaPrestadoresRoute> {
            val catalog = OpenProviderCatalog().open(locationAllowed = true) as ProviderCatalog.Open
            MapaPrestadoresScreen(
                rows = catalog.rows,
                onOpenAssistance = { navController.navigate(AsistenciaSitioRoute) },
            )
        }
        composable<AsistenciaSitioRoute> {
            val request = remember { OpenAssistanceRequest() }
            val form = remember { request.open(locationAllowed = true) }
            if (form != null) {
                AsistenciaSitioScreen(
                    form = form,
                    onContinue = {},
                    onCancel = {
                        request.cancel()
                        navController.popBackStack()
                    },
                )
            }
        }
        composable<SiniestroDetalleRoute> { entry ->
            val route = entry.toRoute<SiniestroDetalleRoute>()
            SiniestroDetalleScreen(
                claimId = route.claimId,
                onBack = { navController.popBackStack() },
            )
        }
        composable<PerfilRoute> {
            PerfilScreen(
                originationActive = originationActive,
                onSignedOut = onSignedOut,
            )
        }
        composable<EmisionEnCursoRoute> { entry ->
            val route = entry.toRoute<EmisionEnCursoRoute>()
            val viewModel: IssuanceViewModel = koinViewModel { parametersOf(route.offerId) }
            val issuance by viewModel.state.collectAsState()
            LaunchedEffect(issuance) {
                when (val step = issuance) {
                    is IssuanceUi.Issued -> navController.navigate(PolizaEmitidaRoute(step.numero)) {
                        popUpTo<EmisionEnCursoRoute> { inclusive = true }
                    }
                    is IssuanceUi.Refused -> navController.navigate(SuscripcionRechazadaRoute) {
                        popUpTo<EmisionEnCursoRoute> { inclusive = true }
                    }
                    IssuanceUi.Waiting -> Unit
                }
            }
            EmisionEnCursoScreen()
        }
        composable<SuscripcionRechazadaRoute> {
            SuscripcionRechazadaScreen(
                onHome = { navController.leaveIssuance(InicioRoute) },
                onUnderstood = { navController.leaveIssuance(InicioRoute) },
            )
        }
        composable<PolizaEmitidaRoute> { entry ->
            val route = entry.toRoute<PolizaEmitidaRoute>()
            PolizaEmitidaScreen(
                policyId = route.numero,
                onGoHome = { navController.leaveIssuance(InicioRoute) },
                onGoPolicy = { navController.leaveIssuanceToPolicy(route.numero) },
            )
        }
    }
}

fun NavBackStackEntry.toSolventaRoute(): Any {
    val destination = destination
    return when {
        destination.hasRoute<InicioRoute>() -> InicioRoute
        destination.hasRoute<CotizacionRoute>() -> toRoute<CotizacionRoute>()
        destination.hasRoute<VerOfertaRoute>() -> toRoute<VerOfertaRoute>()
        destination.hasRoute<PolizasRoute>() -> PolizasRoute
        destination.hasRoute<PolizaDetalleRoute>() -> toRoute<PolizaDetalleRoute>()
        destination.hasRoute<SiniestrosRoute>() -> SiniestrosRoute
        destination.hasRoute<MapaPrestadoresRoute>() -> MapaPrestadoresRoute
        destination.hasRoute<AsistenciaSitioRoute>() -> AsistenciaSitioRoute
        destination.hasRoute<SiniestroDetalleRoute>() -> toRoute<SiniestroDetalleRoute>()
        destination.hasRoute<PerfilRoute>() -> PerfilRoute
        destination.hasRoute<EmisionEnCursoRoute>() -> toRoute<EmisionEnCursoRoute>()
        destination.hasRoute<PolizaEmitidaRoute>() -> toRoute<PolizaEmitidaRoute>()
        destination.hasRoute<SuscripcionRechazadaRoute>() -> SuscripcionRechazadaRoute
        destination.hasRoute<OfertaHipotecarioRoute>() -> OfertaHipotecarioRoute
        else -> InicioRoute
    }
}

fun NavHostController.openDestination(destination: Destination) {
    val current = currentBackStackEntry?.toSolventaRoute()
    val currentParent = current?.let { selectedDestination(it) }
    val currentMode = current?.let { shellMode(it, signedIn = true) }
    if (currentParent == destination && currentMode == ShellMode.Root) return
    if (currentParent == destination) {
        popBackStack(destination.rootRoute(), inclusive = false)
        return
    }
    navigate(destination.rootRoute()) {
        popUpTo(graph.findStartDestination().id) {
            saveState = true
        }
        launchSingleTop = true
        restoreState = true
    }
}

fun NavHostController.leaveIssuance(route: Any) {
    navigate(route) {
        popUpTo(graph.findStartDestination().id) {
            inclusive = false
        }
        launchSingleTop = true
    }
}

private fun NavHostController.openParentThen(parent: Any, child: Any) {
    navigate(parent) {
        popUpTo(graph.findStartDestination().id) {
            saveState = true
        }
        launchSingleTop = true
        restoreState = true
    }
    navigate(child)
}

private fun NavHostController.leaveIssuanceToPolicy(numero: String) {
    navigate(PolizasRoute) {
        popUpTo(graph.findStartDestination().id) {
            saveState = true
        }
        launchSingleTop = true
        restoreState = true
    }
    navigate(PolizaDetalleRoute(numero))
}
