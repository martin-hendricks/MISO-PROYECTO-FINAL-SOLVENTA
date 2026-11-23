package com.grupo8_uniandes.solventa.issuance

import androidx.compose.ui.test.SemanticsNodeInteractionsProvider
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput

fun SemanticsNodeInteractionsProvider.confirmReviewCard() {
    onNodeWithTag("field_titular").performScrollTo().performTextInput("Camila Restrepo")
    onNodeWithTag("field_tarjeta").performScrollTo().performTextInput("4242424242424242")
    onNodeWithTag("field_mes").performScrollTo().performTextInput("08")
    onNodeWithTag("field_anio").performScrollTo().performTextInput("28")
    onNodeWithTag("field_codigo").performScrollTo().performTextInput("123")
    onNodeWithText("Confirmar pago").performScrollTo().performClick()
}
