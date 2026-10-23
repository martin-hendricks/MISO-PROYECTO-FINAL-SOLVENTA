package com.grupo8_uniandes.solventa.navigation

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.data.bff.MobileBff
import com.grupo8_uniandes.solventa.data.region.SharedPrefsRegionRepository
import com.grupo8_uniandes.solventa.domain.bff.offer.RequestFirmOffer
import com.grupo8_uniandes.solventa.domain.bff.offer.ShowFirmOffer
import com.grupo8_uniandes.solventa.offer.OfferViewModel
import com.grupo8_uniandes.solventa.quote.QuoteViewModel
import androidx.navigation.NavBackStackEntry
import androidx.navigation.NavDestination.Companion.hasRoute
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.toRoute
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.ui.shell.CotizacionScreen
import com.grupo8_uniandes.solventa.ui.shell.EmisionEnCursoScreen
import com.grupo8_uniandes.solventa.ui.shell.VerOfertaScreen
import com.grupo8_uniandes.solventa.ui.shell.InicioScreen
import com.grupo8_uniandes.solventa.ui.shell.PerfilScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizaDetalleScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizaEmitidaScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizasScreen
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
) {
    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier.padding(contentPadding),
    ) {
        composable<InicioRoute> {
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
            )
        }
        composable<VerOfertaRoute> { entry ->
            val route = entry.toRoute<VerOfertaRoute>()
            val context = LocalContext.current
            val region = remember(context) {
                SharedPrefsRegionRepository(context.applicationContext).read().appliedRegion
            }
            val viewModel = remember(route.cotizacionId, region) {
                OfferViewModel(
                    showFirmOffer = ShowFirmOffer(MobileBff().offer),
                    cotizacionId = route.cotizacionId,
                    region = region,
                )
            }
            val state by viewModel.state.collectAsState()
            VerOfertaScreen(
                state = state,
                onAccept = { offerId -> navController.navigate(EmisionEnCursoRoute(offerId)) },
                onQuoteAgain = { navController.navigate(CotizacionRoute(route.cotizacionId)) },
            )
        }
        composable<CotizacionRoute> { entry ->
            val route = entry.toRoute<CotizacionRoute>()
            val viewModel = remember(route.cotizacionId) {
                QuoteViewModel(
                    request = RequestFirmOffer(MobileBff().offer),
                    contextId = route.cotizacionId,
                )
            }
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
            )
        }
        composable<PolizasRoute> {
            PolizasScreen(
                onOpenPolicy = { navController.navigate(PolizaDetalleRoute()) },
            )
        }
        composable<PolizaDetalleRoute> { entry ->
            val route = entry.toRoute<PolizaDetalleRoute>()
            PolizaDetalleScreen(
                policyId = route.policyId,
                onSecondary = { navController.popBackStack() },
            )
        }
        composable<SiniestrosRoute> {
            SiniestrosScreen()
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
            EmisionEnCursoScreen(
                offerId = route.offerId,
                onFinished = { navController.navigate(PolizaEmitidaRoute) },
            )
        }
        composable<PolizaEmitidaRoute> {
            PolizaEmitidaScreen(
                policyId = stringResource(R.string.sample_policy_id),
                onGoHome = { navController.leaveIssuance(InicioRoute) },
                onGoPolicy = { navController.leaveIssuanceToPolicy() },
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
        destination.hasRoute<SiniestroDetalleRoute>() -> toRoute<SiniestroDetalleRoute>()
        destination.hasRoute<PerfilRoute>() -> PerfilRoute
        destination.hasRoute<EmisionEnCursoRoute>() -> toRoute<EmisionEnCursoRoute>()
        destination.hasRoute<PolizaEmitidaRoute>() -> PolizaEmitidaRoute
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

private fun NavHostController.leaveIssuance(route: Any) {
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

private fun NavHostController.leaveIssuanceToPolicy() {
    navigate(PolizasRoute) {
        popUpTo(graph.findStartDestination().id) {
            saveState = true
        }
        launchSingleTop = true
        restoreState = true
    }
    navigate(PolizaDetalleRoute())
}
