package com.grupo8_uniandes.solventa.bff

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.bff.remote.BffCache
import com.grupo8_uniandes.solventa.domain.bff.billetera.Deposit
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositType
import com.grupo8_uniandes.solventa.domain.bff.billetera.Wallet
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import java.math.BigDecimal

@RunWith(RobolectricTestRunner::class)
class BffCacheTest {
    private val context = ApplicationProvider.getApplicationContext<Context>()

    @Test
    fun anotherCustomerWipesTheWallet() {
        val cache = BffCache(context)
        cache.retainOwner("one")
        cache.writeBilletera(wallet(), "ayer")
        cache.retainOwner("two")
        assertNull(cache.readBilletera())
    }

    @Test
    fun signOutWipesTheWallet() {
        val cache = BffCache(context)
        cache.writeBilletera(wallet(), "ayer")
        cache.clear()
        assertNull(cache.readBilletera())
    }

    @Test
    fun theSameCustomerKeepsTheWallet() {
        val cache = BffCache(context)
        cache.retainOwner("one")
        cache.writeBilletera(wallet(), "ayer")
        cache.retainOwner("one")
        assertEquals("CMP-1", cache.readBilletera()?.wallet?.movimientos?.single()?.comprobante)
    }

    @Test
    fun aNewCacheReadsTheSavedWallet() {
        BffCache(context).writeBilletera(wallet(), "ayer")
        val saved = BffCache(context).readBilletera()
        assertEquals("ayer", saved?.savedAt)
        assertEquals("CMP-1", saved?.wallet?.movimientos?.single()?.comprobante)
        assertEquals(BigDecimal.ONE, saved?.wallet?.totalRecibido)
    }

    private fun wallet() = Wallet(
        "COP",
        BigDecimal.ONE,
        listOf(Deposit("a", "SIN", DepositType.Assisted, "", "", "", BigDecimal.ONE, "COP", "CMP-1", "")),
    )
}
