Feature: Back-office shell
  Scenario: The advisor lands on Clientes
    Given an asesor signed in to the back-office
    Then the back-office shows its four destinations
    And the clientes destination is the current one
    And the client list shows 5 clients

  Scenario: A role without permission keeps the shell
    Given an asesor signed in to the back-office
    When the user opens the avisos destination
    Then the back-office shows its four destinations
    And the avisos destination is the current one
    And the content says the role asesor needs the role operador

  Scenario: The operator lands on Avisos
    Given an operador signed in to the back-office
    Then the avisos destination is the current one
    When the user opens the clientes destination
    Then the content says the role operador needs the role asesor

  Scenario: Signing out returns to the back-office login
    Given an asesor signed in to the back-office
    When the user signs out of the back-office
    Then the back-office login is visible

  Scenario: A customer session does not open the back-office
    Given the customer is signed in
    And the user shell is visible
    When the visitor opens the back-office
    Then the back-office login is visible
