package com.grupo8_uniandes.solventa.ui.shell

import androidx.activity.OnBackPressedCallback
import androidx.activity.compose.LocalOnBackPressedDispatcherOwner
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.grupo8_uniandes.solventa.R
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

@Composable
fun CustomerShell(
    signedIn: Boolean = true,
    modifier: Modifier = Modifier,
) {
    val navController = rememberNavController()
    val homeViewModel: HomeViewModel = viewModel()
    val homeState by homeViewModel.state.collectAsState()
    val entry by navController.currentBackStackEntryAsState()
    val route = entry?.toSolventaRoute() ?: InicioRoute
    val mode = shellMode(route, signedIn)
    val selected = selectedDestination(route)
    val showBottomBar = mode == ShellMode.Root || mode == ShellMode.Nested

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
        if (!signedIn) {
            Box(Modifier.fillMaxSize())
        } else {
            CustomerNavHost(
                navController = navController,
                homeState = homeState,
                contentPadding = padding,
            )
        }
    }

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
