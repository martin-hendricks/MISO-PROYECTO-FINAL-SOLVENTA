package com.grupo8_uniandes.solventa.navigation

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import com.grupo8_uniandes.solventa.R
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
import com.grupo8_uniandes.solventa.ui.shell.InicioScreen
import com.grupo8_uniandes.solventa.ui.shell.PerfilScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizaDetalleScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizaEmitidaScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizasScreen
import com.grupo8_uniandes.solventa.ui.shell.SiniestrosScreen

@Composable
fun CustomerNavHost(
    navController: NavHostController,
    homeState: HomeUiState,
    contentPadding: PaddingValues,
    modifier: Modifier = Modifier,
    startDestination: Any = InicioRoute,
) {
    NavHost(
        navController = navController,
        startDestination = startDestination,
        modifier = modifier.padding(contentPadding),
    ) {
        composable<InicioRoute> {
            InicioScreen(
                state = homeState,
                onNewQuote = { navController.navigate(CotizacionRoute) },
            )
        }
        composable<CotizacionRoute> {
            CotizacionScreen(
                onAccept = { navController.navigate(EmisionEnCursoRoute) },
                onCancel = { navController.popBackStack() },
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
        composable<PerfilRoute> {
            PerfilScreen()
        }
        composable<EmisionEnCursoRoute> {
            EmisionEnCursoScreen(
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
        destination.hasRoute<CotizacionRoute>() -> CotizacionRoute
        destination.hasRoute<PolizasRoute>() -> PolizasRoute
        destination.hasRoute<PolizaDetalleRoute>() -> toRoute<PolizaDetalleRoute>()
        destination.hasRoute<SiniestrosRoute>() -> SiniestrosRoute
        destination.hasRoute<PerfilRoute>() -> PerfilRoute
        destination.hasRoute<EmisionEnCursoRoute>() -> EmisionEnCursoRoute
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
