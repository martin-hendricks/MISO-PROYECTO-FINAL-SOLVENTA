package com.grupo8_uniandes.solventa.billetera

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.billetera.Deposit
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositRepository
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositType
import com.grupo8_uniandes.solventa.domain.bff.billetera.InMemoryDepositStore
import com.grupo8_uniandes.solventa.domain.bff.billetera.ListDeposits
import com.grupo8_uniandes.solventa.domain.bff.billetera.Wallet
import com.grupo8_uniandes.solventa.domain.bff.billetera.WalletNotice
import com.grupo8_uniandes.solventa.domain.bff.billetera.WalletSource
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.math.BigDecimal

class ListDepositsTest {
    @Test
    fun readyWritesTheCopyOnce() = runBlocking {
        val memory = InMemoryDepositStore()
        val repo = ScriptedWallet(StandInAnswer.Ready(sample()))
        val read = ListDeposits(repo, memory) { "2026-07-11T00:00:00Z" }.invoke()

        assertEquals(WalletSource.Fresh, read.source)
        assertEquals("2026-07-11T00:00:00Z", memory.read()?.savedAt)
        assertEquals(sample().totalRecibido, memory.read()?.wallet?.totalRecibido)
    }

    @Test
    fun failureReturnsTheCopy() = runBlocking {
        val memory = InMemoryDepositStore()
        val repo = ScriptedWallet(StandInAnswer.Ready(sample()))
        ListDeposits(repo, memory) { "ayer" }.invoke()
        repo.answer = StandInAnswer.Failed
        val read = ListDeposits(repo, memory) { "hoy" }.invoke()

        assertEquals(WalletSource.Copy, read.source)
        assertEquals(WalletNotice.Offline, read.notice)
        assertEquals("ayer", read.savedAt)
        assertEquals("ayer", memory.read()?.savedAt)
    }

    @Test
    fun failureWithoutACopyNeedsTheFirstLoad() = runBlocking {
        val read = ListDeposits(ScriptedWallet(StandInAnswer.Failed), InMemoryDepositStore()).invoke()
        assertEquals(WalletNotice.NeedsFirstLoad, read.notice)
        assertNull(read.wallet)
    }

    @Test
    fun rejectedDoesNotTouchTheCopy() = runBlocking {
        val memory = InMemoryDepositStore()
        val repo = ScriptedWallet(StandInAnswer.Ready(sample()))
        ListDeposits(repo, memory) { "ayer" }.invoke()
        repo.answer = StandInAnswer.Rejected("not_found")
        val read = ListDeposits(repo, memory) { "hoy" }.invoke()

        assertEquals("ayer", memory.read()?.savedAt)
        assertEquals(WalletSource.Copy, read.source)
        assertEquals(sample().comprobantes(), read.wallet?.comprobantes())
    }
}

private fun Wallet.comprobantes() = movimientos.map { it.comprobante }

private fun sample() = Wallet(
    "COP",
    BigDecimal("1070000.00"),
    listOf(
        Deposit(
            "a",
            "SIN-1",
            DepositType.Assisted,
            "ramo",
            "",
            "POL",
            BigDecimal("890000.00"),
            "COP",
            "CMP-1",
            "2026-07-11T15:20:00Z",
        ),
    ),
)

private class ScriptedWallet(var answer: StandInAnswer<Wallet>) : DepositRepository {
    override suspend fun wallet(): StandInAnswer<Wallet> = answer
    override suspend fun deposit(id: String): StandInAnswer<Deposit> = StandInAnswer.Rejected("not_found")
}
