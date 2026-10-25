@quotation @HU-113 @SOLV-237
Feature: View offer

  Scenario: Firm price
    Given a valid quote id
    When the customer opens the offer
    Then the customer sees premium, currency and expiry
    And consulting it again does not recalculate
    And "Aceptar" starts the issuance
