@customer-portal @HU-53 @SOLV-146 @HU-106 @SOLV-230
Feature: Profiling consent managed from Perfil

  Scenario: Revoking the profiling consent from Perfil
    Given the customer is signed in
    And the customer granted the profiling consent
    When the customer revokes the profiling consent from Perfil
    Then the revocation reaches the BFF once
    And Perfil shows the profiling consent as revoked

  Scenario: Cancelling keeps the profiling consent in force
    Given the customer is signed in
    And the customer granted the profiling consent
    When the customer opens the profiling consent from Perfil and cancels
    Then no revocation reaches the BFF
    And Perfil still shows when the profiling consent was granted

  Scenario: No profiling consent to manage
    Given the customer is signed in
    And the customer never granted the profiling consent
    When the customer opens Perfil
    Then Perfil does not list a profiling consent
