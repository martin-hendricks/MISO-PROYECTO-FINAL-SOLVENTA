package com.grupo8_uniandes.solventa.domain.bff.billetera

object WalletChange {
    fun changed(old: Wallet, new: Wallet): Boolean {
        if (old.totalRecibido.compareTo(new.totalRecibido) != 0) return true
        return old.movimientos.map { it.comprobante }.toSet() != new.movimientos.map { it.comprobante }.toSet()
    }
}

fun changed(old: Wallet, new: Wallet): Boolean = WalletChange.changed(old, new)
