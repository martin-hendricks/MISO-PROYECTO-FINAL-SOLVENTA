@quotation @pendiente @HU-58 @SOLV-151
Feature: Advisor mortgage offer

  Scenario: Same internal offer
    Given a profile built by Solventa
    When the mortgage asesor opens the offer in the portal
    Then the asesor sees premium and internal factors without leaving the flow
    And if the stub failed the asesor sees the fallback value
    And this view is not the customer Vida Crediticia card
