package com.grupo8_uniandes.solventa.session

import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class BackupRulesTest {
    @Test
    fun givenBackupRules_whenRead_thenEncryptedTokensAreExcluded() {
        val backup = File("src/main/res/xml/backup_rules.xml").readText()
        val extraction = File("src/main/res/xml/data_extraction_rules.xml").readText()
        assertTrue(backup.contains("""path="solventa.tokens.xml""""))
        assertTrue(extraction.contains("<cloud-backup>"))
        assertTrue(extraction.contains("<device-transfer>"))
        assertTrue(extraction.split("solventa.tokens.xml").size >= 3)
    }
}
