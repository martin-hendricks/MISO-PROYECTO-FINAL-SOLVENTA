package com.grupo8_uniandes.solventa.accessibility

import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assertHeightIsAtLeast
import androidx.compose.ui.test.assertWidthIsAtLeast
import androidx.compose.ui.test.junit4.ComposeContentTestRule
import androidx.compose.ui.unit.dp

fun hasRole(role: Role): SemanticsMatcher =
    SemanticsMatcher.expectValue(SemanticsProperties.Role, role)

fun isHeading(): SemanticsMatcher =
    SemanticsMatcher.keyIsDefined(SemanticsProperties.Heading)

fun hasError(message: String): SemanticsMatcher =
    SemanticsMatcher.expectValue(SemanticsProperties.Error, message)

fun isPassword(): SemanticsMatcher =
    SemanticsMatcher.keyIsDefined(SemanticsProperties.Password)

fun ComposeContentTestRule.assertTouchAtLeast(matcher: SemanticsMatcher) {
    onNode(matcher)
        .assertWidthIsAtLeast(48.dp)
        .assertHeightIsAtLeast(48.dp)
}
