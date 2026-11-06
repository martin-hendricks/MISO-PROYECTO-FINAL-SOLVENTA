package com.grupo8_uniandes.solventa.domain.issuance

/**
 * Month and year typed apart. The month is two digits, with a leading zero
 * when the first digit cannot start 10, 11, or 12. The year is two digits.
 */
object CardExpiry {
    private val monthPattern = Regex("""^(0[1-9]|1[0-2])$""")
    private val yearPattern = Regex("""^\d{2}$""")

    fun month(raw: String): String {
        val digits = raw.filter { it.isDigit() }.take(2)
        if (digits.isEmpty()) return ""
        if (digits.length == 1) {
            return if (digits[0] in '2'..'9') "0$digits" else digits
        }
        val value = digits.toInt()
        if (value !in 1..12) return month(digits.dropLast(1))
        return digits
    }

    fun year(raw: String): String = raw.filter { it.isDigit() }.take(2)

    fun complete(month: String, year: String): Boolean =
        monthPattern.matches(month(month)) && yearPattern.matches(year(year))
}
