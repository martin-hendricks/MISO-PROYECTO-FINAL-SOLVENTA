@backoffice
Feature: Partner registry in the back-office

  Scenario Outline: The <role> lists the partners and sees a new key only once
    Given the BFF lists the partner "Aliado local"
    And an <role> signed in to the back-office
    When the user opens the socios destination
    Then the partner "Aliado local" is listed
    When the user creates the partner "Nuevo aliado" with the scope catalogo:leer
    Then the new API key is shown
    And the current page has no accessibility violations
    And the partner "Nuevo aliado" is listed
    When the user dismisses the API key
    Then the API key is no longer shown

    Examples:
      | role     |
      | asesor   |
      | operador |
