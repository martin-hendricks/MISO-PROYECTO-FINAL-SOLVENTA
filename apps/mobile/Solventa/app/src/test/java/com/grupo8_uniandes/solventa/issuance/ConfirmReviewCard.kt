package com.grupo8_uniandes.solventa.issuance

import androidx.compose.ui.test.SemanticsNodeInteractionsProvider
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput

fun SemanticsNodeInteractionsProvider.confirmReviewCard() {
    onNodeWithTag("field_titular").performTextInput("Camila Restrepo")
    onNodeWithTag("field_tarjeta").performTextInput("4242424242424242")
    onNodeWithTag("field_mes").performTextInput("08")
    onNodeWithTag("field_anio").performTextInput("28")
    onNodeWithTag("field_codigo").performTextInput("123")
    onNodeWithTag("action_confirmar_pago").performClick()
}
