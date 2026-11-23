package com.grupo8_uniandes.solventa.domain.issuance

/**
 * Local card number. Digits stay in state. The grouping follows the franchise
 * read from the prefix. The number never leaves the phone.
 */
enum class CardFranchise {
    Visa,
    Mastercard,
    Amex,
    Diners,
    Unknown,
}

object CardNumber {
    fun franchise(digits: String): CardFranchise {
        val head = digits.filter { it.isDigit() }
        if (head.startsWith("34") || head.startsWith("37")) return CardFranchise.Amex
        if (head.startsWith("36") || head.startsWith("38")) return CardFranchise.Diners
        val three = head.take(3).toIntOrNull()
        if (three != null && three in 300..305) return CardFranchise.Diners
        if (head.startsWith("4")) return CardFranchise.Visa
        val two = head.take(2).toIntOrNull()
        if (head.length >= 2 && two != null && two in 51..55) return CardFranchise.Mastercard
        val four = head.take(4).toIntOrNull()
        if (head.length >= 4 && four != null && four in 2221..2720) return CardFranchise.Mastercard
        return CardFranchise.Unknown
    }

    fun limit(digits: String): Int = when (franchise(digits)) {
        CardFranchise.Amex -> 15
        CardFranchise.Diners -> 14
        else -> 16
    }

    fun digits(raw: String): String {
        val only = raw.filter { it.isDigit() }
        return only.take(limit(only))
    }

    fun grouped(digits: String): String {
        val only = digits.filter { it.isDigit() }
        if (only.isEmpty()) return ""
        val sizes = when (franchise(only)) {
            CardFranchise.Amex -> intArrayOf(4, 6, 5)
            CardFranchise.Diners -> intArrayOf(4, 6, 4)
            else -> intArrayOf(4, 4, 4, 4)
        }
        val out = StringBuilder()
        var index = 0
        for (size in sizes) {
            if (index >= only.length) break
            if (out.isNotEmpty()) out.append(' ')
            val end = minOf(index + size, only.length)
            out.append(only.substring(index, end))
            index = end
        }
        return out.toString()
    }
}
