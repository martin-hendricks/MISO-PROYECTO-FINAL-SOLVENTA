@access @HU-108 @SOLV-232
Feature: Idioma y región web

  Scenario: First launch
    Given a first-time visitor opens the portal
    When the visitor reaches idioma-region
    Then the visitor can choose Español Colombia, México, Chile or Perú
    And Continuar goes to sign-up, not a permissions splash

  Scenario: México locale formats on the channel
    Given a first-time visitor opens the portal
    When the visitor chooses Español México and continues
    Then the sign-up view is shown in the chosen locale

  Scenario: Change from Perfil does not restart sign-up
    Given the customer is signed in
    When the customer opens idioma y región from Perfil
    Then the dialog closes with Listo
    And the customer is not sent to sign-up or data consent
