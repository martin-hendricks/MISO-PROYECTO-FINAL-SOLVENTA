package com.grupo8_uniandes.solventa.billetera

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.billetera.Deposit
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositMemory
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositRepository
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositType
import com.grupo8_uniandes.solventa.domain.bff.billetera.InMemoryDepositStore
import com.grupo8_uniandes.solventa.domain.bff.billetera.ListDeposits
import com.grupo8_uniandes.solventa.domain.bff.billetera.StoredWallet
import com.grupo8_uniandes.solventa.domain.bff.billetera.Wallet
import com.grupo8_uniandes.solventa.domain.bff.billetera.WalletNotice
import com.grupo8_uniandes.solventa.domain.bff.billetera.WalletSource
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.math.BigDecimal

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class BilleteraViewModelTest {
    @Before
    fun main() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun reset() {
        Dispatchers.resetMain()
    }

    @Test
    fun chipsFilterTheLoadedList() {
        val repo = Scripted(StandInAnswer.Ready(two()))
        val viewModel = BilleteraViewModel(ListDeposits(repo, InMemoryDepositStore()) { "t" }, FakeNetworkMonitor(true))
        assertEquals(1, viewModel.reads)
        assertEquals(2, viewModel.state.value.visible.size)
        viewModel.select(DepositType.Automatic)
        assertEquals(1, viewModel.reads)
        assertEquals(listOf(DepositType.Automatic), viewModel.state.value.visible.map { it.tipo })
    }

    @Test
    fun failureWithoutACopyShowsNoTotal() {
        val viewModel = BilleteraViewModel(
            ListDeposits(Scripted(StandInAnswer.Failed), InMemoryDepositStore()) { "t" },
            FakeNetworkMonitor(true),
        )
        assertEquals(WalletPhase.FirstLoad, viewModel.state.value.phase)
        assertNull(viewModel.state.value.wallet)
    }

    @Test
    fun networkReturnReadsOnceAndAnnouncesAChange() {
        val repo = Scripted(StandInAnswer.Ready(two()))
        val network = FakeNetworkMonitor(true)
        val viewModel = BilleteraViewModel(ListDeposits(repo, InMemoryDepositStore()) { "t" }, network)
        repo.answer = StandInAnswer.Failed
        viewModel.refresh()
        assertEquals(WalletSource.Copy, viewModel.state.value.source)
        val before = viewModel.reads
        repo.answer = StandInAnswer.Ready(two(extra = true))
        network.set(false)
        network.set(true)
        assertEquals(before + 1, viewModel.reads)
        assertEquals(WalletNotice.Updated, viewModel.state.value.notice)
        assertEquals(3, viewModel.state.value.wallet?.movimientos?.size)
    }

    @Test
    fun failedRefreshKeepsTheCopy() {
        val repo = Scripted(StandInAnswer.Ready(two()))
        val network = FakeNetworkMonitor(true)
        val viewModel = BilleteraViewModel(ListDeposits(repo, InMemoryDepositStore()) { "t" }, network)
        repo.answer = StandInAnswer.Failed
        viewModel.refresh()
        val kept = viewModel.state.value.wallet
        network.set(false)
        network.set(true)
        assertEquals(kept, viewModel.state.value.wallet)
        assertEquals(WalletNotice.Offline, viewModel.state.value.notice)
    }

    @Test
    fun offlineDetailDisablesDownloadAndAsksForNetwork() {
        val deposit = two().movimientos.first()
        val memory = object : DepositMemory {
            override fun read() = StoredWallet(two(), "ayer")
            override fun write(wallet: Wallet, savedAt: String) = Unit
        }
        val repo = object : DepositRepository {
            override suspend fun wallet() = StandInAnswer.Failed as StandInAnswer<Wallet>
            override suspend fun deposit(id: String) = StandInAnswer.Failed as StandInAnswer<Deposit>
        }
        val viewModel = DepositoViewModel(deposit.id, repo, memory, FakeNetworkMonitor(false))
        assertEquals(deposit.comprobante, viewModel.state.value.deposit?.comprobante)
        assertFalse(viewModel.state.value.downloadEnabled)
        assertNull(viewModel.openClaim())
        assertTrue(viewModel.state.value.needsNetwork)
    }
}

private class Scripted(var answer: StandInAnswer<Wallet>) : DepositRepository {
    override suspend fun wallet(): StandInAnswer<Wallet> = answer
    override suspend fun deposit(id: String): StandInAnswer<Deposit> = StandInAnswer.Rejected("not_found")
}

private fun two(extra: Boolean = false): Wallet {
    val rows = mutableListOf(
        row("a", DepositType.Assisted, "CMP-1", "2026-07-11T15:20:00Z"),
        row("b", DepositType.Automatic, "CMP-2", "2026-07-02T09:05:00Z"),
    )
    if (extra) rows += row("c", DepositType.Assisted, "CMP-3", "2026-07-12T00:00:00Z")
    return Wallet("COP", BigDecimal(rows.size), rows)
}

private fun row(id: String, tipo: DepositType, receipt: String, at: String) = Deposit(
    id, "SIN-$id", tipo, "ramo", "", "POL", BigDecimal.ONE, "COP", receipt, at,
)
