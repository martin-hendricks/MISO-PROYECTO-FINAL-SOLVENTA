@prestadores
Feature: Providers near a claim

  Scenario: Geotagged claim fixes the ramo and labels the distance
    Given a geotagged claim with providers
    When the customer opens providers for "sin-1988"
    Then the claim providers are fixed to the event

  Scenario: A claim without a geotag offers near me
    Given a claim without a geotag
    When the customer opens providers for "sin-vacio"
    Then the claim offers to use the customer location
    When the customer uses their location from the claim
    Then the providers switch to near me

  Scenario: Another customer's claim is not found
    Given another customer's claim
    When the customer opens providers for "ajeno"
    Then the claim providers are not found
