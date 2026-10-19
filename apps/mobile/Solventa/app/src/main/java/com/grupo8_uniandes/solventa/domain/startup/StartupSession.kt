package com.grupo8_uniandes.solventa.domain.startup

enum class StartupSession {
    /** The customer has not completed first-run language and region. Default on launch. */
    FirstUse,

    /** The customer can sign in. Injected. This story does not create an account. */
    ExistingAccount,
}
