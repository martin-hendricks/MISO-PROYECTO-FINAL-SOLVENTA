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
        assertEquals(ShellMode.Nested, shellMode(CotizacionRoute, signedIn = true))
        assertEquals(Destination.Inicio, selectedDestination(CotizacionRoute))
        val detail = PolizaDetalleRoute(policyId = "SOL-0001")
        assertEquals(ShellMode.Nested, shellMode(detail, signedIn = true))
        assertEquals(Destination.Polizas, selectedDestination(detail))
    }

    @Test
    fun givenIssuance_whenSignedIn_thenNoSelectedDestination() {
        assertEquals(ShellMode.Issuance, shellMode(EmisionEnCursoRoute, signedIn = true))
        assertEquals(ShellMode.Issuance, shellMode(PolizaEmitidaRoute, signedIn = true))
        assertNull(selectedDestination(EmisionEnCursoRoute))
        assertNull(selectedDestination(PolizaEmitidaRoute))
    }
}
