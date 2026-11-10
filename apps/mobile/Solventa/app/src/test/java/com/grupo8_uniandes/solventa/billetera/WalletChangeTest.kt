package com.grupo8_uniandes.solventa.billetera

import com.grupo8_uniandes.solventa.domain.bff.billetera.Deposit
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositType
import com.grupo8_uniandes.solventa.domain.bff.billetera.Wallet
import com.grupo8_uniandes.solventa.domain.bff.billetera.changed
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.math.BigDecimal

class WalletChangeTest {
    @Test
    fun totalOrReceiptSetChanges() {
        val first = wallet(BigDecimal("10"), "CMP-1", "CMP-2")
        assertTrue(changed(first, wallet(BigDecimal("11"), "CMP-1", "CMP-2")))
        assertTrue(changed(first, wallet(BigDecimal("10"), "CMP-1", "CMP-3")))
        assertFalse(changed(first, wallet(BigDecimal("10.00"), "CMP-2", "CMP-1")))
    }

    private fun wallet(total: BigDecimal, vararg receipts: String) = Wallet(
        "COP",
        total,
        receipts.map {
            Deposit("id-$it", "SIN", DepositType.Assisted, "", "", "", BigDecimal.ONE, "COP", it, "")
        },
    )
}
