package com.grupo8_uniandes.solventa.domain.login

sealed interface SignInResult {
    data object Incomplete : SignInResult

    data object Rejected : SignInResult

    data object Unavailable : SignInResult

    data object SignedIn : SignInResult
}
