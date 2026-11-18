@prestadores
Feature: Customer provider map

  Scenario: Near me with a stubbed location
    Given providers near the customer
    When the customer opens providers near me
    Then the provider list shows the nearest workshop and its distance
    And the provider list is shown without a map

  Scenario: Blocked location offers cities and hides distances
    Given providers near the customer
    When the customer opens providers without location
    Then the provider list has no distances and offers the cities

  Scenario: Missing map key keeps the list
    Given providers near the customer
    When the customer opens providers near me
    Then the provider list is shown without a map
