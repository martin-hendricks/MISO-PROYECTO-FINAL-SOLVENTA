@customer-portal @HU-109 @SOLV-233
Feature: Customer home

  Scenario: Cards by customer state
    Given the customer is signed in
    When the customer opens Inicio
    Then the customer sees the valid offer card when a quote can be consulted again
    And the customer sees a shortcut to the policy detail when there is a valid policy
    And the customer sees a shortcut to the open claim when there is one
    And the customer sees the Vida Crediticia card when there is an origination

  Scenario: The quote CTA does not replace Accept
    Given a valid offer on Inicio
    Then "Nueva cotización" is below "Aceptar oferta"
    And accepting starts the issuance, not a recalculation
