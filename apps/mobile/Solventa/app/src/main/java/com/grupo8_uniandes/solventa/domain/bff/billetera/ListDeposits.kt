package com.grupo8_uniandes.solventa.domain.bff.billetera

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

enum class WalletSource { Fresh, Copy, None }

enum class WalletNotice { None, Offline, Updated, NeedsFirstLoad }

data class WalletRead(
    val wallet: Wallet?,
    val source: WalletSource,
    val notice: WalletNotice,
    val savedAt: String?,
)

class ListDeposits(
    private val repository: DepositRepository,
    private val memory: DepositMemory,
    private val clock: () -> String = { java.time.Instant.now().toString() },
) {
    suspend operator fun invoke(): WalletRead = when (val answer = repository.wallet()) {
        is StandInAnswer.Ready -> {
            val savedAt = clock()
            memory.write(answer.value, savedAt)
            WalletRead(answer.value, WalletSource.Fresh, WalletNotice.None, savedAt)
        }
        StandInAnswer.Failed, StandInAnswer.Pending, is StandInAnswer.Rejected -> remembered()
    }

    private fun remembered(): WalletRead {
        val stored = memory.read() ?: return WalletRead(null, WalletSource.None, WalletNotice.NeedsFirstLoad, null)
        return WalletRead(stored.wallet, WalletSource.Copy, WalletNotice.Offline, stored.savedAt)
    }
}
