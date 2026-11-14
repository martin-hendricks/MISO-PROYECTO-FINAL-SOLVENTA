package com.grupo8_uniandes.solventa.navigation

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.PaddingValues
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
import com.grupo8_uniandes.solventa.claim.DetailPhase
import com.grupo8_uniandes.solventa.claim.ParametricTarget
import com.grupo8_uniandes.solventa.claim.SiniestroDetalleViewModel
import com.grupo8_uniandes.solventa.claim.SiniestrosViewModel
import com.grupo8_uniandes.solventa.offer.OfferViewModel
import com.grupo8_uniandes.solventa.issuance.ConfirmacionTarjetaViewModel
import com.grupo8_uniandes.solventa.policy.IssuanceUi
import com.grupo8_uniandes.solventa.policy.IssuanceViewModel
import com.grupo8_uniandes.solventa.policy.RenewalChoiceViewModel
import com.grupo8_uniandes.solventa.policy.AvisoVigenciaViewModel
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
import com.grupo8_uniandes.solventa.mortgage.MortgageOfferViewModel
import com.grupo8_uniandes.solventa.ui.shell.ConfirmacionTarjetaScreen
import com.grupo8_uniandes.solventa.ui.shell.CotizacionScreen
import com.grupo8_uniandes.solventa.ui.shell.VidaHipotecarioFlow
import com.grupo8_uniandes.solventa.ui.shell.EmisionEnCursoScreen
import com.grupo8_uniandes.solventa.ui.shell.VerOfertaScreen
import com.grupo8_uniandes.solventa.ui.shell.InicioScreen
import com.grupo8_uniandes.solventa.ui.shell.PerfilScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizaDetalleScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizaEmitidaScreen
import com.grupo8_uniandes.solventa.ui.shell.ConsentimientoRevocadoScreen
import com.grupo8_uniandes.solventa.ui.shell.SuscripcionRechazadaScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizasScreen
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenParametricPayment
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenProviderCatalog
import com.grupo8_uniandes.solventa.domain.bff.claim.ProviderCatalog
import com.grupo8_uniandes.solventa.ui.shell.AsistenciaSitioScreen
import com.grupo8_uniandes.solventa.ui.shell.MapaPrestadoresScreen
import com.grupo8_uniandes.solventa.ui.shell.SiniestroDetalleScreen
import androidx.activity.ComponentActivity
import com.grupo8_uniandes.solventa.claim.AvisoSiniestroViewModel
import com.grupo8_uniandes.solventa.claim.ParametricoViewModel
import com.grupo8_uniandes.solventa.domain.bff.claim.NoticePhase
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenAssistanceRequest
import com.grupo8_uniandes.solventa.domain.bff.push.NoticeDestination
import com.grupo8_uniandes.solventa.domain.bff.push.NoticeEntry
import com.grupo8_uniandes.solventa.domain.push.PushTarget
import com.grupo8_uniandes.solventa.ui.region.findActivity
import com.grupo8_uniandes.solventa.ui.shell.AvisoSiniestroScreen
import com.grupo8_uniandes.solventa.ui.shell.ConfirmacionAvisoScreen
import com.grupo8_uniandes.solventa.ui.shell.EvidenciaAvisoScreen
import com.grupo8_uniandes.solventa.ui.shell.AvisoVigenciaScreen
import com.grupo8_uniandes.solventa.ui.shell.ParametricoScreen
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
    paymentPush: NoticeEntry? = null,
    pushTarget: PushTarget? = null,
    onPushHandled: () -> Unit = {},
) {
    startSolventaKoin(LocalContext.current)
    LaunchedEffect(paymentPush) {
        val push = paymentPush ?: return@LaunchedEffect
        when (push.destino) {
            NoticeDestination.PARAMETRICO ->
                if (OpenParametricPayment.opens(push)) navController.navigate(ParametricoRoute)
            // La ruta solo depende del tipo de aviso; qué póliza real coincide
            // se resuelve dentro de la pantalla (AvisoVigenciaViewModel.openPush,
            // vía OpenValidityNotice) contra la lista real de avisos, no aquí.
            NoticeDestination.AVISO_VENCIMIENTO -> navController.navigate(AvisoVencimientoRoute)
            NoticeDestination.AVISO_RENOVACION -> navController.navigate(AvisoRenovacionRoute)
            NoticeDestination.DETALLE_SINIESTRO -> Unit
        }
    }
    LaunchedEffect(pushTarget) {
        val target = pushTarget ?: return@LaunchedEffect
        when (target) {
            is PushTarget.PolizaDetalle -> navController.navigate(PolizaDetalleRoute(target.numero))
            PushTarget.Inicio -> navController.navigate(InicioRoute) {
                popUpTo(navController.graph.findStartDestination().id) {
                    saveState = true
                }
                launchSingleTop = true
                restoreState = true
            }
        }
        onPushHandled()
    }
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
                onAcceptOffer = { offerId -> navController.navigate(ConfirmacionTarjetaRoute(offerId)) },
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
            val viewModel: MortgageOfferViewModel = koinViewModel()
            VidaHipotecarioFlow(
                viewModel = viewModel,
                region = region,
                onAccept = { prima, moneda ->
                    navController.navigate(ConfirmacionTarjetaRoute(prima = prima, moneda = moneda))
                },
                onDecline = { navController.popBackStack() },
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
                onAccept = { offerId ->
                    navController.navigate(
                        ConfirmacionTarjetaRoute(offerId, state.prima, state.moneda),
                    )
                },
                onQuoteAgain = { navController.navigate(CotizacionRoute(route.cotizacionId)) },
                onDecline = { navController.popBackStack(InicioRoute, inclusive = false) },
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
                onModelChange = viewModel::onModel,
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
            val avisos: AvisoVigenciaViewModel = koinViewModel()
            val renewal: RenewalChoiceViewModel = koinViewModel { parametersOf(route.policyId) }
            val renewalState by renewal.state.collectAsState()
            LaunchedEffect(state.detail?.renovacionAutomatica) {
                state.detail?.let { renewal.adopt(it.renovacionAutomatica) }
            }
            PolizaDetalleScreen(
                state = state,
                renewalChecked = renewalState.checked,
                renewalMissing = renewalState.missing,
                onRenewal = renewal::onChecked,
                onOpenClaim = { id -> navController.navigate(SiniestroDetalleRoute(id)) },
                onReportClaim = { navController.navigate(AvisoSiniestroRoute) },
                onExpiryNotices = {
                    avisos.requestExpiry(route.policyId) { reading ->
                        if (reading != null) navController.navigate(AvisoVencimientoRoute)
                    }
                },
            )
        }
        composable<AvisoVencimientoRoute> {
            ValidityNoticeRoute(
                navController = navController,
                load = AvisoVigenciaViewModel::loadExpiry,
                onLeave = { navController.popBackStack() },
            )
        }
        composable<AvisoRenovacionRoute> {
            ValidityNoticeRoute(
                navController = navController,
                load = AvisoVigenciaViewModel::loadRenewal,
                onLeave = { navController.popBackStack(InicioRoute, inclusive = false) },
            )
        }
        composable<SiniestrosRoute> {
            val viewModel: SiniestrosViewModel = koinViewModel()
            val state by viewModel.state.collectAsState()
            LaunchedEffect(Unit) { viewModel.refresh() }
            LaunchedEffect(state.openedClaimId) {
                val id = state.openedClaimId ?: return@LaunchedEffect
                if (state.openParametric) {
                    navController.navigate(ParametricoRoute)
                } else {
                    navController.navigate(SiniestroDetalleRoute(id))
                }
                viewModel.consumeOpenedClaim()
            }
            SiniestrosScreen(
                claims = state.visible,
                chip = state.chip,
                onChip = viewModel::selectChip,
                filterMiss = state.phase == ClaimsPhase.Ready &&
                    state.claims.isNotEmpty() &&
                    state.visible.isEmpty(),
                failed = state.phase == ClaimsPhase.Failed,
                onRetry = viewModel::refresh,
                onOpenClaim = viewModel::openClaim,
                onReport = { navController.navigate(AvisoSiniestroRoute) },
            )
        }
        composable<MapaPrestadoresRoute> {
            val catalog = OpenProviderCatalog().open(locationAllowed = true) as ProviderCatalog.Open
            MapaPrestadoresScreen(
                rows = catalog.rows,
                onOpenAssistance = { navController.navigate(AsistenciaSitioRoute) },
                onReport = { navController.navigate(AvisoSiniestroRoute) },
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
        composable<AvisoSiniestroRoute> {
            val viewModel = avisoViewModel()
            LaunchedEffect(Unit) { viewModel.reopen() }
            val aviso by viewModel.state.collectAsState()
            AvisoSiniestroScreen(
                sentences = listOf(
                    aviso.draft.poliza,
                    aviso.draft.fechaHecho,
                    aviso.draft.descripcion,
                    aviso.draft.lugar,
                ),
                problems = aviso.problems,
                policies = aviso.policyOptions,
                policiesLoaded = aviso.policiesLoaded,
                geotag = aviso.draft.geotag,
                geo = aviso.draft.geo,
                locationDenied = aviso.draft.locationDenied,
                locating = aviso.locating,
                onRevise = viewModel::revise,
                onToggleGeotag = viewModel::toggleGeotag,
                onUseLocation = viewModel::useCurrentLocation,
                onLocationDenied = viewModel::denyCurrentLocation,
                onContinue = {
                    if (viewModel.continueToEvidence()) navController.navigate(EvidenciaAvisoRoute)
                },
                onCancel = {
                    viewModel.cancel()
                    navController.popBackStack()
                },
            )
        }
        composable<EvidenciaAvisoRoute> {
            val viewModel = avisoViewModel()
            val state by viewModel.state.collectAsState()
            LaunchedEffect(state.receiptId) {
                if (state.phase == NoticePhase.Confirmation && state.receiptId.isNotBlank()) {
                    navController.navigate(ConfirmacionAvisoRoute(state.receiptId)) {
                        popUpTo(AvisoSiniestroRoute) { inclusive = true }
                        launchSingleTop = true
                    }
                }
            }
            EvidenciaAvisoScreen(
                draft = state.draft,
                onAttach = { attachment, bytes -> viewModel.attach(attachment, bytes) },
                onRemove = viewModel::remove,
                onCameraDenied = viewModel::markCameraDenied,
                onSend = viewModel::send,
                onQueue = viewModel::queue,
                sending = state.sending,
                queued = state.queued,
                rejection = state.rejection,
                fileRejected = state.fileRejected,
            )
        }
        composable<ConfirmacionAvisoRoute> { entry ->
            val route = entry.toRoute<ConfirmacionAvisoRoute>()
            val notice = avisoViewModel()
            ConfirmacionAvisoScreen(
                siniestroId = route.siniestroId,
                onMyClaims = {
                    notice.reopen()
                    navController.showClaimsList()
                },
                onHome = {
                    notice.reopen()
                    navController.leaveIssuance(InicioRoute)
                },
            )
        }
        composable<ParametricoRoute> {
            val viewModel: ParametricoViewModel = koinViewModel()
            val state by viewModel.state.collectAsState()
            val context = LocalContext.current
            LaunchedEffect(Unit) {
                val id = ParametricTarget.claimId
                if (id.isNotBlank()) viewModel.loadStored(id) else viewModel.load()
            }
            val notice = state.notice
            if (notice != null) {
                ParametricoScreen(
                    notice = notice,
                    onBack = { navController.popBackStack() },
                    renewalChecked = state.renewalChecked,
                    onRenewal = viewModel::setRenewal,
                    onDownload = {
                        val receipt = viewModel.offerReceipt() ?: return@ParametricoScreen
                        val text = listOf(receipt.asunto, receipt.disparo, receipt.lineaDepositada)
                            .joinToString("\n")
                        val share = Intent(Intent.ACTION_SEND).apply {
                            type = "text/plain"
                            putExtra(Intent.EXTRA_TEXT, text)
                        }
                        runCatching { context.startActivity(Intent.createChooser(share, null)) }
                    },
                )
            }
        }
        composable<SiniestroDetalleRoute> { entry ->
            val route = entry.toRoute<SiniestroDetalleRoute>()
            val viewModel: SiniestroDetalleViewModel = koinViewModel { parametersOf(route.claimId) }
            val detail by viewModel.state.collectAsState()
            val context = LocalContext.current
            SiniestroDetalleScreen(
                claimId = route.claimId,
                claim = detail.claim,
                missing = detail.phase == DetailPhase.Missing,
                failed = detail.phase == DetailPhase.Failed,
                onRetry = viewModel::load,
                onOpenPolicy = { numero -> navController.navigate(PolizaDetalleRoute(numero)) },
                onOpenEvidence = { url ->
                    val view = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                    runCatching { context.startActivity(view) }
                },
            )
        }
        composable<PerfilRoute> {
            PerfilScreen(
                originationActive = originationActive,
                onSignedOut = onSignedOut,
            )
        }
        composable<ConfirmacionTarjetaRoute> { entry ->
            val route = entry.toRoute<ConfirmacionTarjetaRoute>()
            val viewModel: ConfirmacionTarjetaViewModel = koinViewModel {
                parametersOf(route.offerId, route.prima, route.moneda)
            }
            val state by viewModel.state.collectAsState()
            ConfirmacionTarjetaScreen(
                state = state,
                onTitular = viewModel::onTitular,
                onNumero = viewModel::onNumero,
                onMes = viewModel::onMes,
                onAnio = viewModel::onAnio,
                onCodigo = viewModel::onCodigo,
                onConfirm = {
                    if (viewModel.confirm()) {
                        navController.navigate(EmisionEnCursoRoute(route.offerId))
                    }
                },
                onBackToOffer = {
                    viewModel.discard()
                    navController.popBackStack()
                },
                onLeave = viewModel::discard,
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
                    IssuanceUi.ConsentRevoked -> navController.navigate(ConsentimientoRevocadoRoute) {
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
        composable<ConsentimientoRevocadoRoute> {
            ConsentimientoRevocadoScreen(
                onNewQuote = { navController.leaveIssuance(CotizacionRoute()) },
                onHome = { navController.leaveIssuance(InicioRoute) },
            )
        }
        composable<PolizaEmitidaRoute> { entry ->
            val route = entry.toRoute<PolizaEmitidaRoute>()
            val renewal: RenewalChoiceViewModel = koinViewModel { parametersOf(route.numero) }
            val renewalState by renewal.state.collectAsState()
            PolizaEmitidaScreen(
                policyId = route.numero,
                renewalChecked = renewalState.checked,
                renewalMissing = renewalState.missing,
                onRenewal = renewal::onChecked,
                onGoHome = { navController.leaveIssuance(InicioRoute) },
                onGoPolicy = { navController.leaveIssuanceToPolicy(route.numero) },
            )
        }
    }
}

@Composable
private fun ValidityNoticeRoute(
    navController: NavHostController,
    load: AvisoVigenciaViewModel.() -> Unit,
    onLeave: () -> Unit,
) {
    val viewModel: AvisoVigenciaViewModel = koinViewModel()
    val reading by viewModel.reading.collectAsState()
    LaunchedEffect(Unit) { viewModel.load() }
    val notice = reading
    if (notice != null) {
        AvisoVigenciaScreen(
            reading = notice,
            onViewPolicy = { navController.navigate(PolizaDetalleRoute(notice.poliza)) },
            onLeave = onLeave,
        )
    }
}

@Composable
private fun avisoViewModel(): AvisoSiniestroViewModel {
    val activity = LocalContext.current.findActivity() as? ComponentActivity
    return if (activity != null) {
        koinViewModel(viewModelStoreOwner = activity)
    } else {
        koinViewModel()
    }
}

fun NavBackStackEntry.toSolventaRoute(): Any {
    val destination = destination
    return when {
        destination.hasRoute<InicioRoute>() -> InicioRoute
        destination.hasRoute<CotizacionRoute>() -> toRoute<CotizacionRoute>()
        destination.hasRoute<VerOfertaRoute>() -> toRoute<VerOfertaRoute>()
        destination.hasRoute<ConfirmacionTarjetaRoute>() -> toRoute<ConfirmacionTarjetaRoute>()
        destination.hasRoute<PolizasRoute>() -> PolizasRoute
        destination.hasRoute<PolizaDetalleRoute>() -> toRoute<PolizaDetalleRoute>()
        destination.hasRoute<SiniestrosRoute>() -> SiniestrosRoute
        destination.hasRoute<AvisoSiniestroRoute>() -> AvisoSiniestroRoute
        destination.hasRoute<ParametricoRoute>() -> ParametricoRoute
        destination.hasRoute<AvisoVencimientoRoute>() -> AvisoVencimientoRoute
        destination.hasRoute<AvisoRenovacionRoute>() -> AvisoRenovacionRoute
        destination.hasRoute<EvidenciaAvisoRoute>() -> EvidenciaAvisoRoute
        destination.hasRoute<ConfirmacionAvisoRoute>() -> toRoute<ConfirmacionAvisoRoute>()
        destination.hasRoute<MapaPrestadoresRoute>() -> MapaPrestadoresRoute
        destination.hasRoute<AsistenciaSitioRoute>() -> AsistenciaSitioRoute
        destination.hasRoute<SiniestroDetalleRoute>() -> toRoute<SiniestroDetalleRoute>()
        destination.hasRoute<PerfilRoute>() -> PerfilRoute
        destination.hasRoute<EmisionEnCursoRoute>() -> toRoute<EmisionEnCursoRoute>()
        destination.hasRoute<PolizaEmitidaRoute>() -> toRoute<PolizaEmitidaRoute>()
        destination.hasRoute<SuscripcionRechazadaRoute>() -> SuscripcionRechazadaRoute
        destination.hasRoute<ConsentimientoRevocadoRoute>() -> ConsentimientoRevocadoRoute
        destination.hasRoute<OfertaHipotecarioRoute>() -> OfertaHipotecarioRoute
        else -> InicioRoute
    }
}

fun NavHostController.openDestination(destination: Destination) {
    if (destination == Destination.Polizas) {
        reopenPolizas()
        return
    }
    val current = currentBackStackEntry?.toSolventaRoute()
    val currentParent = current?.let { selectedDestination(it) }
    val currentMode = current?.let { shellMode(it, signedIn = true) }
    if (currentParent == destination && currentMode == ShellMode.Root) return
    if (currentParent == destination && popBackStack(destination.rootRoute(), inclusive = false)) {
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

fun NavHostController.showClaimsList() {
    if (popBackStack(SiniestrosRoute, inclusive = false)) return
    navigate(SiniestrosRoute) {
        popUpTo(graph.findStartDestination().id) {
            saveState = true
        }
        launchSingleTop = true
        restoreState = false
    }
}

private fun NavHostController.reopenPolizas() {
    popBackStack(PolizasRoute, inclusive = true)
    navigate(PolizasRoute) {
        popUpTo(graph.findStartDestination().id) {
            saveState = true
        }
        launchSingleTop = true
        restoreState = false
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
