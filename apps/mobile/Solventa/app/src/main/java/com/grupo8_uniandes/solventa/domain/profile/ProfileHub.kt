package com.grupo8_uniandes.solventa.domain.profile

import com.grupo8_uniandes.solventa.domain.consent.ConsentState
import com.grupo8_uniandes.solventa.domain.region.Region

data class ProfileIdentity(
    val name: String,
    val document: String,
)

enum class PermissionKind {
    Location,
    Camera,
    Photos,
}

data class PermissionRow(
    val kind: PermissionKind,
    val published: Boolean,
)

data class ProfileHub(
    val identity: ProfileIdentity?,
    val region: Region,
    val permissions: List<PermissionRow>,
    val consent: ConsentState,
    val originationActive: Boolean,
    val sessionOpen: Boolean,
)

fun profileIdentity(
    givenName: String,
    surnames: String,
    documentType: String,
    documentNumber: String,
): ProfileIdentity {
    val name = listOf(givenName, surnames).map { it.trim() }.filter { it.isNotEmpty() }.joinToString(" ")
    val document = listOf(documentType, documentNumber).map { it.trim() }.filter { it.isNotEmpty() }.joinToString(" ")
    return ProfileIdentity(name = name, document = document)
}
