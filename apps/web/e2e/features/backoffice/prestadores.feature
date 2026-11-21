@prestadores @backoffice
Feature: Operator provider catalog

  Scenario: The operator creates, edits, deactivates and reactivates
    Given the operator catalog lists the Chapinero workshop
    And an operador signed in to the back-office
    When the operator opens the provider catalog
    Then the provider catalog shows the city counts
    When the operator creates, edits, deactivates and reactivates a provider
    Then the provider is active again
    And the current page has no accessibility violations

  Scenario: Chía with climate and flights is an empty filter
    Given the operator catalog lists the Chapinero workshop
    And an operador signed in to the back-office
    When the operator opens the provider catalog
    And the operator filters providers in Chía for climate and flights
    Then the provider catalog explains the empty filter
    And the current page has no accessibility violations
    When the operator clears the provider filters
    Then the provider catalog shows the city counts

  Scenario: The advisor cannot change the catalog
    Given the operator catalog lists the Chapinero workshop
    And an asesor signed in to the back-office
    When the operator opens the provider catalog
    Then the advisor cannot create or deactivate a provider

  Scenario: Operator filters by country
    Given the operator catalog lists the Chapinero workshop and a Santiago point
    And an operador signed in to the back-office
    When the operator opens the provider catalog
    And the operator filters providers by the country "CL"
    Then the city filter offers "Santiago, Valparaíso, Concepción"
    And the provider catalog lists only the Santiago point with the Chilean counts

  Scenario: Form cities follow the country
    Given the operator catalog lists the Chapinero workshop
    And an operador signed in to the back-office
    When the operator opens a new provider form
    Then the form cities are "Bogotá, Medellín, Chía"
    And the current page has no accessibility violations
    When the operator picks the country "MX" in the form
    Then the form cities are "Ciudad de México, Guadalajara, Monterrey"
