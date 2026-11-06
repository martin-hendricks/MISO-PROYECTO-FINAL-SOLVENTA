package com.grupo8_uniandes.solventa.domain.bff.policy

sealed interface RenewalSave {
    data class Saved(val enabled: Boolean) : RenewalSave

    data object Missing : RenewalSave

    data object Failed : RenewalSave
}

interface RenewalPreferenceRepository {
    suspend fun save(numero: String, enabled: Boolean): RenewalSave
}

class StandInRenewalPreferenceRepository : RenewalPreferenceRepository {
    override suspend fun save(numero: String, enabled: Boolean): RenewalSave = RenewalSave.Saved(enabled)
}

class SaveRenewalPreference(
    private val repository: RenewalPreferenceRepository,
) {
    suspend operator fun invoke(numero: String, enabled: Boolean): RenewalSave =
        repository.save(numero, enabled)
}
