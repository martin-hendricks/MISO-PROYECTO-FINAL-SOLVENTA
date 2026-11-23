package com.grupo8_uniandes.solventa.domain.bff.offer

/** Spanish explanation from a quote the BFF refused. It is not an offer. */
class QuoteExplained(val detail: String) : RuntimeException()
