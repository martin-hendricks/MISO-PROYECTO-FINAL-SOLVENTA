package com.grupo8_uniandes.solventa.domain.bff.billetera

object WalletChange {
    fun changed(old: Wallet, new: Wallet): Boolean {
        val oldTotal = old.totalRecibido
        val newTotal = new.totalRecibido
        val totalsDiffer = when {
            oldTotal == null && newTotal == null -> false
            oldTotal == null || newTotal == null -> true
            else -> oldTotal.compareTo(newTotal) != 0
        }
        if (totalsDiffer) return true
        return old.movimientos.map { it.comprobante }.toSet() != new.movimientos.map { it.comprobante }.toSet()
    }
}

fun changed(old: Wallet, new: Wallet): Boolean = WalletChange.changed(old, new)
