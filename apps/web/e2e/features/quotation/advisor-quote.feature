@quotation @HU-10 @SOLV-103
Feature: Advisor quote

  Scenario: Request and view an offer
    Given the catalog of a line of business
    When the asesor sends the product and the minimum risk data
    Then the asesor gets a quote id and sees the firm offer
    And consulting it again by id does not recalculate

  Scenario: Invalid risk data
    Given the asesor capturing a SOAT motorcycle quote
    When the asesor types an engine size out of the allowed range
    Then the field is marked as an error with the valid range
    And the "Calcular prima" button is disabled
    And the offer panel shows "Sin oferta" without losing the captured data
