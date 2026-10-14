@backoffice @HU-8 @SOLV-101
Feature: Back-office navigation

  Scenario: The advisor lands on Clientes
    Given an asesor signed in to the back-office
    Then the back-office shows its four destinations
    And the clientes destination is the current one

  Scenario: The operator lands on Avisos
    Given an operador signed in to the back-office
    Then the back-office shows its four destinations
    And the avisos destination is the current one

  Scenario: The advisor moves to another destination
    Given an asesor signed in to the back-office
    When the user opens the cotizaciones destination
    Then the cotizaciones destination is the current one
