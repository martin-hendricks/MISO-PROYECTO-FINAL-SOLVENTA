Feature: Advisor quote
  Scenario: The advisor prices a device and sees the firm offer
    Given an asesor signed in to the back-office
    When the user opens the cotizaciones destination
    And the advisor starts a new quote
    And the advisor fills the quote for a device worth 1200000
    And the advisor calculates the premium
    Then the firm offer shows the premium "$89.000 COP"
    And the advisor can continue to issuance

  Scenario: Asking again does not price the quote again
    Given an asesor signed in to the back-office
    When the user opens the cotizaciones destination
    And the advisor starts a new quote
    And the advisor fills the quote for a device worth 1200000
    And the advisor calculates the premium
    And the advisor calculates the premium
    Then the firm offer shows the premium "$89.000 COP"
    And the quote was priced 1 time and read by id 1 time

  Scenario: An invalid insured value is solved in the same view
    Given an asesor signed in to the back-office
    When the user opens the cotizaciones destination
    And the advisor starts a new quote
    And the advisor fills the quote for a device worth 0
    Then the insured value shows its valid range
    And the premium cannot be calculated
    And the offer panel says there is no offer
    And the quote keeps the captured client
