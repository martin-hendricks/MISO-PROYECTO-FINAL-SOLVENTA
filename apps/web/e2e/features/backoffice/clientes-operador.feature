@backoffice
Feature: Operator customer directory

  Scenario: The operator sees who can receive push and can edit
    Given the operator directory lists Ana with a device and Luis without one
    And an operador signed in to the back-office
    When the user opens the clientes destination
    Then Ana can receive push and Luis cannot
    And the operator can create a customer

  Scenario: The advisor keeps a read-only Clientes
    Given the operator directory lists Ana with a device and Luis without one
    And an asesor signed in to the back-office
    When the user opens the clientes destination
    Then the customer list is visible
    And the customer write controls are hidden
    And the Notificaciones destination is absent
    When the user quotes Ana
    Then the advisor quote starts for Ana
