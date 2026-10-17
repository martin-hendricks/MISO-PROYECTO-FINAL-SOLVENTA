@subscription @pendiente @HU-19 @SOLV-112
Feature: Advisor assisted issuance

  Scenario: Core states
    Given a valid unused offer
    When the asesor accepts, signs and issues it
    Then the screen shows the real core states
    And it does not show "emitida" if the core rejected it

  Scenario: The core rejects the subscription
    Given a valid offer outside the risk appetite
    When the asesor sends the issuance request
    Then the Emisión step of the stepper is marked as an error
    And the decision badge shows Rechazada with the reason
    And no policy is issued nor shown as issued
    And the asesor can quote another product without capturing the customer data again
