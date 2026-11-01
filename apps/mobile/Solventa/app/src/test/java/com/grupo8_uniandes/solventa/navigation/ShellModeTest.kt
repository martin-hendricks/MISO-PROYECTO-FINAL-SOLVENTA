package com.grupo8_uniandes.solventa.navigation

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ShellModeTest {
    @Test
    fun destinationsStayInOrder() {
        assertEquals(
            listOf(Destination.Inicio, Destination.Polizas, Destination.Siniestros, Destination.Perfil),
            Destination.entries.toList(),
        )
        assertEquals(listOf(0, 1, 2, 3), Destination.entries.map { it.order })
    }

    @Test
    fun givenSignedOut_whenAnyRoute_thenPreLogin() {
        assertEquals(ShellMode.PreLogin, shellMode(InicioRoute, signedIn = false))
        assertEquals(ShellMode.PreLogin, shellMode(PolizasRoute, signedIn = false))
    }

    @Test
    fun givenRootRoutes_whenSignedIn_thenRootAndParentSelected() {
        assertEquals(ShellMode.Root, shellMode(InicioRoute, signedIn = true))
        assertEquals(Destination.Inicio, selectedDestination(InicioRoute))
        assertEquals(ShellMode.Root, shellMode(PolizasRoute, signedIn = true))
        assertEquals(Destination.Polizas, selectedDestination(PolizasRoute))
        assertEquals(ShellMode.Root, shellMode(SiniestrosRoute, signedIn = true))
        assertEquals(Destination.Siniestros, selectedDestination(SiniestrosRoute))
        assertEquals(ShellMode.Root, shellMode(PerfilRoute, signedIn = true))
        assertEquals(Destination.Perfil, selectedDestination(PerfilRoute))
    }

    @Test
    fun givenNestedRoutes_whenSignedIn_thenNestedKeepsParent() {
        assertEquals(ShellMode.Nested, shellMode(CotizacionRoute(), signedIn = true))
        assertEquals(Destination.Inicio, selectedDestination(CotizacionRoute()))
        val offer = VerOfertaRoute(cotizacionId = "COT-1042")
        assertEquals(ShellMode.Nested, shellMode(offer, signedIn = true))
        assertEquals(Destination.Inicio, selectedDestination(offer))
        assertEquals(ShellMode.Nested, shellMode(OfertaHipotecarioRoute, signedIn = true))
        assertEquals(Destination.Inicio, selectedDestination(OfertaHipotecarioRoute))
        val detail = PolizaDetalleRoute(policyId = "SOL-0001")
        assertEquals(ShellMode.Nested, shellMode(detail, signedIn = true))
        assertEquals(Destination.Polizas, selectedDestination(detail))
        val claim = SiniestroDetalleRoute(claimId = "CLM-1")
        assertEquals(ShellMode.Nested, shellMode(claim, signedIn = true))
        assertEquals(Destination.Siniestros, selectedDestination(claim))
        assertEquals(ShellMode.Nested, shellMode(AvisoSiniestroRoute, signedIn = true))
        assertEquals(Destination.Siniestros, selectedDestination(AvisoSiniestroRoute))
        assertEquals(ShellMode.Nested, shellMode(ParametricoRoute, signedIn = true))
        assertEquals(Destination.Siniestros, selectedDestination(ParametricoRoute))
        assertEquals(ShellMode.Nested, shellMode(AvisoVencimientoRoute, signedIn = true))
        assertEquals(Destination.Polizas, selectedDestination(AvisoVencimientoRoute))
        assertEquals(ShellMode.Nested, shellMode(AvisoRenovacionRoute, signedIn = true))
        assertEquals(Destination.Polizas, selectedDestination(AvisoRenovacionRoute))
        assertEquals(ShellMode.Nested, shellMode(EvidenciaAvisoRoute, signedIn = true))
        assertEquals(Destination.Siniestros, selectedDestination(EvidenciaAvisoRoute))
        val sent = ConfirmacionAvisoRoute(siniestroId = "SIN-441")
        assertEquals(ShellMode.Nested, shellMode(sent, signedIn = true))
        assertEquals(Destination.Siniestros, selectedDestination(sent))
    }

    @Test
    fun givenIssuance_whenSignedIn_thenNoSelectedDestination() {
        assertEquals(EmisionEnCursoRoute("Q-1"), EmisionEnCursoRoute("Q-1").copy())
        assertEquals("", EmisionEnCursoRoute().offerId)
        assertEquals(SiniestroDetalleRoute("CLM-1"), SiniestroDetalleRoute("CLM-1").copy(claimId = "CLM-1"))
        assertEquals(ShellMode.Issuance, shellMode(EmisionEnCursoRoute(), signedIn = true))
        assertEquals(ShellMode.Issuance, shellMode(PolizaEmitidaRoute(), signedIn = true))
        assertNull(selectedDestination(EmisionEnCursoRoute()))
        assertNull(selectedDestination(PolizaEmitidaRoute()))
        assertEquals(ShellMode.Nested, shellMode(SuscripcionRechazadaRoute, signedIn = true))
        assertEquals(Destination.Inicio, selectedDestination(SuscripcionRechazadaRoute))
    }

    @Test
    fun givenAnUnknownRoute_whenSignedIn_thenItStaysOnTheRoot() {
        assertEquals(ShellMode.Root, shellMode("otra", signedIn = true))
        assertNull(selectedDestination("otra"))
        assertEquals(InicioRoute, Destination.Inicio.rootRoute())
        assertEquals(PolizasRoute, Destination.Polizas.rootRoute())
        assertEquals(SiniestrosRoute, Destination.Siniestros.rootRoute())
        assertEquals(PerfilRoute, Destination.Perfil.rootRoute())
        assertEquals("SOL-0001", PolizaDetalleRoute().policyId)
    }
}
