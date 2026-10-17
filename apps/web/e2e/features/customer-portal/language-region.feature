@customer-portal @pendiente @HU-108 @SOLV-232
Feature: Language and region

  Scenario: First launch
    Given the customer opens the portal for the first time
    When the customer reaches language and region
    Then the customer can choose Español Colombia, México, Chile or Perú
    And "Continuar" goes to sign-up, not to a permissions splash

  Scenario: Mexico locale formats the channel
    Given the customer chooses Español México
    Then a sample premium is shown as "$1,234.56 MXN"
    And the sample date is "09/07/2026"

  Scenario: Changing it from Perfil does not restart sign-up
    Given the customer is signed in
    When the customer opens language and region from Perfil
    Then the dialog closes with "Listo"
    And the customer does not go to sign-up or to sign-up consent
