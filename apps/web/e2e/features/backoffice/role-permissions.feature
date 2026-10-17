@backoffice @HU-8 @SOLV-101
Feature: Back-office role permissions

  Scenario: An advisor opening Avisos keeps the shell
    Given an asesor signed in to the back-office
    When the user opens the avisos destination
    Then the back-office shows its four destinations
    And the avisos destination is the current one
    And the content says the role asesor needs the role operador

  Scenario: An operator opening Clientes keeps the shell
    Given an operador signed in to the back-office
    When the user opens the clientes destination
    Then the clientes destination is the current one
    And the content says the role operador needs the role asesor

  Scenario: The no-permission state leads back to the role home
    Given an asesor signed in to the back-office
    When the user opens the avisos destination
    And the user goes back from the no-permission state
    Then the clientes destination is the current one

  Scenario: A customer session does not open the back-office
    Given the customer is signed in
    When the visitor opens the back-office
    Then the back-office login is visible
