package com.grupo8_uniandes.solventa.policy

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.notice.OpenValidityNotice
import com.grupo8_uniandes.solventa.domain.bff.notice.ValidityKind
import com.grupo8_uniandes.solventa.domain.bff.notice.ValidityReading
import com.grupo8_uniandes.solventa.navigation.Destination
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.shell.AvisoVigenciaScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class AvisoVigenciaTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Before
    fun accessibilityChecks() {
        rule.enableAccessibilityChecks()
    }

    @Test
    fun givenAPolicyAboutToExpire_whenTheNoticeIsShown_thenTheCustomerCannotRenew() {
        show(ValidityKind.EXPIRY, "12 mar 2028", "screen_aviso_vencimiento")
        rule.onNodeWithText("Avisos").assertIsDisplayed()
        rule.onNodeWithText(
            "Tu póliza ${OpenValidityNotice.POLICY} vence el 12 mar 2028. La renovación la confirma un operador.",
        ).assertIsDisplayed()
        rule.onNodeWithText("Ver póliza").assertIsDisplayed()
        rule.onNodeWithText("Entendido").assertIsDisplayed()
        rule.onNodeWithTag("tab_Polizas").assertIsSelected()
        rule.onAllNodesWithTag("notification_bell").assertCountEquals(0)
        rule.onAllNodesWithText("Renovar").assertCountEquals(0)
        rule.onAllNodesWithText("Cancelar").assertCountEquals(0)
    }

    @Test
    fun givenARenewalInForce_whenTheNoticeIsShown_thenTheCustomerDoesNotRunTheCommand() {
        show(ValidityKind.RENEWAL, null, "screen_aviso_renovacion")
        rule.onNodeWithText(
            "Renovación confirmada · tu póliza ${OpenValidityNotice.POLICY} sigue vigente. La ejecuta un operador; aquí solo la consultas.",
        ).assertIsDisplayed()
        rule.onNodeWithText("Ver póliza").assertIsDisplayed()
        rule.onNodeWithText("Ir al inicio").assertIsDisplayed()
        rule.onNodeWithTag("tab_Polizas").assertIsSelected()
        rule.onAllNodesWithTag("notification_bell").assertCountEquals(0)
        rule.onAllNodesWithText("Renovar").assertCountEquals(0)
    }

    private fun show(kind: ValidityKind, venceEn: String?, tag: String) {
        rule.setContent {
            SolventaTheme {
                Box(Modifier.fillMaxSize()) {
                    Text(stringResource(R.string.validity_title))
                    AvisoVigenciaScreen(
                        reading = ValidityReading(kind, OpenValidityNotice.POLICY, venceEn),
                        onViewPolicy = {},
                        onLeave = {},
                    )
                    SolventaBottomBar(
                        selected = Destination.Polizas,
                        onSelect = {},
                        modifier = Modifier.align(Alignment.BottomCenter),
                    )
                }
            }
        }
        rule.onNodeWithTag(tag).assertIsDisplayed()
    }
}
