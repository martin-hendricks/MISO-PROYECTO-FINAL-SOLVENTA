package com.grupo8_uniandes.solventa.domain.registration

import java.math.BigDecimal
import java.math.RoundingMode

/**
 * COP amounts sent on registration. The customer may type a whole amount, a comma
 * decimal, or thousand separators. The wire value always has two fraction digits.
 * Income is greater than zero. Spending may be zero. The phone does not compare them.
 */
object MonthlyAmounts {
    private val dotDecimal = Regex("""^\d+\.\d{1,2}$""")
    private val commaDecimal = Regex("""^\d+,\d{1,2}$""")
    private val grouped = Regex("""^\d{1,3}(\.\d{3})+$""")
    private val groupedDecimal = Regex("""^\d{1,3}(\.\d{3})+,\d{1,2}$""")

    fun income(raw: String): String? = decimal(raw)?.takeIf { it > BigDecimal.ZERO }?.let(::wire)

    fun spending(raw: String): String? = decimal(raw)?.takeIf { it >= BigDecimal.ZERO }?.let(::wire)

    fun pair(income: String, spending: String): Pair<String, String>? {
        val left = income(income) ?: return null
        val right = spending(spending) ?: return null
        return left to right
    }

    private fun wire(amount: BigDecimal): String =
        amount.setScale(2, RoundingMode.UNNECESSARY).toPlainString()

    private fun decimal(raw: String): BigDecimal? {
        val text = raw.trim().removePrefix("$").replace(" ", "")
        val plain = when {
            groupedDecimal.matches(text) -> text.replace(".", "").replace(',', '.')
            grouped.matches(text) -> text.replace(".", "")
            commaDecimal.matches(text) -> text.replace(',', '.')
            dotDecimal.matches(text) -> text
            text.matches(Regex("""^\d+$""")) -> text
            else -> return null
        }
        return plain.toBigDecimalOrNull()
    }
}
