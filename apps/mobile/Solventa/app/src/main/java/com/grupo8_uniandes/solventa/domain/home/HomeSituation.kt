package com.grupo8_uniandes.solventa.domain.home

import java.time.Instant

/**
 * A price the customer might still accept. Only a quote that can be consulted again
 * can become the current offer.
 */
data class Quote(
    /** Identifies the offer Aceptar oferta starts issuance for. Not a new price. */
    val id: String,
    /** `true` when the quote can be consulted again. `false` drops it even if it is newer. */
    val consultable: Boolean,
    /** Compared only among consultable quotes. The latest one is the current offer. */
    val becameCurrentAt: Instant,
)

/**
 * A policy in force. Inicio links to its detail and does not list the rest.
 */
data class PolicyCandidate(
    /** The policy detail route receives this id. Shown in the amount face. */
    val id: String,
    /** Only `true` can be the shortcut. */
    val active: Boolean,
    /** Among active policies, the latest one is the shortcut. */
    val issuedAt: Instant,
)

/**
 * An open case. Inicio links to that case and does not list the rest.
 */
data class ClaimCandidate(
    /** The claim placeholder receives this id. Shown in the amount face. */
    val id: String,
    /** Only `true` can be the shortcut. */
    val inProgress: Boolean,
    /** Among cases in progress, the latest one is the shortcut. */
    val openedAt: Instant,
)

/**
 * The condition for Vida Crediticia. It is not a destination and it is not a Perfil entry.
 */
data class Origination(
    /** `true` shows the Vida Crediticia card on Inicio. `false` omits it. */
    val present: Boolean = false,
)

/**
 * The repository's answer. Empty lists and `present = false` are a home with no cards.
 */
data class HomeSituation(
    /** May be empty. */
    val quotes: List<Quote> = emptyList(),
    /** May include inactive rows. Those are dropped. */
    val policies: List<PolicyCandidate> = emptyList(),
    /** May include closed rows. Those are dropped. */
    val claims: List<ClaimCandidate> = emptyList(),
    /** One flag. */
    val origination: Origination = Origination(),
)

/**
 * What Inicio is allowed to draw. Each slot is independent. There is no premium.
 */
data class HomePanel(
    val offerId: String? = null,
    val policyId: String? = null,
    val claimId: String? = null,
    val vidaCrediticia: Boolean = false,
)
