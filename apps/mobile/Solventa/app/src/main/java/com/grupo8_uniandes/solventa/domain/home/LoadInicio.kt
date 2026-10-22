package com.grupo8_uniandes.solventa.domain.home

import java.time.Instant

/**
 * Selects one panel from the situation. It does not rate a price and it does not write.
 * A tie on the timestamp keeps the later item in the repository list.
 */
class LoadInicio(
    private val repository: HomeRepository,
) {
    fun panel(): HomePanel = select(repository.load())

    fun select(situation: HomeSituation): HomePanel {
        val offer = keepLatest(situation.quotes.filter { it.consultable }) { it.becameCurrentAt }
        val policy = keepLatest(situation.policies.filter { it.active }) { it.issuedAt }
        val claim = keepLatest(situation.claims.filter { it.inProgress }) { it.openedAt }
        return HomePanel(
            offerId = offer?.id,
            policyId = policy?.id,
            claimId = claim?.id,
            vidaCrediticia = situation.origination.present,
        )
    }
}

private fun <T> keepLatest(items: List<T>, moment: (T) -> Instant): T? {
    var kept: T? = null
    var keptAt: Instant? = null
    for (item in items) {
        val at = moment(item)
        if (keptAt == null || !at.isBefore(keptAt)) {
            kept = item
            keptAt = at
        }
    }
    return kept
}
