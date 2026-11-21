@prestadores
Feature: Customer provider map

  Scenario: Near me with a stubbed location
    Given providers near the customer
    When the customer opens providers near me
    Then the provider list shows the nearest workshop and its distance
    And the provider list is shown without a map

  Scenario: Blocked location offers the catalog cities and hides distances
    Given providers near the customer
    When the customer opens providers without location
    Then the provider list has no distances and offers the cities

  Scenario: Blocked location in es-MX offers Mexican cities
    Given providers in Mexico for a customer using es-MX
    When the customer opens providers without location
    Then the Mexican cities are offered with Ciudad de México marked
    And the five Mexico City providers are listed without distances
    When the customer picks the city "Guadalajara"
    Then the four Guadalajara providers are listed

  Scenario: Missing map key keeps the list
    Given providers near the customer
    When the customer opens providers near me
    Then the provider list is shown without a map
